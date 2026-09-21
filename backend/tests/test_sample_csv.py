"""The shipped sample CSVs must behave exactly as the demo script promises.

`samples/mplad-works-sample.csv` is imported live in front of judges. Two ways
that goes wrong, both of which happened:

1. The file parses but its categories, agencies and statuses are *near* the
   controlled vocabulary rather than in it. Nothing errors - the import succeeds
   - but the new works group with nothing, add count-of-one entries to every
   filter, and show English on a Hindi page. Invisible until someone looks.
2. The file stops parsing at all, because a column was renamed on one side.

These tests parse the files with the same rules `BulkImportDialog.parseCsv`
applies, then check every controlled value against its source of record.

`mplad-works-with-errors.csv` is the opposite: it must keep failing, in exactly
the ways the demo relies on, or the rejection screen has nothing to show.
"""
from __future__ import annotations

import csv
import io
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.enums import ProjectStatus  # noqa: E402
from seed import reference_data as ref  # noqa: E402

SAMPLES = ROOT.parent / "samples"
GOOD = SAMPLES / "mplad-works-sample.csv"
BAD = SAMPLES / "mplad-works-with-errors.csv"
DIALOG = ROOT.parent / "frontend" / "src" / "features" / "admin" / "BulkImportDialog.tsx"

#: Kept in step with REQUIRED_COLUMNS in BulkImportDialog.tsx - asserted below.
REQUIRED_COLUMNS = [
    "title",
    "mp_name",
    "state",
    "district",
    "category",
    "executing_agency",
    "sanction_year",
    "allocated_amount",
]

NUMERIC_COLUMNS = {
    "sanction_year",
    "allocated_amount",
    "spent_amount",
    "estimated_cost",
    "progress_percent",
    "planned_progress_percent",
    "beneficiaries",
    "latitude",
    "longitude",
}

MAX_KM_FROM_HEADQUARTERS = 40.0


def _parse(path: pathlib.Path) -> tuple[list[dict], list[str]]:
    """Mirror of the browser-side parser: column count, then numeric fields."""
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    reader = csv.reader(io.StringIO("\n".join(lines)))
    headers = next(reader)
    errors: list[str] = []
    rows: list[dict] = []

    missing = [column for column in REQUIRED_COLUMNS if column not in headers]
    if missing:
        return [], [f"Missing required column(s): {', '.join(missing)}"]

    for line_number, cells in enumerate(reader, start=2):
        if len(cells) != len(headers):
            errors.append(
                f"Row {line_number}: expected {len(headers)} columns, found {len(cells)}."
            )
            continue
        record: dict = {}
        failed = False
        for header, raw in zip(headers, cells):
            if raw == "":
                continue
            if header in NUMERIC_COLUMNS:
                try:
                    record[header] = float(raw)
                except ValueError:
                    errors.append(
                        f'Row {line_number}: "{header}" must be a number, found "{raw}".'
                    )
                    failed = True
            else:
                record[header] = raw
        if not failed:
            rows.append(record)
    return rows, errors


def _haversine_km(first: tuple[float, float], second: tuple[float, float]) -> float:
    import math

    dlat = math.radians(second[0] - first[0])
    dlon = math.radians(second[1] - first[1])
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(first[0]))
        * math.cos(math.radians(second[0]))
        * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def test_the_required_columns_match_the_dialog() -> None:
    """If the UI renames a column, this list is stale and every test below lies."""
    source = DIALOG.read_text(encoding="utf-8")
    block = source[source.index("const REQUIRED_COLUMNS") : source.index("] as const")]
    declared = [line.strip().strip("',") for line in block.splitlines() if line.strip().startswith("'")]
    assert declared == REQUIRED_COLUMNS, f"dialog requires {declared}, this test assumes {REQUIRED_COLUMNS}"


def test_the_sample_imports_without_a_single_rejection() -> None:
    rows, errors = _parse(GOOD)
    assert not errors, f"the demo sample would show errors: {errors}"
    assert len(rows) == 10, f"expected 10 rows, parsed {len(rows)}"


