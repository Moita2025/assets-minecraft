import json

from configs import ID_JSON_FILE


def get_english_to_alias_dict():
    """
    从 ID_JSON_FILE 构建 englishId -> aliasID 的映射。

    每个条目使用 idDetails[-1]（即当前版本的实际 ID）作为 key，
    aliasID 作为 value。缺少 idDetails 或 aliasID 的条目会被跳过。
    """
    with open(ID_JSON_FILE, "r", encoding="utf-8") as f:
        id_data = json.load(f)

    en_to_alias = {}

    for item in id_data:
        id_details = item.get("idDetails")
        if not id_details:
            continue

        last = id_details[-1]
        if not isinstance(last, dict):
            continue

        english_id = last.get("englishId")
        alias = item.get("aliasID")
        if english_id is None or alias is None:
            continue

        en_to_alias[english_id] = alias

    return en_to_alias
