"""A very small PDF writer - no third-party dependency.

Why not reportlab or WeasyPrint
-------------------------------
Both are large, and WeasyPrint needs system libraries (cairo, pango) that turn
a one-command deploy into a platform-specific chore. What this project actually
needs is a tabular report on A4 with a header, a footer and page numbers. That
is a few hundred lines against the PDF 1.4 spec, so it is written here rather
than pulled in.

What it supports
----------------
A4 in either orientation (landscape by default - nine columns of tabular data
do not fit across a portrait page), the three built-in Helvetica faces with
real AFM advance widths, left/right-aligned text, horizontal rules, automatic
pagination and page numbering.

Known limitation - encoding
---------------------------
The built-in PDF fonts are single-byte (WinAnsi), so this writer can only emit
Latin-1 text. Devanagari would require embedding and subsetting a TrueType
font, which is a much larger job. The export is therefore English-only, and
`transliterate_to_latin1` replaces anything unmappable rather than producing a
corrupt file. `docs/ASSUMPTIONS.md` records this.
"""
from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from typing import List, Sequence, Tuple

# A4 at 72 dpi.
A4_SHORT = 595.28
A4_LONG = 841.89
MARGIN = 40.0

#: Nine columns of tabular data do not fit across a portrait page, so the
#: report is landscape - which is also how a printed register is normally laid
#: out. Portrait remains available for narrower reports.
PAGE_WIDTH = A4_LONG
PAGE_HEIGHT = A4_SHORT


def text_width(landscape: bool = True) -> float:
    """Usable width between the margins."""
    return (A4_LONG if landscape else A4_SHORT) - 2 * MARGIN


FONT_REGULAR = "F1"
FONT_BOLD = "F2"
FONT_OBLIQUE = "F3"


def transliterate_to_latin1(value: str) -> str:
    """Make `value` safe for a single-byte PDF font.

    Decomposes accents where possible, then drops anything still unmappable.
    A missing character is better than a file that will not open.
    """
    if not value:
        return ""
    normalised = unicodedata.normalize("NFKD", value)
    out: List[str] = []
    for char in normalised:
        if char in ("‘", "’"):
            out.append("'")
        elif char in ("“", "”"):
            out.append('"')
        elif char in ("–", "—"):
            out.append("-")
        elif char == "₹":  # rupee sign has no Latin-1 code point
            out.append("Rs.")
        elif char == "·":
            out.append("-")
        else:
            try:
                char.encode("latin-1")
            except UnicodeEncodeError:
                continue
            out.append(char)
    return "".join(out)


# ---------------------------------------------------------------------------
# Font metrics
#
# Estimating an "average" character width is not good enough: at 8pt an
# uppercase work code is far wider than the same number of lowercase letters,
# so a code overflowed into the next column while a title still had room.
# These are the real Helvetica advance widths from the Adobe AFM files, in
# 1/1000 em, for printable ASCII. Everything else falls back to the width of
# "n", which is mid-range.
# ---------------------------------------------------------------------------
_HELVETICA = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667, "'": 191,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584, "?": 556,
    "@": 1015, "A": 667, "B": 667, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 500, "K": 667, "L": 556, "M": 833, "N": 722, "O": 778,
    "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "`": 333, "a": 556, "b": 556, "c": 500, "d": 556, "e": 556, "f": 278, "g": 556,
    "h": 556, "i": 222, "j": 222, "k": 500, "l": 222, "m": 833, "n": 556, "o": 556,
    "p": 556, "q": 556, "r": 333, "s": 500, "t": 278, "u": 556, "v": 500, "w": 722,
    "x": 500, "y": 500, "z": 500, "{": 334, "|": 260, "}": 334, "~": 584,
}

_HELVETICA_BOLD = {
    " ": 278, "!": 333, '"': 474, "#": 556, "$": 556, "%": 889, "&": 722, "'": 238,
    "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333, ".": 278, "/": 278,
    "0": 556, "1": 556, "2": 556, "3": 556, "4": 556, "5": 556, "6": 556, "7": 556,
    "8": 556, "9": 556, ":": 333, ";": 333, "<": 584, "=": 584, ">": 584, "?": 611,
    "@": 975, "A": 722, "B": 722, "C": 722, "D": 722, "E": 667, "F": 611, "G": 778,
    "H": 722, "I": 278, "J": 556, "K": 722, "L": 611, "M": 833, "N": 722, "O": 778,
    "P": 667, "Q": 778, "R": 722, "S": 667, "T": 611, "U": 722, "V": 667, "W": 944,
    "X": 667, "Y": 667, "Z": 611, "[": 333, "\\": 278, "]": 333, "^": 584, "_": 556,
    "`": 333, "a": 556, "b": 611, "c": 556, "d": 611, "e": 556, "f": 333, "g": 611,
    "h": 611, "i": 278, "j": 278, "k": 556, "l": 278, "m": 889, "n": 611, "o": 611,
    "p": 611, "q": 611, "r": 389, "s": 556, "t": 333, "u": 611, "v": 556, "w": 778,
    "x": 556, "y": 556, "z": 500, "{": 389, "|": 280, "}": 389, "~": 584,
}

