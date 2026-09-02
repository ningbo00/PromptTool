"""
AI 服务商配置 + ai_config.json 读写
"""
from dataclasses import dataclass
import json
import os
import sys


if getattr(sys, "frozen", False):
    _BASE_DIR = os.path.dirname(sys.executable)
else:
    _BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    _BASE_DIR = os.path.dirname(_BASE_DIR)

AI_CONFIG_FILE = os.path.join(_BASE_DIR, "ai_config.json")


@dataclass(frozen=True)
class AIProviderSpec:
    key: str
    label: str
    url: str
    api_key_attr: str
    model_attr: str
    models: tuple[str, ...]
    note: str


AI_PROVIDERS = {
    "kimi": AIProviderSpec(
        key="kimi",
        label="Kimi (Moonshot)",
        url="https://api.moonshot.cn/v1/chat/completions",
        api_key_attr="KIMI_API_KEY",
        model_attr="KIMI_MODEL",
        models=(
            "moonshot-v1-8k-vision-preview",
            "kimi-k2.5",
            "kimi-k2-0905-preview",
            "kimi-k2-thinking",
            "moonshot-v1-8k",
            "moonshot-v1-32k",
            "moonshot-v1-128k",
        ),
        note="API 文档: platform.moonshot.cn  ·  端点: api.moonshot.cn",
    ),
    "bailian": AIProviderSpec(
        key="bailian",
        label="阿里百炼 (Qwen)",
        url="https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions",
        api_key_attr="BAILIAN_API_KEY",
        model_attr="BAILIAN_MODEL",
        models=(
            "qwen-vl-max",
            "qwen-vl-plus",
            "qwen-vl-plus-latest",
            "qwen2.5-vl-72b-instruct",
            "qwen2.5-vl-32b-instruct",
            "qwen-max",
            "qwen-max-latest",
            "qwen-plus",
            "qwen-plus-latest",
            "qwen-turbo",
            "qwen-long",
            "qwen2.5-72b-instruct",
            "qwen2.5-14b-instruct",
            "qwen2.5-7b-instruct",
        ),
        note="API 文档: bailian.console.aliyun.com  ·  端点: dashscope.aliyuncs.com",
    ),
    "doubao": AIProviderSpec(
        key="doubao",
        label="豆包 / 火山方舟",
        url="https://ark.cn-beijing.volces.com/api/v3/chat/completions",
        api_key_attr="DOUBAO_API_KEY",
        model_attr="DOUBAO_MODEL",
        models=(
            "doubao-1.5-vision-pro",
            "doubao-1.5-vision-lite",
            "doubao-seed-1-6",
            "doubao-seed-1-6-flash",
            "doubao-seed-1-6-thinking",
            "doubao-1.5-pro-32k",
            "doubao-1.5-lite-32k",
        ),
        note="API 文档: 火山方舟 Ark  ·  OpenAI 兼容端点: ark.cn-beijing.volces.com",
    ),
    "deepseek": AIProviderSpec(
        key="deepseek",
        label="DeepSeek 官网",
        url="https://api.deepseek.com/chat/completions",
        api_key_attr="DEEPSEEK_API_KEY",
        model_attr="DEEPSEEK_MODEL",
        models=(
            "deepseek-v4-pro",
            "deepseek-v4-flash",
            "deepseek-chat",
            "deepseek-reasoner",
        ),
        note="API 文档: api-docs.deepseek.com  ·  端点: api.deepseek.com",
    ),
    "openai": AIProviderSpec(
        key="openai",
        label="ChatGPT / OpenAI",
        url="https://api.openai.com/v1/chat/completions",
        api_key_attr="OPENAI_API_KEY",
        model_attr="OPENAI_MODEL",
        models=(
            "gpt-5.1",
            "gpt-5.1-chat-latest",
            "gpt-5",
            "gpt-4.1",
            "gpt-4o",
            "gpt-4o-mini",
        ),
        note="API 文档: platform.openai.com  ·  端点: api.openai.com",
    ),
}


KIMI_API_KEY = ""
KIMI_API_URL = AI_PROVIDERS["kimi"].url
KIMI_MODEL = "kimi-k2.5"

BAILIAN_API_KEY = ""
BAILIAN_API_URL = AI_PROVIDERS["bailian"].url
BAILIAN_MODEL = "qwen-plus"

DOUBAO_API_KEY = ""
DOUBAO_API_URL = AI_PROVIDERS["doubao"].url
DOUBAO_MODEL = "doubao-seed-1-6"

DEEPSEEK_API_KEY = ""
DEEPSEEK_API_URL = AI_PROVIDERS["deepseek"].url
DEEPSEEK_MODEL = "deepseek-v4-pro"

OPENAI_API_KEY = ""
OPENAI_API_URL = AI_PROVIDERS["openai"].url
OPENAI_MODEL = "gpt-5.1"

AI_PROVIDER = "bailian"
SCREENSHOT_SHORTCUT = "Ctrl+Shift+S"
SCREENSHOT_PROVIDER = "bailian"
SCREENSHOT_MODEL = "qwen-vl-max"
SCREENSHOT_ANALYSIS_MODE = "full_reverse"
SCREENSHOT_ANALYSIS_CUSTOM = ""
SCREENSHOT_PROMPT_DETAIL = "full"

