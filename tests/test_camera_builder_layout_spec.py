from app.camera_builder_layout import CameraBuilderLayoutSpec


def test_camera_builder_layout_uses_four_steps():
    spec = CameraBuilderLayoutSpec.default()

    assert [step.key for step in spec.steps] == ["scene", "style", "camera", "output"]


def test_camera_builder_layout_maps_existing_tabs_to_steps():
    spec = CameraBuilderLayoutSpec.default()

    assert spec.step("scene").tabs == ["subject"]
    assert spec.step("style").tabs == ["preset", "style", "filter", "extractor"]
    assert spec.step("camera").tabs == ["params", "camera"]
    assert spec.step("output").tabs == ["detail"]
