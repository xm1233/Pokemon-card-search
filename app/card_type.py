"""根据 TCG API custom_attributes 判断是否为宝可梦（Pokémon）卡。"""

from typing import Any

BULK_CARDS_CHUNK = 100


def card_type_from_attributes(attrs: dict[str, Any] | None) -> str | None:
    if not attrs:
        return None
    raw = attrs.get("cardType") or attrs.get("card_type")
    if raw is None:
        return None
    if isinstance(raw, list):
        if not raw:
            return None
        raw = raw[0]
    text = str(raw).strip()
    return text or None


def is_pokemon_card_attributes(attrs: dict[str, Any] | None) -> bool:
    """训练家 / 场地 / 能量等 cardType 非 Pokemon。"""
    label = card_type_from_attributes(attrs)
    if label is None:
        return False
    return label.casefold() == "pokemon"
