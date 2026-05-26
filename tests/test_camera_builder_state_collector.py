from tests.test_camera_builder_step_modules import _camera_builder_methods


def test_camera_builder_widget_no_longer_owns_prompt_collectors():
    methods = _camera_builder_methods()

    for name in [
        "_build_prompt",
        "_build_prompt_zh",
        "_build_subject_scene_zh",
        "_build_style_mood_zh",
        "_build_detail_tech_zh",
        "_build_negative_zh",
    ]:
        assert name not in methods


def test_state_collector_type_exists():
    from features.camera_builder.state_collector import CameraBuilderStateCollector

    assert CameraBuilderStateCollector.__name__ == "CameraBuilderStateCollector"