def test_every_sample_category_is_in_the_vocabulary() -> None:
    """A near-miss category imports fine and then groups with nothing."""
    rows, _ = _parse(GOOD)
    unknown = sorted({row["category"] for row in rows} - set(ref.CATEGORIES))
    assert not unknown, f"categories outside reference_data.CATEGORIES: {unknown}"


def test_every_sample_agency_is_in_the_vocabulary() -> None:
    rows, _ = _parse(GOOD)
    unknown = sorted({row["executing_agency"] for row in rows} - set(ref.AGENCIES))
    assert not unknown, f"agencies outside reference_data.AGENCIES: {unknown}"


def test_every_sample_status_is_a_real_enum_value() -> None:
    rows, _ = _parse(GOOD)
    valid = {status.value for status in ProjectStatus}
    unknown = sorted({row.get("status", "") for row in rows if row.get("status")} - valid)
    assert not unknown, f"statuses outside ProjectStatus: {unknown}"


def test_every_sample_district_has_coordinates_and_hindi() -> None:
    """Otherwise the imported works appear in English on a Hindi page."""
    rows, _ = _parse(GOOD)
    districts = {row["district"] for row in rows}
    missing_coords = sorted(districts - set(ref.DISTRICT_COORDINATES))
    assert not missing_coords, f"districts with no coordinates: {missing_coords}"

    vocabulary = (
        ROOT.parent / "frontend" / "src" / "i18n" / "vocabulary.ts"
    ).read_text(encoding="utf-8")
    for district in sorted(districts):
        key = f"'{district}'" if " " in district else district
        assert f"{key}:" in vocabulary, f"{district} has no Hindi in vocabulary.ts"


def test_sample_coordinates_sit_inside_their_district() -> None:
    rows, _ = _parse(GOOD)
    for row in rows:
        if "latitude" not in row:
            continue
        centre = ref.DISTRICT_COORDINATES[row["district"]]
        distance = _haversine_km(centre, (row["latitude"], row["longitude"]))
        assert distance <= MAX_KM_FROM_HEADQUARTERS, (
            f"{row['title'][:40]}: {distance:.1f} km from {row['district']} headquarters"
        )


def test_money_and_progress_are_internally_consistent() -> None:
    """A row that spends more than it was allocated would be flagged on import."""
    rows, _ = _parse(GOOD)
    for row in rows:
        allocated = row["allocated_amount"]
        spent = row.get("spent_amount", 0.0)
        progress = row.get("progress_percent", 0.0)
        assert spent <= allocated, f"{row['title'][:40]}: spent {spent} of {allocated}"
        assert 0 <= progress <= 100, f"{row['title'][:40]}: progress {progress}"
        if row.get("status") == "Completed":
            assert progress == 100, f"{row['title'][:40]}: completed at {progress}%"
        if row.get("status") == "Not Started":
            assert progress == 0, f"{row['title'][:40]}: not started at {progress}%"


def test_the_error_file_still_demonstrates_every_rejection() -> None:
    """The demo shows this file being refused. If it starts parsing, there is
    nothing on screen to point at."""
    rows, errors = _parse(BAD)
    assert len(rows) == 2, f"expected 2 valid rows, got {len(rows)}"
    assert len(errors) == 4, f"expected 4 rejections, got {len(errors)}: {errors}"

    joined = " ".join(errors)
    assert "allocated_amount" in joined, "no non-numeric amount rejection"
    assert "sanction_year" in joined, "no non-numeric year rejection"
    assert "progress_percent" in joined, "no non-numeric progress rejection"
    assert "expected 16 columns" in joined, "no wrong-column-count rejection"

    # Every message must name its line, or a reviewer cannot act on it.
    for error in errors:
        assert error.startswith("Row "), f"error without a line number: {error}"


def _run_all() -> int:
    import traceback

    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failures = 0
    for test in tests:
        try:
            test()
            print(f"  PASS  {test.__name__}")
        except Exception:
            failures += 1
            print(f"  FAIL  {test.__name__}")
            traceback.print_exc()
    print(f"\n{len(tests) - failures}/{len(tests)} sample CSV tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
