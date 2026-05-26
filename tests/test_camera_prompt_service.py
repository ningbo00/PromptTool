from core.services.camera_prompt_service import CameraPromptSpec, build_camera_prompt


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
