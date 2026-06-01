from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "23_export_apcd_k6_candidate_setup_fsp.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("candidate_setup_export", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate setup export script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_script_can_be_imported() -> None:
    module = _load_script_module()

    assert module.DEFAULT_VARIANT_ID == "baseline"


def test_default_variant_id_and_output_path_are_baseline() -> None:
    module = _load_script_module()
    args = module.parse_args([])
    output_path = module.resolve_fsp_output(args.variant_id, args.fsp_output)

    assert args.variant_id == "baseline"
    assert output_path == REPO_ROOT / "outputs" / "apcd_k6_phase_state_candidates" / "baseline" / "baseline_setup.fsp"


def test_baseline_config_exists_and_geometry_is_alpha_pass() -> None:
    module = _load_script_module()
    config_path = module.candidate_config_path("baseline")
    config = module.load_candidate_config("baseline")
    p1 = config.geometry.nanopillar_1
    p2 = config.geometry.nanopillar_2

    assert config_path.exists()
    assert p1.length_nm == 130
    assert p1.width_nm == 70
    assert p1.rotation_deg == 67.5
    assert p2.length_nm == 85
    assert p2.width_nm == 150
    assert p2.rotation_deg == 112.5
    assert not (p2.length_nm == 150 and p2.width_nm == 85)


def test_dry_run_plan_reports_geometry_without_writing_fsp(tmp_path: Path) -> None:
    module = _load_script_module()
    fsp_output = tmp_path / "baseline_setup.fsp"
    plan = module.dry_run_plan("baseline", "configs/runtime.yaml", fsp_output)

    assert plan["status"] == "dry_run_setup_only_plan"
    assert plan["variant_id"] == "baseline"
    assert plan["no_fdtd_run"] is True
    assert plan["no_fsp_written"] is True
    assert plan["pillar_1"] == "130 x 70 nm, rotation 67.5 deg"
    assert plan["pillar_2"] == "85 x 150 nm, rotation 112.5 deg"
    assert not fsp_output.exists()


def test_cli_dry_run_does_not_generate_fsp(tmp_path: Path) -> None:
    fsp_output = tmp_path / "baseline_setup.fsp"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--variant-id",
            "baseline",
            "--fsp-output",
            str(fsp_output),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=dry_run_setup_only_plan" in completed.stdout
    assert "variant_id=baseline" in completed.stdout
    assert "no_fdtd_run=True" in completed.stdout
    assert "no_fsp_written=True" in completed.stdout
    assert not fsp_output.exists()


def test_setup_only_uses_runner_without_fdtd_run_when_mocked(tmp_path: Path) -> None:
    module = _load_script_module()
    calls: list[dict[str, object]] = []

    class _FakeRunner:
        def __init__(self, **kwargs: object) -> None:
            self.kwargs = kwargs

        def run(self) -> dict[str, object]:
            calls.append(self.kwargs)
            return {
                "status": "setup_only",
                "gate_pass": "",
                "target_conversion": "",
                "opposite_spin_leakage": "",
                "spin_ER_dB": "",
                "note": "mock model saved; solver was not run",
                "PD": "",
            }

    def _factory(**kwargs: object) -> _FakeRunner:
        return _FakeRunner(**kwargs)

    runtime = tmp_path / "runtime.yaml"
    runtime.write_text("runtime:\n  enable_lumerical: false\nlumapi:\n  python_api_dir: ''\n", encoding="utf-8")
    fsp_output = tmp_path / "baseline_setup.fsp"

    row = module.export_candidate_setup_only(
        variant_id="baseline",
        runtime=str(runtime),
        fsp_output=fsp_output,
        runner_factory=_factory,
        summary_writer=lambda _row, path: path,
    )

    assert row["status"] == "setup_only"
    assert calls
    assert calls[0]["setup_only"] is True
    assert calls[0]["dry_run"] is False
    assert calls[0]["fsp_output"] == fsp_output
    assert not fsp_output.exists()


def test_script_text_does_not_call_fdtd_run_or_save_directly() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_setup_export_report_states_boundaries() -> None:
    text = (REPO_ROOT / "reports" / "apcd_k6_candidate_setup_export_workflow.md").read_text(encoding="utf-8")

    assert "08-P6" in text
    assert "single-candidate setup-only" in text
    assert "default candidate is `baseline`" in text
    assert "does not run FDTD" in text
    assert "does not evaluate any real candidate" in text
    assert "does not do K=7" in text
    assert "does not do a sweep" in text
    assert "does not build a phase-ramp supercell" in text
    assert "does not prove `+15 deg` steering" in text
    assert "must not enter Git" in text
    assert "future run is not part of 08-P6" in text
