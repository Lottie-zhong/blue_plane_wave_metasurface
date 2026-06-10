from __future__ import annotations

from pathlib import Path
import csv
import copy
import math
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

BASE_ID = "p185_fh300_p060_from_aggr_lhs_retention_dy_05"
BASE_CONFIG = ROOT / "configs/apcd_k6_phase_state_candidates" / f"{BASE_ID}.yaml"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p201_h300_60_to_0_candidate_plan.csv"
OUT_SELECTION = ROOT / "outputs/apcd_k6_active_learning/p201_h300_60_to_0_fdtd_selection.csv"
REPORT = ROOT / "reports/p201_h300_60_to_0_plan.md"

FIXED_H = 300.0
SOURCE_ANCHOR = BASE_ID

# Base reference:
# phase≈72.24°, target≈0.857, leakage≈0.103, ratio≈8.33
#
# Goal:
# pull phase from healthy 60-bin anchor toward 0-bin
# while preserving APCD selectivity.

VARIANTS = [
    # Family A: p2 length down + width up.
    # Highest priority: phase pull + selectivity compensation.
    {
        "group": "A_p2_length_down_width_up",
        "variant": "p2L_m2_p2W_p1",
        "purpose": "mild p2 phase pull with width compensation",
        "ops": [
            {"type": "lateral_delta", "target": "p2", "dL": -2.0, "dW": +1.0},
        ],
        "selected": True,
    },
    {
        "group": "A_p2_length_down_width_up",
        "variant": "p2L_m4_p2W_p2",
        "purpose": "main p2 phase-pull trend point",
        "ops": [
            {"type": "lateral_delta", "target": "p2", "dL": -4.0, "dW": +2.0},
        ],
        "selected": True,
    },
    {
        "group": "A_p2_length_down_width_up",
        "variant": "p2L_m6_p2W_p3",
        "purpose": "stronger p2 phase pull, check leakage boundary",
        "ops": [
            {"type": "lateral_delta", "target": "p2", "dL": -6.0, "dW": +3.0},
        ],
        "selected": True,
    },

    # Family B: coordinated common area / aspect restoration.
    {
        "group": "B_common_area_down_aspect_restore",
        "variant": "p1p2_Lm2_Wp1",
        "purpose": "coordinated mild dynamic phase shift with aspect recovery",
        "ops": [
            {"type": "lateral_delta", "target": "p1", "dL": -2.0, "dW": +1.0},
            {"type": "lateral_delta", "target": "p2", "dL": -2.0, "dW": +1.0},
        ],
        "selected": True,
    },
    {
        "group": "B_common_area_down_aspect_restore",
        "variant": "p1p2_Lm4_Wp2",
        "purpose": "coordinated stronger dynamic phase shift",
        "ops": [
            {"type": "lateral_delta", "target": "p1", "dL": -4.0, "dW": +2.0},
            {"type": "lateral_delta", "target": "p2", "dL": -4.0, "dW": +2.0},
        ],
        "selected": False,
    },
    {
        "group": "B_common_area_down_aspect_restore",
        "variant": "p1Lm2_p2Lm4_p2Wp2",
        "purpose": "asymmetric phase pull dominated by p2 with mild p1 trim",
        "ops": [
            {"type": "lateral_delta", "target": "p1", "dL": -2.0, "dW": 0.0},
            {"type": "lateral_delta", "target": "p2", "dL": -4.0, "dW": +2.0},
        ],
        "selected": True,
    },

    # Family C: tiny relative rotation micro bias.
    # Not common rotation. Only small differential probes.
    {
        "group": "C_relative_rotation_micro_bias",
        "variant": "p2rot_p2p5",
        "purpose": "tiny p2 rotation phase/selectivity bias",
        "ops": [
            {"type": "rotation_delta", "target": "p2", "dRot": +2.5},
        ],
        "selected": True,
    },
    {
        "group": "C_relative_rotation_micro_bias",
        "variant": "p2rot_m2p5",
        "purpose": "opposite tiny p2 rotation bias",
        "ops": [
            {"type": "rotation_delta", "target": "p2", "dRot": -2.5},
        ],
        "selected": False,
    },
    {
        "group": "C_relative_rotation_micro_bias",
        "variant": "p1rot_m2p5_p2rot_p2p5",
        "purpose": "tiny differential relative-angle bias",
        "ops": [
            {"type": "rotation_delta", "target": "p1", "dRot": -2.5},
            {"type": "rotation_delta", "target": "p2", "dRot": +2.5},
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

        if op["type"] == "lateral_delta":
            old_l = safe_float(p.get("length_nm"))
            old_w = safe_float(p.get("width_nm"))
            p["length_nm"] = float(old_l + float(op.get("dL", 0.0)))
            p["width_nm"] = float(old_w + float(op.get("dW", 0.0)))
            changed.append(
                f"{op['target']}.length_nm {old_l}->{p['length_nm']}; "
                f"{op['target']}.width_nm {old_w}->{p['width_nm']}"
            )

        elif op["type"] == "rotation_delta":
            old_r = safe_float(p.get("rotation_deg"))
            p["rotation_deg"] = float(old_r + float(op.get("dRot", 0.0)))
            changed.append(
                f"{op['target']}.rotation_deg {old_r}->{p['rotation_deg']}"
            )

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

    heights = []
    integer_lateral_ok = True
    dimension_ok = True

    for _, p in pillars:
        h = safe_float(p.get("height_nm"))
        if not math.isnan(h):
            heights.append(round(h, 6))

        l = safe_float(p.get("length_nm"))
        w = safe_float(p.get("width_nm"))

        if math.isnan(l) or math.isnan(w) or l <= 0 or w <= 0 or l > 220 or w > 220:
            dimension_ok = False

        if not is_integer_nm(p.get("length_nm")) or not is_integer_nm(p.get("width_nm")):
            integer_lateral_ok = False

    same_height = len(set(heights)) == 1 if heights else False
    fixed_height_ok = same_height and abs(heights[0] - FIXED_H) < 1e-6

    gap = rough_core_gap_nm(cfg)
    min_gap_ok = gap >= 50.0

    geom = get_geometry(cfg)
    no_helper = "nanopillar_helper" not in geom

    return {
        "pillar_count": len(pillars),
        "same_height": same_height,
        "fixed_height_ok": fixed_height_ok,
        "integer_lateral_ok": integer_lateral_ok,
        "dimension_ok": dimension_ok,
        "rough_core_gap_nm": gap,
        "min_gap_ok": min_gap_ok,
        "no_helper": no_helper,
        "rough_geometry_pass": bool(
            fixed_height_ok and integer_lateral_ok and dimension_ok and min_gap_ok and no_helper
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
    if not BASE_CONFIG.exists():
        raise RuntimeError(f"Missing base config: {BASE_CONFIG}")

    with open(BASE_CONFIG, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    rows = []

    for item in VARIANTS:
        cfg = copy.deepcopy(base)

        remove_helper(cfg)
        set_all_heights(cfg, FIXED_H)
        changed = apply_ops(cfg, item["ops"])
        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p201_h300_60to0_{item['group']}_{item['variant']}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p201_h300_60_to_0_phase_bias_scout"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["no_helper_branch"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p201_h300_60_to_0_phase_bias_scout"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p201_source_anchor"] = SOURCE_ANCHOR
        cfg["metadata"]["p201_source_summary"] = "h300 60deg early-pass anchor: phase≈72.24, target≈0.857, leakage≈0.103, ratio≈8.33"
        cfg["metadata"]["p201_group"] = item["group"]
        cfg["metadata"]["p201_variant"] = item["variant"]
        cfg["metadata"]["p201_purpose"] = item["purpose"]
        cfg["metadata"]["p201_success_primary"] = "-30<=phase_deg<=30 and early_pass=True"
        cfg["metadata"]["p201_success_healthy_trend"] = "30<phase_deg<=45 and early_pass=True"
        cfg["metadata"]["p201_useful_nearmiss"] = "phase_deg<=45, leakage<=0.25, 4<=ratio<6"
        cfg["metadata"]["p201_ops"] = item["ops"]
        cfg["metadata"]["p201_changed_fields"] = changed

        update_result_dir(cfg, candidate_id)
        sanity = geometry_sanity(cfg)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "group": item["group"],
            "variant": item["variant"],
            "selected_for_fdtd": bool(item["selected"]),
            "purpose": item["purpose"],
            "source_anchor": SOURCE_ANCHOR,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "pillar_count": sanity["pillar_count"],
            "same_height": sanity["same_height"],
            "fixed_height_ok": sanity["fixed_height_ok"],
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

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "candidate_id",
        "group",
        "variant",
        "selected_for_fdtd",
        "purpose",
        "source_anchor",
        "config_path",
        "pillar_count",
        "same_height",
        "fixed_height_ok",
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
        "# P201 h300 60-to-0 phase-bias scout",
        "",
        "## Scope",
        "",
        "- Fixed height h300 only.",
        f"- Source anchor: `{SOURCE_ANCHOR}`.",
        "- Start from healthy 60deg early-pass anchor and bias phase toward 0deg.",
        "- No helper branch.",
        "- No K=6 / steering claim.",
        "- No mixed height.",
        "",
        "## Candidate plan",
        "",
        "| candidate_id | group | variant | selected | rough gap nm | pass | purpose |",
        "|---|---|---|---|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| `{r['candidate_id']}` | {r['group']} | {r['variant']} | "
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

    lines += [
        "",
        "## Decision rules",
        "",
        "- Primary success: nearest_bin=0 and early_pass=True.",
        "- Healthy trend: 30<phase_deg<=45 and early_pass=True.",
        "- Useful near-miss: phase_deg<=45, leakage<=0.25, 4<=ratio<6.",
        "- Failure mode: phase decreases but leakage rises to 0.35+ or ratio collapses.",
    ]

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"selection={OUT_SELECTION}")
    print(f"report={REPORT}")
    print("")
    print("candidate_id\tgroup\tvariant\tselected_for_fdtd\tpurpose\tsource_anchor\tconfig_path\tpillar_count\tsame_height\tfixed_height_ok\tinteger_lateral_ok\tdimension_ok\trough_core_gap_nm\tmin_gap_ok\tno_helper\trough_geometry_pass")
    for r in rows:
        print(
            f"{r['candidate_id']}\t{r['group']}\t{r['variant']}\t"
            f"{r['selected_for_fdtd']}\t{r['purpose']}\t{r['source_anchor']}\t"
            f"{r['config_path']}\t{r['pillar_count']}\t{r['same_height']}\t"
            f"{r['fixed_height_ok']}\t{r['integer_lateral_ok']}\t"
            f"{r['dimension_ok']}\t{r['rough_core_gap_nm']}\t"
            f"{r['min_gap_ok']}\t{r['no_helper']}\t{r['rough_geometry_pass']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
