"""Every controlled vocabulary the backend emits must have Hindi.

`tools/check_i18n.py` proves the *dictionary* is complete. It cannot prove the
*vocabularies* are, because those live in `seed/reference_data.py` and in the
risk rules rather than in a translation file - and `translateEnum` falls through
to the raw English value when a key is missing, so a gap is invisible at runtime
and shows up only as an English word on a Hindi page in front of a judge.

These tests close that loop: they read the Python source of record and the
TypeScript map, and fail when the two drift apart. Adding a district to the seed
without adding its Hindi now breaks the build.

The maps are parsed with a regex rather than executed - there is no TypeScript
runtime here - so the parser is kept deliberately strict and asserts it found a
plausible number of entries before comparing.
"""
from __future__ import annotations

import ast
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from seed import reference_data as ref  # noqa: E402

VOCABULARY = ROOT.parent / "frontend" / "src" / "i18n" / "vocabulary.ts"
RISK_DIR = ROOT / "app" / "risk"

#: Matches a key in a map literal: bare (Pune:), single-quoted, or double.
KEY_RE = re.compile(r"^\s{2}(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_][A-Za-z0-9_]*)):", re.M)


def _map_body(name: str) -> str:
    """The text between `export const NAME ... = {` and its closing brace."""
    text = VOCABULARY.read_text(encoding="utf-8")
    start = text.index(f"export const {name}")
    open_brace = text.index("{", start)
    depth = 0
    for index in range(open_brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[open_brace : index + 1]
    raise AssertionError(f"unbalanced braces in {name}")


def _keys(name: str) -> set[str]:
    return {a or b or c for a, b, c in KEY_RE.findall(_map_body(name))}


def _districts() -> set[str]:
    return {district for districts in ref.STATES.values() for district, _ in districts}


def _constituencies() -> set[str]:
    return {seat for districts in ref.STATES.values() for _, seat in districts}


def _risk_factor_titles() -> set[str]:
    """Every literal passed as `title=` in the risk package."""
    titles: set[str] = set()
    for path in sorted(RISK_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            for keyword in node.keywords:
                if keyword.arg == "title" and isinstance(keyword.value, ast.Constant):
                    if isinstance(keyword.value.value, str):
                        titles.add(keyword.value.value)
    return titles


def test_the_parser_found_the_maps() -> None:
    """A regex that silently matched nothing would make every test below pass."""
    assert len(_keys("STATE_HI")) >= 10, "STATE_HI parsed as near-empty"
    assert len(_keys("DISTRICT_HI")) >= 50, "DISTRICT_HI parsed as near-empty"
    assert len(_keys("CATEGORY_HI")) >= 15, "CATEGORY_HI parsed as near-empty"


def test_every_state_has_hindi() -> None:
    missing = sorted(set(ref.STATES) - _keys("STATE_HI"))
    assert not missing, f"states with no Hindi: {missing}"


def test_every_district_has_hindi() -> None:
    missing = sorted(_districts() - _keys("DISTRICT_HI"))
    assert not missing, f"districts with no Hindi: {missing}"


def test_every_constituency_has_hindi() -> None:
    # CONSTITUENCY_HI spreads DISTRICT_HI, which the regex cannot see, so the
    # district names are allowed to come from there.
    covered = _keys("CONSTITUENCY_HI") | _keys("DISTRICT_HI")
    missing = sorted(_constituencies() - covered)
    assert not missing, f"constituencies with no Hindi: {missing}"


def test_every_category_has_hindi() -> None:
    missing = sorted(set(ref.CATEGORIES) - _keys("CATEGORY_HI"))
    assert not missing, f"categories with no Hindi: {missing}"


def test_every_agency_has_hindi() -> None:
    missing = sorted(set(ref.AGENCIES) - _keys("AGENCY_HI"))
    assert not missing, f"agencies with no Hindi: {missing}"


def test_every_risk_factor_title_has_hindi() -> None:
    """These are the first line an officer reads on a flagged work."""
    titles = _risk_factor_titles()
    assert len(titles) >= 15, f"only found {len(titles)} risk titles - parser broken?"
    missing = sorted(titles - _keys("RISK_FACTOR_TITLE_HI"))
    assert not missing, f"risk factor titles with no Hindi: {missing}"


def test_no_stale_entries() -> None:
    """A translation for a value the backend no longer emits is dead weight."""
    stale = sorted(_keys("CATEGORY_HI") - set(ref.CATEGORIES))
    assert not stale, f"CATEGORY_HI has entries the seed never emits: {stale}"
    stale = sorted(_keys("AGENCY_HI") - set(ref.AGENCIES))
    assert not stale, f"AGENCY_HI has entries the seed never emits: {stale}"


def test_nothing_was_left_in_english() -> None:
    """A copy-paste that forgot to translate would read as Latin text."""
    body = "".join(
        _map_body(name)
        for name in (
            "STATE_HI",
            "DISTRICT_HI",
            "CATEGORY_HI",
            "AGENCY_HI",
            "RISK_FACTOR_TITLE_HI",
        )
    )
    untranslated = [
        line.strip()
        for line in body.splitlines()
        # A value line that carries Latin letters but no Devanagari.
        if re.search(r":\s*'[^']*[A-Za-z]{3}", line)
        and not re.search(r"[ऀ-ॿ]", line)
        and not line.strip().startswith(("//", "*", "/*"))
        and ":" in line
        and line.strip().endswith(",")
    ]
    assert not untranslated, f"values left in English: {untranslated}"


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
    print(f"\n{len(tests) - failures}/{len(tests)} vocabulary coverage tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
