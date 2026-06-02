from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


NEIGHBORHOOD_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
    "source_reference",
    "selection_reason",
    "expected_risk",
    "intended_phase_region",
    "p1_length_nm",
    "p1_width_nm",
    "p2_length_nm",
    "p2_width_nm",
    "internal_dx_nm",
    "internal_dy_nm",
    "p1_rotation_deg",
    "p2_rotation_deg",
    "geometry_pass",
    "recommended_for_fdtd",
    "requires_fdtd",
    "status",
    "notes",
]

PREFERRED_SELECTION_IDS = [
    "nhood_p1w_dx_05",
    "nhood_p1w_dx_02",
    "nhood_lhs_leakred_06",
]

SELECTION_REASONS = {
    "nhood_p1w_dx_05": "Closest low-risk dx-neighborhood probe: keep p1_width=60 nm from doe_p1w_dx_01 and move internal_dx from -30 to -35 nm.",
    "nhood_p1w_dx_02": "Low-risk p1-width probe: keep internal_dx=-30 nm from doe_p1w_dx_01 and narrow p1_width from 60 to 55 nm.",
    "nhood_lhs_leakred_06": "Conservative lhs-like leakage-reduction probe: retain p1w_dx geometry and add only small internal_dy=5 nm to test lower-leakage 60-90 deg trend.",
}


def load_neighborhood_candidate_pool(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_neighborhood_geometry_validation(path: str | Path) -> dict[str, dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def filter_recommended_neighborhood_candidates(
    candidates: Iterable[dict[str, str]],
    validation_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for candidate in candidates:
        validation = validation_by_id.get(candidate["candidate_id"], {})
        if validation.get("overall_geometry_pass") == "True" and validation.get("recommended_for_fdtd") == "True":
            rows.append(
                {
                    **candidate,
                    "geometry_pass": validation.get("overall_geometry_pass", ""),
                    "recommended_for_fdtd": validation.get("recommended_for_fdtd", ""),
                }
            )
    return rows


def select_neighborhood_fdtd_candidates(
    candidates: Iterable[dict[str, str]],
    validation_by_id: dict[str, dict[str, str]],
    *,
    selected_ids: Sequence[str] = PREFERRED_SELECTION_IDS,
) -> list[dict[str, object]]:
    if not 2 <= len(selected_ids) <= 4:
        raise ValueError("selected_ids should select 2-4 candidates")

    eligible = filter_recommended_neighborhood_candidates(candidates, validation_by_id)
    by_id = {row["candidate_id"]: row for row in eligible}
    missing = [candidate_id for candidate_id in selected_ids if candidate_id not in by_id]
    if missing:
        raise ValueError(f"selected candidates are not geometry-pass/recommended: {missing}")

    selected = [_selection_row(rank, by_id[candidate_id]) for rank, candidate_id in enumerate(selected_ids, start=1)]
    _validate_selection_policy(selected)
    return selected


def export_neighborhood_fdtd_selection_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NEIGHBORHOOD_SELECTION_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in NEIGHBORHOOD_SELECTION_FIELDS} for row in row_list)
    return output_path


def summarize_neighborhood_fdtd_selection(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    families = Counter(str(row["candidate_family"]) for row in rows)
    ids = [str(row["candidate_id"]) for row in rows]
    reasons = {str(row["candidate_id"]): str(row["selection_reason"]) for row in rows}
    return {
        "selected_count": len(rows),
        "selected_candidate_ids": ids,
        "family_counts": dict(sorted(families.items())),
        "selection_reasons": reasons,
        "unique_candidate_ids": len(ids) == len(set(ids)),
        "contains_p1w_dx_neighborhood": any(row["candidate_family"] == "p1w_dx_neighborhood" for row in rows),
        "lhs_like_leakage_reduction_count": families.get("lhs_like_leakage_reduction", 0),
        "status_values": sorted({str(row["status"]) for row in rows}),
    }


def write_neighborhood_fdtd_selection_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    summary = summarize_neighborhood_fdtd_selection(rows)
    family_lines = [f"- `{family}`: {count}" for family, count in summary["family_counts"].items()]
    reason_lines = [
        f"- `{candidate_id}`: {reason}" for candidate_id, reason in summary["selection_reasons"].items()
    ]
    lines = [
        "# APCD K=6 Neighborhood FDTD Selection v1 Summary",
        "",
        "Scope: 09-P8 selection only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.",
        "",
        f"Selected count: {summary['selected_count']}",
        f"Selected candidate IDs: {', '.join(summary['selected_candidate_ids'])}",
        f"Unique candidate IDs: {summary['unique_candidate_ids']}",
        f"Contains p1w_dx_neighborhood: {summary['contains_p1w_dx_neighborhood']}",
        f"lhs_like_leakage_reduction count: {summary['lhs_like_leakage_reduction_count']}",
        f"Status values: {', '.join(summary['status_values'])}",
        "",
        "Family distribution:",
        "",
        *family_lines,
        "",
        "Selection reasons:",
        "",
        *reason_lines,
        "",
        "These candidates are selected for the next real-FDTD step only. The selection does not imply optical pass, phase coverage, leakage, ratio, or steering performance.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _selection_row(rank: int, candidate: dict[str, str]) -> dict[str, object]:
    candidate_id = candidate["candidate_id"]
    return {
        "selection_rank": rank,
        "candidate_id": candidate_id,
        "candidate_family": candidate["candidate_family"],
        "source_reference": candidate["source_reference"],
        "selection_reason": SELECTION_REASONS.get(candidate_id, "rule-based neighborhood FDTD selection"),
        "expected_risk": candidate["expected_risk"],
        "intended_phase_region": candidate["intended_phase_region"],
        "p1_length_nm": _number(candidate["p1_length_nm"]),
        "p1_width_nm": _number(candidate["p1_width_nm"]),
        "p2_length_nm": _number(candidate["p2_length_nm"]),
        "p2_width_nm": _number(candidate["p2_width_nm"]),
        "internal_dx_nm": _number(candidate["internal_dx_nm"]),
        "internal_dy_nm": _number(candidate["internal_dy_nm"]),
        "p1_rotation_deg": _number(candidate["p1_rotation_deg"]),
        "p2_rotation_deg": _number(candidate["p2_rotation_deg"]),
        "geometry_pass": candidate["geometry_pass"],
        "recommended_for_fdtd": candidate["recommended_for_fdtd"],
        "requires_fdtd": candidate["requires_fdtd"],
        "status": "selected_not_run",
        "notes": "09-P8 rule-based selection only; no surrogate prediction; no FDTD run yet.",
    }


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if not 2 <= len(rows) <= 4:
        raise ValueError("selection count must be 2-4")
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate selected candidate_id")
    families = Counter(str(row["candidate_family"]) for row in rows)
    if families.get("p1w_dx_neighborhood", 0) < 1:
        raise ValueError("selection must include at least one p1w_dx_neighborhood candidate")
    if families.get("lhs_like_leakage_reduction", 0) > 1:
        raise ValueError("selection must include at most one lhs_like_leakage_reduction candidate")
    if any(str(row["geometry_pass"]) != "True" for row in rows):
        raise ValueError("all selected rows must be geometry pass")
    if any(str(row["recommended_for_fdtd"]) != "True" for row in rows):
        raise ValueError("all selected rows must be recommended_for_fdtd")


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number
