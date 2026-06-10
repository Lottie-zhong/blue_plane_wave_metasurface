from __future__ import annotations

from pathlib import Path
import csv
import copy
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

LIB = ROOT / "outputs/apcd_k6_active_learning/p179_stage10_frozen_phase_library.csv"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"

OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p187_fixed_height_platform_scan_plan.csv"
REPORT = ROOT / "reports/p187_fixed_height_platform_scan_plan.md"

HEIGHTS = [240, 260, 280, 320, 350, 375, 400]

SOURCE_CANDIDATES = {
    -180: "cpk_resphase_scale104_nohelper_01",
    0: "cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01",
    60: "aggr_lhs_retention_dy_05",
}

BIN_LABELS = {
    -180: "m180",
    0: "p000",
    60: "p060",
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


def height_owners(data: dict) -> list[dict]:
    out = []

    def walk(obj):
        if isinstance(obj, dict):
            if "height_nm" in obj:
                out.append(obj)
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(data)
    return out


def set_all_heights(data: dict, h: int) -> int:
    owners = height_owners(data)
    if not owners:
        raise RuntimeError("No height_nm found")
    for obj in owners:
        obj["height_nm"] = float(h)
    return len(owners)


def get_heights(data: dict) -> list[float]:
    return sorted({float(obj["height_nm"]) for obj in height_owners(data)})


def update_result_dir(data: dict, candidate_id: str) -> None:
    data.setdefault("output", {})
    data["output"]["result_dir"] = (
        f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"
    )


def main() -> int:
    lib = load_csv(LIB)

    by_candidate = {r["candidate_id"]: r for r in lib}

    rows = []

    for source_bin, source_id in SOURCE_CANDIDATES.items():
        if source_id not in by_candidate:
            raise RuntimeError(f"Missing source candidate in P179 library: {source_id}")

        source_row = by_candidate[source_id]
        source_config_rel = source_row["config_path"]
        source_path = ROOT / source_config_rel

        with open(source_path, "r", encoding="utf-8") as f:
            source_cfg = yaml.safe_load(f)

        source_heights = get_heights(source_cfg)

        for h in HEIGHTS:
            cfg = copy.deepcopy(source_cfg)
            height_field_count = set_all_heights(cfg, h)
            heights_after = get_heights(cfg)

            if heights_after != [float(h)]:
                raise RuntimeError(f"Failed to enforce h={h} for {source_id}: {heights_after}")

            bin_label = BIN_LABELS[source_bin]
            candidate_id = sanitize(f"p187_fh{h}_{bin_label}_from_{source_id}")
            config_path = CONFIG_DIR / f"{candidate_id}.yaml"

            cfg.setdefault("project", {})
            cfg["project"]["stage"] = "p187_fixed_height_platform_scan"

            cfg.setdefault("boundary", {})
            cfg["boundary"]["fixed_height_platform_scan"] = True
            cfg["boundary"]["fabrication_aware_same_height"] = True
            cfg["boundary"]["not_k6_supercell"] = True
            cfg["boundary"]["not_steering_result"] = True
            cfg["boundary"]["not_micro_led_result"] = True

            cfg.setdefault("metadata", {})
            cfg["metadata"]["p187_source_candidate_id"] = source_id
            cfg["metadata"]["p187_source_bin_deg"] = source_bin
            cfg["metadata"]["p187_fixed_height_nm"] = h
            cfg["metadata"]["p187_note"] = (
                "Fixed-height platform scan from robust P185/P186B source families. "
                "All height_nm fields are globally fixed; lateral geometry is preserved."
            )

            update_result_dir(cfg, candidate_id)
            dump_yaml(cfg, config_path)

            rows.append({
                "candidate_id": candidate_id,
                "fixed_height_nm": h,
                "source_bin_deg": source_bin,
                "source_candidate_id": source_id,
                "source_config_path": source_config_rel,
                "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
                "source_unique_heights_nm": ";".join(str(x) for x in source_heights),
                "candidate_unique_heights_nm": ";".join(str(x) for x in heights_after),
                "height_field_count": height_field_count,
            })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P187 fixed-height platform scan plan",
        "",
        "## Scope",
        "",
        "- Single-dimer fixed-height platform scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "- No Micro-LED claim.",
        "",
        "## Heights",
        "",
        ", ".join(str(h) for h in HEIGHTS),
        "",
        "## Source families",
        "",
        "| source bin | source candidate | role |",
        "|---:|---|---|",
        "| -180 | `cpk_resphase_scale104_nohelper_01` | h300 opened 120 with strong selectivity |",
        "| 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | reliable h232 0 anchor |",
        "| 60 | `aggr_lhs_retention_dy_05` | reliable 60 plateau |",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Queue",
        "",
        "| h | source bin | candidate |",
        "|---:|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['fixed_height_nm']} | {r['source_bin_deg']} | `{r['candidate_id']}` |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
