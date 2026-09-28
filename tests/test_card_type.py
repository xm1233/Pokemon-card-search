"""宝可梦卡 cardType 判定（不调用 TCG API）。"""

from app.card_type import card_type_from_attributes, is_pokemon_card_attributes


def test_pokemon_card_type():
    assert is_pokemon_card_attributes({"cardType": ["Pokemon"], "hp": 60})
    assert is_pokemon_card_attributes({"cardType": "Pokemon"})


def test_non_pokemon_card_types():
    assert not is_pokemon_card_attributes({"cardType": ["Trainer"]})
    assert not is_pokemon_card_attributes({"cardType": ["Stadium"]})
    assert not is_pokemon_card_attributes({"cardType": ["Energy"]})
    assert not is_pokemon_card_attributes(None)
    assert not is_pokemon_card_attributes({})


def test_card_type_from_list():
    assert card_type_from_attributes({"cardType": ["Pokemon", "Other"]}) == "Pokemon"
