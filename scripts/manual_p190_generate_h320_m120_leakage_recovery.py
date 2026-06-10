from __future__ import annotations

from pathlib import Path
import csv
import copy
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]

P189_PLAN = ROOT / "outputs/apcd_k6_active_learning/p189_h320_rotation_scout_plan.csv"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"

OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p190_h320_m120_leakage_recovery_plan.csv"
REPORT = ROOT / "reports/p190_h320_m120_leakage_recovery_plan.md"

FIXED_H = 320

BASE_IDS = {
    "crot_p20": "p189_h320_m120_m180_base_crot_p20",
    "crot_p25": "p189_h320_m120_m180_base_crot_p25",
    "crot_p30": "p189_h320_m120_m180_base_crot_p30",
}

VARIANTS = [
    # Best near-threshold: c30, phase already -120, ratio ~5.45
    ("crot_p30", "p2W_p2", "reduce leakage by p2 width +2", [{"target": "p2", "kind": "width", "delta": 2.0}]),
    ("crot_p30", "p2W_p4", "reduce leakage by p2 width +4", [{"target": "p2", "kind": "width", "delta": 4.0}]),
    ("crot_p30", "p2L_p2", "p2 length +2", [{"target": "p2", "kind": "length", "delta": 2.0}]),
    ("crot_p30", "p2L_p4", "p2 length +4", [{"target": "p2", "kind": "length", "delta": 4.0}]),
    ("crot_p30", "p1W_m2_p2W_p2", "width contrast compensation", [
        {"target": "p1", "kind": "width", "delta": -2.0},
        {"target": "p2", "kind": "width", "delta": 2.0},
    ]),
    ("crot_p30", "p1L_m2_p2L_p2", "length contrast compensation", [
        {"target": "p1", "kind": "length", "delta": -2.0},
        {"target": "p2", "kind": "length", "delta": 2.0},
    ]),

    # c25: deeper in -120 phase window but weaker ratio
    ("crot_p25", "p2W_p2", "c25 p2 width +2", [{"target": "p2", "kind": "width", "delta": 2.0}]),
    ("crot_p25", "p2W_p4", "c25 p2 width +4", [{"target": "p2", "kind": "width", "delta": 4.0}]),
    ("crot_p25", "p2L_p2", "c25 p2 length +2", [{"target": "p2", "kind": "length", "delta": 2.0}]),
    ("crot_p25", "p1W_m2_p2W_p2", "c25 width contrast compensation", [
        {"target": "p1", "kind": "width", "delta": -2.0},
        {"target": "p2", "kind": "width", "delta": 2.0},
    ]),

    # c20: best ratio but still -180; small geometry push may move it into -120
    ("crot_p20", "p2L_p4", "c20 push phase toward -120 with p2 length +4", [{"target": "p2", "kind": "length", "delta": 4.0}]),
    ("crot_p20", "p2W_p4", "c20 selectivity recovery with p2 width +4", [{"target": "p2", "kind": "width", "delta": 4.0}]),
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


def set_all_heights(data: dict, h: int) -> None:
    owners = height_owners(data)
    if not owners:
        raise RuntimeError("No height_nm found.")
    for obj in owners:
        obj["height_nm"] = float(h)


def is_geometry_path(path: str) -> bool:
    p = path.lower()
    return any(t in p for t in [
        "geometry", "pillar", "nanopillar", "helper", "atom",
        "rect", "ellipse", "dimer", "meta", "p1", "p2"
    ])


def is_length_key(k: str, path: str) -> bool:
    s = k.lower()
    p = path.lower()
    return (
        "length" in s or "long_axis" in s or "major_axis" in s
        or s in {"l_nm", "len_nm"}
        or ("x_span" in s and is_geometry_path(p))
    )


def is_width_key(k: str, path: str) -> bool:
    s = k.lower()
    p = path.lower()
    return (
        "width" in s or "short_axis" in s or "minor_axis" in s
        or s in {"w_nm"}
        or ("y_span" in s and is_geometry_path(p))
    )


def pillar_tag(path: str) -> str:
    p = path.lower()
    if "helper" in p or "aux" in p:
        return "helper"

    p1_patterns = ["p1", "pillar1", "pillar_1", "nanopillar1", "nanopillar_1", "atom1", "atom_1", "rect1", "rect_1"]
    p2_patterns = ["p2", "pillar2", "pillar_2", "nanopillar2", "nanopillar_2", "atom2", "atom_2", "rect2", "rect_2"]

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


def lateral_fields(data: dict, kind: str):
    out = []
    for parent, key, path, obj, value in iter_numeric_fields(data):
        if not is_geometry_path(path):
            continue
        if kind == "length" and not is_length_key(key, path):
            continue
        if kind == "width" and not is_width_key(key, path):
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
    parents = sorted(groups.keys(), key=lambda x: x.lower())
    return [groups[p] for p in parents]


def select_fields(data: dict, target: str, kind: str):
    fields = lateral_fields(data, kind=kind)

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

    raise ValueError(f"Unknown target={target}")


def apply_ops(data: dict, ops: list[dict]) -> list[str]:
    changed = []

    for op in ops:
        fields = select_fields(data, op["target"], op["kind"])
        if not fields:
            raise RuntimeError(f"No selected fields for op={op}")

        for f in fields:
            old = float(f["obj"][f["key"]])
            new = old + float(op["delta"])

            if new <= 20 or new >= 300:
                raise RuntimeError(f"Unphysical new value {new} at {f['path']}")

            f["obj"][f["key"]] = float(round(new, 6))
            changed.append(f"{f['path']}:{old}->{new}")

    return changed


def update_result_dir(data: dict, candidate_id: str) -> None:
    data.setdefault("output", {})
    data["output"]["result_dir"] = (
        f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"
    )


def main() -> int:
    p189 = {r["candidate_id"]: r for r in load_csv(P189_PLAN)}
    rows = []

    for base_key, variant_id, purpose, ops in VARIANTS:
        base_id = BASE_IDS[base_key]

        if base_id not in p189:
            raise RuntimeError(f"Missing P189 base candidate in plan: {base_id}")

        base_config_rel = p189[base_id]["config_path"]
        base_config_path = ROOT / base_config_rel

        with open(base_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        set_all_heights(cfg, FIXED_H)
        changed = apply_ops(cfg, ops)
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p190_h320_m120_{base_key}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p190_h320_m120_leakage_recovery"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p190_m120_leakage_recovery"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p190_base_key"] = base_key
        cfg["metadata"]["p190_base_candidate_id"] = base_id
        cfg["metadata"]["p190_variant_id"] = variant_id
        cfg["metadata"]["p190_purpose"] = purpose
        cfg["metadata"]["p190_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p190_ops"] = ops
        cfg["metadata"]["p190_changed_fields"] = changed[:50]

        update_result_dir(cfg, candidate_id)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
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
        "# P190 h320 m120 leakage recovery plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: recover early-pass -120 from P189 rotation phase hits.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Candidate queue",
        "",
        "| base | variant | candidate | changed fields | purpose |",
        "|---|---|---|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['base_key']} | {r['variant_id']} | `{r['candidate_id']}` | "
            f"{r['changed_field_count']} | {r['purpose']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
