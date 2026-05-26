from core.services.camera_prompt_service import (
    CameraPromptSpec,
    append_negative_as_positive,
    build_camera_prompt,
    build_negative_zh,
)


def test_build_camera_prompt_keeps_order_and_skips_empty_values():
    spec = CameraPromptSpec(
        subject="  red-haired girl  ",
        environment="sunset beach",
        parameters=["85mm lens", "", "f/1.8"],
        camera_terms=["close-up shot"],
        filters=["cinematic color"],
        style_terms=["film photography"],
        detail_terms=["high detail"],
        render="Octane render",
        ratio="16:9",
        extra="soft wind",
    )

    assert build_camera_prompt(spec) == (
        "red-haired girl, sunset beach, 85mm lens, f/1.8, close-up shot, "
        "cinematic color, film photography, high detail, Octane render, "
        "aspect ratio 16:9, soft wind"
    )


def test_build_camera_prompt_ignores_unspecified_ratio_and_render():
    spec = CameraPromptSpec(
        subject="cat",
        render="（不指定）",
        ratio="（不指定）",
    )

    assert build_camera_prompt(spec) == "cat"


def test_append_negative_as_positive_terms():
    assert append_negative_as_positive("cat", "blurry, no text, (bad hands:1.4)") == (
        "cat, no blurry, no text, (bad hands:0.4)"
    )


def test_append_negative_as_positive_without_base_prompt():
    assert append_negative_as_positive("", "blurry") == "no blurry"


def test_build_negative_zh_handles_weighted_terms():
    result = build_negative_zh(
        "(bad hands:1.4), blurry, unknown",
        zh_map={"bad hands": "坏手", "blurry": "模糊"},
        fallback=lambda value: f"ZH:{value}",
    )

    assert result == "⚡强力压制：坏手\n模糊\nZH:unknown"
