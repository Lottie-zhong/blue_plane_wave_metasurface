from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_dimer import APCDSingleDimerRunner, write_apcd_single_dimer_summary
from metasurface.config import APCDSingleDimerConfig, load_apcd_single_dimer_config


DEFAULT_VARIANT_ID = "baseline"
CONFIG_DIR = REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates"
DEFAULT_RUNTIME = "configs/runtime.yaml"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export one APCD K=6 candidate setup-only FSP.")
    parser.add_argument("--variant-id", default=DEFAULT_VARIANT_ID, help="Single candidate variant_id to export.")
    parser.add_argument("--runtime", default=DEFAULT_RUNTIME, help="Runtime YAML for Lumerical setup-only export.")
    parser.add_argument("--fsp-output", default=None, help="Output .fsp path. Defaults to variant setup path.")
    parser.add_argument("--setup-only", action="store_true", help="Build and save setup without running FDTD.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned setup export without importing Lumerical.")
    return parser.parse_args(argv)


def candidate_config_path(variant_id: str) -> Path:
    return CONFIG_DIR / f"{variant_id}.yaml"


def default_fsp_output_path(variant_id: str) -> Path:
    return REPO_ROOT / "outputs" / "apcd_k6_phase_state_candidates" / variant_id / f"{variant_id}_setup.fsp"


def resolve_fsp_output(variant_id: str, fsp_output: str | None) -> Path:
    if fsp_output is None:
        return default_fsp_output_path(variant_id)
    path = Path(fsp_output)
    return path if path.is_absolute() else REPO_ROOT / path


def load_candidate_config(variant_id: str) -> APCDSingleDimerConfig:
    config_path = candidate_config_path(variant_id)
    if not config_path.exists():
        raise FileNotFoundError(f"Candidate config not found: {config_path}")
    config = load_apcd_single_dimer_config(config_path)
    _validate_candidate_config(config, variant_id)
    return config


def candidate_geometry_summary(config: APCDSingleDimerConfig) -> dict[str, object]:
    p1 = config.geometry.nanopillar_1
    p2 = config.geometry.nanopillar_2
    return {
        "wavelength_nm": config.target.wavelength_nm,
        "period_x_nm": config.geometry.period_x_nm,
        "period_y_nm": config.geometry.period_y_nm,
        "height_nm": config.geometry.height_nm,
        "material": f"{config.material.meta_material} / {config.material.substrate}",
        "pillar_1": f"{p1.length_nm:g} x {p1.width_nm:g} nm, rotation {p1.rotation_deg:g} deg",
        "pillar_2": f"{p2.length_nm:g} x {p2.width_nm:g} nm, rotation {p2.rotation_deg:g} deg",
    }


def dry_run_plan(variant_id: str, runtime: str, fsp_output: Path) -> dict[str, object]:
    config = load_candidate_config(variant_id)
    summary = candidate_geometry_summary(config)
    return {
        "status": "dry_run_setup_only_plan",
        "variant_id": variant_id,
        "config": _relative_posix(candidate_config_path(variant_id)),
        "runtime": runtime,
        "fsp_output": _relative_posix(fsp_output),
        "no_fdtd_run": True,
        "no_fsp_written": True,
        "not_steering_result": True,
        **summary,
    }


def export_candidate_setup_only(
    *,
    variant_id: str,
    runtime: str,
    fsp_output: Path,
    runner_factory: Callable[..., APCDSingleDimerRunner] = APCDSingleDimerRunner.from_runtime_file,
    summary_writer: Callable[[dict[str, object], Path], Path] = write_apcd_single_dimer_summary,
) -> dict[str, object]:
    config = load_candidate_config(variant_id)
    runtime_path = Path(runtime)
    if not runtime_path.is_absolute():
        runtime_path = REPO_ROOT / runtime_path
    if not runtime_path.exists():
        raise FileNotFoundError(
            f"Runtime config not found: {runtime_path}. Use --dry-run to inspect without Lumerical."
        )
    runner = runner_factory(
        config=config,
        runtime_path=runtime_path,
        dry_run=False,
        setup_only=True,
        fsp_output=fsp_output,
    )
    row = runner.run()
    summary_path = summary_writer(row, config.output.result_dir / "setup_summary.md")
    row["variant_id"] = variant_id
    row["fsp_output"] = fsp_output
    row["summary"] = summary_path
    return row


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    variant_id = args.variant_id or DEFAULT_VARIANT_ID
    fsp_output = resolve_fsp_output(variant_id, args.fsp_output)

    if args.dry_run:
        plan = dry_run_plan(variant_id, args.runtime, fsp_output)
        _print_mapping(plan)
        return 0

    if not args.setup_only:
        raise SystemExit("Pass --setup-only to export setup, or --dry-run to inspect without Lumerical.")

    row = export_candidate_setup_only(
        variant_id=variant_id,
        runtime=args.runtime,
        fsp_output=fsp_output,
    )
    print(f"status={row['status']}")
    print(f"variant_id={variant_id}")
    print(f"fsp_output={fsp_output}")
    print(f"summary={row['summary']}")
    print("note=setup-only export requested; solver run is not called by this workflow")
    return 0


def _validate_candidate_config(config: APCDSingleDimerConfig, variant_id: str) -> None:
    if config.target.wavelength_nm != 633:
        raise ValueError(f"{variant_id}: wavelength_nm must be 633")
    if config.material.meta_material != "c-Si" or config.material.substrate != "Al2O3":
        raise ValueError(f"{variant_id}: material must be c-Si / Al2O3")
    p2 = config.geometry.nanopillar_2
    if p2.length_nm == 150 and p2.width_nm == 85:
        raise ValueError(f"{variant_id}: beta-selective pillar 2 geometry 150 x 85 nm is not allowed")


def _print_mapping(values: dict[str, object]) -> None:
    for key, value in values.items():
        print(f"{key}={value}")


def _relative_posix(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
