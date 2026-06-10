from __future__ import annotations

from pathlib import Path
import csv
import copy
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

BASE_CONFIG = ROOT / "configs/apcd_k6_phase_state_candidates/p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5.yaml"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p200_v3_h300_zero_valid_helper_plan.csv"
REPORT = ROOT / "reports/p200_v3_h300_zero_valid_helper_plan.md"

FIXED_H = 300

VARIANTS = [
    (
        "helper_mid_35x35_r45",
        "valid schema middle helper, test real helper effect",
        {"length": 35.0, "width": 35.0, "rotation": 45.0, "x": 0.0, "y": 0.0},
    ),
    (
        "helper_diag_p35_30x40_r45",
        "valid schema diagonal helper near p1 side",
        {"length": 30.0, "width": 40.0, "rotation": 45.0, "x": 35.0, "y": 35.0},
    ),
    (
        "helper_diag_m35_30x40_r45",
        "valid schema diagonal helper near p2 side",
        {"length": 30.0, "width": 40.0, "rotation": 45.0, "x": -35.0, "y": -35.0},
    ),
    (
        "helper_far_p55_30x40_r45",
        "valid schema farther helper near p1 side",
        {"length": 30.0, "width": 40.0, "rotation": 45.0, "x": 55.0, "y": 55.0},
    ),
    (
        "helper_far_m55_30x40_r45",
        "valid schema farther helper near p2 side",
        {"length": 30.0, "width": 40.0, "rotation": 45.0, "x": -55.0, "y": -55.0},
    ),
    (
        "helper_rect_mid_40x80_r45",
        "valid schema stronger rectangular middle helper",
        {"length": 40.0, "width": 80.0, "rotation": 45.0, "x": 0.0, "y": 0.0},
    ),
]


def sanitize(s: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s).strip("_")


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


def ensure_geometry(cfg: dict) -> dict:
    if "geometry" not in cfg or not isinstance(cfg["geometry"], dict):
        raise RuntimeError("Missing geometry dict in base YAML.")
    return cfg["geometry"]


def make_helper_from_p1(geom: dict, helper_spec: dict) -> dict:
    if "nanopillar_1" not in geom:
        raise RuntimeError("Missing geometry.nanopillar_1 in base YAML.")

    helper = copy.deepcopy(geom["nanopillar_1"])

    # Use the exact valid builder-recognized key:
    # geometry.nanopillar_helper
    helper["length_nm"] = float(helper_spec["length"])
    helper["width_nm"] = float(helper_spec["width"])
    helper["rotation_deg"] = float(helper_spec["rotation"])
    helper["x_nm"] = float(helper_spec["x"])
    helper["y_nm"] = float(helper_spec["y"])

    # Some YAMLs keep height globally, but if per-pillar height exists,
    # keep it fabrication-aware.
    helper["height_nm"] = float(FIXED_H)

    helper["role"] = "nanopillar_helper"
    helper["name"] = "nanopillar_helper"

    return helper


def update_result_dir(cfg: dict, candidate_id: str) -> None:
    cfg.setdefault("output", {})
    cfg["output"]["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}"


def dump_yaml(cfg: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)


def pillar_paths(cfg: dict) -> str:
    out = []

    def rec(x, path):
        if isinstance(x, dict) and "length_nm" in x and "width_nm" in x:
            out.append(path)
        if isinstance(x, dict):
            for k, v in x.items():
                rec(v, f"{path}.{k}" if path else str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, f"{path}[{i}]")

    rec(cfg, "")
    return " | ".join(out)


def main() -> int:
    if not BASE_CONFIG.exists():
        raise RuntimeError(f"Missing base config: {BASE_CONFIG}")

    with open(BASE_CONFIG, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    rows = []

    for variant_id, purpose, helper_spec in VARIANTS:
        cfg = copy.deepcopy(base)
        geom = ensure_geometry(cfg)

        # Force correct helper schema.
        geom["nanopillar_helper"] = make_helper_from_p1(geom, helper_spec)

        set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p200v3_h300_zero_validhelper_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p200_v3_h300_zero_valid_helper"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p200_v3_valid_helper_schema"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p200v3_base_candidate_id"] = "p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5"
        cfg["metadata"]["p200v3_base_summary"] = "phase≈23.47, nearest=0, target≈0.586, leakage≈0.376, ratio≈1.56"
        cfg["metadata"]["p200v3_purpose"] = purpose
        cfg["metadata"]["p200v3_helper_schema"] = "geometry.nanopillar_helper"
        cfg["metadata"]["p200v3_success"] = "nearest_bin=0, target>=0.5, leakage<=0.2, ratio>=6"
        cfg["metadata"]["p200v3_helper_spec"] = helper_spec

        update_result_dir(cfg, candidate_id)
        dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "variant_id": variant_id,
            "purpose": purpose,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "pillar_paths": pillar_paths(cfg),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["candidate_id", "variant_id", "purpose", "config_path", "pillar_paths"],
        )
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P200 v3 h300 zero valid-helper plan",
        "",
        "## Scope",
        "",
        "- Fixed height h300 only.",
        "- Base: `p199_h300_zero_B_diff_rot_p1_m2p5_p2_p5`.",
        "- Helper is written using the validated schema: `geometry.nanopillar_helper`.",
        "- No FDTD in this generation step.",
        "",
        "| candidate_id | variant_id | purpose | config_path | pillar_paths |",
        "|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| `{r['candidate_id']}` | {r['variant_id']} | {r['purpose']} | "
            f"`{r['config_path']}` | {r['pillar_paths']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print("")
    print("candidate_id\tvariant_id\tpurpose\tconfig_path\tpillar_paths")
    for r in rows:
        print(
            f"{r['candidate_id']}\t{r['variant_id']}\t{r['purpose']}\t"
            f"{r['config_path']}\t{r['pillar_paths']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
