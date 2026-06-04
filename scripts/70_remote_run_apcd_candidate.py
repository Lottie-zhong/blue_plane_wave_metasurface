from __future__ import annotations

import argparse
import cmath
import csv
import math
import subprocess
import sys
from pathlib import Path
from typing import Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


TARGET_BINS_DEG = [-180.0, -120.0, -60.0, 0.0, 60.0, 120.0]
REMAINING_MISSING_BINS_DEG = [-60.0, 0.0, 60.0]
DEFAULT_SSH_HOST = "lumerical-win"
DEFAULT_SERVER_ROOT = r"D:\project\blue_plane_wave_metasurface"
DEFAULT_SERVER_PYTHON = r"N:\anaconda_envs\RCP_LCP\python.exe"
DEFAULT_RUNTIME = r"configs\runtime.yaml"
RUNNER_SCRIPT = r"scripts\13_run_apcd_single_dimer.py"
SELF_SCRIPT = r"scripts\70_remote_run_apcd_candidate.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run one APCD candidate on the Lumerical server and print compact metrics.")
    parser.add_argument("--candidate-id", required=True)
    parser.add_argument("--config", default=None, help="Candidate YAML path relative to repo root.")
    parser.add_argument("--ssh-host", default=DEFAULT_SSH_HOST)
    parser.add_argument("--server-root", default=DEFAULT_SERVER_ROOT)
    parser.add_argument("--server-python", default=DEFAULT_SERVER_PYTHON)
    parser.add_argument("--runtime", default=DEFAULT_RUNTIME)
    parser.add_argument(
        "--parse-local-only",
        action="store_true",
        help="Server-side helper mode: parse existing results.csv and print compact metrics only.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = args.config or default_config_for_candidate(args.candidate_id)
    if args.parse_local_only:
        metrics = compact_metrics_for_candidate(args.candidate_id)
        print_compact_metrics(metrics)
        return 0

    command = build_ssh_command(
        ssh_host=args.ssh_host,
        server_root=args.server_root,
        server_python=args.server_python,
        candidate_id=args.candidate_id,
        config=config,
        runtime=args.runtime,
    )
    subprocess.run(command, cwd=REPO_ROOT, check=True)
    return 0


def default_config_for_candidate(candidate_id: str) -> str:
    return rf"configs\apcd_k6_phase_state_candidates\{candidate_id}.yaml"


def build_ssh_command(
    *,
    ssh_host: str,
    server_root: str,
    server_python: str,
    candidate_id: str,
    config: str,
    runtime: str,
) -> list[str]:
    remote_command = build_remote_powershell_command(
        server_root=server_root,
        server_python=server_python,
        candidate_id=candidate_id,
        config=config,
        runtime=runtime,
    )
    return [
        "ssh",
        ssh_host,
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-Command",
        remote_command,
    ]


def build_remote_powershell_command(
    *,
    server_root: str,
    server_python: str,
    candidate_id: str,
    config: str,
    runtime: str,
) -> str:
    quoted_root = ps_quote(server_root)
    quoted_python = ps_quote(server_python)
    quoted_candidate = ps_quote(candidate_id)
    quoted_config = ps_quote(config)
    quoted_runtime = ps_quote(runtime)
    return "; ".join(
        [
            "$ErrorActionPreference = 'Stop'",
            f"Set-Location -LiteralPath {quoted_root}",
            "git pull --ff-only | Out-Null",
            (
                f"& {quoted_python} {ps_quote(RUNNER_SCRIPT)} --config {quoted_config} "
                f"--runtime {quoted_runtime} | Out-Null"
            ),
            "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
            (
                f"& {quoted_python} {ps_quote(SELF_SCRIPT)} --candidate-id {quoted_candidate} "
                f"--config {quoted_config} --runtime {quoted_runtime} --parse-local-only"
            ),
            "if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }",
        ]
    )


def ps_quote(value: str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def compact_metrics_for_candidate(candidate_id: str) -> dict[str, object]:
    result_path = result_csv_path(candidate_id)
    if not result_path.exists():
        raise FileNotFoundError(f"Real FDTD result missing on server: {result_path}")
    rows = read_csv_rows(result_path)
    if not rows:
        raise ValueError(f"Result CSV contains no rows: {result_path}")
    return compact_metrics_from_raw(candidate_id, rows[0])


def result_csv_path(candidate_id: str) -> Path:
    return REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / candidate_id / "results.csv"


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def compact_metrics_from_raw(candidate_id: str, raw: dict[str, str]) -> dict[str, object]:
    phase = phase_deg_from_complex(required_text(raw, "t_alpha_star_from_alpha"))
    nearest_bin, _nearest_error = nearest_phase_bin(phase, TARGET_BINS_DEG)
    missing_bin, _missing_error = nearest_phase_bin(phase, REMAINING_MISSING_BINS_DEG)
    target_conversion = required_float(raw, "target_conversion")
    leakage = required_float(raw, "opposite_spin_leakage")
    ratio = required_float(raw, "conversion_to_leakage_ratio")
    pd = required_float(raw, "PD")
    early = early_pass(target_conversion, leakage, ratio)
    near = near_pass(target_conversion, leakage, ratio, early)
    return {
        "candidate_id": candidate_id,
        "phase_deg": phase,
        "nearest_target_bin_deg": _number(nearest_bin),
        "best_remaining_missing_bin_deg": _number(missing_bin),
        "target_conversion": target_conversion,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": pd,
        "early_pass": early,
        "near_pass": near,
        "opens_missing_bin": opens_missing_bin(nearest_bin, early),
    }


def print_compact_metrics(metrics: dict[str, object]) -> None:
    for key in [
        "candidate_id",
        "phase_deg",
        "nearest_target_bin_deg",
        "best_remaining_missing_bin_deg",
        "target_conversion",
        "opposite_spin_leakage",
        "conversion_to_leakage_ratio",
        "PD",
        "early_pass",
        "near_pass",
        "opens_missing_bin",
    ]:
        print(f"{key}={metrics[key]}")


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def nearest_phase_bin(phase_deg: float, bins: Sequence[float]) -> tuple[float, float]:
    if not bins:
        raise ValueError("bins must not be empty")
    nearest = min((float(item) for item in bins), key=lambda item: (abs(wrap_phase_deg(float(phase_deg) - item)), item))
    return nearest, abs(wrap_phase_deg(float(phase_deg) - nearest))


def early_pass(target_conversion: float, leakage: float, ratio: float) -> bool:
    return target_conversion >= 0.5 and leakage <= 0.2 and ratio >= 6.0


def near_pass(target_conversion: float, leakage: float, ratio: float, early: bool | None = None) -> bool:
    is_early = early_pass(target_conversion, leakage, ratio) if early is None else early
    return (not is_early) and target_conversion >= 0.5 and leakage <= 0.25 and ratio >= 3.0


def opens_missing_bin(nearest_bin: float, early: bool) -> bool:
    return bool(early and float(nearest_bin) in set(REMAINING_MISSING_BINS_DEG))


def required_text(row: dict[str, str], key: str) -> str:
    value = row.get(key, "")
    if value == "":
        raise ValueError(f"Result CSV is missing {key}")
    return value


def required_float(row: dict[str, str], key: str) -> float:
    return float(required_text(row, key))


def _number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else float(value)


if __name__ == "__main__":
    raise SystemExit(main())
