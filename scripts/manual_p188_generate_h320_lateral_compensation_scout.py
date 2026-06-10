from __future__ import annotations

from pathlib import Path
import csv
import copy
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

P187_PLAN = ROOT / "outputs/apcd_k6_active_learning/p187_fixed_height_platform_scan_plan.csv"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"

OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p188_h320_lateral_compensation_scout_plan.csv"
REPORT = ROOT / "reports/p188_h320_lateral_compensation_scout_plan.md"

FIXED_H = 320

BASE_IDS = {
    "m180": "p187_fh320_m180_from_cpk_resphase_scale104_nohelper_01",
    "p000": "p187_fh320_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01",
    "p060": "p187_fh320_p060_from_aggr_lhs_retention_dy_05",
}

# First scout: only L/W/aspect. No height, no helper, no gap, no rotation.
VARIANTS = [
    # Pull h320 legacy60 branch from phase~99 toward 60
    ("p060", "scale098", "pull 99deg toward 60 by weakening resonance", [{"mode": "scale", "target": "all_core", "factor": 0.98}]),
    ("p060", "scale096", "stronger pull 99deg toward 60", [{"mode": "scale", "target": "all_core", "factor": 0.96}]),
    ("p060", "p2L_m4", "p2 length down", [{"mode": "delta", "target": "p2", "kind": "length", "delta": -4.0}]),
    ("p060", "p2W_m4", "p2 width down", [{"mode": "delta", "target": "p2", "kind": "width", "delta": -4.0}]),
    ("p060", "p1p2L_m4", "both core lengths down", [{"mode": "delta", "target": "p1p2", "kind": "length", "delta": -4.0}]),
    ("p060", "p2L_m4_W_p2", "p2 length down with width compensation", [
        {"mode": "delta", "target": "p2", "kind": "length", "delta": -4.0},
        {"mode": "delta", "target": "p2", "kind": "width", "delta": 2.0},
    ]),

    # Pull h320 zero-family from phase~104 toward 60/0
    ("p000", "scale096", "pull zero-family 104deg downward", [{"mode": "scale", "target": "all_core", "factor": 0.96}]),
    ("p000", "scale094", "stronger zero-family downward pull", [{"mode": "scale", "target": "all_core", "factor": 0.94}]),
    ("p000", "p2L_m6", "zero-family p2 length down", [{"mode": "delta", "target": "p2", "kind": "length", "delta": -6.0}]),
    ("p000", "p1p2L_m6", "zero-family both lengths down", [{"mode": "delta", "target": "p1p2", "kind": "length", "delta": -6.0}]),
    ("p000", "p1p2W_m4", "zero-family both widths down", [{"mode": "delta", "target": "p1p2", "kind": "width", "delta": -4.0}]),
    ("p000", "p2L_m8_W_p2", "strong p2 length down with width compensation", [
        {"mode": "delta", "target": "p2", "kind": "length", "delta": -8.0},
        {"mode": "delta", "target": "p2", "kind": "width", "delta": 2.0},
    ]),

    # Push h320 -180 branch from phase~161 toward wrapped -120 direction
    ("m180", "scale102", "push -180 branch toward -120", [{"mode": "scale", "target": "all_core", "factor": 1.02}]),
    ("m180", "scale104", "stronger push toward -120", [{"mode": "scale", "target": "all_core", "factor": 1.04}]),
    ("m180", "p2L_p4", "p2 length up", [{"mode": "delta", "target": "p2", "kind": "length", "delta": 4.0}]),
    ("m180", "p2W_p4", "p2 width up", [{"mode": "delta", "target": "p2", "kind": "width", "delta": 4.0}]),
    ("m180", "p1p2L_p4", "both core lengths up", [{"mode": "delta", "target": "p1p2", "kind": "length", "delta": 4.0}]),
    ("m180", "p2L_p6_W_m2", "p2 length up with width compensation", [
        {"mode": "delta", "target": "p2", "kind": "length", "delta": 6.0},
        {"mode": "delta", "target": "p2", "kind": "width", "delta": -2.0},
    ]),
]


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
        raise RuntimeError("No height_nm found.")
    for obj in owners:
        obj["height_nm"] = float(h)
    return len(owners)


def iter_numeric_fields(data: dict):
    def walk(obj, parent_path=""):
        if isinstance(obj, dict):
            for k, v in obj.items():
                path = f"{parent_path}.{k}" if parent_path else str(k)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    yield parent_path, k, path, obj, float(v)
                yield from walk(v, path)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                path = f"{parent_path}[{i}]"
                yield from walk(v, path)
    yield from walk(data)


def is_length_key(k: str, full_path: str) -> bool:
    s = k.lower()
    p = full_path.lower()
    return (
        "length" in s
        or "long_axis" in s
        or "major_axis" in s
        or s in {"l_nm", "len_nm"}
        or ("x_span" in s and is_geometry_path(p))
    )


def is_width_key(k: str, full_path: str) -> bool:
    s = k.lower()
    p = full_path.lower()
    return (
        "width" in s
        or "short_axis" in s
        or "minor_axis" in s
        or s in {"w_nm"}
        or ("y_span" in s and is_geometry_path(p))
    )


def is_geometry_path(path: str) -> bool:
    p = path.lower()
    tokens = [
        "geometry", "pillar", "nanopillar", "helper", "atom",
        "rect", "ellipse", "dimer", "meta", "p1", "p2"
    ]
    return any(t in p for t in tokens)


