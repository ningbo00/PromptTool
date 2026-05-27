from features.ai_settings.widget import PROVIDER_COLORS
from shared.config import AI_PROVIDERS


def test_ai_settings_lists_all_configured_providers():
    assert set(PROVIDER_COLORS) >= set(AI_PROVIDERS)
    assert AI_PROVIDERS["doubao"].label.startswith("豆包")
    assert AI_PROVIDERS["deepseek"].label.startswith("DeepSeek")
    assert "ChatGPT" in AI_PROVIDERS["openai"].label


def test_ai_settings_model_catalogs_include_requested_models():
    assert "doubao-seed-1-6" in AI_PROVIDERS["doubao"].models
    assert "deepseek-v4-pro" in AI_PROVIDERS["deepseek"].models
    assert "deepseek-v4-flash" in AI_PROVIDERS["deepseek"].models
    assert "gpt-5.1" in AI_PROVIDERS["openai"].models
