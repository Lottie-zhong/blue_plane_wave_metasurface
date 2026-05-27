from __future__ import annotations

import argparse
import csv
import math
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_pb_supercell_config
from metasurface.pb_supercell import (
    PBSupercellRunner,
    collect_pb_order_spectrum_from_fsp,
    write_pb_order_spectrum,
    write_pb_supercell_summary,
)


SWEEP_FIELDS = [
    "case_id",
    "atoms",
    "atom_period_nm",
    "length_nm",
    "width_nm",
    "height_nm",
    "target_efficiency_from_lcp",
    "target_leakage_from_rcp",
    "spin_extinction_ratio_db",
    "rcp_dominant_channel",
    "rcp_dominant_efficiency",
    "unpolarized_target_equivalent_efficiency",
    "status",
    "note",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run PB supercell LCP/RCP parameter sweep.")
    parser.add_argument("--config", required=True, help="Path to PB sweep YAML config.")
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Path to local runtime YAML.")
    parser.add_argument("--plan-only", action="store_true", help="Write generated case configs without lumapi.")
    parser.add_argument("--skip-completed", action="store_true", help="Skip cases that already have summary CSVs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sweep = _read_yaml(Path(args.config))
    rows = _build_plan_rows(sweep)
    lcp_base = _read_yaml(Path(sweep["base_configs"]["lcp"]))
    rcp_base = _read_yaml(Path(sweep["base_configs"]["rcp"]))

    summary_rows: list[dict[str, object]] = []
    for row in rows:
        _write_case_config_pair(row, lcp_base, rcp_base)
        if args.plan_only:
            summary_rows.append(_planned_summary_row(row))
            print(f"planned={row['case_id']}")
            continue
        if args.skip_completed and Path(row["handedness_summary"]).exists():
            summary_rows.append(_read_single_row(Path(row["handedness_summary"])))
            print(f"skipped={row['case_id']}")
            continue
        summary_rows.append(_run_case(row, args.runtime))

    output_path = Path(sweep["output"]["result_dir"]) / "pb_sweep_summary.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SWEEP_FIELDS)
        writer.writeheader()
        writer.writerows(sorted(summary_rows, key=_summary_sort_key))

    completed = sum(1 for row in summary_rows if row["status"] == "ok")
    print(f"completed={completed}")
    print(f"total={len(rows)}")
    print(f"output={output_path}")
    if completed:
        best = sorted(summary_rows, key=_summary_sort_key)[0]
        print(
            "best="
            f"{best['case_id']} "
            f"target_efficiency={best['target_efficiency_from_lcp']} "
            f"leakage={best['target_leakage_from_rcp']}"
        )
    return 0


def _build_plan_rows(sweep: dict[str, Any]) -> list[dict[str, object]]:
    sweep_data = sweep["sweep"]
    result_dir = Path(sweep["output"]["result_dir"])
    rows: list[dict[str, object]] = []
    for height_nm in sweep_data["height_nm"]:
        for rotation_start_deg in sweep_data["rotation_start_deg"]:
            for length_nm in sweep_data["length_nm"]:
                for width_nm in sweep_data["width_nm"]:
                    case_id = _case_id(sweep_data["atoms"], length_nm, width_nm, height_nm, rotation_start_deg)
                    case_dir = result_dir / case_id
                    rows.append(
                        {
                            "case_id": case_id,
                            "case_dir": case_dir,
                            "atoms": sweep_data["atoms"],
                            "atom_period_nm": sweep_data["atom_period_nm"],
                            "rotation_step_deg": sweep_data["rotation_step_deg"],
                            "rotation_start_deg": rotation_start_deg,
                            "length_nm": length_nm,
                            "width_nm": width_nm,
                            "height_nm": height_nm,
                            "lcp_config": case_dir / f"{case_id}_lcp.yaml",
                            "rcp_config": case_dir / f"{case_id}_rcp.yaml",
                            "lcp_fsp": case_dir / f"{case_id}_lcp.fsp",
                            "rcp_fsp": case_dir / f"{case_id}_rcp.fsp",
                            "lcp_summary": case_dir / f"{case_id}_lcp_summary.csv",
                            "rcp_summary": case_dir / f"{case_id}_rcp_summary.csv",
                            "lcp_spectrum": case_dir / f"{case_id}_lcp_order_spectrum.csv",
                            "rcp_spectrum": case_dir / f"{case_id}_rcp_order_spectrum.csv",
                            "handedness_summary": case_dir / f"{case_id}_handedness_summary.csv",
                        }
                    )
    return rows


def _write_case_config_pair(row: dict[str, object], lcp_base: dict[str, Any], rcp_base: dict[str, Any]) -> None:
    for polarization, base in (("lcp", lcp_base), ("rcp", rcp_base)):
        data = deepcopy(base)
        data["project"]["stage"] = f"p3_pb_sweep_{row['case_id']}_{polarization}"
        data["geometry"]["atoms"] = row["atoms"]
        data["geometry"]["atom_period_nm"] = row["atom_period_nm"]
        data["geometry"]["length_nm"] = row["length_nm"]
        data["geometry"]["width_nm"] = row["width_nm"]
        data["geometry"]["height_nm"] = row["height_nm"]
        data["geometry"]["rotation_start_deg"] = row["rotation_start_deg"]
        data["geometry"]["rotation_step_deg"] = row["rotation_step_deg"]
        data["output"]["result_dir"] = str(row["case_dir"] / polarization)
        config_path = Path(row[f"{polarization}_config"])
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with config_path.open("w", encoding="utf-8") as handle:
            yaml.safe_dump(data, handle, sort_keys=False)


def _run_case(row: dict[str, object], runtime_path: str) -> dict[str, object]:
    for polarization in ("lcp", "rcp"):
        config = load_pb_supercell_config(row[f"{polarization}_config"])
        fsp_path = Path(row[f"{polarization}_fsp"])
        setup_rows = PBSupercellRunner.from_runtime_file(
            config=config,
            runtime_path=runtime_path,
            dry_run=False,
            setup_only=True,
            fsp_output=fsp_path,
        ).run()
        write_pb_supercell_summary(setup_rows, row[f"{polarization}_summary"])
        run_rows = PBSupercellRunner.from_runtime_file(
            config=config,
            runtime_path=runtime_path,
            dry_run=False,
            load_fsp=fsp_path,
        ).run()
        write_pb_supercell_summary(run_rows, row[f"{polarization}_summary"])
        spectrum_rows = collect_pb_order_spectrum_from_fsp(config, runtime_path, fsp_path)
        write_pb_order_spectrum(spectrum_rows, row[f"{polarization}_spectrum"])
        print(f"ran={row['case_id']} polarization={polarization} status={run_rows[0]['status']}")
    summary = _summarize_handedness(row)
    _write_single_summary(summary, Path(row["handedness_summary"]))
    return summary


def _summarize_handedness(row: dict[str, object]) -> dict[str, object]:
    lcp_rows = _read_rows(Path(row["lcp_spectrum"]))
    rcp_rows = _read_rows(Path(row["rcp_spectrum"]))
    target_lcp = _find_order(lcp_rows, order_n=1)
    target_rcp = _find_order(rcp_rows, order_n=1)
    dominant_rcp = max(rcp_rows, key=lambda item: float(item["order_efficiency_total"]))
    target_efficiency = float(target_lcp["order_efficiency_rcp_estimate"])
    target_leakage = float(target_rcp["order_efficiency_rcp_estimate"])
    return {
        "case_id": row["case_id"],
        "atoms": row["atoms"],
        "atom_period_nm": row["atom_period_nm"],
        "length_nm": row["length_nm"],
        "width_nm": row["width_nm"],
        "height_nm": row["height_nm"],
        "target_efficiency_from_lcp": target_efficiency,
        "target_leakage_from_rcp": target_leakage,
        "spin_extinction_ratio_db": 10 * math.log10(target_efficiency / max(target_leakage, 1e-12)),
        "rcp_dominant_channel": f"LCP,{_signed_order(dominant_rcp['order_n'])}",
        "rcp_dominant_efficiency": dominant_rcp["order_efficiency_lcp_estimate"],
        "unpolarized_target_equivalent_efficiency": 0.5 * (target_efficiency + target_leakage),
        "status": "ok",
        "note": "RCP/LCP estimates use gratingpolar Etheta +/- i*Ephi spherical-basis convention",
    }


def _planned_summary_row(row: dict[str, object]) -> dict[str, object]:
    return {
        "case_id": row["case_id"],
        "atoms": row["atoms"],
        "atom_period_nm": row["atom_period_nm"],
        "length_nm": row["length_nm"],
        "width_nm": row["width_nm"],
        "height_nm": row["height_nm"],
        "target_efficiency_from_lcp": "",
        "target_leakage_from_rcp": "",
        "spin_extinction_ratio_db": "",
        "rcp_dominant_channel": "",
        "rcp_dominant_efficiency": "",
        "unpolarized_target_equivalent_efficiency": "",
        "status": "planned",
        "note": "",
    }


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"YAML file must contain a mapping: {path}")
    return data


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_single_row(path: Path) -> dict[str, str]:
    rows = _read_rows(path)
    if len(rows) != 1:
        raise ValueError(f"Expected exactly one row in {path}, got {len(rows)}")
    return rows[0]


def _find_order(rows: list[dict[str, str]], order_n: int) -> dict[str, str]:
    for row in rows:
        if int(row["order_n"]) == order_n and int(row["order_m"]) == 0:
            return row
    raise ValueError(f"Missing order n={order_n}, m=0")


def _write_single_summary(row: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SWEEP_FIELDS)
        writer.writeheader()
        writer.writerow(row)


def _summary_sort_key(row: dict[str, object]) -> tuple[int, float, float, str]:
    if row["status"] != "ok":
        return (1, 0.0, math.inf, str(row["case_id"]))
    return (
        0,
        -float(row["target_efficiency_from_lcp"]),
        float(row["target_leakage_from_rcp"]),
        str(row["case_id"]),
    )


def _case_id(atoms: int, length_nm: float, width_nm: float, height_nm: float, rotation_start_deg: float) -> str:
    return (
        f"N{atoms}_"
        f"L{_format_number(length_nm)}_"
        f"W{_format_number(width_nm)}_"
        f"H{_format_number(height_nm)}_"
        f"R{_format_number(rotation_start_deg)}"
    )


def _format_number(value: float) -> str:
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f"{number:g}".replace(".", "p")


def _signed_order(value: str) -> str:
    order = int(value)
    if order > 0:
        return f"+{order}"
    return str(order)


if __name__ == "__main__":
    raise SystemExit(main())
