from __future__ import annotations

from pathlib import Path
import csv
import copy
import math
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

LIB = ROOT / "outputs/apcd_k6_active_learning/p179_stage10_frozen_phase_library.csv"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p185_fixed_height_projection_candidate_plan.csv"
OUT_SELECTION = ROOT / "outputs/apcd_k6_active_learning/p185_fixed_height_projection_fdtd_selection.csv"
REPORT = ROOT / "reports/p185_fixed_height_phase_library_projection_plan.md"

FIXED_HEIGHTS = [232, 300, 425]

# First diagnostic queue: 3 candidates per height.
# h232: zero-friendly height
# h300: legacy-60-friendly height
# h425: negative-bin reference height
SELECTION_BINS = {
    232: [0, 60, -60],
    300: [0, 60, 120],
    425: [-180, -120, -60],
}

BIN_LABELS = {
    -180: "m180",
    -120: "m120",
    -60: "m060",
    0: "p000",
    60: "p060",
    120: "p120",
}


def sanitize(s: str) -> str:
    s = re.sub(r"[^A-Za-z0-9_]+", "_", s)
    return re.sub(r"_+", "_", s).strip("_")


def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def dump_yaml(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)




def height_dicts(data: dict) -> list[tuple[str, dict]]:
    """Recursively collect every dictionary that owns a height_nm field.

    This is intentionally broad for P185 projection:
    fixed-height fabrication means every height_nm in the single-dimer YAML
    should be set to the same global height.
    """
    out: list[tuple[str, dict]] = []

    def walk(obj, prefix: str = "") -> None:
        if isinstance(obj, dict):
            if "height_nm" in obj:
                out.append((prefix or "height_owner", obj))
            for key, value in obj.items():
                walk(value, f"{prefix}.{key}" if prefix else str(key))
        elif isinstance(obj, list):
            for i, value in enumerate(obj):
                walk(value, f"{prefix}[{i}]")

    walk(data)
    return out


def pillar_dicts(data: dict) -> list[tuple[str, dict]]:
    """Collect height_nm owners that look like physical pillars/helpers."""
    out = []
    for name, p in height_dicts(data):
        has_lateral = (
            ("length_nm" in p and "width_nm" in p)
            or ("x_span_nm" in p and "y_span_nm" in p)
            or ("diameter_nm" in p)
        )
        if has_lateral:
            out.append((name, p))
    return out


def set_all_heights(data: dict, fixed_h: float) -> int:
    count = 0
    for _, p in height_dicts(data):
        p["height_nm"] = float(fixed_h)
        count += 1
    if count == 0:
        raise RuntimeError("No height_nm fields found anywhere in YAML.")
    return count


def get_heights(data: dict) -> list[float]:
    return sorted({float(p["height_nm"]) for _, p in height_dicts(data)})


def bbox_half(length_nm: float, width_nm: float, rot_deg: float) -> tuple[float, float]:
    t = math.radians(rot_deg)
    hx = abs(math.cos(t)) * length_nm / 2 + abs(math.sin(t)) * width_nm / 2
    hy = abs(math.sin(t)) * length_nm / 2 + abs(math.cos(t)) * width_nm / 2
    return hx, hy


def approximate_min_gap_nm(data: dict) -> float:
    ps = []
    for name, p in pillar_dicts(data):
        x = float(p.get("x_nm", p.get("center_x_nm", 0.0)))
        y = float(p.get("y_nm", p.get("center_y_nm", 0.0)))
        L = float(p.get("length_nm", p.get("x_span_nm", 0.0)))
        W = float(p.get("width_nm", p.get("y_span_nm", 0.0)))
        rot = float(p.get("rotation_deg", 0.0))
        hx, hy = bbox_half(L, W, rot)
        ps.append((name, x, y, hx, hy))

    if len(ps) < 2:
        return 999.0

    gaps = []
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            _, x1, y1, hx1, hy1 = ps[i]
            _, x2, y2, hx2, hy2 = ps[j]
            dx = abs(x1 - x2) - (hx1 + hx2)
            dy = abs(y1 - y2) - (hy1 + hy2)
            if dx >= 0 and dy >= 0:
                gap = math.hypot(dx, dy)
            else:
                gap = max(dx, dy)
            gaps.append(gap)
    return min(gaps)


def update_result_dir(data: dict, candidate_id: str) -> None:
    data.setdefault("output", {})
    data["output"]["result_dir"] = (
        f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"
    )


