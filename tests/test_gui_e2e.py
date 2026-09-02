import json
from types import SimpleNamespace

import pytest
from shared import qt_compat as tk


@pytest.fixture
def gui_app(tmp_path, monkeypatch):
    from features.prompt_list import widget as prompt_widget

    data_file = tmp_path / "prompts.json"
    monkeypatch.setattr(prompt_widget, "DATA_FILE", str(data_file))
    copied = []
    monkeypatch.setattr(prompt_widget.pyperclip, "copy", copied.append)

    class FakeHotkeys:
        def __init__(self):
            self.next_id = 1
            self.registered = []
            self.unregistered = []

        def register(self, sequence, callback):
            hotkey_id = self.next_id
            self.next_id += 1
            self.registered.append((hotkey_id, sequence, callback))
            return hotkey_id

        def unregister(self, hotkey_id):
            self.unregistered.append(hotkey_id)

    monkeypatch.setattr(prompt_widget, "global_hotkeys", FakeHotkeys())
    try:
        app = prompt_widget.PromptTool()
    except RuntimeError as exc:
        pytest.skip(f"Qt GUI is not available: {exc}")
    app.withdraw()
    app.update_idletasks()
    yield app, data_file, copied
    try:
        for child in list(app.winfo_children()):
            if child.winfo_exists():
                child.destroy()
        app.destroy()
    except RuntimeError:
        pass


def test_prompt_tool_and_camera_builder_key_workflows_e2e(gui_app, monkeypatch):
    app, data_file, copied = gui_app

    app._new_prompt()
    app.title_var.set("E2E Prompt")
    app.shortcut_var.set("Ctrl+Alt+1")
    app.text_area.insert("1.0", "cinematic cat, soft light")
    app._save_edit()
    app.update_idletasks()

    assert app.selected_index == 0
    assert app.prompts[0].title == "E2E Prompt"
    assert app.prompts[0].shortcut == "Ctrl+Alt+1"
    assert app.btn_frame.winfo_children()
    saved_prompt = json.loads(data_file.read_text(encoding="utf-8"))[0]
    assert saved_prompt["content"] == "cinematic cat, soft light"
    assert saved_prompt["shortcut"] == "Ctrl+Alt+1"

    app._select(0)
    app._copy_current()
    assert copied[-1] == "cinematic cat, soft light"

    app._copy_prompt_by_shortcut(0)
    assert copied[-1] == "cinematic cat, soft light"

    app._select_all_prompts()
    app._copy_checked_prompts()
    assert "cinematic cat" in copied[-1]

    from features.camera_builder.widget import CameraBuilder
    from features.camera_builder.light_panel import sphere_click
    from features.camera_builder.negative_panel import fill_negative_preset
    from features.camera_builder.extractor_actions import (
        apply_extractor_style,
        select_extractor_preset,
    )

    inserted = []
    monkeypatch.setattr("shared.qt_compat.simpledialog.askstring", lambda *args, **kwargs: "Builder E2E")
    builder = CameraBuilder(app, on_insert=lambda title, content: inserted.append((title, content)))
    builder.withdraw()
    builder.update_idletasks()

    builder.subject_text.delete("1.0", tk.END)
    builder.subject_text.insert("1.0", "red fox")
    builder.environ_text.delete("1.0", tk.END)
    builder.environ_text.insert("1.0", "misty forest")
    builder.light_dir_enabled.set(True)
    sphere_click(builder, SimpleNamespace(x=120, y=70))
    fill_negative_preset(builder, "通用")
    select_extractor_preset(builder, 0)
    apply_extractor_style(builder)
    builder._generate()

    prompt = builder._state_collector.build_prompt()
    assert "red fox" in prompt
    assert "misty forest" in prompt
    assert "lighting" in prompt
    assert builder.neg_text.get("1.0", tk.END).strip()

    builder._insert()
    assert inserted and inserted[0][0] == "Builder E2E"
    assert "red fox" in inserted[0][1]
    assert not builder.winfo_exists()


