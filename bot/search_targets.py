"""
The eBay searches the bot runs.

Each target:
  name        - short label shown in Discord
  keywords    - the eBay search query
  min_price   - ignore listings below this (USD), or None for no floor
  category_id - eBay category to restrict the search to (one of the constants below), or
                None to search all categories
  required    - list of words/phrases that must ALL appear in a listing's title, or it's
                dropped from the response. Case- and accent-insensitive ("pokemon" matches
                "Pokémon"). Blank "" entries are ignored, so an all-blank list filters nothing.
                Example: required=["jungle", "japanese", "pack"]
"""

import unicodedata
from dataclasses import dataclass, field

# eBay US category IDs for category_id (eBay accepts one per search).
CCG_INDIVIDUAL_CARDS = "183454"  # single cards
CCG_SEALED_BOOSTER_PACKS = "183456"  # sealed packs
COLLECTIBLES_GRADED = "183051"  # where many graded/slabbed (PSA) sealed packs are listed


def _normalize(text: str) -> str:
    """Lowercase and strip accents so 'Pokémon' == 'pokemon'."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


@dataclass(frozen=True)
class SearchTarget:
    name: str
    keywords: str
    min_price: float | None = None
    category_id: str | None = None
    required: list[str] = field(default_factory=list)

    def matches(self, title: str) -> bool:
        """True if the title contains every required string (blank "" entries are ignored)."""
        title = _normalize(title)
        return all(_normalize(word) in title for word in self.required if word.strip())


SEARCH_TARGETS: list[SearchTarget] = [
    SearchTarget(
        name="Jungle",
        keywords="Nintendo Pokémon TCG Jungle 1995 Japanese sealed booster pack",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Jungle", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
    SearchTarget(
        name="Neo 2",
        keywords="2000 Pokemon Japanese Neo 2 Discovery Booster packs",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Neo", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
    SearchTarget(
        name="Gym 2",
        keywords="1996 Pokemon Japanese Gym Challenge 2 Booster Packs",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Gym", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
    SearchTarget(
        name="Fossil",
        keywords="1997 JAPANESE POKEMON FOSSIL BOOSTER PACK",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Fossil", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
    SearchTarget(
        name="Rocket Gang",
        keywords="1997 Pokemon Japanese Rocket Gang sealed booster pack",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Rocket", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
    SearchTarget(
        name="Neo Gen",
        keywords="1999 Pokemon Japanese Neo Genesis Booster sealed booster pack",
        min_price=700,
        category_id=CCG_SEALED_BOOSTER_PACKS,  # or CCG_SEALED_BOOSTER_PACKS, etc.
        required=["Neo", "Japanese"],  # fill in: listing titles must contain ALL of these
    ),
]


def active_targets() -> list[SearchTarget]:
    """Targets that have been filled in (skips the TODO placeholders)."""
    return [t for t in SEARCH_TARGETS if t.keywords and t.keywords != "TODO"]
