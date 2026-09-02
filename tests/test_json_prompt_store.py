import json

from core.domain.prompt_library import Prompt
from infrastructure.json_prompt_store import JsonPromptStore


def test_json_prompt_store_loads_missing_file_as_empty_library(tmp_path):
    store = JsonPromptStore(tmp_path / "prompts.json")

    library = store.load()

    assert library.prompts == []


def test_json_prompt_store_cleans_invalid_prompt_items(tmp_path):
    path = tmp_path / "prompts.json"
    path.write_text(
        json.dumps(
            [
                {"title": "  A  ", "content": "  first  ", "shortcut": " Ctrl+Alt+1 "},
                {"title": "  ", "content": "  "},
                ["not", "a", "dict"],
                {"title": "B", "content": ""},
            ],
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    store = JsonPromptStore(path)

    library = store.load()

    assert library.prompts == [Prompt("A", "first", "Ctrl+Alt+1"), Prompt("B", "")]


def test_json_prompt_store_saves_domain_library(tmp_path):
    path = tmp_path / "prompts.json"
    store = JsonPromptStore(path)

    store.save([Prompt("镜头", "wide angle", "F8"), Prompt("光线", "soft light")])

    assert json.loads(path.read_text(encoding="utf-8")) == [
        {"title": "镜头", "content": "wide angle", "shortcut": "F8"},
        {"title": "光线", "content": "soft light"},
    ]
