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
OFFICIAL_HEIGHT_NM = 233
BASE_P1_LENGTH_NM = 120
BASE_P1_WIDTH_NM = 58
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
ANCHOR_CONFIG = CONFIG_DIR / f"{ANCHOR_ID}.yaml"
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
PLAN_CSV = ACTIVE_DIR / "combined_phase_knob_p173_fixed_h233_resonance_phase_candidate_plan.csv"
REPORT_MD = REPO_ROOT / "reports/combined_phase_knob_p173_fixed_h233_resonance_phase_candidate_plan.md"

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
    "p2_shape",
    "p2_length_nm",
    "p2_width_nm",
    "p2_notch_depth_nm",
    "p2_notch_width_nm",
    "p2_notch_side",
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
    p1_length_nm: int
    p1_width_nm: int
    p2_length_nm: int
    p2_width_nm: int
    rationale: str
    p1_shape: str = "rectangle"
    p1_notch_depth_nm: int | None = None
    p1_notch_width_nm: int | None = None
    p1_notch_side: str | None = None
    p2_shape: str = "rectangle"
    p2_notch_depth_nm: int | None = None
    p2_notch_width_nm: int | None = None
    p2_notch_side: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Stage 09 P173 fixed-h233 integer resonance-phase candidate YAMLs only."
    )
    parser.add_argument("--anchor-config", type=Path, default=ANCHOR_CONFIG)
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--plan-csv", type=Path, default=PLAN_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    notch_supported = repo_supports_notch_schema(REPO_ROOT)
    specs = build_candidate_specs(notch_supported=notch_supported)
    if len(specs) > 12:
        raise ValueError(f"P173 selected too many candidates: {len(specs)}")
    anchor_config = load_yaml(args.anchor_config)
    rows = []
    for spec in specs:
        config = build_candidate_config(anchor_config, spec)
        config_path = args.config_dir / f"{spec.candidate_id}.yaml"
        write_yaml(config_path, config)
        rows.append(plan_row(spec, config_path))
    assert_integer_geometry(rows)
    write_csv_rows(rows, args.plan_csv, PLAN_FIELDS)
    write_report(args.report, rows, notch_supported)
    print(f"plan_csv={args.plan_csv}")
    print(f"report={args.report}")
    print(f"candidate_yaml_count={len(rows)}")
    print("status=stage09_fixed_h233_resonance_phase_yaml_generated_no_fdtd_no_lumapi")
    return 0


def build_candidate_specs(*, notch_supported: bool) -> list[CandidateSpec]:
    specs = [
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom74x135_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=74,
            p2_width_nm=135,
            rationale="Mild p2 length -1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom76x135_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=76,
            p2_width_nm=135,
            rationale="Mild p2 length +1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom75x134_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=75,
            p2_width_nm=134,
            rationale="Mild p2 width -1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom75x136_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=75,
            p2_width_nm=136,
            rationale="Mild p2 width +1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom74x134_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=74,
            p2_width_nm=134,
            rationale="Coupled p2 length/width -1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x58_p2geom76x136_01",
            group="A",
            family="p2_dynamic_resonance_phase_scan",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=76,
            p2_width_nm=136,
            rationale="Coupled p2 length/width +1 nm resonance-phase check at fixed h233.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom119x58_01",
            group="B",
            family="p1_minor_compensation_fixed_h233",
            p1_length_nm=119,
            p1_width_nm=58,
            p2_length_nm=75,
            p2_width_nm=135,
            rationale="p1 length -1 nm compensation while preserving fixed h233 route.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom118x58_01",
            group="B",
            family="p1_minor_compensation_fixed_h233",
            p1_length_nm=118,
            p1_width_nm=58,
            p2_length_nm=75,
            p2_width_nm=135,
            rationale="p1 length -2 nm compensation while preserving fixed h233 route.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h233_p1geom120x57_01",
            group="B",
            family="p1_minor_compensation_fixed_h233",
            p1_length_nm=120,
            p1_width_nm=57,
            p2_length_nm=75,
            p2_width_nm=135,
            rationale="p1 width -1 nm compensation while preserving fixed h233 route.",
        ),
    ]
    if notch_supported:
        specs.extend(
            [
                CandidateSpec(
                    candidate_id="cpk_zero_l60_h233_p1geom120x58_notch_p1_right4_01",
                    group="C",
                    family="mild_notch_fixed_h233",
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p2_length_nm=75,
                    p2_width_nm=135,
                    p1_shape="notched_rectangle",
                    p1_notch_depth_nm=4,
                    p1_notch_width_nm=18,
                    p1_notch_side="right",
                    rationale="Mild p1 right-side notch at fixed h233 using existing schema.",
                ),
                CandidateSpec(
                    candidate_id="cpk_zero_l60_h233_p1geom120x58_notch_p1_left4_01",
                    group="C",
                    family="mild_notch_fixed_h233",
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p2_length_nm=75,
                    p2_width_nm=135,
                    p1_shape="notched_rectangle",
                    p1_notch_depth_nm=4,
                    p1_notch_width_nm=18,
                    p1_notch_side="left",
                    rationale="Mild p1 left-side notch at fixed h233 using existing schema.",
                ),
                CandidateSpec(
                    candidate_id="cpk_zero_l60_h233_p1geom120x58_notch_p2_right4_01",
                    group="C",
                    family="mild_notch_fixed_h233",
                    p1_length_nm=120,
                    p1_width_nm=58,
                    p2_length_nm=75,
                    p2_width_nm=135,
                    p2_shape="notched_rectangle",
                    p2_notch_depth_nm=4,
                    p2_notch_width_nm=20,
                    p2_notch_side="right",
                    rationale="Mild p2 right-side notch at fixed h233 using existing schema.",
                ),
            ]
        )
    return specs


