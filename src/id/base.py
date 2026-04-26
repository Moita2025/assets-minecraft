import json

from configs import ID_JSON_FILE

def get_id_dict():
    # 读取 ID 映射表
    with open(ID_JSON_FILE, "r", encoding="utf-8") as f:
        id_data = json.load(f)

    # 构建 englishId -> 中文 的映射
    en_to_zh = {}

    for item in id_data:
        if "idDetails" not in item or not item["idDetails"]:
            continue

        last = item["idDetails"][-1]

        if "englishId" in last:
            en = last["englishId"]
            zh = item.get("chineseName", en)  # fallback
            en_to_zh[en] = zh

    return en_to_zh