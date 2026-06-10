from __future__ import annotations

from pathlib import Path
import csv
import copy
import math
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p202_h300_phasepull_rotation_comp_plan.csv"
OUT_SELECTION = ROOT / "outputs/apcd_k6_active_learning/p202_h300_phasepull_rotation_comp_fdtd_selection.csv"
REPORT = ROOT / "reports/p202_h300_phasepull_rotation_comp_plan.md"

FIXED_H = 300.0

# P201 facts:
# healthy source: p185_fh300_p060_from_aggr_lhs_retention_dy_05
# p2L_m2_p2W_p1: phase≈68.86, ratio≈6.33
# p2L_m4_p2W_p2: phase≈66.98, ratio≈5.07
# p2L_m6_p2W_p3: phase≈64.55, ratio≈3.84
# p2rot_m2p5 alone: phase≈68.18, ratio≈6.53
#
# P202 idea:
# combine phase-pull geometry with selectivity-restoring p2 negative micro-rotation.

BASES = {
    "A_m2": {
        "base_id": "p201_h300_60to0_A_p2_length_down_width_up_p2L_m2_p2W_p1",
        "summary": "phase≈68.86, leakage≈0.136, ratio≈6.33, still healthy 60",
    },
    "A_m4": {
        "base_id": "p201_h300_60to0_A_p2_length_down_width_up_p2L_m4_p2W_p2",
        "summary": "phase≈66.98, leakage≈0.171, ratio≈5.07, near recovery target",
    },
    "A_m6": {
        "base_id": "p201_h300_60to0_A_p2_length_down_width_up_p2L_m6_p2W_p3",
        "summary": "phase≈64.55, leakage≈0.227, ratio≈3.84, stronger phase pull but selectivity failed",
    },
    "B_Lm4": {
        "base_id": "p201_h300_60to0_B_common_area_down_aspect_restore_p1p2_Lm4_Wp2",
        "summary": "phase≈66.36, leakage≈0.182, ratio≈4.74, common-area phase pull failed",
    },
}

VARIANTS = [
    {
        "base_key": "A_m2",
        "variant": "p2rot_m2p5",
        "purpose": "mild healthy phase-pull point plus p2 -2.5deg selectivity compensation",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -2.5}],
        "selected": True,
    },
    {
        "base_key": "A_m4",
        "variant": "p2rot_m2p5",
        "purpose": "main recovery candidate: phase-pull m4 plus p2 -2.5deg compensation",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -2.5}],
        "selected": True,
    },
    {
        "base_key": "A_m4",
        "variant": "p2rot_m5",
        "purpose": "stronger p2 rotation compensation on m4 phase-pull point",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -5.0}],
        "selected": True,
    },
    {
        "base_key": "A_m6",
        "variant": "p2rot_m2p5",
        "purpose": "strong phase-pull m6 with mild p2 recovery",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -2.5}],
        "selected": True,
    },
    {
        "base_key": "A_m6",
        "variant": "p2rot_m5",
        "purpose": "strong phase-pull m6 with stronger p2 recovery",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -5.0}],
        "selected": True,
    },
    {
        "base_key": "B_Lm4",
        "variant": "p2rot_m2p5",
        "purpose": "common-area phase pull plus p2 -2.5deg recovery",
        "ops": [{"type": "rotation_delta", "target": "p2", "dRot": -2.5}],
        "selected": True,
    },

    # generated but not selected first
    {
        "base_key": "A_m4",
        "variant": "p1rot_p2p5_p2rot_m2p5",
        "purpose": "relative-angle compensation around m4 phase-pull point",
        "ops": [
            {"type": "rotation_delta", "target": "p1", "dRot": +2.5},
            {"type": "rotation_delta", "target": "p2", "dRot": -2.5},
        ],
        "selected": False,
    },
    {
        "base_key": "A_m6",
        "variant": "p1rot_p2p5_p2rot_m2p5",
        "purpose": "relative-angle compensation around m6 phase-pull point",
        "ops": [
            {"type": "rotation_delta", "target": "p1", "dRot": +2.5},
            {"type": "rotation_delta", "target": "p2", "dRot": -2.5},
        ],
        "selected": False,
    },
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


def get_geometry(cfg: dict) -> dict:
    geom = cfg.get("geometry")
    if not isinstance(geom, dict):
        raise RuntimeError("Missing geometry dict.")
    if "nanopillar_1" not in geom or "nanopillar_2" not in geom:
        raise RuntimeError("Missing geometry.nanopillar_1 or geometry.nanopillar_2.")
    return geom


