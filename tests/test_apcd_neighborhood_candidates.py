from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_neighborhood_candidates import (
    NEIGHBORHOOD_CANDIDATE_FIELDS,
    build_neighborhood_candidate_pool,
    export_neighborhood_candidate_pool,
    load_reference_candidate_config,
    summarize_neighborhood_candidate_pool,
    validate_neighborhood_candidate_bounds,
)


P1W_DX_CONFIG = REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates" / "doe_p1w_dx_01.yaml"
LHS_CONFIG = REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates" / "doe_lhs_like_01.yaml"
SCRIPT_PATH = REPO_ROOT / "scripts" / "31_generate_apcd_k6_neighborhood_candidate_pool.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_neighborhood_candidate_pool_v1_note.md"


def _candidate_pool() -> list[dict[str, object]]:
    p1w_dx = load_reference_candidate_config(P1W_DX_CONFIG)
    lhs = load_reference_candidate_config(LHS_CONFIG)
    return build_neighborhood_candidate_pool(p1w_dx, lhs)


def test_can_read_reference_candidate_configs() -> None:
    p1w_dx = load_reference_candidate_config(P1W_DX_CONFIG)
    lhs = load_reference_candidate_config(LHS_CONFIG)

    assert p1w_dx["candidate_id"] == "doe_p1w_dx_01"
    assert p1w_dx["p1_width_nm"] == 60
    assert p1w_dx["internal_dx_nm"] == -30
    assert lhs["candidate_id"] == "doe_lhs_like_01"
    assert lhs["p1_length_nm"] == 110
    assert lhs["internal_dy_nm"] == 30


def test_neighborhood_candidate_count_is_20_to_36() -> None:
    candidates = _candidate_pool()

    assert 20 <= len(candidates) <= 36


def test_candidate_ids_are_unique() -> None:
    candidates = _candidate_pool()
    ids = [row["candidate_id"] for row in candidates]

    assert len(ids) == len(set(ids))


def test_candidate_families_include_required_groups() -> None:
    candidates = _candidate_pool()
    summary = summarize_neighborhood_candidate_pool(candidates)

    assert summary["family_counts"] == {
        "bridge_dx_lhs": 4,
        "lhs_like_leakage_reduction": 10,
        "p1w_dx_neighborhood": 10,
    }


def test_all_parameters_are_in_bounds_and_rotations_fixed() -> None:
    candidates = _candidate_pool()

    for candidate in candidates:
        assert validate_neighborhood_candidate_bounds(candidate, strict=False) == []
        assert candidate["p1_rotation_deg"] == 67.5
        assert candidate["p2_rotation_deg"] == 112.5


def test_no_beta_selective_pillar2_baseline() -> None:
    candidates = _candidate_pool()

    for candidate in candidates:
        assert not (candidate["p2_length_nm"] == 150 and candidate["p2_width_nm"] == 85)


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    candidates = _candidate_pool()
    output_csv = export_neighborhood_candidate_pool(candidates, tmp_path / "neighborhood.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == NEIGHBORHOOD_CANDIDATE_FIELDS
    assert len(loaded) == len(candidates)
    assert {row["status"] for row in loaded} == {"not_evaluated"}
    assert {row["requires_fdtd"] for row in loaded} == {"true"}
    assert {row["requires_geometry_validation"] for row in loaded} == {"true"}


def test_cli_dry_run_does_not_write_outputs_or_generate_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "neighborhood_candidate_pool_v1.csv"
    summary_md = tmp_path / "neighborhood_candidate_pool_v1_summary.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--output-csv",
            str(output_csv),
            "--summary-md",
            str(summary_md),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=neighborhood_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    assert "candidate_count=24" in completed.stdout
    assert "dry_run=true; no output files written" in completed.stdout
    assert not output_csv.exists()
    assert not summary_md.exists()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run_or_save() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_neighborhood_candidates.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in script_text
    assert "fdtd.run" not in script_text
    assert "fdtd.save" not in script_text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_candidate_pool_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P6" in text
    assert "only generates a neighborhood candidate pool" in text
    assert "No FDTD run was" in text
    assert "no lumapi call" in text
    assert "no surrogate was trained" in text
    assert "no `.fsp` file was exported" in text
    assert "not a `+15 deg` steering result" in text
    assert "candidate-pool only" in text
