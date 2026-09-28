"""Load English international cards for one species name."""

import logging
import threading
from math import ceil
from urllib.error import HTTPError, URLError

from tcgdexsdk import Query, TCGdex

from app.match import (
    apostrophe_forms,
    card_name_matches_species,
    local_id_sort_key,
    set_id_from_card_id,
)

logger = logging.getLogger(__name__)

PAGE_SIZE = 24
FETCH_PAGE_SIZE = 250

TYPE_ZH = {
    "Colorless": "无色",
    "Darkness": "恶",
    "Dragon": "龙",
    "Fairy": "妖",
    "Fighting": "斗",
    "Fire": "火",
    "Grass": "草",
    "Lightning": "电",
    "Metal": "钢",
    "Psychic": "超",
    "Water": "水",
}


class TcgdexError(Exception):
    """TCGdex could not be reached or its response could not be read."""


class Catalog:
    def __init__(self, species: list[dict], sdk: TCGdex | None = None):
        self.species = species
        self.english_names = {item["en"] for item in species}
        self.sdk = sdk or TCGdex("en")
        self._cards: dict[str, list[dict]] = {}
        self._set_names: dict[str, str] | None = None
        self._lock = threading.Lock()

    def zh_names_for(self, english_name: str) -> list[str]:
        return [item["zh"] for item in self.species if item["en"] == english_name]

    def cards_page(self, english_name: str, page: int) -> dict:
        cards = self._filtered_cards(english_name)
        total = len(cards)
        zh_names = self.zh_names_for(english_name)
        if total == 0:
            return {
                "en": english_name,
                "zhNames": zh_names,
                "page": 1,
                "pageSize": PAGE_SIZE,
                "total": 0,
                "pages": 0,
                "items": [],
            }
        pages = ceil(total / PAGE_SIZE)
        page = min(max(page, 1), pages)
        start = (page - 1) * PAGE_SIZE
        return {
            "en": english_name,
            "zhNames": zh_names,
            "page": page,
            "pageSize": PAGE_SIZE,
            "total": total,
            "pages": pages,
            "items": cards[start : start + PAGE_SIZE],
        }

    def card_detail(self, card_id: str) -> dict | None:
        try:
            card = self.sdk.card.getSync(card_id)
        except HTTPError as exc:
            if exc.code == 404:
                return None
            raise TcgdexError("TCGdex 暂时查不到，请稍后再试") from exc
        except Exception as exc:
            logger.exception("tcgdex card detail failed")
            raise TcgdexError("TCGdex 暂时查不到，请稍后再试") from exc
        if card is None:
            return None
        return _detail(card)

    def _filtered_cards(self, english_name: str) -> list[dict]:
        with self._lock:
            cached = self._cards.get(english_name)
            if cached is not None:
                return cached
            cards = self._load_cards(english_name)
            self._cards[english_name] = cards
            return cards

    def _load_cards(self, english_name: str) -> list[dict]:
        resumes = self._list_name_contains(english_name)
        set_names = self._set_name_index()
        matched = []
        for card in resumes:
            if not card_name_matches_species(card.name, english_name):
                continue
            set_id = set_id_from_card_id(card.id, list(set_names))
            if set_id is None:
                set_id = _set_id_from_image(card.image) or ""
            image = card.get_image_url("low", "webp") if card.image else None
            matched.append(
                {
                    "id": card.id,
                    "name": card.name,
                    "localId": card.localId,
                    "setId": set_id,
                    "setName": set_names.get(set_id, set_id),
                    "image": image,
                }
            )
        matched.sort(
            key=lambda item: (
                item["setId"],
                local_id_sort_key(item["localId"]),
                item["id"],
            )
        )
        return matched

    def _list_name_contains(self, english_name: str) -> list:
        found = []
        seen: set[str] = set()
        errors: list[TcgdexError] = []
        for spelling in apostrophe_forms(english_name):
            try:
                self._collect_spelling(spelling, found, seen)
            except TcgdexError as exc:
                errors.append(exc)
        if not found and errors:
            raise errors[0]
        return found

    def _collect_spelling(self, spelling: str, found: list, seen: set[str]) -> None:
        page = 1
        while True:
            query = Query().contains("name", spelling).paginate(page, FETCH_PAGE_SIZE)
            batch = self._call(lambda query=query: self.sdk.card.listSync(query))
            if not batch:
                return
            fresh = [card for card in batch if card.id not in seen]
            if not fresh:
                return
            seen.update(card.id for card in fresh)
            found.extend(fresh)
            if len(batch) < FETCH_PAGE_SIZE:
                return
            page += 1

    def _set_name_index(self) -> dict[str, str]:
        if self._set_names is None:
            sets = self._call(lambda: self.sdk.set.listSync())
            self._set_names = {item.id: item.name for item in sets}
        return self._set_names

    def _call(self, fn):
        try:
            return fn()
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            raise TcgdexError("TCGdex 暂时查不到，请稍后再试") from exc
        except Exception as exc:
            logger.exception("tcgdex request failed")
            raise TcgdexError("TCGdex 暂时查不到，请稍后再试") from exc


def _set_id_from_image(image: str | None) -> str | None:
    if not image:
        return None
    parts = [part for part in image.rstrip("/").split("/") if part]
    if len(parts) >= 2:
        return parts[-2]
    return None


def _type_label(english: str) -> dict:
    return {"en": english, "zh": TYPE_ZH.get(english, english)}


def _detail(card) -> dict:
    attacks = []
    for attack in card.attacks or []:
        damage = attack.damage
        attacks.append(
            {
                "name": attack.name or "",
                "damage": None if damage is None else str(damage),
                "effect": attack.effect,
                "cost": [_type_label(cost) for cost in (attack.cost or [])],
            }
        )
    official = None
    if getattr(card, "set", None) is not None and card.set.cardCount is not None:
        official = card.set.cardCount.official
    return {
        "id": card.id,
        "name": card.name,
        "localId": card.localId,
        "setId": card.set.id if card.set else "",
        "setName": card.set.name if card.set else "",
        "officialCount": official,
        "image": card.get_image_url("high", "webp") if card.image else None,
        "hp": card.hp,
        "types": [_type_label(item) for item in (card.types or [])],
        "attacks": attacks,
    }
