from tests.test_camera_builder_step_modules import _camera_builder_methods


def test_camera_builder_widget_no_longer_owns_auxiliary_callbacks():
    methods = _camera_builder_methods()

    for name in [
        "_sphere_xy_from_angles",
        "_angles_from_sphere_xy",
        "_draw_light_sphere",
        "_blend_color",
        "_sphere_click",
        "_sphere_drag",
        "_sphere_release",
        "_light_keyword",
        "_pick_light_color",
        "_set_hemi",
        "_fill_neg_preset",
        "_select_extractor_preset",
        "_extractor_apply_style",
        "_extractor_clear_style",
        "_extractor_append_extra",
    ]:
        assert name not in methods
