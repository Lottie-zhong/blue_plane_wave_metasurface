from __future__ import annotations

from pathlib import Path
import csv
import copy
import yaml
import math

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

BASE_CONFIG = ROOT / "configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5.yaml"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p200_h300_zero_leakage_cancel_mechanism_plan.csv"
REPORT = ROOT / "reports/p200_h300_zero_leakage_cancel_mechanism_plan.md"

FIXED_H = 300

VARIANTS = [
    ("A_helper_cancel", "helper_mid_35x35_r45", "add weak middle helper, scalar leakage-cancel probe", [
        {"type": "add_helper", "length": 35.0, "width": 35.0, "rotation": 45.0, "x": 0.0, "y": 0.0},
    ]),
    ("A_helper_cancel", "helper_diag_p35_30x40_r45", "add weak diagonal helper near p1 side", [
        {"type": "add_helper", "length": 30.0, "width": 40.0, "rotation": 45.0, "x": 35.0, "y": 35.0},
    ]),
    ("A_helper_cancel", "helper_diag_m35_30x40_r45", "add weak diagonal helper near p2 side", [
        {"type": "add_helper", "length": 30.0, "width": 40.0, "rotation": 45.0, "x": -35.0, "y": -35.0},
    ]),

    ("B_p2_aniso", "p2L_m2", "reduce p2 length slightly, test leakage suppression", [
        {"type": "lateral_delta", "target": "p2", "length_delta": -2.0, "width_delta": 0.0},
    ]),
    ("B_p2_aniso", "p2W_p2", "increase p2 width slightly, test leakage suppression", [
        {"type": "lateral_delta", "target": "p2", "length_delta": 0.0, "width_delta": 2.0},
    ]),
    ("B_p2_aniso", "p2L_m2_W_p2", "p2 aspect compensation: shorter and wider", [
        {"type": "lateral_delta", "target": "p2", "length_delta": -2.0, "width_delta": 2.0},
    ]),

    ("C_gap_coupling", "y_in_2", "bring two pillars closer along y by 2 nm each", [
        {"type": "position_delta", "target": "p1", "dx": 0.0, "dy": -2.0},
        {"type": "position_delta", "target": "p2", "dx": 0.0, "dy": 2.0},
    ]),
    ("C_gap_coupling", "x_in_2", "bring two pillars closer along x by 2 nm each", [
        {"type": "position_delta", "target": "p1", "dx": -2.0, "dy": 0.0},
        {"type": "position_delta", "target": "p2", "dx": 2.0, "dy": 0.0},
    ]),
    ("C_gap_coupling", "shear_y_p1down_p2up", "small shear coupling perturbation, preserve 0-bin phase", [
        {"type": "position_delta", "target": "p1", "dx": 0.0, "dy": -3.0},
        {"type": "position_delta", "target": "p2", "dx": 0.0, "dy": 1.0},
    ]),

    ("D_helper_p2_combo", "helper_mid_p2W_p2", "middle helper plus p2 width recovery", [
        {"type": "add_helper", "length": 35.0, "width": 35.0, "rotation": 45.0, "x": 0.0, "y": 0.0},
        {"type": "lateral_delta", "target": "p2", "length_delta": 0.0, "width_delta": 2.0},
    ]),
    ("D_helper_p2_combo", "helper_mid_p2L_m2_W_p2", "middle helper plus p2 aspect compensation", [
        {"type": "add_helper", "length": 35.0, "width": 35.0, "rotation": 45.0, "x": 0.0, "y": 0.0},
        {"type": "lateral_delta", "target": "p2", "length_delta": -2.0, "width_delta": 2.0},
    ]),
    ("D_helper_p2_combo", "helper_diag_p35_p2W_p2", "diagonal helper plus p2 width recovery", [
        {"type": "add_helper", "length": 30.0, "width": 40.0, "rotation": 45.0, "x": 35.0, "y": 35.0},
        {"type": "lateral_delta", "target": "p2", "length_delta": 0.0, "width_delta": 2.0},
    ]),
]


def sanitize(s: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s).strip("_")


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def set_all_heights(obj, h: float) -> None:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "height_nm":
                obj[k] = float(h)
            else:
                set_all_heights(v, h)
    elif isinstance(obj, list):
        for v in obj:
            set_all_heights(v, h)


def is_pillar_dict(x) -> bool:
    return isinstance(x, dict) and "length_nm" in x and "width_nm" in x


def collect_pillars_with_parent(obj):
    """
    Returns entries:
      {
        pillar: dict,
        parent: parent object,
        parent_kind: "list" or "dict",
        key: list index or dict key
      }

    This is more robust than assuming a direct pillar list.
    """
    found = []

    def rec(x, parent=None, parent_kind="", key=None):
        if is_pillar_dict(x):
            found.append({
                "pillar": x,
                "parent": parent,
                "parent_kind": parent_kind,
                "key": key,
            })

        if isinstance(x, dict):
            for k, v in x.items():
                rec(v, x, "dict", k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, x, "list", i)

    rec(obj)
    return found


