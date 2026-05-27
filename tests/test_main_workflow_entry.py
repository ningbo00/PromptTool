from pathlib import Path

from app.layout import MainLayoutSpec


def test_main_layout_promotes_core_workflow_entries():
    spec = MainLayoutSpec.default()

    assert spec.featured_actions == ["builder", "ai_optimize"]


def test_tools_panel_keeps_builder_and_ai_as_first_class_actions():
    spec = MainLayoutSpec.default()
    tools = spec.section("tools")

    assert tools.action_groups["hero"] == ["builder", "ai_optimize"]


def test_prompt_tool_source_uses_prominent_core_entry_copy():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "AI Command Center" in source
    assert "Prompt Studio" in source
    assert "BG_ELEVATED" in source
