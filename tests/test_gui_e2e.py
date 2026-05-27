import json
import tkinter as tk
from types import SimpleNamespace

import pytest


@pytest.fixture
def gui_app(tmp_path, monkeypatch):
    from features.prompt_list import widget as prompt_widget

    data_file = tmp_path / "prompts.json"
    monkeypatch.setattr(prompt_widget, "DATA_FILE", str(data_file))
    copied = []
    monkeypatch.setattr(prompt_widget.pyperclip, "copy", copied.append)
    try:
        app = prompt_widget.PromptTool()
    except tk.TclError as exc:
        pytest.skip(f"Tk GUI is not available: {exc}")
    app.withdraw()
    app.update_idletasks()
    yield app, data_file, copied
    try:
        for child in list(app.winfo_children()):
            if child.winfo_exists():
                child.destroy()
        app.destroy()
    except tk.TclError:
        pass


def test_prompt_tool_and_camera_builder_key_workflows_e2e(gui_app, monkeypatch):
    app, data_file, copied = gui_app

    app._new_prompt()
    app.title_var.set("E2E Prompt")
    app.text_area.insert("1.0", "cinematic cat, soft light")
    app._save_edit()
    app.update_idletasks()

    assert app.selected_index == 0
    assert app.prompts[0].title == "E2E Prompt"
    assert json.loads(data_file.read_text(encoding="utf-8"))[0]["content"] == "cinematic cat, soft light"

    app._select(0)
    app._copy_current()
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
    monkeypatch.setattr("tkinter.simpledialog.askstring", lambda *args, **kwargs: "Builder E2E")
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
