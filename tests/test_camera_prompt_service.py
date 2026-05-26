from core.services.camera_prompt_service import (
    CameraPromptSpec,
    append_negative_as_positive,
    build_detail_tech_zh,
    build_camera_prompt,
    build_negative_zh,
    build_prompt_zh,
    build_style_mood_zh,
    build_subject_scene_zh,
    resolve_preset_values,
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


def test_build_subject_scene_zh():
    assert build_subject_scene_zh("girl", "beach") == "【主体描述】girl\n【场景环境】beach"


def test_build_style_mood_zh():
    result = build_style_mood_zh(
        styles=["cinematic"],
        aesthetics=["minimalism"],
        moods=["warm"],
        motion="running",
        style_map={"cinematic": "电影感"},
        aesthetic_map={"minimalism": "极简主义"},
        mood_map={"warm": "温暖"},
        fallback=lambda value: f"ZH:{value}",
    )

    assert result == "【风格】电影感\n【美学流派】极简主义\n【情绪氛围】温暖\n【动作动态】ZH:running"


def test_build_detail_tech_zh():
    result = build_detail_tech_zh(
        qualities=["high detail"],
        textures=["silk"],
        colors=["red and gold"],
        render="Octane",
        ratio="16:9",
        quality_map={"high detail": "高细节"},
        texture_map={"silk": "丝绸"},
        color_map={"red and gold": "红金"},
    )

    assert result == "【质量词块】高细节\n【细节质感】丝绸\n【色彩补充】红金\n【渲染引擎】Octane\n【输出比例】16:9"


def test_build_prompt_zh_combines_sections():
    result = build_prompt_zh(
        mode="实拍",
        subject_scene="【主体描述】cat",
        params=["【镜头】85mm"],
        camera=["【景别】特写"],
        filters=["电影感"],
        style_mood="【风格】写实",
        detail_tech="【质量词块】高细节",
        extra="soft light",
    )

    assert result == (
        "═══ 中文参数对照（实拍模式）═══\n"
        "【主体描述】cat\n"
        "【镜头】85mm\n"
        "【景别】特写\n"
        "【滤镜效果】电影感\n"
        "【风格】写实\n"
        "【质量词块】高细节\n"
        "【附加词】soft light"
    )


def test_resolve_preset_values_exact_fuzzy_custom_and_extra():
    resolved = resolve_preset_values(
        preset={"Lens": "85mm", "Camera": "full frame camera", "Other": "custom", "_extra": "film grain"},
        param_options={
            "Lens": ["35mm", "85mm"],
            "Camera": ["full frame"],
            "Other": ["known"],
        },
    )

    assert resolved.extra == "film grain"
    assert resolved.param_values == {"Lens": "85mm", "Camera": "full frame"}
    assert resolved.custom_values == {"Other": "custom"}
