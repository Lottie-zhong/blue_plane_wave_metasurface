from __future__ import annotations

from pathlib import Path
import csv
import copy
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

P187_PLAN = ROOT / "outputs/apcd_k6_active_learning/p187_fixed_height_platform_scan_plan.csv"
P188_PLAN = ROOT / "outputs/apcd_k6_active_learning/p188_h320_lateral_compensation_scout_plan.csv"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p189_h320_rotation_scout_plan.csv"
REPORT = ROOT / "reports/p189_h320_rotation_scout_plan.md"

FIXED_H = 320

BASES = {
    # robust -180 anchors
    "m180_base": ("p187", "p187_fh320_m180_from_cpk_resphase_scale104_nohelper_01"),
    "m180_bestlw": ("p188", "p188_h320_m180_p2W_p4"),

    # 60 recovery bases
    "p060_base": ("p187", "p187_fh320_p060_from_aggr_lhs_retention_dy_05"),
    "p060_scale098": ("p188", "p188_h320_p060_scale098"),
    "p060_p2Wm4": ("p188", "p188_h320_p060_p2W_m4"),
}

VARIANTS = [
    # Target -120 from robust -180 branch.
    # PB intuition: common rotation can shift target-channel global phase.
    ("m120", "m180_base", "crot_p20", "common rotation +20 deg: move -180 branch toward -120", [{"target": "all_core", "delta": 20.0}]),
    ("m120", "m180_base", "crot_p25", "common rotation +25 deg", [{"target": "all_core", "delta": 25.0}]),
    ("m120", "m180_base", "crot_p30", "common rotation +30 deg", [{"target": "all_core", "delta": 30.0}]),
    ("m120", "m180_base", "crot_p35", "common rotation +35 deg", [{"target": "all_core", "delta": 35.0}]),
    ("m120", "m180_base", "crot_p40", "common rotation +40 deg", [{"target": "all_core", "delta": 40.0}]),

    ("m120", "m180_bestlw", "bestlw_crot_p20", "best L/W -180 anchor + common rot +20", [{"target": "all_core", "delta": 20.0}]),
    ("m120", "m180_bestlw", "bestlw_crot_p25", "best L/W -180 anchor + common rot +25", [{"target": "all_core", "delta": 25.0}]),
    ("m120", "m180_bestlw", "bestlw_crot_p30", "best L/W -180 anchor + common rot +30", [{"target": "all_core", "delta": 30.0}]),

    # Target 60 recovery from h320 p060 branch.
    # Try modest common rotation downward and relative rotation recovery.
    ("p060", "p060_base", "crot_m5", "baseline 120-ish p060 branch, common rot -5", [{"target": "all_core", "delta": -5.0}]),
    ("p060", "p060_base", "crot_m10", "baseline p060 branch, common rot -10", [{"target": "all_core", "delta": -10.0}]),
    ("p060", "p060_base", "crot_m15", "baseline p060 branch, common rot -15", [{"target": "all_core", "delta": -15.0}]),

    ("p060", "p060_scale098", "crot_m2p5", "near-boundary scale098, common rot -2.5", [{"target": "all_core", "delta": -2.5}]),
    ("p060", "p060_scale098", "crot_m5", "near-boundary scale098, common rot -5", [{"target": "all_core", "delta": -5.0}]),
    ("p060", "p060_scale098", "rel_p1m2p5_p2p2p5", "relative rotation recovery A", [
        {"target": "p1", "delta": -2.5},
        {"target": "p2", "delta": 2.5},
    ]),
    ("p060", "p060_scale098", "rel_p1p2p5_p2m2p5", "relative rotation recovery B", [
        {"target": "p1", "delta": 2.5},
        {"target": "p2", "delta": -2.5},
    ]),

    ("p060", "p060_p2Wm4", "crot_m5", "p2W_m4 borderline leakage, common rot -5", [{"target": "all_core", "delta": -5.0}]),
    ("p060", "p060_p2Wm4", "rel_p1m2p5_p2p2p5", "p2W_m4 relative recovery A", [
        {"target": "p1", "delta": -2.5},
        {"target": "p2", "delta": 2.5},
    ]),
    ("p060", "p060_p2Wm4", "rel_p1p2p5_p2m2p5", "p2W_m4 relative recovery B", [
        {"target": "p1", "delta": 2.5},
        {"target": "p2", "delta": -2.5},
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


def is_geometry_path(path: str) -> bool:
    p = path.lower()
    tokens = [
        "geometry", "pillar", "nanopillar", "helper", "atom",
        "rect", "ellipse", "dimer", "meta", "p1", "p2"
    ]
    return any(t in p for t in tokens)


def is_rotation_key(key: str, path: str) -> bool:
    k = key.lower()
    p = path.lower()
    return (
        "rotation" in k
        or k in {"rot_deg", "theta_deg", "angle_deg"}
        or k.endswith("_rot_deg")
        or ("rot" in k and is_geometry_path(p))
    )


def pillar_tag(full_path: str) -> str:
    p = full_path.lower()

    if "helper" in p or "aux" in p:
        return "helper"

    p1_patterns = [
        "p1", "pillar1", "pillar_1", "nanopillar1", "nanopillar_1",
        "atom1", "atom_1", "rect1", "rect_1", "fin1", "fin_1"
    ]
    p2_patterns = [
        "p2", "pillar2", "pillar_2", "nanopillar2", "nanopillar_2",
        "atom2", "atom_2", "rect2", "rect_2", "fin2", "fin_2"
    ]

    if any(x in p for x in p1_patterns):
        return "p1"
    if any(x in p for x in p2_patterns):
        return "p2"

    return ""


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


def rotation_fields(data: dict):
    out = []
    for parent, key, path, obj, value in iter_numeric_fields(data):
        if not is_geometry_path(path):
            continue
        if not is_rotation_key(key, path):
            continue
        out.append({
            "parent": parent,
            "key": key,
            "path": path,
            "obj": obj,
            "value": value,
            "tag": pillar_tag(path),
        })
    return out


def fallback_parent_groups(fields):
    groups = {}
    for f in fields:
        if f["tag"] == "helper":
            continue
        groups.setdefault(f["parent"], []).append(f)

    parents = sorted(groups.keys(), key=lambda x: ("helper" in x.lower(), x.lower()))
    return [groups[p] for p in parents]


def select_rotation_fields(data: dict, target: str):
    fields = rotation_fields(data)

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

    raise ValueError(f"Unknown rotation target={target}")


def apply_rotation_ops(data: dict, ops: list[dict]) -> list[str]:
    changed = []

    for op in ops:
        fields = select_rotation_fields(data, target=op["target"])
        if not fields:
            available = [f["path"] for f in rotation_fields(data)]
            raise RuntimeError(f"No rotation fields selected for op={op}. Available={available}")

        delta = float(op["delta"])
        for f in fields:
            old = float(f["obj"][f["key"]])
            new = old + delta
            f["obj"][f["key"]] = float(round(new, 6))
            changed.append(f"{f['path']}:{old}->{new}")

    return changed


def update_result_dir(data: dict, candidate_id: str) -> None:
    data.setdefault("output", {})
    data["output"]["result_dir"] = (
        f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"
    )


def main() -> int:
    p187 = {r["candidate_id"]: r for r in load_csv(P187_PLAN)}
    p188 = {r["candidate_id"]: r for r in load_csv(P188_PLAN)}

    rows = []

    for target_branch, base_key, variant_id, purpose, ops in VARIANTS:
        source_plan, base_id = BASES[base_key]

        if source_plan == "p187":
            base_row = p187[base_id]
        elif source_plan == "p188":
            base_row = p188[base_id]
        else:
            raise RuntimeError(source_plan)

        base_config_rel = base_row["config_path"]
        base_config_path = ROOT / base_config_rel

        with open(base_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        set_all_heights(cfg, FIXED_H)
        changed = apply_rotation_ops(cfg, ops)
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p189_h320_{target_branch}_{base_key}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p189_h320_rotation_scout"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p189_rotation_only"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p189_target_branch"] = target_branch
        cfg["metadata"]["p189_base_key"] = base_key
        cfg["metadata"]["p189_base_candidate_id"] = base_id
        cfg["metadata"]["p189_variant_id"] = variant_id
        cfg["metadata"]["p189_purpose"] = purpose
        cfg["metadata"]["p189_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p189_ops"] = ops
        cfg["metadata"]["p189_changed_fields"] = changed[:50]

        update_result_dir(cfg, candidate_id)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "target_branch": target_branch,
            "base_key": base_key,
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
        "# P189 h320 rotation scout plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Rotation scout only.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "- No Micro-LED claim.",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Candidate queue",
        "",
        "| target | base | variant | candidate | changed fields | purpose |",
        "|---|---|---|---|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['target_branch']} | {r['base_key']} | {r['variant_id']} | "
            f"`{r['candidate_id']}` | {r['changed_field_count']} | {r['purpose']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
