from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_pb_supercell_config
from metasurface.pb_supercell import collect_pb_order_spectrum_from_fsp, write_pb_order_spectrum


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract PB supercell grating-order spectrum.")
    parser.add_argument("--config", required=True, help="Path to PB supercell YAML config.")
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Path to local runtime YAML.")
    parser.add_argument("--load-fsp", required=True, help="Solved or setup .fsp file to run/extract.")
    parser.add_argument("--output", default=None, help="Optional order spectrum CSV path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_pb_supercell_config(args.config)
    rows = collect_pb_order_spectrum_from_fsp(config, args.runtime, args.load_fsp)
    output_path = Path(args.output) if args.output else config.output.result_dir / "pb_order_spectrum.csv"
    written_path = write_pb_order_spectrum(rows, output_path)
    print(f"orders={len(rows)}")
    print(f"output={written_path}")
    if rows:
        best = max(rows, key=lambda row: float(row["order_efficiency_total"]))
        print(
            "best="
            f"n={best['order_n']} "
            f"total={best['order_efficiency_total']} "
            f"rcp={best['order_efficiency_rcp_estimate']} "
            f"lcp={best['order_efficiency_lcp_estimate']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
