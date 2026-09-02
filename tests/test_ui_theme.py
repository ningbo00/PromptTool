from pathlib import Path

from shared import ui_kit


def test_ui_theme_uses_refined_compact_dark_tokens():
    assert ui_kit.THEME_NAME == "midnight_graph_ui"
    assert ui_kit.BG_BASE == "#181818"
    assert ui_kit.BG_SURFACE == "#242424"
    assert ui_kit.BORDER_SUBTLE == "#3a3a3a"
    assert ui_kit.ACCENT_BLUE == "#3794ff"
    assert ui_kit.FONT_FAMILY == "Microsoft YaHei UI"
    assert ui_kit.RADIUS_PROXY_PAD == 10
    assert ui_kit.BUTTON_STYLE == "outline"


def test_prompt_tool_source_uses_compact_refined_surface_copy():
    source = open("features/prompt_list/widget.py", encoding="utf-8").read()

    assert "Prompt Studio" in source
    assert "BG_ELEVATED" in source
    assert "_inspector_action_card" in source
    assert "_compact_action_bar" in source
    assert "本地提示词工作台" in source


def test_prompt_tool_source_uses_reference_layout_language():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "Outliner" in source
    assert "Canvas" in source
    assert "Inspector" in source
    assert "当前提示词" in source
    assert "常用操作" in source
    assert "提示词生成器" in source
    assert "AI 优化" in source


def test_prompt_tool_hides_internal_design_language_from_user():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    for internal_copy in (
        "Midnight Graph UI",
        "Document Surface",
        "Focus Rail",
        "Primary workflow",
        "Open Builder",
        "Open AI",
    ):
        assert internal_copy not in source
    for internal_label in ('"Generate"', '"Optimize"', '"Configure"', '"Open"'):
        assert internal_label not in source


def test_prompt_tool_topbar_avoids_emoji_button_labels():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    for emoji in ("📌", "📍", "🗂", "⚙", "❓"):
        assert emoji not in source


def test_prompt_tool_uses_full_width_inspector_action_cards():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "_inspector_action_card(" in source
    assert "anchor=\"w\"" in source
    assert "justify=tk.LEFT" in source
    assert "fill=tk.X" in source
    assert "action_text" not in source


def test_prompt_tool_empty_state_guides_primary_actions():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "选择左侧提示词" in source
    assert "新建提示词" in source
    assert "打开生成器" in source


def test_prompt_tool_removes_decorative_node_graph():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "ghost_node_canvas" not in source
    assert "_ghost_node" not in source
    assert "_draw_ghost_mindmap" not in source
    assert "create_line(" not in source


def test_dialogs_use_midnight_graph_shell_copy():
    ai_source = Path("features/ai_optimize/panels.py").read_text(encoding="utf-8")
    camera_source = Path("features/camera_builder/widget.py").read_text(encoding="utf-8")
    preview_source = Path("features/camera_builder/preview_panel.py").read_text(encoding="utf-8")

    assert "Command Strip" in ai_source
    assert "Result Matrix" in ai_source
    assert "Generation Console" in camera_source
    assert "Output Deck" in preview_source