def main() -> int:
    lib = load_csv(LIB)

    plan_rows = []
    generated = {}

    for row in lib:
        source_bin = int(float(row["bin_deg"]))
        source_id = row["candidate_id"]
        source_config_rel = row.get("config_path") or row.get("source_config_path")
        if not source_config_rel:
            raise RuntimeError(f"No config_path for {source_id}")

        source_path = ROOT / source_config_rel
        if not source_path.exists():
            raise FileNotFoundError(source_path)

        with open(source_path, "r", encoding="utf-8") as f:
            source_cfg = yaml.safe_load(f)

        source_heights = get_heights(source_cfg)

        for fixed_h in FIXED_HEIGHTS:
            cfg = copy.deepcopy(source_cfg)
            pillar_count = set_all_heights(cfg, fixed_h)
            heights_after = get_heights(cfg)

            if heights_after != [float(fixed_h)]:
                raise RuntimeError(f"height enforcement failed for {source_id} at h={fixed_h}")

            bin_label = BIN_LABELS[source_bin]
            candidate_id = sanitize(f"p185_fh{fixed_h}_{bin_label}_from_{source_id}")
            out_path = CONFIG_DIR / f"{candidate_id}.yaml"

            cfg.setdefault("project", {})
            cfg["project"]["stage"] = "p185_fixed_height_phase_library_projection"
            cfg.setdefault("boundary", {})
            cfg["boundary"]["fixed_height_projection"] = True
            cfg["boundary"]["fabrication_aware_same_height"] = True
            cfg["boundary"]["not_k6_supercell"] = True
            cfg["boundary"]["not_steering_result"] = True
            cfg["boundary"]["not_micro_led_result"] = True

            cfg.setdefault("metadata", {})
            cfg["metadata"]["p185_source_candidate_id"] = source_id
            cfg["metadata"]["p185_source_target_bin_deg"] = source_bin
            cfg["metadata"]["p185_fixed_height_nm"] = fixed_h
            cfg["metadata"]["p185_source_config_path"] = source_config_rel
            cfg["metadata"]["p185_note"] = (
                "Projection from mixed-height frozen library to a globally fixed-height "
                "single-dimer candidate. Lateral geometry is preserved in this first diagnostic pass."
            )

            update_result_dir(cfg, candidate_id)
            dump_yaml(cfg, out_path)

            min_gap = approximate_min_gap_nm(cfg)
            is_selected = fixed_h in SELECTION_BINS and source_bin in SELECTION_BINS[fixed_h]

            plan_row = {
                "candidate_id": candidate_id,
                "fixed_height_nm": fixed_h,
                "source_target_bin_deg": source_bin,
                "source_candidate_id": source_id,
                "source_config_path": source_config_rel,
                "config_path": str(out_path.relative_to(ROOT)).replace("\\", "/"),
                "source_unique_heights_nm": ";".join(str(h) for h in source_heights),
                "candidate_unique_heights_nm": ";".join(str(h) for h in heights_after),
                "pillar_count": pillar_count,
                "approx_min_gap_nm": f"{min_gap:.6f}",
                "integer_height": fixed_h == int(fixed_h),
                "same_height_enforced": heights_after == [float(fixed_h)],
                "selected_for_fdtd": is_selected,
                "selection_reason": (
                    f"diagnostic_{fixed_h}_for_bin_{source_bin}" if is_selected else ""
                ),
            }
            plan_rows.append(plan_row)
            generated[(fixed_h, source_bin)] = plan_row

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(plan_rows[0].keys()))
        writer.writeheader()
        writer.writerows(plan_rows)

    selection_rows = [
        generated[(h, b)]
        for h, bins in SELECTION_BINS.items()
        for b in bins
    ]

    if len(selection_rows) != 9:
        raise RuntimeError(f"Expected 9 selected candidates, got {len(selection_rows)}")

    with open(OUT_SELECTION, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(selection_rows[0].keys()))
        writer.writeheader()
        writer.writerows(selection_rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P185 fixed-height phase-library projection plan",
        "",
        "## Scope",
        "",
        "- Mainline changed to fabrication-aware same-height / fixed-height single-dimer phase library.",
        "- Current mixed-height P179/P181/P183 K=6 result is archived as numerical proof-of-concept only.",
        "- This P185 step does not run K=6, does not claim +15 deg steering, and does not use Micro-LED.",
        "",
        "## Fixed heights",
        "",
        "- h232: zero-bin priority height.",
        "- h300: legacy-60-friendly middle height.",
        "- h425: negative-bin reference height.",
        "",
        "## Generation rule",
        "",
        "- For each frozen six-state source dimer, set every pillar height to the selected fixed height.",
        "- Preserve lateral geometry in this first diagnostic pass.",
        "- Enforce integer nm height and same-height within each candidate.",
        "- No sub-nm height, no multi-height candidate, no K=6 supercell.",
        "",
        f"- generated_candidates: {len(plan_rows)}",
        f"- selected_for_fdtd: {len(selection_rows)}",
        "",
        "## Selected FDTD queue",
        "",
        "| fixed h | source bin | new candidate | source | approx min gap nm |",
        "|---:|---:|---|---|---:|",
    ]

    for r in selection_rows:
        lines.append(
            f"| {r['fixed_height_nm']} | {r['source_target_bin_deg']} | "
            f"`{r['candidate_id']}` | `{r['source_candidate_id']}` | {r['approx_min_gap_nm']} |"
        )

    lines += [
        "",
        "## Decision after FDTD",
        "",
        "- Compare which fixed height keeps the most useful APCD selectivity and phase diversity.",
        "- Do not pick final height before seeing projection results.",
        "- If one height shows phase diversity but leakage failure, use lateral compensation next.",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"selection={OUT_SELECTION}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(plan_rows)}")
    print(f"selected_for_fdtd={len(selection_rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
