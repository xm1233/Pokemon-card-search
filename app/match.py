"""中文物种前缀匹配与英文卡名整词过滤。"""

import unicodedata

# 候选列表最多返回条数
SUGGESTION_LIMIT = 30
# PokeAPI / 卡面可能使用的各类撇号，统一后再比对
_APOSTROPHES = "’‘ʼ＇`"


def normalize_apostrophes(name: str) -> str:
    """弯引号与直引号视为同一字符（如 Farfetch'd）。"""
    for character in _APOSTROPHES:
        name = name.replace(character, "'")
    return name


def apostrophe_forms(name: str) -> list[str]:
    """生成要向 TCGdex 查询的英文名变体，覆盖两种撇号写法。"""
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
    """简体名以 query 为前缀的物种（前缀匹配，非包含）。"""
    query = query.strip()
    if not query:
        return []
    return [item for item in species if str(item["zh"]).startswith(query)]


def card_name_matches_species(card_name: str, species_name: str) -> bool:
    """卡名中是否出现物种英文名，且前后为词界（非字母）。

    例如 Mew 匹配 Mew ex，不匹配 Mewtwo；Pikachu 匹配 Pikachu-GX。
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
        # 物种名前后不能紧挨其它字母，避免 Mew 误匹配 Mewtwo
        before_ok = index == 0 or not _is_letter(haystack[index - 1])
        after_ok = end == len(haystack) or not _is_letter(haystack[end])
        if before_ok and after_ok:
            return True
        start = index + 1


def set_id_from_card_id(card_id: str, set_ids: list[str]) -> str | None:
    """从全局卡 id（如 swsh3-136）解析套装 id。

    套装 id 可能含连字符（tk-ex-latia），取最长前缀匹配。
    """
    best: str | None = None
    best_length = -1
    for set_id in set_ids:
        prefix = f"{set_id}-"
        if card_id.startswith(prefix) and len(prefix) > best_length:
            best = set_id
            best_length = len(prefix)
    return best


def local_id_sort_key(local_id: str) -> tuple:
    """卡编号排序：纯数字按数值，非数字（如 TG01）排在后面。"""
    if local_id.isdigit():
        return (0, int(local_id), "")
    return (1, 0, local_id)


def _is_letter(character: str) -> bool:
    return unicodedata.category(character).startswith("L")