def pillar_tag(full_path: str) -> str:
    p = full_path.lower()

    p1_patterns = [
        "p1", "pillar1", "pillar_1", "nanopillar1", "nanopillar_1",
        "atom1", "atom_1", "rect1", "rect_1", "fin1", "fin_1"
    ]
    p2_patterns = [
        "p2", "pillar2", "pillar_2", "nanopillar2", "nanopillar_2",
        "atom2", "atom_2", "rect2", "rect_2", "fin2", "fin_2"
    ]

    if "helper" in p or "aux" in p:
        return "helper"

    if any(x in p for x in p1_patterns):
        return "p1"
    if any(x in p for x in p2_patterns):
        return "p2"

    return ""


def lateral_fields(data: dict, kind: str | None = None):
    fields = []
    for parent, k, path, obj, value in iter_numeric_fields(data):
        if not is_geometry_path(path):
            continue

        is_len = is_length_key(k, path)
        is_wid = is_width_key(k, path)

        if kind == "length" and not is_len:
            continue
        if kind == "width" and not is_wid:
            continue
        if kind is None and not (is_len or is_wid):
            continue

        fields.append({
            "parent": parent,
            "key": k,
            "path": path,
            "obj": obj,
            "value": value,
            "kind": "length" if is_len else "width",
            "tag": pillar_tag(path),
        })

    return fields


def fallback_parent_groups(fields):
    groups = {}
    for f in fields:
        if f["tag"] == "helper":
            continue
        groups.setdefault(f["parent"], []).append(f)

    parents = sorted(groups.keys(), key=lambda x: ("helper" in x.lower(), x.lower()))
    return [groups[p] for p in parents]


def select_fields(data: dict, target: str, kind: str | None):
    fields = lateral_fields(data, kind=kind)

    if target == "all":
        return fields

    if target == "all_core":
        core = [f for f in fields if f["tag"] != "helper"]
        return core if core else fields

    if target in {"p1", "p2"}:
        tagged = [f for f in fields if f["tag"] == target]
        if tagged:
            return tagged

        groups = fallback_parent_groups(fields)
        if target == "p1" and len(groups) >= 1:
            return groups[0]
        if target == "p2" and len(groups) >= 2:
            return groups[1]
        return []

    if target == "p1p2":
        tagged = [f for f in fields if f["tag"] in {"p1", "p2"}]
        if tagged:
            return tagged

        groups = fallback_parent_groups(fields)
        if len(groups) >= 2:
            return groups[0] + groups[1]
        return []

    raise ValueError(f"Unknown target={target}")


def apply_ops(data: dict, ops: list[dict]) -> list[str]:
    changed = []

    for op in ops:
        mode = op["mode"]
        target = op["target"]
        kind = op.get("kind")

        fields = select_fields(data, target=target, kind=kind)
        if not fields:
            raise RuntimeError(f"No fields selected for op={op}")

        for f in fields:
            old = float(f["obj"][f["key"]])

            if mode == "scale":
                new = old * float(op["factor"])
            elif mode == "delta":
                new = old + float(op["delta"])
            else:
                raise ValueError(f"Unknown mode={mode}")

            if new <= 20 or new >= 300:
                raise RuntimeError(f"Unphysical lateral value {new} at {f['path']} from op={op}")

            f["obj"][f["key"]] = float(round(new, 6))
            changed.append(f"{f['path']}:{old}->{new}")

    return changed


def update_result_dir(data: dict, candidate_id: str) -> None:
    data.setdefault("output", {})
    data["output"]["result_dir"] = (
        f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"
    )


def main() -> int:
    p187 = load_csv(P187_PLAN)
    by_id = {r["candidate_id"]: r for r in p187}

    rows = []

    for branch, variant_id, purpose, ops in VARIANTS:
        base_id = BASE_IDS[branch]
        if base_id not in by_id:
            raise RuntimeError(f"Missing base candidate in P187 plan: {base_id}")

        base_config_rel = by_id[base_id]["config_path"]
        base_config_path = ROOT / base_config_rel

        with open(base_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)

        set_all_heights(cfg, FIXED_H)
        changed = apply_ops(cfg, ops)
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p188_h320_{branch}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p188_h320_lateral_compensation_scout"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p188_lateral_compensation_only"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p188_base_candidate_id"] = base_id
        cfg["metadata"]["p188_branch"] = branch
        cfg["metadata"]["p188_variant_id"] = variant_id
        cfg["metadata"]["p188_purpose"] = purpose
        cfg["metadata"]["p188_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p188_ops"] = ops
        cfg["metadata"]["p188_changed_fields"] = changed[:50]

        update_result_dir(cfg, candidate_id)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "branch": branch,
            "variant_id": variant_id,
            "purpose": purpose,
            "base_candidate_id": base_id,
            "fixed_height_nm": FIXED_H,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "changed_field_count": len(changed),
            "changed_fields_preview": " | ".join(changed[:6]),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P188 h320 lateral compensation scout plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- L/W/aspect compensation only.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "- No Micro-LED claim.",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Candidate queue",
        "",
        "| branch | variant | candidate | changed fields | purpose |",
        "|---|---|---|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['branch']} | {r['variant_id']} | `{r['candidate_id']}` | "
            f"{r['changed_field_count']} | {r['purpose']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