_FALLBACK_WIDTH = 556


def measure_text(value: str, size: float, bold: bool = False) -> float:
    """Width of `value` in points when set in Helvetica at `size`."""
    table = _HELVETICA_BOLD if bold else _HELVETICA
    units = sum(table.get(char, _FALLBACK_WIDTH) for char in value)
    return units * size / 1000.0


def fit_text(value: str, max_width: float, size: float, bold: bool = False) -> str:
    """Clip `value` to `max_width` points, appending an ellipsis if clipped."""
    text = transliterate_to_latin1(str(value or ""))
    if measure_text(text, size, bold) <= max_width:
        return text

    ellipsis_width = measure_text("...", size, bold)
    budget = max_width - ellipsis_width
    if budget <= 0:
        return ""

    out: list[str] = []
    used = 0.0
    table = _HELVETICA_BOLD if bold else _HELVETICA
    for char in text:
        advance = table.get(char, _FALLBACK_WIDTH) * size / 1000.0
        if used + advance > budget:
            break
        out.append(char)
        used += advance
    return "".join(out).rstrip() + "..."


def escape_pdf_text(value: str) -> str:
    """Escape the three characters that are special inside a PDF string."""
    return value.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


@dataclass
class Column:
    """One column of the table. `width` is in points, including its padding."""

    header: str
    width: float
    align: str = "left"


@dataclass
class _Page:
    """Accumulated drawing commands for one page."""

    operations: List[str] = field(default_factory=list)


