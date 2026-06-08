from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def p179():
    path = REPO_ROOT / "scripts/manual_p179_freeze_stage10_phase_library.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    module.main([])
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p179_frozen_library_has_six_bins(p179) -> None:
    rows = read_csv(p179.FROZEN_LIBRARY_CSV)

    assert [row["bin_deg"] for row in rows] == ["-180", "-120", "-60", "0", "60", "120"]
    assert len(rows) == 6
    assert len({row["candidate_id"] for row in rows}) == 6


def test_p179_zero_anchor_is_correct(p179) -> None:
    rows = read_csv(p179.FROZEN_LIBRARY_CSV)
    zero = next(row for row in rows if row["bin_deg"] == "0")

    assert zero["candidate_id"] == "cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01"
    assert zero["early_pass"] == "True"
    assert "p178_zero_bin_opened_final_decision.md" in zero["results_csv"]


def test_p179_all_selected_anchors_are_early_pass(p179) -> None:
    rows = read_csv(p179.FROZEN_LIBRARY_CSV)

    assert all(row["early_pass"] == "True" for row in rows)


def test_p179_sanity_missing_bins_is_empty(p179) -> None:
    rows = read_csv(p179.SANITY_CSV)
    sanity = {row["check"]: row for row in rows}

    assert sanity["missing_bins"]["status"] == "pass"
    assert sanity["missing_bins"]["details"] == "[]"
    assert all(row["status"] == "pass" for row in rows)


def test_p179_report_no_overclaim_wording_exists(p179) -> None:
    text = p179.REPORT_MD.read_text(encoding="utf-8")

    assert "not K=6 steering yet" in text
    assert "not a K=6 phase-ramp supercell" in text
    assert "not a +15 deg beam deflection result" in text
    assert "not a Micro-LED result" in text
    assert "does not run FDTD" in text
