from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/70_remote_run_apcd_candidate.py"


@pytest.fixture(scope="module")
def remote_runner_module():
    spec = importlib.util.spec_from_file_location("apcd_remote_candidate_runner", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_ssh_command_construction(remote_runner_module) -> None:
    command = remote_runner_module.build_ssh_command(
        ssh_host="lumerical-win",
        server_root=r"D:\project\blue_plane_wave_metasurface",
        server_python=r"N:\anaconda_envs\RCP_LCP\python.exe",
        candidate_id="cpk_mbin_lower_transition_01",
        config=r"configs\apcd_k6_phase_state_candidates\cpk_mbin_lower_transition_01.yaml",
        runtime=r"configs\runtime.yaml",
    )

    assert command[:7] == [
        "ssh",
        "lumerical-win",
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
    ]
    remote = command[-1]
    assert "git pull --ff-only | Out-Null" in remote
    assert r"N:\anaconda_envs\RCP_LCP\python.exe" in remote
    assert r"scripts\13_run_apcd_single_dimer.py" in remote
    assert r"scripts\70_remote_run_apcd_candidate.py" in remote
    assert "--parse-local-only" in remote
    assert "--candidate-id 'cpk_mbin_lower_transition_01'" in remote


def test_remote_command_suppresses_noncompact_stdout(remote_runner_module) -> None:
    remote = remote_runner_module.build_remote_powershell_command(
        server_root=r"D:\project\blue_plane_wave_metasurface",
        server_python=r"N:\anaconda_envs\RCP_LCP\python.exe",
        candidate_id="cpk_mbin_lower_transition_01",
        config=r"configs\apcd_k6_phase_state_candidates\cpk_mbin_lower_transition_01.yaml",
        runtime=r"configs\runtime.yaml",
    )

    assert "git pull --ff-only | Out-Null" in remote
    assert r"scripts\13_run_apcd_single_dimer.py" in remote
    assert r"--runtime 'configs\runtime.yaml' | Out-Null" in remote


def test_phase_and_bin_logic(remote_runner_module) -> None:
    assert remote_runner_module.phase_deg_from_complex("-1+0j") == pytest.approx(-180.0)
    assert remote_runner_module.phase_deg_from_complex("0+1j") == pytest.approx(90.0)

    nearest, error = remote_runner_module.nearest_phase_bin(179.0, remote_runner_module.TARGET_BINS_DEG)
    assert nearest == -180.0
    assert error == pytest.approx(1.0)

    nearest, error = remote_runner_module.nearest_phase_bin(59.5, remote_runner_module.REMAINING_MISSING_BINS_DEG)
    assert nearest == 60.0
    assert error == pytest.approx(0.5)


def test_compact_parser_logic(remote_runner_module) -> None:
    raw = {
        "t_alpha_star_from_alpha": "0.5+0.8660254037844386j",
        "target_conversion": "0.9",
        "opposite_spin_leakage": "0.1",
        "conversion_to_leakage_ratio": "9.0",
        "PD": "0.8",
    }
    metrics = remote_runner_module.compact_metrics_from_raw("cpk_mbin_lower_transition_01", raw)

    assert metrics == {
        "candidate_id": "cpk_mbin_lower_transition_01",
        "phase_deg": pytest.approx(60.0),
        "nearest_target_bin_deg": 60,
        "best_remaining_missing_bin_deg": 60,
        "target_conversion": pytest.approx(0.9),
        "opposite_spin_leakage": pytest.approx(0.1),
        "conversion_to_leakage_ratio": pytest.approx(9.0),
        "PD": pytest.approx(0.8),
        "early_pass": True,
        "near_pass": False,
        "opens_missing_bin": True,
    }


def test_near_pass_compact_parser_logic(remote_runner_module) -> None:
    raw = {
        "t_alpha_star_from_alpha": "1+0j",
        "target_conversion": "0.7",
        "opposite_spin_leakage": "0.24",
        "conversion_to_leakage_ratio": "3.5",
        "PD": "0.5",
    }
    metrics = remote_runner_module.compact_metrics_from_raw("cpk_mbin_lower_transition_01", raw)

    assert metrics["nearest_target_bin_deg"] == 0
    assert metrics["early_pass"] is False
    assert metrics["near_pass"] is True
    assert metrics["opens_missing_bin"] is False


def test_print_compact_metrics_order(remote_runner_module, capsys) -> None:
    metrics = {
        "candidate_id": "cpk_mbin_lower_transition_01",
        "phase_deg": 60.0,
        "nearest_target_bin_deg": 60,
        "best_remaining_missing_bin_deg": 60,
        "target_conversion": 0.9,
        "opposite_spin_leakage": 0.1,
        "conversion_to_leakage_ratio": 9.0,
        "PD": 0.8,
        "early_pass": True,
        "near_pass": False,
        "opens_missing_bin": True,
    }

    remote_runner_module.print_compact_metrics(metrics)
    lines = capsys.readouterr().out.splitlines()

    assert lines == [
        "candidate_id=cpk_mbin_lower_transition_01",
        "phase_deg=60.0",
        "nearest_target_bin_deg=60",
        "best_remaining_missing_bin_deg=60",
        "target_conversion=0.9",
        "opposite_spin_leakage=0.1",
        "conversion_to_leakage_ratio=9.0",
        "PD=0.8",
        "early_pass=True",
        "near_pass=False",
        "opens_missing_bin=True",
    ]


def test_no_raw_results_fsp_pre_run_or_npy_files_are_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    tracked = completed.stdout.splitlines()
    forbidden = [
        path
        for path in tracked
        if path.endswith("/results.csv")
        or path.endswith("/summary.md")
        or path.endswith(".fsp")
        or path.endswith(".npy")
        or "/pre_run" in path
    ]
    assert forbidden == []