def build_candidate_config(anchor: dict[str, object], spec: CandidateSpec) -> dict[str, object]:
    config = copy.deepcopy(anchor)
    config.setdefault("project", {})
    config["project"]["stage"] = "09_p173_fixed_h233_resonance_phase_candidate_yaml_only"
    config["candidate"] = {
        "variant_id": spec.candidate_id,
        "candidate_type": spec.family,
        "scheme_name": "fabrication_aware_fixed_h233_zero_resonance_phase_stage09",
        "description": f"P173 fixed-h233 zero resonance-phase candidate {spec.candidate_id}",
        "target_bins_deg": "0",
        "source_stage": "09-P173",
        "anchor_candidate_id": ANCHOR_ID,
        "baseline_candidate_id": "cpk_zero_l60_lhs_h233_p1geom120x58_01",
        "baseline_phase_deg": 36.27,
        "baseline_nearest_bin_deg": 60,
        "source_note_md": "reports/combined_phase_knob_p172_fixed_h233_resonance_phase_note.md",
        "source_plan_csv": relative_path(PLAN_CSV),
        "fabrication_rule": "official candidates use integer-nm geometry at fixed height_nm=233",
        "notes": (
            "Stage 09 YAML-only fixed-h233 zero-bin resonance-phase candidate; not K=6 phase-ramp, "
            "not steering, not stage 10, and not a Micro-LED result."
        ),
    }
    config["boundary"] = {
        "no_k7": True,
        "not_phase_ramp_supercell": True,
        "not_steering_result": True,
        "not_complete_k6_library_claim": True,
        "not_stage10": True,
        "no_fdtd_run_by_generator": True,
        "integer_nm_official_geometry": True,
        "fixed_height_nm": OFFICIAL_HEIGHT_NM,
    }
    geometry = config.setdefault("geometry", {})
    geometry["period_x_nm"] = 340
    geometry["period_y_nm"] = 340
    geometry["height_nm"] = OFFICIAL_HEIGHT_NM
    p1 = geometry.setdefault("nanopillar_1", {})
    p1["shape"] = spec.p1_shape
    p1["length_nm"] = spec.p1_length_nm
    p1["width_nm"] = spec.p1_width_nm
    clear_notch(p1)
    if spec.p1_shape == "notched_rectangle":
        p1["notch_depth_nm"] = spec.p1_notch_depth_nm
        p1["notch_width_nm"] = spec.p1_notch_width_nm
        p1["notch_side"] = spec.p1_notch_side
    p2 = geometry.setdefault("nanopillar_2", {})
    p2["shape"] = spec.p2_shape
    p2["length_nm"] = spec.p2_length_nm
    p2["width_nm"] = spec.p2_width_nm
    clear_notch(p2)
    if spec.p2_shape == "notched_rectangle":
        p2["notch_depth_nm"] = spec.p2_notch_depth_nm
        p2["notch_width_nm"] = spec.p2_notch_width_nm
        p2["notch_side"] = spec.p2_notch_side
    output = config.setdefault("output", {})
    output["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{spec.candidate_id}"
    return config


def clear_notch(pillar: dict[str, object]) -> None:
    for key in ("notch_depth_nm", "notch_width_nm", "notch_side"):
        pillar.pop(key, None)


def plan_row(spec: CandidateSpec, config_path: Path) -> dict[str, object]:
    return {
        "candidate_id": spec.candidate_id,
        "group": spec.group,
        "family": spec.family,
        "anchor_candidate_id": ANCHOR_ID,
        "height_nm": OFFICIAL_HEIGHT_NM,
        "period_x_nm": 340,
        "period_y_nm": 340,
        "p1_shape": spec.p1_shape,
        "p1_length_nm": spec.p1_length_nm,
        "p1_width_nm": spec.p1_width_nm,
        "p1_notch_depth_nm": "" if spec.p1_notch_depth_nm is None else spec.p1_notch_depth_nm,
        "p1_notch_width_nm": "" if spec.p1_notch_width_nm is None else spec.p1_notch_width_nm,
        "p1_notch_side": "" if spec.p1_notch_side is None else spec.p1_notch_side,
        "p2_shape": spec.p2_shape,
        "p2_length_nm": spec.p2_length_nm,
        "p2_width_nm": spec.p2_width_nm,
        "p2_notch_depth_nm": "" if spec.p2_notch_depth_nm is None else spec.p2_notch_depth_nm,
        "p2_notch_width_nm": "" if spec.p2_notch_width_nm is None else spec.p2_notch_width_nm,
        "p2_notch_side": "" if spec.p2_notch_side is None else spec.p2_notch_side,
        "target_bin_deg": 0,
        "config_path": relative_path(config_path),
        "fdtd_status": "not_run",
        "rationale": spec.rationale,
    }


def assert_integer_geometry(rows: Sequence[dict[str, object]]) -> None:
    integer_fields = [
        "height_nm",
        "period_x_nm",
        "period_y_nm",
        "p1_length_nm",
        "p1_width_nm",
        "p1_notch_depth_nm",
        "p1_notch_width_nm",
        "p2_length_nm",
        "p2_width_nm",
        "p2_notch_depth_nm",
        "p2_notch_width_nm",
    ]
    for row in rows:
        for field in integer_fields:
            value = row.get(field, "")
            if value == "":
                continue
            if float(value) != int(float(value)):
                raise ValueError(f"Non-integer official geometry found for {row['candidate_id']}: {field}={value}")


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
        "# P173 fixed h233 resonance-phase candidate plan",
        "",
        "## Scope",
        "",
        "Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering.",
        "",
        "## Design Basis",
        "",
        "- h232 route reaches the 0-bin but fails selection.",
        "- h233 p1geom120x58 preserves selection and is about 6 deg from the 0-bin boundary.",
        "- official route fixes `height_nm = 233`.",
        "- all official P173 geometry parameters are integer nm values.",
        "- target: move phase below 30 deg while keeping target >= 0.5, leakage <= 0.2, ratio >= 6.",
        "",
        "## Candidate Groups",
        "",
        f"- Group A p2 dynamic-resonance phase scan: {group_counts['A']} candidates",
        f"- Group B p1 minor compensation at fixed h233: {group_counts['B']} candidates",
        f"- Group C mild notch at fixed h233: {group_counts['C']} candidates",
        "",
        "## Notch Schema Check",
        "",
        (
            "Existing `notched_rectangle` schema was found in the repo, so Group C was generated using that schema."
            if notch_supported
            else "No compatible existing notch schema was found, so Group C was skipped rather than inventing YAML fields."
        ),
        "",
        "## Next Step",
        "",
        "Review these YAMLs, then run real FDTD manually on the server if approved. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
