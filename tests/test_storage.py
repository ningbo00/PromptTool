import json

from tests.conftest import reload_module


def _storage_with_file(monkeypatch, tmp_path):
    storage = reload_module("shared.storage")
    monkeypatch.setattr(storage, "DATA_FILE", str(tmp_path / "prompts.json"))
    return storage


def test_load_prompts_returns_empty_list_when_file_missing(monkeypatch, tmp_path):
    storage = _storage_with_file(monkeypatch, tmp_path)

    assert storage.load_prompts() == []


def test_load_prompts_returns_empty_list_for_invalid_json(monkeypatch, tmp_path):
    storage = _storage_with_file(monkeypatch, tmp_path)
    (tmp_path / "prompts.json").write_text("{ invalid json", encoding="utf-8")

    assert storage.load_prompts() == []


def test_load_prompts_cleans_invalid_items(monkeypatch, tmp_path):
    storage = _storage_with_file(monkeypatch, tmp_path)
    raw_data = [
        {"title": "  Title  ", "content": "  Content  "},
        {"title": "", "content": "Only content"},
        {"title": "Only title", "content": ""},
        {"title": "  ", "content": "  "},
        ["not", "a", "dict"],
    ]
    (tmp_path / "prompts.json").write_text(
        json.dumps(raw_data, ensure_ascii=False),
        encoding="utf-8",
    )

    assert storage.load_prompts() == [
        {"title": "Title", "content": "Content"},
        {"title": "", "content": "Only content"},
        {"title": "Only title", "content": ""},
    ]


def test_save_prompts_round_trips_json(monkeypatch, tmp_path):
    storage = _storage_with_file(monkeypatch, tmp_path)
    prompts = [
        {"title": "镜头", "content": "wide angle"},
        {"title": "光线", "content": "soft light"},
    ]

    storage.save_prompts(prompts)

    assert storage.load_prompts() == prompts
