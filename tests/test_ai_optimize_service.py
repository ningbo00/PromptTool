from core.services.ai_optimize_service import (
    AIOptimizeService,
    AIOptimizeValidationError,
)


def test_prepare_action_rejects_empty_original():
    service = AIOptimizeService()

    try:
        service.prepare_action("zh_to_en", original="")
    except AIOptimizeValidationError as exc:
        assert "原始 Prompt 为空" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_prepare_action_requires_custom_direction_text():
    service = AIOptimizeService(custom_direction_label="自定义指令（在下方输入）")

    try:
        service.prepare_action(
            "optimize_current",
            original="a cat",
            direction="自定义指令（在下方输入）",
            custom_direction="",
        )
    except AIOptimizeValidationError as exc:
        assert "自定义指令" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_prepare_optimize_action_resolves_custom_direction():
    service = AIOptimizeService(custom_direction_label="自定义指令（在下方输入）")

    request = service.prepare_action(
        "optimize_current",
        original="a cat",
        direction="自定义指令（在下方输入）",
        custom_direction="make cinematic",
        length="简短",
    )

    assert request.history_label == "make cinematic"
    assert request.temperature == 0.7
    assert "优化要求：make cinematic" in request.messages[1]["content"]


def test_prepare_score_action_uses_low_temperature():
    service = AIOptimizeService()

    request = service.prepare_action("score", original="a cat")

    assert request.temperature == 0.3
    assert request.history_label == "AI评分"


def test_prepare_compliance_action_uses_low_temperature():
    service = AIOptimizeService()

    request = service.prepare_action("compliance_check", original="a cat")

    assert request.temperature == 0.2
    assert request.history_label == "合规检验"


def test_parse_variants_supports_bracket_format():
    service = AIOptimizeService()

    variants = service.parse_variants("[变体1]\none\n[变体2]\ntwo\n[变体3]\nthree")

    assert variants == ["one", "two", "three"]


def test_parse_variants_supports_numbered_list():
    service = AIOptimizeService()

    variants = service.parse_variants("1. one\n2. two\n3. three")

    assert variants == ["one", "two", "three"]


def test_parse_keywords_splits_comma_text():
    service = AIOptimizeService()

    assert service.parse_keywords("cat, soft light, , cinematic") == [
        "cat",
        "soft light",
        "cinematic",
    ]


def test_parse_negative_groups():
    service = AIOptimizeService()

    groups = service.parse_negative_groups(
        "通用质量问题|blurry, low quality\n"
        "风格一致性|bad style"
    )

    assert groups == [
        ("通用质量问题", ["blurry", "low quality"]),
        ("风格一致性", ["bad style"]),
    ]


def test_prepare_improve_by_score_requires_feedback():
    service = AIOptimizeService()

    try:
        service.prepare_action("improve_by_score", original="a cat", feedback="")
    except AIOptimizeValidationError as exc:
        assert "评分建议" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_prepare_improve_by_score_uses_feedback_and_history_label():
    service = AIOptimizeService()

    request = service.prepare_action(
        "improve_by_score",
        original="a cat",
        feedback="评分: 6/10",
    )

    assert request.history_label == "按评分建议优化"
    assert "评分: 6/10" in request.messages[1]["content"]


def test_prepare_expand_only_request():
    service = AIOptimizeService()

    request = service.prepare_action("expand_only", original="a cat")

    assert request.history_label == "仅扩写"
    assert request.temperature == 0.7


def test_prepare_compliance_fix_requires_report():
    service = AIOptimizeService()

    try:
        service.prepare_action("compliance_fix", original="a cat", feedback="")
    except AIOptimizeValidationError as exc:
        assert "合规检验报告" in str(exc)
    else:
        raise AssertionError("Expected validation error")


def test_prepare_compliance_fix_uses_report():
    service = AIOptimizeService()

    request = service.prepare_action(
        "compliance_fix",
        original="a cat",
        feedback="存在风险",
    )

    assert request.history_label == "合规修复"
    assert "存在风险" in request.messages[1]["content"]
