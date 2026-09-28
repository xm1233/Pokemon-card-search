"""从 PokeAPI 生成 data/species.json（简体名 ↔ 英文名）。

运行期搜索只读该 JSON，不访问 PokeAPI。全国图鉴新增物种时再执行本脚本。
"""

import csv
import io
import json
import urllib.request
from pathlib import Path

CSV_URL = (
    "https://raw.githubusercontent.com/PokeAPI/pokeapi/master/"
    "data/v2/csv/pokemon_species_names.csv"
)
# PokeAPI languages.csv 中的 local_language_id
ZH_HANS = "12"
EN = "9"
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "species.json"


def _straight_apostrophe(name: str) -> str:
    """英文名统一为直撇号，与卡面及 match 模块一致。"""
    for character in "’‘ʼ＇`":
        name = name.replace(character, "'")
    return name


def build_species(csv_text: str) -> list[dict]:
    zh_names: dict[int, str] = {}
    en_names: dict[int, str] = {}
    reader = csv.DictReader(io.StringIO(csv_text))
    for row in reader:
        name = (row.get("name") or "").strip()
        if not name:
            continue
        species_id = int(row["pokemon_species_id"])
        language_id = row["local_language_id"]
        if language_id == ZH_HANS:
            zh_names[species_id] = name
        elif language_id == EN:
            en_names[species_id] = _straight_apostrophe(name)

    species = []
    # 仅保留同时有简体与英文名的物种
    for species_id in sorted(set(zh_names) & set(en_names)):
        species.append(
            {
                "id": species_id,
                "zh": zh_names[species_id],
                "en": en_names[species_id],
            }
        )
    return species


def main() -> None:
    with urllib.request.urlopen(CSV_URL) as response:
        csv_text = response.read().decode("utf-8-sig")
    species = build_species(csv_text)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(species, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(species)} species to {OUT}")


if __name__ == "__main__":
    main()
