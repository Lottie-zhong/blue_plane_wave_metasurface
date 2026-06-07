from __future__ import annotations

import argparse
import copy
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


ANCHOR_ID = "aggr_lhs_retention_dy_05"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
ANCHOR_CONFIG = CONFIG_DIR / f"{ANCHOR_ID}.yaml"
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
PLAN_CSV = ACTIVE_DIR / "combined_phase_knob_p165_zero_cliff_recovery_candidate_plan.csv"
REPORT_MD = REPO_ROOT / "reports/combined_phase_knob_p165_zero_cliff_recovery_candidate_plan.md"

PLAN_FIELDS = [
    "candidate_id",
    "group",
    "family",
    "anchor_candidate_id",
    "height_nm",
    "period_x_nm",
    "period_y_nm",
    "p1_shape",
    "p1_length_nm",
    "p1_width_nm",
    "p1_notch_depth_nm",
    "p1_notch_width_nm",
    "p1_notch_side",
    "target_bin_deg",
    "config_path",
    "fdtd_status",
    "rationale",
]


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    group: str
    family: str
    height_nm: float
    p1_length_nm: float
    p1_width_nm: float
    rationale: str
    p1_shape: str = "rectangle"
    p1_notch_depth_nm: float | None = None
    p1_notch_width_nm: float | None = None
    p1_notch_side: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Stage 09 P165 zero-cliff recovery candidate YAMLs only.")
    parser.add_argument("--anchor-config", type=Path, default=ANCHOR_CONFIG)
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--plan-csv", type=Path, default=PLAN_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notch_supported = repo_supports_notch_schema(REPO_ROOT)
    specs = build_candidate_specs(notch_supported=notch_supported)
    anchor_config = load_yaml(args.anchor_config)
    rows = []
    for spec in specs:
        config = build_candidate_config(anchor_config, spec)
        config_path = args.config_dir / f"{spec.candidate_id}.yaml"
        write_yaml(config_path, config)
        rows.append(plan_row(spec, config_path))
    write_csv_rows(rows, args.plan_csv, PLAN_FIELDS)
    write_report(args.report, rows, notch_supported)
    print(f"plan_csv={args.plan_csv}")
    print(f"report={args.report}")
    print(f"candidate_yaml_count={len(rows)}")
    print("status=stage09_zero_cliff_yaml_generated_no_fdtd_no_lumapi")
    return 0


def build_candidate_specs(*, notch_supported: bool) -> list[CandidateSpec]:
    specs: list[CandidateSpec] = []
    for height in [232.49, 232.48, 232.47, 232.46, 232.45, 232.44]:
        token = height_token(height)
        specs.append(
            CandidateSpec(
                candidate_id=f"cpk_zero_l60_lhs_{token}_p1geom120x58_01",
                group="A",
                family="ultra_fine_height_scan",
                height_nm=height,
                p1_length_nm=120,
                p1_width_nm=58,
                rationale=(
                    "Ultra-fine interpolation between the h232.5 early 60-bin point and the h232.4 "
                    "0-bin selectivity cliff."
                ),
            )
        )
    specs.extend(
        [
            CandidateSpec(
                candidate_id="cpk_zero_l60_lhs_h232p4_p1geom121x58_01",
                group="C",
                family="p1_minor_compensation",
                height_nm=232.4,
                p1_length_nm=121,
                p1_width_nm=58,
                rationale="Length +1 nm compensation at the h232.4 0-bin cliff point.",
            ),
            CandidateSpec(
                candidate_id="cpk_zero_l60_lhs_h232p4_p1geom120x57_01",
                group="C",
                family="p1_minor_compensation",
                height_nm=232.4,
                p1_length_nm=120,
                p1_width_nm=57,
                rationale="Width -1 nm compensation at the h232.4 0-bin cliff point.",
            ),
            CandidateSpec(
                candidate_id="cpk_zero_l60_lhs_h232p4_p1geom119x58_01",
                group="C",
                family="p1_minor_compensation",
                height_nm=232.4,
                p1_length_nm=119,
                p1_width_nm=58,
                rationale="Length -1 nm compensation at the h232.4 0-bin cliff point.",
            ),
        ]
    )
    if notch_supported:
        specs.extend(
            [
                CandidateSpec(
                    candidate_id="cpk_zero_l60_lhs_h232p4_p1geom120x58_notch_p1_right4_01",
                    group="B",
                    family="mild_p1_notch_compensation",
                    height_nm=232.4,
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p1_shape="notched_rectangle",
                    p1_notch_depth_nm=4,
                    p1_notch_width_nm=18,
                    p1_notch_side="right",
                    rationale="Mild right-side p1 notch using existing notched_rectangle schema.",
                ),
                CandidateSpec(
                    candidate_id="cpk_zero_l60_lhs_h232p4_p1geom120x58_notch_p1_right6_01",
                    group="B",
                    family="mild_p1_notch_compensation",
                    height_nm=232.4,
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p1_shape="notched_rectangle",
                    p1_notch_depth_nm=6,
                    p1_notch_width_nm=20,
                    p1_notch_side="right",
                    rationale="Slightly stronger but still mild p1 notch using existing notched_rectangle schema.",
                ),
                CandidateSpec(
                    candidate_id="cpk_zero_l60_lhs_h232p4_p1geom120x58_notch_p1_left4_01",
                    group="B",
                    family="mild_p1_notch_compensation",
                    height_nm=232.4,
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p1_shape="notched_rectangle",
                    p1_notch_depth_nm=4,
                    p1_notch_width_nm=18,
                    p1_notch_side="left",
                    rationale="Opposite-side mild p1 notch check using existing notched_rectangle schema.",
                ),
            ]
        )
    return specs


