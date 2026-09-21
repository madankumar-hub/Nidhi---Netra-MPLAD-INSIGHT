"""Accessibility affordances the GIGW claim depends on (NFR / SRS §8).

`README.md` and `docs/ARCHITECTURE.md` claim GIGW 3.0 conventions. Two of those
are structural rather than visual, so they are easy to add on one layout and
forget on the other - which is exactly what happened: the citizen portal had a
skip link and the officials portal did not, so an officer navigating by keyboard
tabbed through the entire sidebar on every route change.

These parse the JSX as text rather than rendering it. That is enough: what is
being asserted is that the markup exists and that the anchor points at a target
that also exists, which is precisely the pair that drifts apart.
"""
from __future__ import annotations

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LAYOUTS = ROOT.parent / "frontend" / "src" / "layouts"
COMPONENTS = ROOT.parent / "frontend" / "src" / "components"
STYLES = ROOT.parent / "frontend" / "src"


def _layouts() -> list[pathlib.Path]:
    found = sorted(LAYOUTS.glob("*Layout.tsx"))
    assert len(found) >= 2, f"expected at least two layouts, found {[p.name for p in found]}"
    return found


def test_every_layout_has_a_skip_link() -> None:
    missing = [p.name for p in _layouts() if 'className="skip-link"' not in p.read_text(encoding="utf-8")]
    assert not missing, f"layouts with no skip link: {missing}"


def test_every_skip_link_points_at_a_target_in_the_same_layout() -> None:
    """A skip link to an id that does not exist is worse than none: it looks
    correct in review and does nothing when pressed."""
    for path in _layouts():
        source = path.read_text(encoding="utf-8")
        anchors = re.findall(r'href="#([A-Za-z0-9_-]+)"\s+className="skip-link"', source)
        assert anchors, f"{path.name}: skip link has no href"
        for target in anchors:
            assert f'id="{target}"' in source, (
                f"{path.name}: skip link points at #{target}, which is not in this layout"
            )


def test_every_layout_has_exactly_one_main_landmark() -> None:
    for path in _layouts():
        source = path.read_text(encoding="utf-8")
        count = len(re.findall(r"<main[\s>]", source))
        assert count == 1, f"{path.name}: found {count} <main> elements, expected exactly 1"


def test_the_skip_link_is_visible_when_focused() -> None:
    """`.skip-link` is parked off-screen until focus. If the focus rule is lost
    the link can never appear, which is the same as not having one.

    The rule is written with Tailwind's `focus:` variant inside `@apply` rather
    than as a literal `.skip-link:focus` selector, so this reads the declaration
    block and accepts either form. (The first version of this test looked only
    for the literal selector and failed against perfectly correct CSS - worth
    remembering that a test can be wrong about the thing it is guarding.)
    """
    css_files = list(STYLES.rglob("*.css"))
    assert css_files, "no stylesheet found"
    combined = "\n".join(p.read_text(encoding="utf-8") for p in css_files)
    assert ".skip-link" in combined, "no .skip-link rule in any stylesheet"

    block = re.search(r"\.skip-link\s*\{(.*?)\}", combined, re.S)
    literal = re.search(r"\.skip-link:focus", combined)
    assert block or literal, ".skip-link has no declaration block"

    if literal:
        return
    body = block.group(1)
    assert re.search(r"focus(-visible)?[:\-]", body), (
        ".skip-link declares no focus state, so it can never become visible: "
        f"{body.strip()[:120]}"
    )
    # Parked off-screen the rest of the time, or it covers the header.
    assert re.search(r"-translate-y|top:\s*-|clip|sr-only", body), (
        ".skip-link is not hidden when unfocused"
    )


def test_the_accessibility_bar_offers_text_size_and_contrast() -> None:
    bar = COMPONENTS / "layout" / "AccessibilityBar.tsx"
    assert bar.exists(), "AccessibilityBar.tsx is missing"
    source = bar.read_text(encoding="utf-8")
    for key in ("a11y.decreaseText", "a11y.increaseText", "a11y.resetText", "a11y.contrast"):
        assert key in source, f"the accessibility bar does not offer {key}"
    assert "data-contrast" in source, "the contrast toggle sets no document attribute"


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
    print(f"\n{len(tests) - failures}/{len(tests)} accessibility tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