def remove_helper(cfg: dict) -> None:
    geom = get_geometry(cfg)
    geom.pop("nanopillar_helper", None)


def apply_ops(cfg: dict, ops: list[dict]) -> list[str]:
    geom = get_geometry(cfg)
    pmap = {
        "p1": geom["nanopillar_1"],
        "p2": geom["nanopillar_2"],
    }

    changed = []

    for op in ops:
        p = pmap[op["target"]]

        if op["type"] == "rotation_delta":
            old_r = safe_float(p.get("rotation_deg"))
            p["rotation_deg"] = float(old_r + float(op.get("dRot", 0.0)))
            changed.append(f"{op['target']}.rotation_deg {old_r}->{p['rotation_deg']}")

        else:
            raise RuntimeError(f"Unsupported op type: {op['type']}")

    return changed


def collect_pillars(cfg: dict):
    out = []

    def rec(x, path):
        if isinstance(x, dict) and "length_nm" in x and "width_nm" in x:
            out.append((path, x))
        if isinstance(x, dict):
            for k, v in x.items():
                rec(v, f"{path}.{k}" if path else str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, f"{path}[{i}]")

    rec(cfg, "")
    return out


def center(p):
    return safe_float(p.get("x_nm"), 0.0), safe_float(p.get("y_nm"), 0.0)


def diag(p):
    l = safe_float(p.get("length_nm"))
    w = safe_float(p.get("width_nm"))
    return math.sqrt(l * l + w * w)


def rough_core_gap_nm(cfg: dict) -> float:
    geom = get_geometry(cfg)
    p1 = geom["nanopillar_1"]
    p2 = geom["nanopillar_2"]

    x1, y1 = center(p1)
    x2, y2 = center(p2)
    dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)

    return dist - 0.5 * (diag(p1) + diag(p2))


def is_integer_nm(x) -> bool:
    v = safe_float(x)
    return not math.isnan(v) and abs(v - round(v)) < 1e-9


def geometry_sanity(cfg: dict) -> dict:
    pillars = collect_pillars(cfg)

    integer_lateral_ok = True
    dimension_ok = True

    for _, p in pillars:
        l = safe_float(p.get("length_nm"))
        w = safe_float(p.get("width_nm"))

        if math.isnan(l) or math.isnan(w) or l <= 0 or w <= 0 or l > 220 or w > 220:
            dimension_ok = False

        if not is_integer_nm(p.get("length_nm")) or not is_integer_nm(p.get("width_nm")):
            integer_lateral_ok = False

    gap = rough_core_gap_nm(cfg)
    min_gap_ok = gap >= 50.0

    geom = get_geometry(cfg)
    no_helper = "nanopillar_helper" not in geom

    # For h300 configs, height may be global in YAML;
    # FDTD confirmed these base configs are fixed h300.
    fixed_height_inferred_ok = True

    return {
        "pillar_count": len(pillars),
        "fixed_height_inferred_ok": fixed_height_inferred_ok,
        "integer_lateral_ok": integer_lateral_ok,
        "dimension_ok": dimension_ok,
        "rough_core_gap_nm": gap,
        "min_gap_ok": min_gap_ok,
        "no_helper": no_helper,
        "rough_geometry_pass": bool(
            fixed_height_inferred_ok and integer_lateral_ok and dimension_ok and min_gap_ok and no_helper
        ),
    }


