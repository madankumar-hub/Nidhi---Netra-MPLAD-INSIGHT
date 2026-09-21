#!/usr/bin/env python3
"""Verify the Hindi translation is genuinely complete.

Three checks, because key parity alone is not enough - the original bug was a
dictionary with perfect parity while the UI still rendered English:

1. Key parity          - every key in en.ts exists in hi.ts and vice versa.
2. Untranslated values - no hi.ts value is byte-identical to its English one
                         (allowing a short allowlist of proper nouns).
3. Hardcoded strings   - no user-visible English literal sits in a .tsx file
                         outside a t() / tEnum() call. Three shapes are checked:
                         a JSX attribute, a bare text node, and - added after
                         this check missed both - an English sentence alone on
                         its own line, and a string passed as a label prop.
                         Multi-line JSX comments are skipped: they are prose by
                         design, and flagging one is how a check loses its
                         credibility.

Run:  python3 tools/check_i18n.py
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "frontend" / "src"
I18N = SRC / "i18n"

#: Values that are legitimately identical in both dictionaries - proper nouns,
#: abbreviations and symbols that are not transliterated on government portals.
SAME_IN_BOTH_ALLOWED = {
    "MPLAD Insight",
    "MPLADS",
    "SIH26102",
    "CSV",
    "PDF",
    "ID",
    "API",
    "₹",
    "%",
}

#: JSX attributes whose value is shown to a user and so must be translated.
USER_VISIBLE_ATTRS = ("label", "title", "placeholder", "description", "sublabel", "hint")

KEY_RE = re.compile(r"^\s*'([^']+)':\s*(.*)$", re.M)

#: A line that is nothing but an English sentence - two or more words, starting
#: with a capital, no JSX tag and no code punctuation.
PROSE_LINE = re.compile(r"^[A-Z][a-z]+(?: [A-Za-z,'’-]+){2,}[.!?]?$")

#: Props whose value a user reads. Deliberately narrow: `className` and `key`
#: also take strings and must not be flagged.
USER_VISIBLE_PROPS = (
    "seriesLabel",
    "emptyLabel",
    "retryLabel",
    "allocated",
    "spent",
    "remaining",
    "confirmLabel",
    "cancelLabel",
    "actionLabel",
    "helpText",
    "caption",
)
PROP_STRING = re.compile(
    r"\b(?P<prop>" + "|".join(USER_VISIBLE_PROPS) + r")\s*[:=]\s*['\"](?P<value>[^'\"]{3,})['\"]"
)


def _is_code(line: str) -> bool:
    """Filter out lines that only look like prose - imports, types, JSX attrs."""
    return bool(re.search(r"[{}<>=(\[;]|=>|\bimport\b|\bexport\b", line))


def _looks_like_english_words(value: str) -> bool:
    """Two or more Latin words, so a CSS token or an enum key does not trip it."""
    if not re.fullmatch(r"[A-Za-z][A-Za-z ,'’.-]*", value):
        return False
    return len(value.split()) >= 1 and bool(re.match(r"^[A-Z][a-z]", value))


def load_dictionary(path: pathlib.Path) -> dict[str, str]:
    """Parse the key/value pairs out of a dictionary module."""
    text = path.read_text(encoding="utf-8")
    entries: dict[str, str] = {}
    for match in KEY_RE.finditer(text):
        key, raw = match.group(1), match.group(2).strip()
        # Values may be on the following line for long strings; capture what we
        # can - the comparison only needs the leading literal.
        literal = re.match(r"['\"](.*)['\"],?$", raw)
        entries[key] = literal.group(1) if literal else raw.rstrip(",")
    return entries


def check_parity(en: dict[str, str], hi: dict[str, str]) -> list[str]:
    problems = []
    missing_hi = sorted(set(en) - set(hi))
    extra_hi = sorted(set(hi) - set(en))
    for key in missing_hi:
        problems.append(f"missing from hi.ts: {key}")
    for key in extra_hi:
        problems.append(f"present in hi.ts but not en.ts: {key}")
    return problems


def check_untranslated(en: dict[str, str], hi: dict[str, str]) -> list[str]:
    problems = []
    for key in sorted(set(en) & set(hi)):
        english, hindi = en[key], hi[key]
        if not english or english != hindi:
            continue
        if english.strip() in SAME_IN_BOTH_ALLOWED:
            continue
        # A value with no Latin letters at all (a number, a symbol) is fine.
        if not re.search(r"[A-Za-z]{3}", english):
            continue
        problems.append(f"untranslated (identical in both): {key} = {english!r}")
    return problems


def check_hardcoded(files: list[pathlib.Path]) -> list[str]:
    problems = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        # A JSX comment - {/* ... */} - is prose by design and spans lines, so
        # its inner lines start with no comment marker at all. The prose check
        # below flagged one of these as a hardcoded string, which is the kind of
        # false positive that teaches people to ignore the check. Track the
        # block and skip it.
        in_jsx_comment = False
        for number, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()

            if in_jsx_comment:
                if "*/}" in stripped or stripped.endswith("*/"):
                    in_jsx_comment = False
                continue
            if stripped.startswith("{/*") and "*/}" not in stripped:
                in_jsx_comment = True
                continue
            if stripped.startswith(("//", "*", "/*", "{/*")):
                continue
            for attr in USER_VISIBLE_ATTRS:
                match = re.search(rf'\b{attr}="([A-Z][^"]{{2,}})"', line)
                if match:
                    problems.append(
                        f"{path.relative_to(ROOT)}:{number}: hardcoded {attr}="
                        f'"{match.group(1)}"'
                    )
            # Bare English text as a JSX node. Two words is enough - the
            # original miss here was a "New work" button label.
            text_node = re.search(r">\s*([A-Z][a-z]+(?: [a-z]+){1,})\s*<", line)
            if text_node:
                problems.append(
                    f"{path.relative_to(ROOT)}:{number}: hardcoded text "
                    f'"{text_node.group(1)}"'
                )
            # An English sentence sitting on its own line inside JSX, with no
            # angle bracket to anchor on. The check above cannot see these, and
            # it missed a whole sentence under the filter bar plus four string
            # props on the analytics page - so it is checked separately.
            if PROSE_LINE.match(stripped) and not _is_code(stripped):
                problems.append(
                    f"{path.relative_to(ROOT)}:{number}: hardcoded text "
                    f'"{stripped[:60]}"'
                )
            # A user-visible English string passed as a prop value, e.g.
            # seriesLabel="Occurrences" or labels={{ allocated: 'Released' }}.
            for match in PROP_STRING.finditer(line):
                value = match.group("value")
                if _looks_like_english_words(value):
                    problems.append(
                        f"{path.relative_to(ROOT)}:{number}: hardcoded "
                        f'{match.group("prop")} "{value}"'
                    )
    return problems


def main() -> int:
    en = load_dictionary(I18N / "en.ts")
    hi = load_dictionary(I18N / "hi.ts")

    tsx_files = sorted(
        p
        for p in SRC.rglob("*.tsx")
        if "i18n" not in p.parts
    )

    parity = check_parity(en, hi)
    untranslated = check_untranslated(en, hi)
    hardcoded = check_hardcoded(tsx_files)

    print(f"en.ts: {len(en)} keys")
    print(f"hi.ts: {len(hi)} keys")
    print(f"Scanned {len(tsx_files)} component files for hardcoded English.")
    print()

    all_problems = parity + untranslated + hardcoded
    if not all_problems:
        print("i18n check passed: parity holds, no untranslated values, "
              "no hardcoded user-visible English.")
        return 0

    for problem in all_problems:
        print(f"  {problem}")
    print()
    print(f"i18n check FAILED: {len(all_problems)} problem(s).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
