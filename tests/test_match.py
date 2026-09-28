import json
from pathlib import Path

from app.match import (
    apostrophe_forms,
    card_name_matches_species,
    local_id_sort_key,
    set_id_from_card_id,
    species_by_prefix,
)

SPECIES = [
    {"id": 25, "zh": "皮卡丘", "en": "Pikachu"},
    {"id": 172, "zh": "皮丘", "en": "Pichu"},
    {"id": 6, "zh": "喷火龙", "en": "Charizard"},
]


def test_prefix_matches_pikachu_and_rejects_a_middle_character():
    hits = [item["zh"] for item in species_by_prefix(SPECIES, "皮卡")]
    assert hits == ["皮卡丘"]
    assert species_by_prefix(SPECIES, "丘") == []
    assert species_by_prefix(SPECIES, "   ") == []


def test_prefix_on_the_committed_dictionary():
    path = Path(__file__).resolve().parents[1] / "data" / "species.json"
    species = json.loads(path.read_text(encoding="utf-8"))
    pikachu = next(item for item in species if item["id"] == 25)
    assert pikachu == {"id": 25, "zh": "皮卡丘", "en": "Pikachu"}
    hits = species_by_prefix(species, "皮卡")
    assert any(item["zh"] == "皮卡丘" for item in hits)
    assert all(item["zh"].startswith("皮卡") for item in hits)
    assert all(item["zh"] != "皮卡丘" for item in species_by_prefix(species, "丘"))


def test_whole_word_keeps_suffixes_and_drops_mewtwo():
    assert card_name_matches_species("Pikachu", "Pikachu")
    assert card_name_matches_species("Pikachu V", "Pikachu")
    assert card_name_matches_species("Pikachu-GX", "Pikachu")
    assert card_name_matches_species("Dark Charizard", "Charizard")
    assert card_name_matches_species("Mew ex", "Mew")
    assert not card_name_matches_species("Mewtwo", "Mew")
    assert card_name_matches_species("Mr. Mime", "Mr. Mime")
    assert not card_name_matches_species("Mime Jr.", "Mr. Mime")
    assert card_name_matches_species("pikachu vmax", "Pikachu")
    assert card_name_matches_species("Sirfetch'd", "Sirfetch’d")
    assert card_name_matches_species("Galarian Sirfetch'd", "Sirfetch’d")
    assert card_name_matches_species("Farfetch’d", "Farfetch'd")


def test_apostrophe_forms_cover_both_quote_styles():
    assert apostrophe_forms("Sirfetch'd") == ["Sirfetch'd", "Sirfetch\u2019d"]
    assert apostrophe_forms("Pikachu") == ["Pikachu"]


def test_set_id_uses_the_longest_hyphenated_prefix():
    set_ids = ["tk", "tk-ex", "tk-ex-latia", "swsh3"]
    assert set_id_from_card_id("tk-ex-latia-10", set_ids) == "tk-ex-latia"
    assert set_id_from_card_id("swsh3-136", set_ids) == "swsh3"


def test_local_ids_sort_numerically_before_gallery_numbers():
    assert sorted(["10", "2", "TG01", "1"], key=local_id_sort_key) == [
        "1",
        "2",
        "10",
        "TG01",
    ]
