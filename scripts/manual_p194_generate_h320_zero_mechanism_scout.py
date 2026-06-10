from __future__ import annotations

from pathlib import Path
import csv
import copy
import importlib.util
import yaml

ROOT = Path(__file__).resolve().parents[1]

P187_PLAN = ROOT / "outputs/apcd_k6_active_learning/p187_fixed_height_platform_scan_plan.csv"
P192_HELPER = ROOT / "scripts/manual_p192_generate_h320_p060_nearmiss_refine.py"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p194_h320_zero_mechanism_scout_plan.csv"
REPORT = ROOT / "reports/p194_h320_zero_mechanism_scout_plan.md"

FIXED_H = 320

BASE_ID = "p187_fh320_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01"

# P194 is a mechanism scout:
# success criterion after FDTD is zero phase-hit, not necessarily early-pass.
VARIANTS = [
    # Group A: dynamic phase / aspect compensation from h320 zero-family.
    ("A_dynamic", "p2L_m10_p2W_p4", "strong p2 aspect compensation; seek phase drop toward 0", [
        {"type": "lateral", "target": "p2", "kind": "length", "delta": -10.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 4.0},
    ]),
    ("A_dynamic", "p2L_m15_p2W_p6", "stronger p2 aspect compensation", [
        {"type": "lateral", "target": "p2", "kind": "length", "delta": -15.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 6.0},
    ]),
    ("A_dynamic", "p1L_m5_p2L_m10", "both lengths down, stronger p2", [
        {"type": "lateral", "target": "p1", "kind": "length", "delta": -5.0},
        {"type": "lateral", "target": "p2", "kind": "length", "delta": -10.0},
    ]),
    ("A_dynamic", "p1W_m4_p2W_p4", "width contrast compensation", [
        {"type": "lateral", "target": "p1", "kind": "width", "delta": -4.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 4.0},
    ]),
    ("A_dynamic", "scale090_p2W_p4", "global core scale down with p2 width recovery", [
        {"type": "scale", "target": "all_core", "factor": 0.90},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 4.0},
    ]),

    # Group B: coupling / gap probe.
    # Positive gap_x means increase p1-p2 separation along x; negative means decrease.
    ("B_gap", "gapx_m10", "reduce dimer separation by 10 nm; test hybridized resonance branch", [
        {"type": "gap", "axis": "x", "delta_gap_nm": -10.0},
    ]),
    ("B_gap", "gapx_p10", "increase dimer separation by 10 nm", [
        {"type": "gap", "axis": "x", "delta_gap_nm": 10.0},
    ]),
    ("B_gap", "gapx_m20", "reduce dimer separation by 20 nm", [
        {"type": "gap", "axis": "x", "delta_gap_nm": -20.0},
    ]),
    ("B_gap", "gapx_p20", "increase dimer separation by 20 nm", [
        {"type": "gap", "axis": "x", "delta_gap_nm": 20.0},
    ]),

    # Group C: rotation diagnostic only.
    # This tests whether PB-like shift can reach 0-bin at h320.
    ("C_rotation", "crot_m20", "common rotation -20 deg diagnostic", [
        {"type": "rotation", "target": "all_core", "delta": -20.0},
    ]),
    ("C_rotation", "crot_m30", "common rotation -30 deg diagnostic", [
        {"type": "rotation", "target": "all_core", "delta": -30.0},
    ]),
    ("C_rotation", "crot_m40", "common rotation -40 deg diagnostic", [
        {"type": "rotation", "target": "all_core", "delta": -40.0},
    ]),
]


