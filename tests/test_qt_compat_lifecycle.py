from PySide6.QtWidgets import QApplication

from shared import qt_compat as tk


def _orphan_tk_widgets():
    app = QApplication.instance()
    app.processEvents()
    return [
        widget
        for widget in QApplication.topLevelWidgets()
        if widget.__class__.__module__ == "shared.qt_compat"
        and widget.__class__.__name__ in {"Frame", "Label", "Button", "Entry", "Text", "Checkbutton"}
        and widget.parentWidget() is None
    ]


def test_destroying_child_widget_does_not_promote_it_to_top_level():
    app = tk._app()
    root = tk.Tk()
    child = tk.Frame(root, bg="#222222")
    child.pack(fill=tk.X)
    app.processEvents()

    child.destroy()
    app.processEvents()

    assert child.parentWidget() is root
    assert not child.isWindow()
    assert child not in QApplication.topLevelWidgets()
    root.destroy()


def test_prompt_list_refresh_does_not_create_orphan_frame_windows(tmp_path, monkeypatch):
    from features.prompt_list import widget as prompt_widget

    data_file = tmp_path / "prompts.json"
    monkeypatch.setattr(prompt_widget, "DATA_FILE", str(data_file))

    class FakeHotkeys:
        def register(self, *_args, **_kwargs):
            return 1

        def unregister(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(prompt_widget, "global_hotkeys", FakeHotkeys())
    app = tk._app()
    root = prompt_widget.PromptTool()
    root.show()
    app.processEvents()

    for i in range(6):
        root.prompt_service.add_prompt(f"Prompt {i}", f"content {i}")
    root._sync_prompts()
    root._refresh_buttons()
    root._select(0, flash_copy=False)
    root._refresh_buttons()
    root._select(1, flash_copy=False)
    root._refresh_buttons()
    app.processEvents()

    assert _orphan_tk_widgets() == []
    root.destroy()