VISION_MODEL_MARKERS = (
    "vision",
    "vl",
    "gpt-4o",
    "gpt-4.1",
    "gpt-5",
    "gemini",
)

DEFAULT_SCREENSHOT_MODELS = {
    "openai": "gpt-4o",
    "bailian": "qwen-vl-max",
    "kimi": "moonshot-v1-8k-vision-preview",
    "doubao": "doubao-1.5-vision-pro",
}

SCREENSHOT_MODEL_ALLOWLIST = {
    # User-requested ordinary Qwen entry for screenshot reverse prompt mode.
    "bailian": ("qwen-plus-latest",),
}


def get_ai_config():
    """返回当前激活服务商的 (url, key, model)。"""
    provider = AI_PROVIDERS.get(AI_PROVIDER, AI_PROVIDERS["kimi"])
    return (
        provider.url,
        globals().get(provider.api_key_attr, ""),
        globals().get(provider.model_attr, ""),
    )


def is_vision_model_name(model: str) -> bool:
    """Best-effort check for models that can accept image input."""
    name = (model or "").lower()
    return any(marker in name for marker in VISION_MODEL_MARKERS)


def is_screenshot_model_name(provider_key: str, model: str) -> bool:
    return is_vision_model_name(model) or model in SCREENSHOT_MODEL_ALLOWLIST.get(provider_key, ())


def get_vision_models(provider_key: str) -> tuple[str, ...]:
    provider = AI_PROVIDERS.get(provider_key)
    if provider is None:
        return ()
    return tuple(model for model in provider.models if is_screenshot_model_name(provider_key, model))


def get_vision_provider_keys() -> tuple[str, ...]:
    return tuple(key for key in AI_PROVIDERS if get_vision_models(key))


def get_screenshot_ai_config():
    """返回截图反推专用的 (url, key, model)，与文字分析模型解耦。"""
    provider = AI_PROVIDERS.get(SCREENSHOT_PROVIDER, AI_PROVIDERS["bailian"])
    return (
        provider.url,
        globals().get(provider.api_key_attr, ""),
        SCREENSHOT_MODEL,
    )


def load_ai_config():
    """从 ai_config.json 加载配置，覆盖模块全局变量。"""
    global AI_PROVIDER, SCREENSHOT_SHORTCUT, SCREENSHOT_PROVIDER, SCREENSHOT_MODEL
    global SCREENSHOT_ANALYSIS_MODE, SCREENSHOT_ANALYSIS_CUSTOM, SCREENSHOT_PROMPT_DETAIL
    if not os.path.exists(AI_CONFIG_FILE):
        return
    try:
        with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for provider in AI_PROVIDERS.values():
            globals()[provider.api_key_attr] = saved.get(_json_key(provider, "api_key"), globals()[provider.api_key_attr])
            globals()[provider.model_attr] = saved.get(_json_key(provider, "model"), globals()[provider.model_attr])
        AI_PROVIDER = saved.get("ai_provider", AI_PROVIDER)
        SCREENSHOT_SHORTCUT = saved.get("screenshot_shortcut", SCREENSHOT_SHORTCUT) or SCREENSHOT_SHORTCUT
        SCREENSHOT_PROVIDER = saved.get("screenshot_provider", SCREENSHOT_PROVIDER) or SCREENSHOT_PROVIDER
        SCREENSHOT_MODEL = saved.get("screenshot_model", SCREENSHOT_MODEL) or SCREENSHOT_MODEL
        SCREENSHOT_ANALYSIS_MODE = saved.get("screenshot_analysis_mode", SCREENSHOT_ANALYSIS_MODE) or SCREENSHOT_ANALYSIS_MODE
        SCREENSHOT_ANALYSIS_CUSTOM = saved.get("screenshot_analysis_custom", SCREENSHOT_ANALYSIS_CUSTOM) or ""
        SCREENSHOT_PROMPT_DETAIL = saved.get("screenshot_prompt_detail", SCREENSHOT_PROMPT_DETAIL) or SCREENSHOT_PROMPT_DETAIL
    except Exception:
        pass


def save_ai_config():
    """将当前配置持久化到 ai_config.json。"""
    saved = {
        "ai_provider": AI_PROVIDER,
        "screenshot_shortcut": SCREENSHOT_SHORTCUT,
        "screenshot_provider": SCREENSHOT_PROVIDER,
        "screenshot_model": SCREENSHOT_MODEL,
        "screenshot_analysis_mode": SCREENSHOT_ANALYSIS_MODE,
        "screenshot_analysis_custom": SCREENSHOT_ANALYSIS_CUSTOM,
        "screenshot_prompt_detail": SCREENSHOT_PROMPT_DETAIL,
    }
    for provider in AI_PROVIDERS.values():
        saved[_json_key(provider, "api_key")] = globals().get(provider.api_key_attr, "")
        saved[_json_key(provider, "model")] = globals().get(provider.model_attr, "")
    with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)


def _json_key(provider: AIProviderSpec, suffix: str) -> str:
    return f"{provider.key}_{suffix}"