def unique_core_entries(entries):
    out = []
    seen = set()
    for e in entries:
        p = e["pillar"]
        key = (
            p.get("length_nm"), p.get("width_nm"), p.get("height_nm"),
            p.get("rotation_deg"), p.get("x_nm"), p.get("y_nm")
        )
        if key in seen:
            continue
        seen.add(key)
        out.append(e)
        if len(out) >= 2:
            break
    return out


def add_helper_near_core(core_entry, helper):
    """
    Add helper to the same container as p1 when possible.
    If p1 is inside a list, append to that list.
    If p1 is stored as a dict field, add a sibling dict key.
    """
    parent = core_entry["parent"]
    parent_kind = core_entry["parent_kind"]

    if parent_kind == "list" and isinstance(parent, list):
        parent.append(helper)
        return "append_to_parent_list"

    if parent_kind == "dict" and isinstance(parent, dict):
        base_key = "p200_weak_scalar_helper"
        key = base_key
        idx = 1
        while key in parent:
            idx += 1
            key = f"{base_key}_{idx}"
        parent[key] = helper
        return f"add_sibling_dict_key={key}"

    raise RuntimeError("Cannot add helper: p1 parent container not found.")


def apply_ops(cfg: dict, ops: list[dict]) -> list[str]:
    entries = collect_pillars_with_parent(cfg)
    cores = unique_core_entries(entries)

    if len(cores) < 2:
        debug = []
        for e in entries[:10]:
            p = e["pillar"]
            debug.append(str({
                "length": p.get("length_nm"),
                "width": p.get("width_nm"),
                "height": p.get("height_nm"),
                "rot": p.get("rotation_deg"),
                "x": p.get("x_nm"),
                "y": p.get("y_nm"),
                "parent_kind": e["parent_kind"],
                "key": e["key"],
            }))
        raise RuntimeError("Could not locate two core pillars. Found: " + " ; ".join(debug))

    p1_entry, p2_entry = cores[0], cores[1]
    p1, p2 = p1_entry["pillar"], p2_entry["pillar"]

    target_map = {
        "p1": p1,
        "p2": p2,
    }

    changed = []

    for op in ops:
        typ = op["type"]

        if typ == "lateral_delta":
            p = target_map[op["target"]]
            old_l = safe_float(p.get("length_nm"))
            old_w = safe_float(p.get("width_nm"))
            p["length_nm"] = float(old_l + float(op.get("length_delta", 0.0)))
            p["width_nm"] = float(old_w + float(op.get("width_delta", 0.0)))
            changed.append(f"{op['target']}.length_width_delta=({op.get('length_delta',0.0)},{op.get('width_delta',0.0)})")

        elif typ == "position_delta":
            p = target_map[op["target"]]
            old_x = safe_float(p.get("x_nm"))
            old_y = safe_float(p.get("y_nm"))
            p["x_nm"] = float(old_x + float(op.get("dx", 0.0)))
            p["y_nm"] = float(old_y + float(op.get("dy", 0.0)))
            changed.append(f"{op['target']}.position_delta=({op.get('dx',0.0)},{op.get('dy',0.0)})")

        elif typ == "add_helper":
            helper = copy.deepcopy(p1)
            helper["length_nm"] = float(op["length"])
            helper["width_nm"] = float(op["width"])
            helper["height_nm"] = float(FIXED_H)
            helper["rotation_deg"] = float(op["rotation"])
            helper["x_nm"] = float(op["x"])
            helper["y_nm"] = float(op["y"])
            helper["role"] = "p200_weak_scalar_helper"
            helper["name"] = "p200_weak_scalar_helper"

            how = add_helper_near_core(p1_entry, helper)
            changed.append(f"add_helper_{how}={op['length']}x{op['width']}_r{op['rotation']}_at({op['x']},{op['y']})")

        else:
            raise RuntimeError(f"Unsupported op type: {typ}")

    return changed


def collect_pillars(obj):
    return [e["pillar"] for e in collect_pillars_with_parent(obj)]


def geometry_sanity(cfg: dict) -> dict:
    pillars = collect_pillars(cfg)

    heights = []
    for p in pillars:
        h = safe_float(p.get("height_nm"))
        if not math.isnan(h):
            heights.append(round(h, 6))

    same_height = len(set(heights)) == 1 if heights else False
    fixed_h_ok = same_height and abs(heights[0] - FIXED_H) < 1e-6

    dim_ok = True
    boundary_ok = True
    for p in pillars:
        l = safe_float(p.get("length_nm"))
        w = safe_float(p.get("width_nm"))
        x = safe_float(p.get("x_nm"), 0.0)
        y = safe_float(p.get("y_nm"), 0.0)

        if math.isnan(l) or math.isnan(w) or l <= 0 or w <= 0 or l > 220 or w > 220:
            dim_ok = False
        if abs(x) > 150 or abs(y) > 150:
            boundary_ok = False

    return {
        "pillar_count": len(pillars),
        "same_height": same_height,
        "fixed_height_ok": fixed_h_ok,
        "dimension_bounds_ok": dim_ok,
        "rough_boundary_ok": boundary_ok,
        "rough_geometry_pass": bool(fixed_h_ok and dim_ok and boundary_ok),
    }


