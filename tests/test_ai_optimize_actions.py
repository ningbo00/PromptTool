from core.services.ai_optimize_actions import (
    LENGTH_HINTS,
    build_ai_optimize_messages,
)


def _content(messages, index):
    return messages[index]["content"]


def test_build_optimize_current_messages_with_custom_direction():
    messages = build_ai_optimize_messages(
        action="optimize_current",
        original="a cat",
        direction="make it cinematic",
        length="简短",
    )

    assert "Prompt 优化专家" in _content(messages, 0)
    assert LENGTH_HINTS["简短"] in _content(messages, 0)
    assert "优化要求：make it cinematic" in _content(messages, 1)
    assert "原始 Prompt" in _content(messages, 1)


def test_build_zh_to_en_messages():
    messages = build_ai_optimize_messages(
        action="zh_to_en",
        original="夕阳下的少女",
        length="中等",
    )

    assert "中文场景" in _content(messages, 0)
    assert "只输出英文 Prompt" in _content(messages, 0)
    assert _content(messages, 1) == "夕阳下的少女"


def test_build_generate_variants_messages():
    messages = build_ai_optimize_messages(
        action="generate_variants",
        original="a cat",
        direction="more detail",
        length="详细",
    )

    assert "生成 3 个不同风格的变体版本" in _content(messages, 0)
    assert "[变体1]" in _content(messages, 0)
    assert "优化要求：more detail" in _content(messages, 1)


def test_build_score_messages():
    messages = build_ai_optimize_messages(action="score", original="a cat")

    assert "Prompt 专家评审" in _content(messages, 0)
    assert "评分: X/10" in _content(messages, 0)
    assert "请评分并给出改进建议" in _content(messages, 1)


def test_build_extract_keywords_messages():
    messages = build_ai_optimize_messages(action="extract_keywords", original="a cat")

    assert "提取关键词" in _content(messages, 0)
    assert "10-15" in _content(messages, 0)


def test_build_recommend_negative_messages():
    messages = build_ai_optimize_messages(action="recommend_negative", original="a cat")

    assert "负面词" in _content(messages, 0)
    assert "按分组" in _content(messages, 0)


def test_build_compliance_check_messages():
    messages = build_ai_optimize_messages(action="compliance_check", original="a cat")

    assert "合规" in _content(messages, 0)
    assert "敏感内容" in _content(messages, 0)


def test_build_messages_rejects_unknown_action():
    try:
        build_ai_optimize_messages(action="unknown", original="a cat")
    except ValueError as exc:
        assert "Unknown AI optimize action" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
