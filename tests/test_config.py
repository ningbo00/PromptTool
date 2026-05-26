import json

from tests.conftest import reload_module


def _config_with_file(monkeypatch, tmp_path):
    config = reload_module("shared.config")
    monkeypatch.setattr(config, "AI_CONFIG_FILE", str(tmp_path / "ai_config.json"))
    return config


def test_default_config_uses_empty_api_keys(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)

    assert config.KIMI_API_KEY == ""
    assert config.BAILIAN_API_KEY == ""


def test_load_ai_config_keeps_safe_defaults_when_file_missing(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)

    config.load_ai_config()

    assert config.AI_PROVIDER == "bailian"
    assert config.KIMI_API_KEY == ""
    assert config.BAILIAN_API_KEY == ""


def test_save_and_load_ai_config_round_trips(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)
    config.AI_PROVIDER = "kimi"
    config.KIMI_API_KEY = "test-kimi-key"
    config.KIMI_MODEL = "moonshot-v1-8k"
    config.BAILIAN_API_KEY = "test-bailian-key"
    config.BAILIAN_MODEL = "qwen-plus"

    config.save_ai_config()
    config.AI_PROVIDER = "bailian"
    config.KIMI_API_KEY = ""
    config.KIMI_MODEL = ""
    config.BAILIAN_API_KEY = ""
    config.BAILIAN_MODEL = ""
    config.load_ai_config()

    assert config.AI_PROVIDER == "kimi"
    assert config.KIMI_API_KEY == "test-kimi-key"
    assert config.KIMI_MODEL == "moonshot-v1-8k"
    assert config.BAILIAN_API_KEY == "test-bailian-key"
    assert config.BAILIAN_MODEL == "qwen-plus"


def test_load_ai_config_ignores_invalid_json(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)
    config.KIMI_API_KEY = "before"
    (tmp_path / "ai_config.json").write_text("{ invalid json", encoding="utf-8")

    config.load_ai_config()

    assert config.KIMI_API_KEY == "before"


def test_get_ai_config_returns_active_provider(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)
    config.AI_PROVIDER = "kimi"
    config.KIMI_API_KEY = "kimi-key"
    config.KIMI_MODEL = "kimi-model"

    assert config.get_ai_config() == (
        "https://api.moonshot.cn/v1/chat/completions",
        "kimi-key",
        "kimi-model",
    )


def test_saved_config_does_not_contain_unknown_fields(monkeypatch, tmp_path):
    config = _config_with_file(monkeypatch, tmp_path)

    config.save_ai_config()
    saved = json.loads((tmp_path / "ai_config.json").read_text(encoding="utf-8"))

    assert set(saved) == {
        "kimi_api_key",
        "kimi_model",
        "bailian_api_key",
        "bailian_model",
        "ai_provider",
    }
