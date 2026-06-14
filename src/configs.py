RECIPES_INPUT_DIRECTORY = ""
TAGS_INPUT_DIRECTORIES = []
DEFAULT_NAMESPACE = "minecraft"
DEFAULT_TAG_PREFIX = f"#{DEFAULT_NAMESPACE}:"
SUPPORTED_TAG_PREFIXES = [DEFAULT_TAG_PREFIX]

ANALYSIS_PATH = ""
MERGED_JSON_FILE = f"{ANALYSIS_PATH}/recipes_original.json"
ID_JSON_FILE = f"{ANALYSIS_PATH}/config.json"
FINAL_JSON_FILE = f"{ANALYSIS_PATH}/recipes.json"

# 各 config.json 的 alias 命名空间清单（路径相对仓库根）。
# 新增模组资源时，往这里追加一条 {"path": ..., "namespace": ...} 即可。
ALIAS_CONFIGS = [
    {"path": ID_JSON_FILE,                              "namespace": "mc"},
    {"path": "zh-minecraft-wiki/config.json",           "namespace": "zhwiki"},
    {"path": "www-mcmod-cn/twilight-forest/config.json", "namespace": "twf"},
]