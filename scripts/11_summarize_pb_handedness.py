from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


FIELDS = [
    "target_channel",
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
    parser = argparse.ArgumentParser(description="Summarize PB supercell LCP/RCP handedness validation.")
    parser.add_argument(
        "--lcp-spectrum",
        default="outputs/pb_supercell_L205_W70_H450/pb_order_spectrum.csv",
        help="Order spectrum CSV from LCP incidence.",
    )
    parser.add_argument(
        "--rcp-spectrum",
        default="outputs/pb_supercell_L205_W70_H450_rcp/pb_order_spectrum.csv",
        help="Order spectrum CSV from RCP incidence.",
    )
    parser.add_argument(
        "--output",
        default="outputs/pb_supercell_L205_W70_H450/pb_handedness_summary.csv",
        help="Output handedness summary CSV.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lcp_rows = _read_rows(Path(args.lcp_spectrum))
    rcp_rows = _read_rows(Path(args.rcp_spectrum))
    target_lcp = _find_order(lcp_rows, order_n=1)
    target_rcp = _find_order(rcp_rows, order_n=1)
    dominant_rcp = max(rcp_rows, key=lambda row: float(row["order_efficiency_total"]))

    target_efficiency = float(target_lcp["order_efficiency_rcp_estimate"])
    target_leakage = float(target_rcp["order_efficiency_rcp_estimate"])
    extinction = 10 * math.log10(target_efficiency / max(target_leakage, 1e-12))
    row = {
        "target_channel": "RCP,+1",
        "target_efficiency_from_lcp": target_efficiency,
        "target_leakage_from_rcp": target_leakage,
        "spin_extinction_ratio_db": extinction,
        "rcp_dominant_channel": f"LCP,{_signed_order(dominant_rcp['order_n'])}",
        "rcp_dominant_efficiency": dominant_rcp["order_efficiency_lcp_estimate"],
        "unpolarized_target_equivalent_efficiency": 0.5 * (target_efficiency + target_leakage),
        "status": "ok",
        "note": "RCP/LCP estimates use gratingpolar Etheta +/- i*Ephi spherical-basis convention",
    }

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerow(row)

    print(f"output={output_path}")
    print(f"target_efficiency_from_lcp={target_efficiency}")
    print(f"target_leakage_from_rcp={target_leakage}")
    print(f"spin_extinction_ratio_db={extinction}")
    return 0


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _find_order(rows: list[dict[str, str]], order_n: int) -> dict[str, str]:
    for row in rows:
        if int(row["order_n"]) == order_n and int(row["order_m"]) == 0:
            return row
    raise ValueError(f"Missing order n={order_n}, m=0")


def _signed_order(value: str) -> str:
    order = int(value)
    if order > 0:
        return f"+{order}"
    return str(order)


if __name__ == "__main__":
    raise SystemExit(main())