class PdfDocument:
    """Builds a paginated, tabular PDF."""

    def __init__(
        self, title: str, subtitle: str = "", footer_note: str = "", landscape: bool = True
    ) -> None:
        self.title = transliterate_to_latin1(title)
        self.subtitle = transliterate_to_latin1(subtitle)
        self.footer_note = transliterate_to_latin1(footer_note)
        self.width = A4_LONG if landscape else A4_SHORT
        self.height = A4_SHORT if landscape else A4_LONG
        self.pages: List[_Page] = []
        self._page: _Page | None = None
        self._y = 0.0

    # -- low-level drawing -------------------------------------------------

    def _text(self, x: float, y: float, value: str, size: float, font: str) -> None:
        assert self._page is not None
        escaped = escape_pdf_text(transliterate_to_latin1(value))
        self._page.operations.append(
            f"BT /{font} {size:.1f} Tf 1 0 0 1 {x:.2f} {y:.2f} Tm ({escaped}) Tj ET"
        )

    def _text_right(self, right_x: float, y: float, value: str, size: float, font: str) -> None:
        text = transliterate_to_latin1(value)
        width = measure_text(text, size, bold=font == FONT_BOLD)
        self._text(right_x - width, y, value, size, font)

    def _line(self, x1: float, y1: float, x2: float, y2: float, width: float = 0.5,
              grey: float = 0.75) -> None:
        assert self._page is not None
        self._page.operations.append(
            f"{grey:.2f} G {width:.2f} w {x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S"
        )

    def _rect(self, x: float, y: float, w: float, h: float, grey: float) -> None:
        assert self._page is not None
        self._page.operations.append(f"{grey:.2f} g {x:.2f} {y:.2f} {w:.2f} {h:.2f} re f 0 g")

    # -- page structure ----------------------------------------------------

    def _start_page(self, columns: Sequence[Column]) -> None:
        self._page = _Page()
        self.pages.append(self._page)

        y = self.height - MARGIN

        # Masthead
        self._text(MARGIN, y - 12, self.title, 15, FONT_BOLD)
        y -= 28
        if self.subtitle:
            self._text(MARGIN, y, self.subtitle, 9, FONT_REGULAR)
            y -= 14

        # Saffron-ish rule, rendered as a grey bar (single-channel keeps the
        # content stream simple and prints identically in monochrome).
        self._rect(MARGIN, y - 2, self.width - 2 * MARGIN, 1.6, 0.35)
        y -= 18

        # Column headers
        self._draw_header_row(columns, y)
        self._y = y - 20

    def _draw_header_row(self, columns: Sequence[Column], y: float) -> None:
        self._rect(MARGIN, y - 5, self.width - 2 * MARGIN, 15, 0.92)
        x = MARGIN + 3
        for column in columns:
            header = fit_text(column.header, column.width - 8, 8, bold=True)
            if column.align == "right":
                self._text_right(x + column.width - 6, y, header, 8, FONT_BOLD)
            else:
                self._text(x, y, header, 8, FONT_BOLD)
            x += column.width

    def _finish_page(self, page_number: int) -> None:
        footer_y = MARGIN - 8
        self._line(MARGIN, MARGIN + 6, self.width - MARGIN, MARGIN + 6, 0.5, 0.8)
        if self.footer_note:
            self._text(MARGIN, footer_y, self.footer_note, 7, FONT_OBLIQUE)
        self._text_right(self.width - MARGIN, footer_y, f"Page {page_number}", 7, FONT_REGULAR)

    # -- public API --------------------------------------------------------

    def render_table(self, columns: Sequence[Column], rows: Sequence[Sequence[str]]) -> None:
        """Lay out `rows` across as many pages as needed."""
        bottom_limit = MARGIN + 24
        self._start_page(columns)
        striped = False

        for row in rows:
            if self._y < bottom_limit:
                self._finish_page(len(self.pages))
                self._start_page(columns)
                striped = False

            if striped:
                self._rect(MARGIN, self._y - 4, self.width - 2 * MARGIN, 14, 0.965)
            striped = not striped

            x = MARGIN + 3
            for column, cell in zip(columns, row):
                text = fit_text(cell, column.width - 8, 8)
                if column.align == "right":
                    self._text_right(x + column.width - 6, self._y, text, 8, FONT_REGULAR)
                else:
                    self._text(x, self._y, text, 8, FONT_REGULAR)
                x += column.width

            self._y -= 14

        self._finish_page(len(self.pages))

    def render_empty(self, columns: Sequence[Column], message: str) -> None:
        """A report with no rows still needs to be a valid, readable document."""
        self._start_page(columns)
        self._text(MARGIN, self._y - 10, message, 10, FONT_OBLIQUE)
        self._finish_page(1)

    def to_bytes(self) -> bytes:
        """Serialise to a complete PDF file."""
        if not self.pages:
            raise ValueError("Nothing has been rendered into this document.")

        objects: List[bytes] = []

        def add(body: bytes) -> int:
            objects.append(body)
            return len(objects)  # 1-based object numbers

        font_ids = {
            FONT_REGULAR: add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
                b"/Encoding /WinAnsiEncoding >>"
            ),
            FONT_BOLD: add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold "
                b"/Encoding /WinAnsiEncoding >>"
            ),
            FONT_OBLIQUE: add(
                b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique "
                b"/Encoding /WinAnsiEncoding >>"
            ),
        }

        resources = (
            "<< /Font << "
            + " ".join(f"/{name} {oid} 0 R" for name, oid in font_ids.items())
            + " >> >>"
        ).encode("latin-1")

        # Reserve the Pages object id so each Page can point at its parent.
        pages_id = add(b"")  # placeholder, filled in below

        page_ids: List[int] = []
        for page in self.pages:
            stream = "\n".join(page.operations).encode("latin-1", errors="replace")
            content_id = add(
                b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"
            )
            page_ids.append(
                add(
                    f"<< /Type /Page /Parent {pages_id} 0 R "
                    f"/MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                    f"/Contents {content_id} 0 R /Resources ".encode("latin-1")
                    + resources
                    + b" >>"
                )
            )

        kids = " ".join(f"{pid} 0 R" for pid in page_ids)
        objects[pages_id - 1] = (
            f"<< /Type /Pages /Count {len(page_ids)} /Kids [{kids}] >>".encode("latin-1")
        )

        catalog_id = add(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("latin-1"))
        info_id = add(
            b"<< /Title (" + escape_pdf_text(self.title).encode("latin-1", "replace")
            + b") /Producer (MPLAD Insight) >>"
        )

        # Assemble the file, recording each object's byte offset for the xref.
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets: List[int] = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += f"{number} 0 obj\n".encode("latin-1") + body + b"\nendobj\n"

        xref_offset = len(out)
        count = len(objects) + 1
        out += f"xref\n0 {count}\n".encode("latin-1")
        out += b"0000000000 65535 f \n"
        for offset in offsets:
            out += f"{offset:010d} 00000 n \n".encode("latin-1")
        out += (
            f"trailer\n<< /Size {count} /Root {catalog_id} 0 R /Info {info_id} 0 R >>\n"
            f"startxref\n{xref_offset}\n%%EOF\n"
        ).encode("latin-1")

        return bytes(out)


def build_table_pdf(
    title: str,
    subtitle: str,
    footer_note: str,
    columns: Sequence[Tuple[str, float, str]],
    rows: Sequence[Sequence[str]],
    empty_message: str = "No records matched the selected filters.",
    landscape: bool = True,
) -> bytes:
    """Convenience wrapper: `columns` is (header, width, align)."""
    document = PdfDocument(
        title=title, subtitle=subtitle, footer_note=footer_note, landscape=landscape
    )
    specs = [Column(header=h, width=w, align=a) for h, w, a in columns]
    if rows:
        document.render_table(specs, rows)
    else:
        document.render_empty(specs, empty_message)
    return document.to_bytes()