def test_prompt_tool_rejects_duplicate_prompt_shortcut(gui_app, monkeypatch):
    from features.prompt_list import widget as prompt_widget

    app, data_file, _copied = gui_app
    messages = []
    monkeypatch.setattr(prompt_widget.messagebox, "showinfo", lambda *args, **kwargs: messages.append(args))

    first = app.prompt_service.add_prompt("First", "one", "Ctrl+Alt+1")
    second = app.prompt_service.add_prompt("Second", "two")
    app._sync_prompts()

    app._select(second, flash_copy=False)
    app._set_edit_mode(True)
    app.shortcut_var.set("Ctrl+Alt+1")
    app._save_edit()

    assert app.prompts[first].shortcut == "Ctrl+Alt+1"
    assert app.prompts[second].shortcut == ""
    assert "已被使用" in messages[-1][1]
    saved = json.loads(data_file.read_text(encoding="utf-8"))
    assert saved[second].get("shortcut", "") == ""


def test_ai_optimize_action_bar_buttons_fit_compact_groups(gui_app):
    from features.ai_optimize.widget import AIOptimizeDialog
    from features.ai_optimize.panels import ActionBar

    app, _data_file, _copied = gui_app
    dialog = AIOptimizeDialog(app, current_prompt="cinematic cat")
    dialog.withdraw()
    dialog.update_idletasks()

    buttons_by_group = {}
    for group_title, container in dialog._action_bar.button_groups.items():
        buttons_by_group[group_title] = [
            child for child in container.winfo_children()
            if getattr(child, "_is_ai_action_button", False)
        ]

    assert len(buttons_by_group["主要流程"]) == 4
    assert len(buttons_by_group["高级工具"]) == 7
    assert len(buttons_by_group["结果操作"]) == 3
    for buttons in buttons_by_group.values():
        assert all(button.maximumHeight() <= 24 for button in buttons)
        assert all(button.minimumWidth() == 0 for button in buttons)
    dialog.destroy()


def test_main_toolbar_has_compact_primary_workflow_buttons(gui_app):
    app, _data_file, _copied = gui_app

    primary_buttons = [
        child for child in app.findChildren(tk.Button)
        if getattr(child, "_is_primary_action", False)
    ]
    dropdown_buttons = [
        child for child in app.findChildren(tk.Button)
        if getattr(child, "_is_primary_dropdown", False)
    ]
    labels = {button.text(): button for button in primary_buttons}

    assert {"提示词生成器", "截图", "AI 优化"} <= set(labels)
    assert [button.text() for button in dropdown_buttons] == ["▼"]
    assert labels["提示词生成器"].maximumWidth() <= 104
    assert labels["截图"].maximumWidth() <= 86
    assert labels["AI 优化"].maximumWidth() <= 100
    assert dropdown_buttons[0].maximumWidth() <= 30
    assert all(button.maximumHeight() <= 32 for button in labels.values())
    assert dropdown_buttons[0].maximumHeight() <= 32
    assert labels["AI 优化"].isEnabled()


def test_compact_overlay_header_keeps_restore_button_visible(gui_app):
    app, _data_file, _copied = gui_app
    app.prompt_service.add_prompt("Long Prompt Title For Compact Mode", "content")
    app._sync_prompts()

    app._open_compact_overlay()
    app.update_idletasks()

    restore_buttons = [
        child for child in app._compact_win.findChildren(tk.Button)
        if child.text() == "恢复"
    ]
    assert len(restore_buttons) == 1
    assert restore_buttons[0].maximumWidth() <= 52
    assert restore_buttons[0].maximumHeight() == 24
    assert getattr(restore_buttons[0], "_is_compact_restore", False)
    assert app._compact_list_inner.winfo_children()

    app._compact_win.destroy()
