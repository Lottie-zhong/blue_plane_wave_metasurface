from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "22_generate_apcd_k6_candidate_config_scaffold.py"
CONFIG_DIR = REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates"
INDEX_CSV = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_candidate_config_index.csv"

VARIANT_IDS = [
    "baseline",
    "p1L_m10",
    "p1L_m5",
    "p1L_p5",
    "p1L_p10",
    "p1W_m5",
    "p1W_p5",
    "p2L_m5",
    "p2L_p5",
    "p2W_m10",
    "p2W_m5",
    "p2W_p5",
    "p2W_p10",
]

BOUNDARY_FLAGS = {
    "no_fdtd_run_in_this_step": True,
    "no_fsp_export_in_this_step": True,
    "not_k7": True,
    "not_sweep": True,
    "not_phase_ramp_supercell": True,
    "not_steering_result": True,
}


def _load_script_module():
    spec = importlib.util.spec_from_file_location("candidate_config_scaffold", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate config scaffold script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    assert isinstance(data, dict)
    return data


def _index_rows() -> list[dict[str, str]]:
    with INDEX_CSV.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_script_can_be_imported_and_reads_13_variants() -> None:
    module = _load_script_module()
    rows = module.read_candidate_route("outputs/apcd_k6_metagrating_633nm/phase_state_candidate_route.csv")

    assert len(rows) == 13
    assert [row["variant_id"] for row in rows] == VARIANT_IDS


def test_variant_ids_are_unique_and_config_count_is_13() -> None:
    index_rows = _index_rows()

    config_paths = [CONFIG_DIR / f"{variant_id}.yaml" for variant_id in VARIANT_IDS]
    assert all(path.is_file() for path in config_paths)
    assert len(index_rows) == 13
    assert len({row["variant_id"] for row in index_rows}) == 13
    assert [row["variant_id"] for row in index_rows] == VARIANT_IDS


def test_baseline_config_uses_alpha_pass_geometry() -> None:
    data = _load_yaml(CONFIG_DIR / "baseline.yaml")
    geometry = data["geometry"]
    assert isinstance(geometry, dict)
    p1 = geometry["nanopillar_1"]
    p2 = geometry["nanopillar_2"]

    assert p1["length_nm"] == 130
    assert p1["width_nm"] == 70
    assert p1["rotation_deg"] == 67.5
    assert p2["length_nm"] == 85
    assert p2["width_nm"] == 150
    assert p2["rotation_deg"] == 112.5


def test_all_configs_preserve_phase1_common_settings_and_boundary_flags() -> None:
    for variant_id in VARIANT_IDS:
        data = _load_yaml(CONFIG_DIR / f"{variant_id}.yaml")
        target = data["target"]
        material = data["material"]
        geometry = data["geometry"]
        boundary = data["boundary"]

        assert target["wavelength_nm"] == 633
        assert target["psi_deg"] == 112.5
        assert target["chi_deg"] == 22.5
        assert material["meta_material"] == "c-Si"
        assert material["substrate"] == "Al2O3"
        assert geometry["period_x_nm"] == 340
        assert geometry["period_y_nm"] == 340
        assert geometry["height_nm"] == 300
        assert boundary == BOUNDARY_FLAGS


def test_no_config_uses_beta_selective_pillar2_baseline() -> None:
    for variant_id in VARIANT_IDS:
        data = _load_yaml(CONFIG_DIR / f"{variant_id}.yaml")
        p2 = data["geometry"]["nanopillar_2"]

        assert not (p2["length_nm"] == 150 and p2["width_nm"] == 85)


def test_p2w_p10_config_sets_pillar2_to_85x160() -> None:
    data = _load_yaml(CONFIG_DIR / "p2W_p10.yaml")
    p2 = data["geometry"]["nanopillar_2"]

    assert p2["length_nm"] == 85
    assert p2["width_nm"] == 160
    assert p2["rotation_deg"] == 112.5


def test_script_text_does_not_call_solver_or_export_fsp() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import_lu" "mapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_dry_run_regenerates_configs_index_and_no_fsp() -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "candidate_count=13" in completed.stdout
    assert "config_count=13" in completed.stdout
    assert "status=dry_run_config_scaffold_only_no_fdtd_no_fsp_not_steering_result" in completed.stdout
    assert all((CONFIG_DIR / f"{variant_id}.yaml").is_file() for variant_id in VARIANT_IDS)
    assert len(_index_rows()) == 13
    assert list(REPO_ROOT.glob("configs/apcd_k6_phase_state_candidates/*.fsp")) == []


def test_p5_report_states_scope_and_next_step() -> None:
    text = (REPO_ROOT / "reports" / "apcd_k6_candidate_config_scaffold_report.md").read_text(
        encoding="utf-8"
    )

    assert "08-P5" in text
    assert "13 single-dimer candidate config scaffolds" in text
    assert "No FDTD run was performed" in text
    assert "No `.fsp` file was exported" in text
    assert "not K=7" in text
    assert "not a large sweep" in text
    assert "not a phase-ramp supercell" in text
    assert "not evidence of `+15 deg` steering" in text
    assert "phase_state_candidate_route.csv" in text
    assert "150 x 85 nm" in text
    assert "future next step is candidate setup-only export workflow" in text
