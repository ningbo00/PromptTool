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
            "qwen-max",
            "qwen-max-latest",
            "qwen-plus",
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


def get_ai_config():
    """返回当前激活服务商的 (url, key, model)。"""
    provider = AI_PROVIDERS.get(AI_PROVIDER, AI_PROVIDERS["kimi"])
    return (
        provider.url,
        globals().get(provider.api_key_attr, ""),
        globals().get(provider.model_attr, ""),
    )


def load_ai_config():
    """从 ai_config.json 加载配置，覆盖模块全局变量。"""
    global AI_PROVIDER
    if not os.path.exists(AI_CONFIG_FILE):
        return
    try:
        with open(AI_CONFIG_FILE, "r", encoding="utf-8") as f:
            saved = json.load(f)
        for provider in AI_PROVIDERS.values():
            globals()[provider.api_key_attr] = saved.get(_json_key(provider, "api_key"), globals()[provider.api_key_attr])
            globals()[provider.model_attr] = saved.get(_json_key(provider, "model"), globals()[provider.model_attr])
        AI_PROVIDER = saved.get("ai_provider", AI_PROVIDER)
    except Exception:
        pass


def save_ai_config():
    """将当前配置持久化到 ai_config.json。"""
    saved = {"ai_provider": AI_PROVIDER}
    for provider in AI_PROVIDERS.values():
        saved[_json_key(provider, "api_key")] = globals().get(provider.api_key_attr, "")
        saved[_json_key(provider, "model")] = globals().get(provider.model_attr, "")
    with open(AI_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(saved, f, ensure_ascii=False, indent=2)


def _json_key(provider: AIProviderSpec, suffix: str) -> str:
    return f"{provider.key}_{suffix}"