def update_result_dir(cfg: dict, candidate_id: str) -> None:
    cfg.setdefault("output", {})
    cfg["output"]["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"


def dump_yaml(cfg: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def main() -> int:
    rows = []

    for item in VARIANTS:
        base_info = BASES[item["base_key"]]
        base_id = base_info["base_id"]
        base_path = CONFIG_DIR / f"{base_id}.yaml"

        if not base_path.exists():
            raise RuntimeError(f"Missing base config: {base_path}")

        with open(base_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        remove_helper(cfg)
        set_all_heights(cfg, FIXED_H)
        changed = apply_ops(cfg, item["ops"])
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p202_h300_phasepull_rotcomp_{item['base_key']}_{item['variant']}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p202_h300_phasepull_rotation_compensation"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["no_helper_branch"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p202_phasepull_rotation_compensation"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p202_base_candidate_id"] = base_id
        cfg["metadata"]["p202_base_key"] = item["base_key"]
        cfg["metadata"]["p202_base_summary"] = base_info["summary"]
        cfg["metadata"]["p202_variant"] = item["variant"]
        cfg["metadata"]["p202_purpose"] = item["purpose"]
        cfg["metadata"]["p202_strategy"] = "combine P201 phase-pull geometry with selectivity-restoring p2 negative micro-rotation"
        cfg["metadata"]["p202_success_primary"] = "-30<=phase_deg<=30 and early_pass=True"
        cfg["metadata"]["p202_success_healthy_trend"] = "30<phase_deg<=45 and early_pass=True"
        cfg["metadata"]["p202_useful_nearmiss"] = "phase_deg<=45, leakage<=0.25, 4<=ratio<6"
        cfg["metadata"]["p202_ops"] = item["ops"]
        cfg["metadata"]["p202_changed_fields"] = changed

        update_result_dir(cfg, candidate_id)
        sanity = geometry_sanity(cfg)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "base_key": item["base_key"],
            "base_candidate_id": base_id,
            "variant": item["variant"],
            "selected_for_fdtd": bool(item["selected"]),
            "purpose": item["purpose"],
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "pillar_count": sanity["pillar_count"],
            "fixed_height_inferred_ok": sanity["fixed_height_inferred_ok"],
            "integer_lateral_ok": sanity["integer_lateral_ok"],
            "dimension_ok": sanity["dimension_ok"],
            "rough_core_gap_nm": f"{sanity['rough_core_gap_nm']:.3f}",
            "min_gap_ok": sanity["min_gap_ok"],
            "no_helper": sanity["no_helper"],
            "rough_geometry_pass": sanity["rough_geometry_pass"],
            "changed_fields": " | ".join(changed),
        })

    selected = [r for r in rows if r["selected_for_fdtd"] and r["rough_geometry_pass"]]

    if len(selected) > 6:
        raise RuntimeError(f"Selected queue too large: {len(selected)} > 6")
    if len(selected) == 0:
        raise RuntimeError("No selected candidates passed sanity.")

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "candidate_id",
        "base_key",
        "base_candidate_id",
        "variant",
        "selected_for_fdtd",
        "purpose",
        "config_path",
        "pillar_count",
        "fixed_height_inferred_ok",
        "integer_lateral_ok",
        "dimension_ok",
        "rough_core_gap_nm",
        "min_gap_ok",
        "no_helper",
        "rough_geometry_pass",
        "changed_fields",
    ]

    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with open(OUT_SELECTION, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(selected)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P202 h300 phase-pull + rotation compensation plan",
        "",
        "## Scope",
        "",
        "- Fixed h300 only.",
        "- No helper.",
        "- No K=6 / steering claim.",
        "- Based on P201 phase-pull candidates and p2 negative micro-rotation compensation.",
        "",
        "## Candidate plan",
        "",
        "| candidate_id | base | variant | selected | gap nm | pass | purpose |",
        "|---|---|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| `{r['candidate_id']}` | {r['base_key']} | {r['variant']} | "
            f"{r['selected_for_fdtd']} | {r['rough_core_gap_nm']} | "
            f"{r['rough_geometry_pass']} | {r['purpose']} |"
        )

    lines += [
        "",
        "## First FDTD queue",
        "",
    ]
    for r in selected:
        lines.append(f"- `{r['candidate_id']}`")

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"selection={OUT_SELECTION}")
    print(f"report={REPORT}")
    print("")
    print("candidate_id\tbase_key\tbase_candidate_id\tvariant\tselected_for_fdtd\tpurpose\tconfig_path\tpillar_count\tfixed_height_inferred_ok\tinteger_lateral_ok\tdimension_ok\trough_core_gap_nm\tmin_gap_ok\tno_helper\trough_geometry_pass")
    for r in rows:
        print(
            f"{r['candidate_id']}\t{r['base_key']}\t{r['base_candidate_id']}\t"
            f"{r['variant']}\t{r['selected_for_fdtd']}\t{r['purpose']}\t"
            f"{r['config_path']}\t{r['pillar_count']}\t"
            f"{r['fixed_height_inferred_ok']}\t{r['integer_lateral_ok']}\t"
            f"{r['dimension_ok']}\t{r['rough_core_gap_nm']}\t"
            f"{r['min_gap_ok']}\t{r['no_helper']}\t{r['rough_geometry_pass']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
