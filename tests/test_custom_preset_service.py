import json

import pytest

from core.services.custom_preset_service import (
    DOUBAO_CARTOON_PRESET_PROMPT,
    DOUBAO_REALISTIC_PRESET_PROMPT,
    CustomPresetService,
    MODE_CARTOON,
    MODE_REALISTIC,
    PresetValidationError,
    camera_presets_from_custom,
    validate_style_preset,
)


def _preset_data(**overrides):
    data = {
        "schema": "prompttool.preset.v1",
        "type": "style_preset",
        "preset_mode": "realistic",
        "id": "space_western_bounty_hunter",
        "label": "太空西部赏金猎人",
        "category": "科幻 / 影视感",
        "description": "旧金属盔甲和太空西部视觉语言。",
        "visual_language": ["space western aesthetic", "weathered metal armor"],
        "rendering_profile": ["live-action cinematic realism"],
        "cinematography_profile": ["wide anamorphic cinematic framing"],
        "color_materials": ["cold steel blue", "warm sand orange"],
        "mood_atmosphere": ["frontier isolation"],
        "negative_prompt": ["cartoonish", "toy-like armor"],
        "usage_notes": "适合叠加到任意主体上。",
        "do_not_include": ["fixed character action"],
    }
    data.update(overrides)
    return data


def test_doubao_prompt_contains_required_schema_and_rules():
    assert "prompttool.preset.v1" in DOUBAO_REALISTIC_PRESET_PROMPT
    assert '"preset_mode": "realistic"' in DOUBAO_REALISTIC_PRESET_PROMPT
    assert '"preset_mode": "cartoon"' in DOUBAO_CARTOON_PRESET_PROMPT
    assert "只输出 JSON" in DOUBAO_REALISTIC_PRESET_PROMPT
    assert "rendering_profile" in DOUBAO_CARTOON_PRESET_PROMPT
    assert "不要写具体镜头路径" in DOUBAO_REALISTIC_PRESET_PROMPT


def test_validate_style_preset_builds_camera_preset():
    preset = validate_style_preset(_preset_data())

    camera_preset = preset.to_camera_preset()

    assert preset.id == "space_western_bounty_hunter"
    assert preset.preset_mode == MODE_REALISTIC
    assert camera_preset["_custom_preset_id"] == "space_western_bounty_hunter"
    assert camera_preset["_preset_mode"] == MODE_REALISTIC
    assert "space western aesthetic" in camera_preset["_extra"]
    assert "live-action cinematic realism" in camera_preset["_extra"]
    assert "toy-like armor" in camera_preset["_negative"]


def test_validate_style_preset_rejects_bad_schema_or_arrays():
    with pytest.raises(PresetValidationError):
        validate_style_preset(_preset_data(schema="bad"))

    with pytest.raises(PresetValidationError):
        validate_style_preset(_preset_data(preset_mode=""))

    with pytest.raises(PresetValidationError):
        validate_style_preset(_preset_data(visual_language="not-list"))

    with pytest.raises(PresetValidationError):
        validate_style_preset(_preset_data(preset_mode=MODE_CARTOON, rendering_profile=[]))


def test_custom_preset_service_imports_from_clipboard_json_and_dedupes(tmp_path):
    service = CustomPresetService(tmp_path / "custom_presets.json")

    first = service.import_from_text(json.dumps(_preset_data(), ensure_ascii=False))
    second = service.import_from_text(
        "```json\n" + json.dumps(_preset_data(), ensure_ascii=False) + "\n```"
    )

    assert first.label == "太空西部赏金猎人"
    assert second.id == "space_western_bounty_hunter_2"
    assert second.label == "太空西部赏金猎人 2"
    assert [preset.id for preset in service.load()] == [
        "space_western_bounty_hunter",
        "space_western_bounty_hunter_2",
    ]


def test_camera_presets_from_custom_returns_label_mapping(tmp_path):
    service = CustomPresetService(tmp_path / "custom_presets.json")
    service.import_from_text(json.dumps(_preset_data(), ensure_ascii=False))
    service.import_from_text(json.dumps(_preset_data(
        preset_mode=MODE_CARTOON,
        id="stylized_game_cg",
        label="卡通游戏CG",
        rendering_profile=["stylized 3D game cinematic"],
    ), ensure_ascii=False))

    real_presets = camera_presets_from_custom(service.path, MODE_REALISTIC)
    cartoon_presets = camera_presets_from_custom(service.path, MODE_CARTOON)

    assert "太空西部赏金猎人" in real_presets
    assert "卡通游戏CG" not in real_presets
    assert "卡通游戏CG" in cartoon_presets
    assert real_presets["太空西部赏金猎人"]["_custom_preset_id"] == "space_western_bounty_hunter"
