"""Seeded work locations must be geographically honest.

This exists because the original seed generated a random point inside a
bounding box of roughly 8.5-32.5N, 70-92E. That box contains Pakistan, Nepal,
China, Bangladesh, the Arabian Sea and the Bay of Bengal, so a work recorded in
Sirohi could be plotted in the middle of the ocean. The map looked absurd and,
worse, the data was silently wrong.

A location that is missing is fine. A location that is confidently wrong is
not, so these tests check both that every district has a plausible point and
that an unknown district gets no coordinates at all.
"""
from __future__ import annotations

import ast
import math
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from seed import reference_data as ref  # noqa: E402

#: Generous bounding box for Indian territory, used only as a sanity check.
INDIA_LAT = (6.4, 35.8)
INDIA_LON = (68.0, 97.5)

#: A work should sit within its own district, not the next state.
MAX_KM_FROM_HEADQUARTERS = 40.0


def _load_jitter_function():
    """Compile the helper out of seed_data without importing the ORM."""
    source = (ROOT / "seed" / "seed_data.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    function = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "jittered_district_point"
    )
    namespace: dict = {"ref": ref}
    exec(compile(ast.Module([function], []), "<seed_data>", "exec"), namespace)
    return namespace["jittered_district_point"]


jittered_district_point = _load_jitter_function()


def _haversine_km(first: tuple[float, float], second: tuple[float, float]) -> float:
    lat1, lon1 = first
    lat2, lon2 = second
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(a))


def _all_districts() -> set[str]:
    return {district for districts in ref.STATES.values() for district, _ in districts}


def test_every_seeded_district_has_coordinates() -> None:
    """A district in the seed with no coordinates would silently lose its map."""
    missing = sorted(_all_districts() - set(ref.DISTRICT_COORDINATES))
    assert not missing, f"districts with no coordinates: {missing}"


def test_every_coordinate_is_inside_india() -> None:
    outside = [
        (district, latitude, longitude)
        for district, (latitude, longitude) in ref.DISTRICT_COORDINATES.items()
        if not (INDIA_LAT[0] <= latitude <= INDIA_LAT[1])
        or not (INDIA_LON[0] <= longitude <= INDIA_LON[1])
    ]
    assert not outside, f"coordinates outside India: {outside}"


def test_coordinates_are_distinct() -> None:
    """Two districts sharing a point means one was copied by mistake."""
    seen: dict[tuple[float, float], str] = {}
    duplicates = []
    for district, point in ref.DISTRICT_COORDINATES.items():
        if point in seen:
            duplicates.append((seen[point], district, point))
        seen[point] = district
    assert not duplicates, f"districts sharing a coordinate: {duplicates}"


def test_a_work_stays_within_its_own_district() -> None:
    rng = random.Random(20260921)
    for district in sorted(_all_districts()):
        centre = ref.DISTRICT_COORDINATES[district]
        for _ in range(200):
            point = jittered_district_point(rng, district)
            assert point is not None, f"{district} produced no point"
            distance = _haversine_km(centre, point)
            assert distance <= MAX_KM_FROM_HEADQUARTERS, (
                f"{district}: work placed {distance:.1f} km from its headquarters"
            )


def test_generated_points_stay_inside_india() -> None:
    rng = random.Random(7)
    for district in sorted(_all_districts()):
        for _ in range(200):
            latitude, longitude = jittered_district_point(rng, district)
            assert INDIA_LAT[0] <= latitude <= INDIA_LAT[1], f"{district}: latitude {latitude}"
            assert INDIA_LON[0] <= longitude <= INDIA_LON[1], f"{district}: longitude {longitude}"


def test_an_unknown_district_gets_no_coordinates() -> None:
    """Never invent a location. An absent marker beats a wrong one."""
    rng = random.Random(1)
    assert jittered_district_point(rng, "Nonexistent District") is None
    assert jittered_district_point(rng, "") is None


def test_points_are_spread_rather_than_stacked() -> None:
    """All markers on one pixel would look like a single work."""
    rng = random.Random(99)
    points = {jittered_district_point(rng, "Sirohi") for _ in range(50)}
    assert len(points) == 50, "jitter produced repeated points"


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
    print(f"\n{len(tests) - failures}/{len(tests)} geography tests passed.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(_run_all())
