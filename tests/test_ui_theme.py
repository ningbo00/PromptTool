from pathlib import Path

from shared import ui_kit


def test_ui_theme_uses_refined_compact_dark_tokens():
    assert ui_kit.THEME_NAME == "noteai_dark_compact"
    assert ui_kit.BG_BASE == "#0b0f14"
    assert ui_kit.BG_SURFACE == "#111821"
    assert ui_kit.BORDER_SUBTLE == "#243241"
    assert ui_kit.FONT_FAMILY == "Microsoft YaHei UI"
    assert ui_kit.RADIUS_PROXY_PAD == 10


def test_prompt_tool_source_uses_compact_refined_surface_copy():
    source = open("features/prompt_list/widget.py", encoding="utf-8").read()

    assert "AI Command Center" in source
    assert "Prompt Studio" in source
    assert "BG_ELEVATED" in source
    assert "核心入口" in source


def test_prompt_tool_source_uses_reference_layout_language():
    source = Path("features/prompt_list/widget.py").read_text(encoding="utf-8")

    assert "Outliner" in source
    assert "Canvas" in source
    assert "Inspector" in source
    assert "ghost_node_canvas" in source
    assert "_ghost_node" in source
