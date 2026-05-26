from app.ai_optimize_layout import AIOptimizeLayoutSpec


def test_ai_optimize_layout_defines_primary_flows():
    spec = AIOptimizeLayoutSpec.default()

    assert spec.action_group("primary") == [
        "optimize_current",
        "zh_to_en",
        "generate_variants",
    ]


def test_ai_optimize_layout_defines_advanced_tools():
    spec = AIOptimizeLayoutSpec.default()

    assert spec.action_group("advanced") == [
        "score",
        "extract_keywords",
        "recommend_negative",
        "compliance_check",
    ]


def test_ai_optimize_layout_defines_result_actions():
    spec = AIOptimizeLayoutSpec.default()

    assert spec.action_group("result") == [
        "apply_to_current",
        "save_as_new",
        "copy_result",
    ]


def test_ai_optimize_layout_has_clear_panel_order():
    spec = AIOptimizeLayoutSpec.default()

    assert spec.panels == ["source", "instruction", "result", "insights"]
