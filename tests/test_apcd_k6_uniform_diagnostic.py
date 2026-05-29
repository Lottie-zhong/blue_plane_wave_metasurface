from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "19_run_apcd_k6_uniform_diffraction_diagnostic.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("k6_diagnostic", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load diagnostic script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _clean_output_dir() -> None:
    output_dir = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "diagnostic_uniform_run"
    if output_dir.exists():
        shutil.rmtree(output_dir)


def test_fake_run_cli_writes_diagnostic_outputs() -> None:
    _clean_output_dir()
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--fake-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output_dir = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "diagnostic_uniform_run"
    assert completed.returncode == 0
    assert (output_dir / "diffraction_orders_X.csv").exists()
    assert (output_dir / "diffraction_orders_Y.csv").exists()
    assert (output_dir / "order_resolved_jones.csv").exists()
    assert (output_dir / "diagnostic_summary.md").exists()
    assert (output_dir / "run_log.txt").exists()
    text = (output_dir / "diagnostic_summary.md").read_text(encoding="utf-8")
    assert "This is not the final metagrating" in text
    assert "diagnostic run" in text
    assert "uniform identical alpha-pass dimer scaffold" in text


def test_fake_fdtd_lifecycle_runs_x_y_and_no_switchtolayout_after_run() -> None:
    module = _load_script_module()
    _clean_output_dir()
    instances = []

    def factory():
        fdtd = module._FakeFDTD()
        instances.append(fdtd)
        return fdtd

    module.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module._run_diagnostic(factory, ["mode=test"])

    assert len(instances) == 4
    assert sum(1 for fdtd in instances if fdtd.run_called) == 2
    assert all(fdtd.switch_after_run is False for fdtd in instances)
    run_instances = [fdtd for fdtd in instances if fdtd.run_called]
    for fdtd in run_instances:
        assert "grating:T" in fdtd.calls
        assert "gratingn:T" in fdtd.calls
        assert "gratingm:T" in fdtd.calls
        assert "gratingu1:T" in fdtd.calls
        assert "gratingu2:T" in fdtd.calls
        assert "transmission:T" in fdtd.calls


def test_fake_gratingvector_available_generates_order_resolved_jones() -> None:
    module = _load_script_module()
    _clean_output_dir()
    module.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module._run_diagnostic(lambda: module._FakeFDTD(), ["mode=test"])

    text = (module.OUTPUT_DIR / "diagnostic_summary.md").read_text(encoding="utf-8")
    assert "gratingvector or complex field extraction: success" in text
    assert "order-resolved Jones construction: success" in text
    assert "target_conversion" in (module.OUTPUT_DIR / "order_resolved_jones.csv").read_text(encoding="utf-8")


def test_missing_gratingvector_marks_jones_unavailable() -> None:
    module = _load_script_module()
    _clean_output_dir()
    instances = []

    def factory():
        fdtd = _FakeFDTDNoVector()
        instances.append(fdtd)
        return fdtd

    module.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    module._run_diagnostic(factory, ["mode=test_no_vector"])

    text = (module.OUTPUT_DIR / "diagnostic_summary.md").read_text(encoding="utf-8")
    assert "gratingvector or complex field extraction: failed" in text
    assert "APCD order-resolved Jones metrics are not available" in text
    assert (module.OUTPUT_DIR / "order_resolved_jones.csv").exists()
    assert sum(1 for fdtd in instances if fdtd.run_called) == 2


def test_dry_run_cli_does_not_run_fdtd() -> None:
    _clean_output_dir()
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    output_dir = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "diagnostic_uniform_run"
    assert completed.returncode == 0
    assert "no FDTD session was created" in (output_dir / "run_log.txt").read_text(encoding="utf-8")


class _FakeFDTDNoVector:
    def __init__(self) -> None:
        self.run_called = False
        self.switch_after_run = False
        self.calls: list[str] = []

    def load(self, _path: str) -> None:
        pass

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fake fsp")

    def setnamed(self, name: str, prop: str, value: object) -> None:
        self.calls.append(f"setnamed:{name}:{prop}:{value}")

    def run(self) -> None:
        self.run_called = True
        self.calls.append("run")

    def switchtolayout(self) -> None:
        if self.run_called:
            self.switch_after_run = True

    def gratingn(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingn:{monitor_name}")
        return [-1, 0, 1]

    def gratingm(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingm:{monitor_name}")
        return [0, 0, 0]

    def gratingu1(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu1:{monitor_name}")
        return [-0.2588190451, 0.0, 0.2588190451]

    def gratingu2(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu2:{monitor_name}")
        return [0.0, 0.0, 0.0]

    def grating(self, monitor_name: str) -> list[float]:
        self.calls.append(f"grating:{monitor_name}")
        return [0.02, 0.96, 0.02]

    def transmission(self, monitor_name: str) -> float:
        self.calls.append(f"transmission:{monitor_name}")
        return 0.5

    def close(self) -> None:
        pass
