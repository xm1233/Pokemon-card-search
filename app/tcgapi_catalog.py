"""通过 TCG API 按物种英文名搜索宝可梦卡并缓存结果。"""

import logging
import re
import threading
from math import ceil
from typing import Any

import httpx
from tcgapi import TCGApi
from tcgapi.errors import NotFoundError, RateLimitError, TcgApiError as TcgApiSdkError

from app.card_type import BULK_CARDS_CHUNK, is_pokemon_card_attributes
from app.match import card_name_matches_species, local_id_sort_key

logger = logging.getLogger(__name__)

PAGE_SIZE = 24
GAME_SLUG = "pokemon"

TYPE_ZH = {
    "Colorless": "无色",
    "Darkness": "恶",
    "Dark": "恶",
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


class TcgApiCatalogError(Exception):
    """TCG API 调用失败，由 HTTP 层转为 502/429。"""


def _network_error(exc: Exception) -> TcgApiCatalogError:
    if isinstance(exc, httpx.ConnectError):
        return TcgApiCatalogError(
            "无法连接 TCG API：本机 HTTP 代理未开启或网络不通，请关闭系统代理或启动代理软件后重试"
        )
    return TcgApiCatalogError("TCG API 暂时查不到，请稍后再试")


class TcgApiCatalog:
    """物种 → 卡牌列表；同一英文名只拉取一次搜索并整词过滤，翻页走内存。"""

    def __init__(self, species: list[dict], client: TCGApi | None = None):
        self.species = species
        self.english_names = {item["en"] for item in species}
        self.client = client or TCGApi()
        self._cards: dict[str, list[dict]] = {}
        self._lock = threading.Lock()

    def zh_names_for(self, english_name: str) -> list[str]:
        return [item["zh"] for item in self.species if item["en"] == english_name]

    def cards_page(self, english_name: str, page: int) -> dict:
        cards = self._filtered_cards(english_name)
        total = len(cards)
        zh_names = self.zh_names_for(english_name)
        if total == 0:
            return {
                "source": "tcgapi",
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
            "source": "tcgapi",
            "en": english_name,
            "zhNames": zh_names,
            "page": page,
            "pageSize": PAGE_SIZE,
            "total": total,
            "pages": pages,
            "items": cards[start : start + PAGE_SIZE],
        }

    def card_detail(self, card_id: int) -> dict | None:
        try:
            card_resp = self.client.cards.get(card_id)
            prices_resp = self.client.cards.prices(card_id)
        except NotFoundError:
            return None
        except RateLimitError as exc:
            raise TcgApiCatalogError("今日 API 请求已达上限，请明天再试或升级套餐") from exc
        except TcgApiSdkError as exc:
            logger.exception("tcgapi card detail failed")
            raise TcgApiCatalogError("TCG API 暂时查不到，请稍后再试") from exc
        except httpx.HTTPError as exc:
            logger.exception("tcgapi card detail network error")
            raise _network_error(exc) from exc
        return _detail(card_resp.data, prices_resp.data)

    def _filtered_cards(self, english_name: str) -> list[dict]:
        with self._lock:
            cached = self._cards.get(english_name)
            if cached is not None:
                return cached
            cards = self._load_cards(english_name)
            self._cards[english_name] = cards
            return cards

    def _load_cards(self, english_name: str) -> list[dict]:
        candidates = []
        try:
            for row in self.client.search.iter(
                english_name,
                game=GAME_SLUG,
                type="Cards",
                sort="name",
            ):
                if row.product_type and row.product_type != "Cards":
                    continue
                if not card_name_matches_species(row.name, english_name):
                    continue
                candidates.append(row)
            pokemon_ids = self._pokemon_card_ids(
                list(dict.fromkeys(row.id for row in candidates))
            )
        except RateLimitError as exc:
            raise TcgApiCatalogError("今日 API 请求已达上限，请明天再试或升级套餐") from exc
        except TcgApiSdkError as exc:
            logger.exception("tcgapi search failed")
            raise TcgApiCatalogError("TCG API 暂时查不到，请稍后再试") from exc
        except httpx.HTTPError as exc:
            logger.exception("tcgapi search network error")
            raise _network_error(exc) from exc

        matched = [_list_item(row) for row in candidates if row.id in pokemon_ids]
        matched.sort(
            key=lambda item: (
                item["setName"],
                local_id_sort_key(item["localId"]),
                item["id"],
            )
        )
        return matched

    def _pokemon_card_ids(self, card_ids: list[int]) -> set[int]:
        if not card_ids:
            return set()
        pokemon: set[int] = set()
        for start in range(0, len(card_ids), BULK_CARDS_CHUNK):
            chunk = card_ids[start : start + BULK_CARDS_CHUNK]
            resp = self.client.bulk.cards(chunk)
            for card in resp.data:
                if is_pokemon_card_attributes(card.custom_attributes):
                    pokemon.add(card.id)
        return pokemon


def _list_item(row) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "localId": row.number or "",
        "setName": row.set_name or "",
        "image": row.image_url,
        "rarity": row.rarity,
        "printing": row.printing,
        "marketPrice": row.market_price,
    }


def _type_label(english: str) -> dict:
    key = english.strip()
    return {"en": key, "zh": TYPE_ZH.get(key, key)}


def _parse_hp(attrs: dict[str, Any]) -> int | None:
    raw = attrs.get("hp")
    if raw is None:
        return None
    digits = re.sub(r"[^\d]", "", str(raw))
    return int(digits) if digits else None


def _parse_types(attrs: dict[str, Any]) -> list[dict]:
    raw = attrs.get("energyType") or attrs.get("energy_type")
    if raw is None:
        return []
    if isinstance(raw, str):
        items = [raw]
    else:
        items = list(raw)
    return [_type_label(str(item).strip()) for item in items if str(item).strip()]


def _parse_attacks(attrs: dict[str, Any]) -> list[dict]:
    attacks = []
    for key in ("attack1", "attack2", "attack3", "attack4"):
        text = attrs.get(key)
        if not text:
            continue
        attacks.append({"name": str(text).strip(), "damage": None, "effect": None, "cost": []})
    return attacks


def _detail(card, prices: list) -> dict:
    attrs = card.custom_attributes or {}
    price_rows = []
    for price in prices or []:
        price_rows.append(
            {
                "printing": price.printing,
                "marketPrice": price.market_price,
                "lowPrice": price.low_price,
                "medianPrice": price.median_price,
            }
        )
    return {
        "source": "tcgapi",
        "id": card.id,
        "name": card.name,
        "localId": card.number or "",
        "setName": card.set_name or "",
        "rarity": card.rarity,
        "image": card.image_url,
        "tcgplayerUrl": card.tcgplayer_url,
        "hp": _parse_hp(attrs),
        "types": _parse_types(attrs),
        "attacks": _parse_attacks(attrs),
        "prices": price_rows,
    }
