from app.layout import MainLayoutSpec


def test_main_layout_uses_three_workbench_columns():
    spec = MainLayoutSpec.default()

    assert [section.key for section in spec.sections] == [
        "library",
        "editor",
        "tools",
    ]


def test_main_layout_keeps_global_actions_in_toolbar():
    spec = MainLayoutSpec.default()

    assert spec.toolbar_actions == ["topmost", "compact", "settings", "help"]


def test_main_layout_exposes_core_editor_actions_only():
    spec = MainLayoutSpec.default()

    editor = spec.section("editor")

    assert editor.primary_actions == ["save", "copy"]


def test_main_layout_groups_library_actions():
    spec = MainLayoutSpec.default()

    library = spec.section("library")

    assert library.action_groups == {
        "main": ["new", "edit", "delete"],
        "order": ["move_up", "move_down"],
        "batch": ["copy_checked", "select_all", "clear_checked"],
    }


def test_main_layout_places_workflows_in_tools_panel():
    spec = MainLayoutSpec.default()

    tools = spec.section("tools")

    assert tools.primary_actions == ["ai_optimize", "builder"]
    assert tools.secondary_actions == ["ai_settings", "help"]


def test_main_layout_groups_tool_actions():
    spec = MainLayoutSpec.default()

    tools = spec.section("tools")

    assert tools.action_groups == {
        "hero": ["builder", "ai_optimize"],
        "workflows": ["ai_optimize", "builder"],
        "support": ["ai_settings", "help"],
    }
