from core.services.camera_extractor_service import (
    append_keywords_to_extra,
    build_extractor_detail,
    count_keyword_matches,
    matched_keywords_by_group,
)
from core.services.camera_negative_service import apply_negative_preset


def test_build_extractor_detail_formats_summary_and_keywords():
    preset = {
        "name": "Sketch Mood",
        "zh_summary": "线稿氛围",
        "linework": "thin lines",
        "zh_details": {"linework": "细线条", "lighting": "柔光"},
        "keywords": ["thin line art", "soft lighting"],
    }

    result = build_extractor_detail(preset)

    assert "【Sketch Mood】" in result
    assert "✦ 线稿氛围" in result
    assert "线条风格：细线条" in result
    assert "打光方式：柔光" in result
    assert "注入关键词（2 个）：thin line art, soft lighting" in result


def test_count_keyword_matches_uses_bidirectional_contains_matching():
    assert count_keyword_matches(
        ["cinematic film lighting", "warm"],
        ["cinematic", "minimalism"],
        ["warm atmosphere"],
    ) == 2


def test_matched_keywords_by_group_returns_grouped_hits():
    result = matched_keywords_by_group(
        ["cinematic film lighting", "dreamy pastel"],
        {"style": ["cinematic"], "mood": ["pastel dream"]},
    )

    assert result == {"style": {"cinematic"}, "mood": set()}


def test_append_keywords_to_extra():
    assert append_keywords_to_extra("base", ["a", "b"]) == "base, a, b"
    assert append_keywords_to_extra("", ["a"]) == "a"
    assert append_keywords_to_extra("base", []) == "base"


def test_apply_negative_preset_appends_with_separator():
    presets = {"通用": "blurry, watermark"}

    assert apply_negative_preset("", "通用", presets) == "blurry, watermark"
    assert apply_negative_preset("bad hands", "通用", presets) == "bad hands, blurry, watermark"
    assert apply_negative_preset("bad hands", "missing", presets) == "bad hands"
