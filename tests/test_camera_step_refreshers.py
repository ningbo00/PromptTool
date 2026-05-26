from tests.test_camera_builder_step_modules import _camera_builder_methods


def test_camera_builder_widget_no_longer_owns_step_refreshers():
    methods = _camera_builder_methods()

    for name in [
        "_refresh_subject_chips",
        "_refresh_style_blocks",
        "_refresh_detail_blocks",
        "_refresh_style_toggle_colors",
    ]:
        assert name not in methods


def test_step_modules_expose_refreshers():
    from features.camera_builder import output_step, scene_step, style_step

    assert hasattr(scene_step, "refresh_subject_chips")
    assert hasattr(style_step, "refresh_style_blocks")
    assert hasattr(style_step, "refresh_style_toggle_colors")
    assert hasattr(output_step, "refresh_detail_blocks")
