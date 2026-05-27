from pathlib import Path

from shared import ui_kit


def test_ui_theme_uses_refined_compact_dark_tokens():
    assert ui_kit.THEME_NAME == "midnight_graph_ui"
    assert ui_kit.BG_BASE == "#0b0f14"
    assert ui_kit.BG_SURFACE == "#111821"
    assert ui_kit.BORDER_SUBTLE == "#243241"
    assert ui_kit.FONT_FAMILY == "Microsoft YaHei UI"
    assert ui_kit.RADIUS_PROXY_PAD == 10
    assert ui_kit.BUTTON_STYLE == "outline"


def test_prompt_tool_source_uses_compact_refined_surface_copy():
    source = open("features/prompt_list/widget.py", encoding="utf-8").read()

    assert "Midnight Graph UI" in source
    assert "Prompt Studio" in source
    assert "BG_ELEVATED" in source
    assert "_workflow_entry" in source
    assert "_mini_toolbar" in source


def test_prompt_tool_source_uses_reference_layout_language():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "Outliner" in source
    assert "Canvas" in source
    assert "Inspector" in source
    assert "Document Surface" in source
    assert "Focus Rail" in source


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
