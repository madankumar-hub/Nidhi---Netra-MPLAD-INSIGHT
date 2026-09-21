"""PDF export (FR12).

The writer is hand-rolled, so these tests check the things a broken PDF writer
gets wrong: the file header and trailer, byte offsets in the cross-reference
table, page counts under pagination, and string escaping. A PDF that a reader
refuses to open is worse than no PDF at all.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.pdf_writer import (  # noqa: E402
    build_table_pdf,
    escape_pdf_text,
    fit_text,
    measure_text,
    transliterate_to_latin1,
)

COLUMNS = [
    ("Work ID", 70.0, "left"),
    ("Title", 200.0, "left"),
    ("District", 80.0, "left"),
    ("Allocated", 70.0, "right"),
]


def _rows(count: int) -> list[list[str]]:
    return [
        [f"MPLAD-{index:04d}", f"Community work {index}", "Sirohi", f"{20 + index}.00"]
        for index in range(count)
    ]


def _build(count: int) -> bytes:
    return build_table_pdf(
        title="MPLAD Insight - Flagged works",
        subtitle="Generated for tests",
        footer_note="Synthetic data",
        columns=COLUMNS,
        rows=_rows(count),
    )


def test_output_is_a_pdf() -> None:
    data = _build(5)
    assert data.startswith(b"%PDF-1.4"), "missing PDF header"
    assert data.rstrip().endswith(b"%%EOF"), "missing EOF marker"


def test_cross_reference_offsets_point_at_real_objects() -> None:
    """A wrong xref offset is the classic way to produce an unopenable PDF."""
    data = _build(20)

    marker = data.rindex(b"startxref")
    xref_offset = int(data[marker + len("startxref") :].split()[0])
    assert data[xref_offset : xref_offset + 4] == b"xref", "startxref does not point at the table"

    section = data[xref_offset:]
    entries = re.findall(rb"^(\d{10}) (\d{5}) ([nf]) ?$", section, re.M)
    assert entries, "no xref entries found"

    for raw_offset, _generation, kind in entries:
        if kind != b"n":
            continue
        offset = int(raw_offset)
        assert 0 < offset < len(data), f"offset {offset} is outside the file"
        # Every in-use entry must land exactly on an "N 0 obj" header.
        assert re.match(rb"\d+ 0 obj", data[offset : offset + 20]), (
            f"offset {offset} does not begin an object"
        )


def test_trailer_size_matches_the_object_count() -> None:
    data = _build(10)
    size = int(re.search(rb"/Size (\d+)", data).group(1))
    objects = len(re.findall(rb"^\d+ 0 obj$", data, re.M))
    # /Size counts the free object 0 as well as every real one.
    assert size == objects + 1, f"/Size {size} but {objects} objects present"


def test_long_tables_paginate() -> None:
    one_page = _build(5).count(b"/Type /Page ")
    many_pages = _build(200).count(b"/Type /Page ")
    assert one_page == 1, f"a short table should be one page, got {one_page}"
    assert many_pages > 3, f"200 rows should span several pages, got {many_pages}"


def test_an_empty_selection_still_produces_a_valid_document() -> None:
    data = build_table_pdf(
        title="Empty", subtitle="", footer_note="", columns=COLUMNS, rows=[],
        empty_message="No works matched the selected filters.",
    )
    assert data.startswith(b"%PDF-1.4")
    assert data.count(b"/Type /Page ") == 1
    assert b"No works matched" in data


def test_parentheses_and_backslashes_are_escaped() -> None:
    """Unescaped brackets terminate a PDF string early and corrupt the file."""
    assert escape_pdf_text("a(b)c") == r"a\(b\)c"
    assert escape_pdf_text("back\\slash") == r"back\\slash"

    data = build_table_pdf(
        title="T", subtitle="", footer_note="", columns=COLUMNS,
        rows=[["X-1", "Road (phase 2) \\ bridge", "Sirohi", "10.00"]],
    )
    assert rb"Road \(phase 2\) \\ bridge" in data


def test_non_latin1_text_does_not_break_the_file() -> None:
    """Built-in PDF fonts are single-byte; Devanagari must degrade, not crash."""
    assert transliterate_to_latin1("₹ 250") == "Rs. 250"
    assert transliterate_to_latin1("‘quoted’") == "'quoted'"

    data = build_table_pdf(
        title="सारांश", subtitle="", footer_note="",
        columns=COLUMNS,
        rows=[["X-1", "सामुदायिक भवन", "Sirohi", "10.00"]],
    )
    assert data.startswith(b"%PDF-1.4")
    assert data.rstrip().endswith(b"%%EOF")


def test_text_is_measured_with_real_font_metrics() -> None:
    """An average-width estimate let uppercase codes overflow their column."""
    # Helvetica: "W" is 944/1000 em, "l" is 222/1000. An averaging model would
    # call these equal, which is how "MPLAD-RJ-700" ran into the next column.
    assert measure_text("W", 10) > measure_text("l", 10) * 4
    assert measure_text("", 10) == 0
    # 8 digits at 556/1000 em, 8pt => 8 * 0.556 * 8 = 35.58pt
    assert abs(measure_text("12345678", 8) - 35.584) < 0.01


def test_cells_are_clipped_to_their_column_width() -> None:
    short = fit_text("short", 100.0, 8)
    assert short == "short", "text that fits must not be altered"

    long_title = "Construction of community hall at Sirohi block phase two"
    clipped = fit_text(long_title, 60.0, 8)
    assert clipped.endswith("...")
    assert measure_text(clipped, 8) <= 60.0, "clipped text still overflows"

    # A column too narrow for even an ellipsis returns nothing rather than
    # spilling into its neighbour.
    assert fit_text("anything", 2.0, 8) == ""


def test_uppercase_codes_fit_their_column() -> None:
    """Regression: the Work ID column overflowed into Title."""
    code = "MPLAD-RJ-700"
    fitted = fit_text(code, 56.0 - 8, 8)
    assert measure_text(fitted, 8) <= 48.0


def test_report_columns_fit_the_page() -> None:
    """Columns wider than the text area spill off the paper.

    Read from the source with `ast` rather than imported, so this runs without
    SQLAlchemy - `export_service` pulls in the ORM models.
    """
    import ast

    source = (ROOT / "app" / "services" / "export_service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    widths: list[float] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "PDF_COLUMNS" not in targets or not isinstance(node.value, ast.List):
            continue
        for element in node.value.elts:
            assert isinstance(element, ast.Tuple), "each column must be a tuple"
            widths.append(ast.literal_eval(element.elts[1]))

    assert widths, "PDF_COLUMNS not found in export_service.py"

    # Landscape A4 is 841.89pt wide; two 40pt margins leave 761.89pt.
    total = sum(widths)
    assert total <= 761.89, f"columns total {total}pt, wider than the 761.89pt text area"


def test_every_csv_row_states_the_data_is_synthetic() -> None:
    """A CSV gets forwarded and opened far from the page it came from.

    `docs/DATA_INGESTION.md` promises the provenance is on every export. The PDF
    carries it in the footer; for a while the CSV carried it nowhere, which made
    the documentation wrong and let a file of government-shaped numbers travel
    with nothing saying it was invented. Read from the source with `ast` so this
    runs without SQLAlchemy.
    """
    import ast

    source = (ROOT / "app" / "services" / "export_service.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    columns: list[str] = []
    note = ""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "COLUMNS" in targets and isinstance(node.value, ast.List):
            columns = [ast.literal_eval(e) for e in node.value.elts]
        if "DATA_SOURCE_NOTE" in targets:
            note = ast.literal_eval(node.value)

    assert columns, "COLUMNS not found in export_service.py"
    assert "data_source" in columns, "the CSV carries no provenance column"
    assert note, "DATA_SOURCE_NOTE not found"
    assert "ynthetic" in note, f"the note does not say the data is synthetic: {note!r}"
    assert "not official" in note.lower(), f"the note does not disclaim officialness: {note!r}"

    # The column must actually be populated, not merely declared.
    assert '"data_source": DATA_SOURCE_NOTE' in source, (
        "data_source is declared as a column but never written to a row"
    )


def test_the_pdf_footer_states_the_data_is_synthetic() -> None:
    source = (ROOT / "app" / "services" / "export_service.py").read_text(encoding="utf-8")
    body = source[source.index("def projects_to_pdf") :]
    assert "footer_note" in body, "the PDF export sets no footer"
    assert "Synthetic" in body, "the PDF footer does not say the data is synthetic"


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
    print(f"\n{len(tests) - failures}/{len(tests)} PDF export tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