def build_candidate_config(anchor: dict[str, object], spec: CandidateSpec) -> dict[str, object]:
    config = copy.deepcopy(anchor)
    config.setdefault("project", {})
    config["project"]["stage"] = "09_p165_zero_cliff_recovery_candidate_yaml_only"
    config["candidate"] = {
        "variant_id": spec.candidate_id,
        "candidate_type": spec.family,
        "scheme_name": "zero_cliff_recovery_stage09",
        "description": f"P165 zero-cliff recovery candidate {spec.candidate_id}",
        "target_bins_deg": "0",
        "source_stage": "09-P165",
        "anchor_candidate_id": ANCHOR_ID,
        "source_branch": "aggr_lhs_retention_dy_05 -> p1geom120x58",
        "source_cliff": "h232.5 p1geom early 60-bin versus h232.4 p1geom 0-bin selectivity failure",
        "source_plan_csv": relative_path(PLAN_CSV),
        "notes": (
            "Stage 09 YAML-only zero-bin recovery candidate; not K=6 phase-ramp, not steering, "
            "not stage 10, and not a Micro-LED result."
        ),
    }
    config["boundary"] = {
        "no_k7": True,
        "not_phase_ramp_supercell": True,
        "not_steering_result": True,
        "not_complete_k6_library_claim": True,
        "not_stage10": True,
        "no_fdtd_run_by_generator": True,
    }
    geometry = config.setdefault("geometry", {})
    geometry["period_x_nm"] = 340
    geometry["period_y_nm"] = 340
    geometry["height_nm"] = spec.height_nm
    p1 = geometry.setdefault("nanopillar_1", {})
    p1["shape"] = spec.p1_shape
    p1["length_nm"] = spec.p1_length_nm
    p1["width_nm"] = spec.p1_width_nm
    for key in ("notch_depth_nm", "notch_width_nm", "notch_side"):
        p1.pop(key, None)
    if spec.p1_shape == "notched_rectangle":
        p1["notch_depth_nm"] = spec.p1_notch_depth_nm
        p1["notch_width_nm"] = spec.p1_notch_width_nm
        p1["notch_side"] = spec.p1_notch_side
    output = config.setdefault("output", {})
    output["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{spec.candidate_id}"
    return config


def plan_row(spec: CandidateSpec, config_path: Path) -> dict[str, object]:
    return {
        "candidate_id": spec.candidate_id,
        "group": spec.group,
        "family": spec.family,
        "anchor_candidate_id": ANCHOR_ID,
        "height_nm": spec.height_nm,
        "period_x_nm": 340,
        "period_y_nm": 340,
        "p1_shape": spec.p1_shape,
        "p1_length_nm": spec.p1_length_nm,
        "p1_width_nm": spec.p1_width_nm,
        "p1_notch_depth_nm": "" if spec.p1_notch_depth_nm is None else spec.p1_notch_depth_nm,
        "p1_notch_width_nm": "" if spec.p1_notch_width_nm is None else spec.p1_notch_width_nm,
        "p1_notch_side": "" if spec.p1_notch_side is None else spec.p1_notch_side,
        "target_bin_deg": 0,
        "config_path": relative_path(config_path),
        "fdtd_status": "not_run",
        "rationale": spec.rationale,
    }


def repo_supports_notch_schema(repo_root: Path) -> bool:
    config_hit = any((repo_root / "configs/apcd_k6_phase_state_candidates").glob("*notch*.yaml"))
    source_path = repo_root / "src/metasurface/apcd_dimer.py"
    source_hit = source_path.exists() and "notched_rectangle" in source_path.read_text(encoding="utf-8")
    return bool(config_hit and source_hit)


def load_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)
    return path


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def write_report(path: Path, rows: Sequence[dict[str, object]], notch_supported: bool) -> Path:
    group_counts = {group: sum(1 for row in rows if row["group"] == group) for group in ("A", "B", "C")}
    lines = [
        "# P165 zero-cliff recovery candidate plan",
        "",
        "## Scope",
        "",
        "Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim steering.",
        "",
        "## Design Basis",
        "",
        "- current early-pass rule: target >= 0.5, leakage <= 0.2, ratio >= 6",
        "- bins: [-180, -120, -60, 0, 60, 120]",
        "- current coverage: [-180, -120, -60, 60, 120]",
        "- missing bin: [0]",
        "- zero branch: `aggr_lhs_retention_dy_05 -> p1geom120x58`",
        "- cliff: h232.5 remains 60-bin early-pass; h232.4 enters 0-bin but fails selectivity",
        "",
        "## Candidate Groups",
        "",
        f"- Group A ultra-fine height scan: {group_counts['A']} candidates",
        f"- Group B mild p1 notch check: {group_counts['B']} candidates",
        f"- Group C p1 minor compensation: {group_counts['C']} candidates",
        "",
        "## Notch Schema Check",
        "",
        (
            "Existing `notched_rectangle` schema was found in the repo, so Group B was generated using that schema."
            if notch_supported
            else "No compatible existing notch schema was found, so Group B was skipped rather than inventing YAML fields."
        ),
        "",
        "## Next Step",
        "",
        "Run real FDTD manually on the server only after reviewing the YAMLs. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def height_token(height_nm: float) -> str:
    text = f"{height_nm:g}".replace(".", "p")
    return f"h{text}"


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