def import_helper(path: Path):
    spec = importlib.util.spec_from_file_location("p192_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import helper: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def position_key_match(key: str, path: str, axis: str) -> bool:
    k = key.lower()
    p = path.lower()

    if axis == "x":
        candidates = {
            "x", "x_nm", "center_x", "center_x_nm", "x_center", "x_center_nm",
            "pos_x", "pos_x_nm", "position_x", "position_x_nm", "cx", "cx_nm"
        }
    elif axis == "y":
        candidates = {
            "y", "y_nm", "center_y", "center_y_nm", "y_center", "y_center_nm",
            "pos_y", "pos_y_nm", "position_y", "position_y_nm", "cy", "cy_nm"
        }
    else:
        raise ValueError(axis)

    bad_tokens = [
        "span", "size", "length", "width", "radius", "diameter",
        "min", "max", "mesh", "period", "pitch"
    ]

    if any(t in k for t in bad_tokens):
        return False

    if k in candidates:
        return True

    # Conservative fallback: accept names ending in _x_nm or _y_nm in geometry paths.
    if axis == "x" and (k.endswith("_x_nm") or k.endswith("_x")):
        return True
    if axis == "y" and (k.endswith("_y_nm") or k.endswith("_y")):
        return True

    return False


def position_fields(h, data: dict, axis: str):
    out = []
    for parent, key, path, obj, value in h.iter_numeric_fields(data):
        if not h.is_geometry_path(path):
            continue
        if not position_key_match(key, path, axis):
            continue
        out.append({
            "parent": parent,
            "key": key,
            "path": path,
            "obj": obj,
            "value": value,
            "tag": h.pillar_tag(path),
        })
    return out


def select_position_pair(h, data: dict, axis: str):
    fields = position_fields(h, data, axis)

    p1 = [f for f in fields if f["tag"] == "p1"]
    p2 = [f for f in fields if f["tag"] == "p2"]

    if p1 and p2:
        return p1[0], p2[0]

    # Fallback: group by parent and use first two non-helper groups.
    groups = {}
    for f in fields:
        if f["tag"] == "helper":
            continue
        groups.setdefault(f["parent"], []).append(f)

    parents = sorted(groups.keys(), key=lambda x: x.lower())
    if len(parents) >= 2:
        return groups[parents[0]][0], groups[parents[1]][0]

    available = [f["path"] for f in fields]
    raise RuntimeError(f"Cannot identify p1/p2 {axis}-position fields. Available={available}")


def apply_gap_op(h, data: dict, axis: str, delta_gap_nm: float) -> list[str]:
    f1, f2 = select_position_pair(h, data, axis)

    x1 = float(f1["obj"][f1["key"]])
    x2 = float(f2["obj"][f2["key"]])

    # Positive delta_gap increases absolute separation.
    sign = 1.0 if x2 >= x1 else -1.0
    move = float(delta_gap_nm) / 2.0

    new1 = x1 - sign * move
    new2 = x2 + sign * move

    f1["obj"][f1["key"]] = float(round(new1, 6))
    f2["obj"][f2["key"]] = float(round(new2, 6))

    return [
        f"{f1['path']}:{x1}->{new1}",
        f"{f2['path']}:{x2}->{new2}",
    ]


def apply_scale_op(h, data: dict, target: str, factor: float) -> list[str]:
    changed = []

    for kind in ["length", "width"]:
        fields = h.select_lateral_fields(data, target, kind)
        if not fields:
            raise RuntimeError(f"No fields for scale target={target}, kind={kind}")

        for f in fields:
            old = float(f["obj"][f["key"]])
            new = old * float(factor)

            if new <= 20 or new >= 300:
                raise RuntimeError(f"Unphysical scaled value {new} at {f['path']}")

            f["obj"][f["key"]] = float(round(new, 6))
            changed.append(f"{f['path']}:{old}->{new}")

    return changed


def apply_p194_ops(h, data: dict, ops: list[dict]) -> list[str]:
    changed = []

    for op in ops:
        if op["type"] in {"lateral", "rotation"}:
            changed.extend(h.apply_ops(data, [op]))
        elif op["type"] == "scale":
            changed.extend(apply_scale_op(h, data, op["target"], float(op["factor"])))
        elif op["type"] == "gap":
            changed.extend(apply_gap_op(h, data, op["axis"], float(op["delta_gap_nm"])))
        else:
            raise ValueError(f"Unknown op type: {op}")

    return changed


def main() -> int:
    h = import_helper(P192_HELPER)

    p187 = {r["candidate_id"]: r for r in load_csv(P187_PLAN)}
    if BASE_ID not in p187:
        raise RuntimeError(f"Missing base in P187 plan: {BASE_ID}")

    base_config = ROOT / p187[BASE_ID]["config_path"]
    rows = []

    for group, variant_id, purpose, ops in VARIANTS:
        with open(base_config, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        h.set_all_heights(cfg, FIXED_H)

        generation_status = "generated"
        generation_error = ""
        changed = []

        try:
            changed = apply_p194_ops(h, cfg, ops)
            h.set_all_heights(cfg, FIXED_H)
        except Exception as exc:
            generation_status = "generation_error"
            generation_error = repr(exc)

        candidate_id = h.sanitize(f"p194_h320_zero_{group}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        if generation_status == "generated":
            cfg.setdefault("project", {})
            cfg["project"]["stage"] = "p194_h320_zero_mechanism_scout"

            cfg.setdefault("boundary", {})
            cfg["boundary"]["fixed_height_nm"] = FIXED_H
            cfg["boundary"]["fabrication_aware_same_height"] = True
            cfg["boundary"]["not_k6_supercell"] = True
            cfg["boundary"]["not_steering_result"] = True
            cfg["boundary"]["not_micro_led_result"] = True
            cfg["boundary"]["p194_zero_mechanism_scout"] = True

            cfg.setdefault("metadata", {})
            cfg["metadata"]["p194_group"] = group
            cfg["metadata"]["p194_variant_id"] = variant_id
            cfg["metadata"]["p194_base_candidate_id"] = BASE_ID
            cfg["metadata"]["p194_purpose"] = purpose
            cfg["metadata"]["p194_fixed_height_nm"] = FIXED_H
            cfg["metadata"]["p194_success_criterion"] = "phase-hit first: nearest_bin=0 and target_conversion>0.5"
            cfg["metadata"]["p194_ops"] = ops
            cfg["metadata"]["p194_changed_fields"] = changed[:60]

            h.update_result_dir(cfg, candidate_id)
            h.dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "group": group,
            "variant_id": variant_id,
            "purpose": purpose,
            "base_candidate_id": BASE_ID,
            "fixed_height_nm": FIXED_H,
            "generation_status": generation_status,
            "generation_error": generation_error,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/") if generation_status == "generated" else "",
            "changed_field_count": len(changed),
            "changed_fields_preview": " | ".join(changed[:8]),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P194 h320 zero-bin mechanism scout plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: find 0-bin phase-hit first.",
        "- Success criterion for this scout is nearest_bin=0 and target_conversion>0.5.",
        "- Early-pass is welcome but not required in this mechanism scout.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "",
        f"generated_candidates: {sum(1 for r in rows if r['generation_status'] == 'generated')}",
        f"generation_errors: {sum(1 for r in rows if r['generation_status'] != 'generated')}",
        "",
        "## Candidate queue",
        "",
        "| group | variant | status | candidate | changed fields | purpose / error |",
        "|---|---|---|---|---:|---|",
    ]

    for r in rows:
        msg = r["purpose"] if r["generation_status"] == "generated" else r["generation_error"]
        lines.append(
            f"| {r['group']} | {r['variant_id']} | {r['generation_status']} | "
            f"`{r['candidate_id']}` | {r['changed_field_count']} | {msg} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={sum(1 for r in rows if r['generation_status'] == 'generated')}")
    print(f"generation_errors={sum(1 for r in rows if r['generation_status'] != 'generated')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
