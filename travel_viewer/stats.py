"""Pure counting helpers over a set of visited alpha-2 codes."""

from __future__ import annotations

from typing import NamedTuple

from travel_viewer.countries import COUNTRIES, REGIONS, Country


class Progress(NamedTuple):
    """Visited-vs-total for some slice of the world."""

    visited: int
    total: int

    @property
    def fraction(self) -> float:
        """Share visited in ``[0, 1]``; 0.0 when the slice is empty."""
        return self.visited / self.total if self.total else 0.0

    @property
    def percent(self) -> int:
        """Share visited as a whole percent, for display."""
        return round(self.fraction * 100)


def overall(visited: set[str]) -> Progress:
    """Progress across all 195 sovereign states."""
    return Progress(len(visited & {c.alpha2 for c in COUNTRIES}), len(COUNTRIES))


def by_region(visited: set[str]) -> dict[str, Progress]:
    """Progress per region, in the fixed display order of ``REGIONS``."""
    counts = {region: [0, 0] for region in REGIONS}
    for country in COUNTRIES:
        counts[country.region][1] += 1
        if country.alpha2 in visited:
            counts[country.region][0] += 1
    return {region: Progress(v, t) for region, (v, t) in counts.items()}


def in_region(region: str) -> list[Country]:
    """Countries in ``region``, alphabetical by display name."""
    return sorted((c for c in COUNTRIES if c.region == region), key=lambda c: c.name)


def _match_rank(country: Country, q: str) -> int | None:
    """How well ``country`` matches ``q``; lower is better, ``None`` means no match.

    Exact code matches outrank names so that typing "pt" finds Portugal rather
    than Egypt, which merely contains those letters.
    """
    if q in (country.alpha2.lower(), country.alpha3.lower()):
        return 0
    name = country.name.lower()
    if name.startswith(q):
        return 1
    if q in name:
        return 2
    return None


def search(query: str) -> list[Country]:
    """Countries matching ``query`` by code or name, best matches first."""
    q = query.strip().lower()
    if not q:
        return []
    ranked = ((rank, c) for c in COUNTRIES if (rank := _match_rank(c, q)) is not None)
    return [c for _, c in sorted(ranked, key=lambda pair: (pair[0], pair[1].name))]
