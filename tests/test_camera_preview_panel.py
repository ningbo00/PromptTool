from tests.test_camera_builder_step_modules import _camera_builder_methods


def test_camera_builder_widget_no_longer_owns_preview_panel_build():
    assert "_build_preview_panel" not in _camera_builder_methods()


def test_preview_panel_exposes_build_and_render():
    from features.camera_builder.preview_panel import PreviewPanel

    assert hasattr(PreviewPanel, "build")
    assert hasattr(PreviewPanel, "render")
