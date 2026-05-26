"""
AI 服务商配置 + ai_config.json 读写
"""
import json
import os
import sys

# ── 路径 ──────────────────────────────────────────────────────
if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    # shared/ 的上一级才是项目根目录
    _BASE_DIR = os.path.dirname(_BASE_DIR)

AI_CONFIG_FILE = os.path.join(_BASE_DIR, "ai_config.json")

# ── Kimi 默认值 ────────────────────────────────────────────────
KIMI_API_KEY = "sk-kimi-ULjccYCKBbFZKXFsr3phpJZAmSBbrg561Ac4WhYeykcAHaER75cQKPPWXAlgzSWW"
KIMI_API_URL = "https://api.moonshot.cn/v1/chat/completions"
KIMI_MODEL   = "kimi-k2.5"

# ── 阿里百炼默认值 ─────────────────────────────────────────────
BAILIAN_API_KEY = "sk-88ea095f249246adb3da8e338abcb664"
BAILIAN_API_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
BAILIAN_MODEL   = "qwen-plus"

# ── 当前激活服务商 ─────────────────────────────────────────────
AI_PROVIDER = "bailian"


def get_ai_config():
    """返回当前激活服务商的 (url, key, model)"""
    if AI_PROVIDER == "bailian":
        return BAILIAN_API_URL, BAILIAN_API_KEY, BAILIAN_MODEL
    return KIMI_API_URL, KIMI_API_KEY, KIMI_MODEL


def load_ai_config():
    """从 ai_config.json 加载配置，覆盖模块全局变量"""
    global KIMI_API_KEY, KIMI_MODEL, BAILIAN_API_KEY, BAILIAN_MODEL, AI_PROVIDER
    if not os.path.exists(AI_CONFIG_FILE):
        return
    try:
        with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        KIMI_API_KEY    = cfg.get("kimi_api_key",    KIMI_API_KEY)
        KIMI_MODEL      = cfg.get("kimi_model",       KIMI_MODEL)
        BAILIAN_API_KEY = cfg.get("bailian_api_key",  BAILIAN_API_KEY)
        BAILIAN_MODEL   = cfg.get("bailian_model",    BAILIAN_MODEL)
        AI_PROVIDER     = cfg.get("ai_provider",      AI_PROVIDER)
    except Exception:
        pass


def save_ai_config():
    """将当前配置持久化到 ai_config.json"""
    cfg = {
        "kimi_api_key":    KIMI_API_KEY,
        "kimi_model":      KIMI_MODEL,
        "bailian_api_key": BAILIAN_API_KEY,
        "bailian_model":   BAILIAN_MODEL,
        "ai_provider":     AI_PROVIDER,
    }
    with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