def update_result_dir(cfg: dict, candidate_id: str) -> None:
    cfg.setdefault("output", {})
    cfg["output"]["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"


def dump_yaml(cfg: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def main() -> int:
    if not BASE_CONFIG.exists():
        raise RuntimeError(f"Missing base config: {BASE_CONFIG}")

    with open(BASE_CONFIG, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    # Quick preflight debug.
    pre_entries = collect_pillars_with_parent(base)
    pre_cores = unique_core_entries(pre_entries)
    print(f"preflight_pillar_like_count={len(pre_entries)}")
    print(f"preflight_core_count={len(pre_cores)}")
    for i, e in enumerate(pre_cores):
        p = e["pillar"]
        print(
            f"core{i+1}: L={p.get('length_nm')} W={p.get('width_nm')} "
            f"H={p.get('height_nm')} rot={p.get('rotation_deg')} "
            f"x={p.get('x_nm')} y={p.get('y_nm')} parent={e['parent_kind']} key={e['key']}"
        )

    rows = []

    for group, variant_id, purpose, ops in VARIANTS:
        cfg = copy.deepcopy(base)
        set_all_heights(cfg, FIXED_H)

        changed = apply_ops(cfg, ops)
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p200_h300_zero_{group}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p200_h300_zero_leakage_cancel_mechanism"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p200_h300_zero_leakage_cancel_mechanism"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p200_base_candidate_id"] = "p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5"
        cfg["metadata"]["p200_base_summary"] = "phase≈23.47, nearest=0, target≈0.586, leakage≈0.376, ratio≈1.56"
        cfg["metadata"]["p200_group"] = group
        cfg["metadata"]["p200_variant_id"] = variant_id
        cfg["metadata"]["p200_purpose"] = purpose
        cfg["metadata"]["p200_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p200_success"] = "nearest_bin=0, target>=0.5, leakage<=0.2, ratio>=6"
        cfg["metadata"]["p200_ops"] = ops
        cfg["metadata"]["p200_changed_fields"] = changed

        update_result_dir(cfg, candidate_id)
        sanity = geometry_sanity(cfg)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "group": group,
            "variant_id": variant_id,
            "purpose": purpose,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "pillar_count": sanity["pillar_count"],
            "same_height": sanity["same_height"],
            "fixed_height_ok": sanity["fixed_height_ok"],
            "dimension_bounds_ok": sanity["dimension_bounds_ok"],
            "rough_boundary_ok": sanity["rough_boundary_ok"],
            "rough_geometry_pass": sanity["rough_geometry_pass"],
            "changed_fields": " | ".join(changed),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "candidate_id",
        "group",
        "variant_id",
        "purpose",
        "config_path",
        "pillar_count",
        "same_height",
        "fixed_height_ok",
        "dimension_bounds_ok",
        "rough_boundary_ok",
        "rough_geometry_pass",
        "changed_fields",
    ]

    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P200 h300 zero leakage-cancel mechanism plan",
        "",
        "## Scope",
        "",
        "- Fixed height h300 only.",
        "- Base: `p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5`.",
        "- Goal: keep nearest_bin=0 while reducing leakage / increasing ratio.",
        "- No FDTD in this generation step.",
        "- No K=6 / steering claim.",
        "- No mixed height.",
        "",
        "## Candidate queue",
        "",
        "| candidate_id | group | variant_id | purpose | pillars | rough pass | config_path |",
        "|---|---|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| `{r['candidate_id']}` | {r['group']} | {r['variant_id']} | "
            f"{r['purpose']} | {r['pillar_count']} | {r['rough_geometry_pass']} | `{r['config_path']}` |"
        )

    lines += [
        "",
        "## Suggested first batch",
        "",
        "1. `p200_h300_zero_A_helper_cancel_helper_mid_35x35_r45`",
        "2. `p200_h300_zero_B_p2_aniso_p2W_p2`",
        "3. `p200_h300_zero_B_p2_aniso_p2L_m2_W_p2`",
        "4. `p200_h300_zero_D_helper_p2_combo_helper_mid_p2W_p2`",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print("")
    print("candidate_id\tgroup\tvariant_id\tpurpose\tconfig_path\tpillar_count\tsame_height\tfixed_height_ok\tdimension_bounds_ok\trough_boundary_ok\trough_geometry_pass")
    for r in rows:
        print(
            f"{r['candidate_id']}\t{r['group']}\t{r['variant_id']}\t{r['purpose']}\t"
            f"{r['config_path']}\t{r['pillar_count']}\t{r['same_height']}\t"
            f"{r['fixed_height_ok']}\t{r['dimension_bounds_ok']}\t"
            f"{r['rough_boundary_ok']}\t{r['rough_geometry_pass']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
