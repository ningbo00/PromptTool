from types import SimpleNamespace


def test_screenshot_analysis_character_mode_builds_focused_messages():
    from features.screenshot_prompt.widget import build_reverse_prompt_messages

    messages = build_reverse_prompt_messages(b"png-bytes", mode="character", detail="concise")

    assert messages[0]["role"] == "system"
    assert "角色反推" in messages[0]["content"]
    assert "character silhouette" in messages[0]["content"]
    assert "30-55" in messages[0]["content"]
    assert "中文预览" in messages[0]["content"]
    assert "Focus on the character design only" in messages[1]["content"][0]["text"]
    assert messages[1]["content"][1]["image_url"]["url"].startswith("data:image/png;base64,")


def test_screenshot_analysis_custom_mode_uses_saved_instruction():
    from features.screenshot_prompt.widget import build_reverse_prompt_messages

    messages = build_reverse_prompt_messages(
        b"png-bytes",
        mode="custom",
        custom="Only describe weapon shapes and material finish.",
    )

    assert "自定义" in messages[0]["content"]
    assert "Only describe weapon shapes" in messages[0]["content"]
    assert messages[1]["content"][0]["text"] == "Only describe weapon shapes and material finish."


def test_reverse_prompt_result_adds_chinese_preview_slot_when_missing():
    from features.screenshot_prompt.widget import format_reverse_prompt_result

    content = format_reverse_prompt_result("cinematic robot, blue light")

    assert content.startswith("English Prompt: cinematic robot")
    assert "中文预览" in content


def test_screenshot_analysis_title_follows_mode(monkeypatch):
    import features.screenshot_prompt.widget as screenshot_widget

    class FakeDateTime:
        @classmethod
        def now(cls):
            return SimpleNamespace(strftime=lambda _fmt: "12:34")

    monkeypatch.setattr(screenshot_widget, "datetime", FakeDateTime)

    assert screenshot_widget.screenshot_prompt_title("cinematography") == "截图镜头语言 12:34"
    assert screenshot_widget.screenshot_prompt_title("negative") == "截图负面词 12:34"


def test_screenshot_settings_dialog_saves_selected_plan(monkeypatch, tmp_path):
    from shared.qt_compat import _app
    import shared.config as cfg
    from features.screenshot_settings.widget import ScreenshotSettingsDialog

    _app()
    monkeypatch.setattr(cfg, "AI_CONFIG_FILE", str(tmp_path / "ai_config.json"))
    cfg.SCREENSHOT_ANALYSIS_MODE = "full_reverse"
    cfg.SCREENSHOT_ANALYSIS_CUSTOM = ""
    cfg.SCREENSHOT_PROMPT_DETAIL = "full"
    saved = []
    dialog = ScreenshotSettingsDialog(None, on_save=lambda: saved.append(True))
    dialog.withdraw()
    dialog._mode_var.set("场景反推")
    dialog._detail_var.set("精简提示词")
    dialog._custom_text.delete("1.0")
    dialog._custom_text.insert("1.0", "Keep scene prompt concise.")

    dialog._save()

    assert cfg.SCREENSHOT_ANALYSIS_MODE == "scene"
    assert cfg.SCREENSHOT_ANALYSIS_CUSTOM == "Keep scene prompt concise."
    assert cfg.SCREENSHOT_PROMPT_DETAIL == "concise"
    assert saved == [True]
