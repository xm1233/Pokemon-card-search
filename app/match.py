"""Chinese species prefix lookup and English whole-word card matching."""

import unicodedata

SUGGESTION_LIMIT = 30
_APOSTROPHES = "’‘ʼ＇`"


def normalize_apostrophes(name: str) -> str:
    """Treat curly and straight apostrophes as the same character."""
    for character in _APOSTROPHES:
        name = name.replace(character, "'")
    return name


def apostrophe_forms(name: str) -> list[str]:
    """Spellings to send to TCGdex so both quote styles are searched."""
    straight = normalize_apostrophes(name)
    forms = [straight]
    if "'" in straight:
        curly = straight.replace("'", "’")
        if curly not in forms:
            forms.append(curly)
    if name not in forms:
        forms.append(name)
    return forms


def species_by_prefix(species: list[dict], query: str) -> list[dict]:
    """Return species whose Simplified Chinese name starts with query."""
    query = query.strip()
    if not query:
        return []
    return [item for item in species if str(item["zh"]).startswith(query)]


def card_name_matches_species(card_name: str, species_name: str) -> bool:
    """True when species_name appears as a whole word in card_name.

    Boundaries are the ends of the string or any character that is not a
    Unicode letter. ``Mew`` matches ``Mew ex`` and does not match ``Mewtwo``.
    ``Pikachu`` matches ``Pikachu-GX`` and ``Dark Charizard`` matches
    ``Charizard``.
    """
    if not card_name or not species_name:
        return False
    haystack = normalize_apostrophes(card_name).casefold()
    needle = normalize_apostrophes(species_name).casefold()
    start = 0
    while True:
        index = haystack.find(needle, start)
        if index < 0:
            return False
        end = index + len(needle)
        before_ok = index == 0 or not _is_letter(haystack[index - 1])
        after_ok = end == len(haystack) or not _is_letter(haystack[end])
        if before_ok and after_ok:
            return True
        start = index + 1


def set_id_from_card_id(card_id: str, set_ids: list[str]) -> str | None:
    """Pick the longest set id that is a prefix of ``setId-localId``."""
    best: str | None = None
    best_length = -1
    for set_id in set_ids:
        prefix = f"{set_id}-"
        if card_id.startswith(prefix) and len(prefix) > best_length:
            best = set_id
            best_length = len(prefix)
    return best


def local_id_sort_key(local_id: str) -> tuple:
    if local_id.isdigit():
        return (0, int(local_id), "")
    return (1, 0, local_id)


def _is_letter(character: str) -> bool:
    return unicodedata.category(character).startswith("L")
