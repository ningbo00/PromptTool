import ast
from pathlib import Path

WIDGET_PATH = Path("features/camera_builder/widget.py")


def _camera_builder_methods():
    tree = ast.parse(WIDGET_PATH.read_text(encoding="utf-8"))
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CameraBuilder")
    return {node.name for node in cls.body if isinstance(node, ast.FunctionDef)}


def test_camera_builder_widget_no_longer_owns_step_body_builders():
    methods = _camera_builder_methods()

    assert "_build_tab_subject" not in methods
    assert "_build_tab_preset" not in methods
    assert "_build_tab_style" not in methods
    assert "_build_tab_filter" not in methods
    assert "_build_tab_params" not in methods
    assert "_build_tab_camera" not in methods
    assert "_build_tab_detail" not in methods
    assert "_build_tab_extractor" not in methods


def test_step_modules_expose_tab_body_builders():
    from features.camera_builder import camera_step, output_step, scene_step, style_step

    assert hasattr(scene_step, "build_subject_tab")
    assert hasattr(style_step, "build_preset_tab")
    assert hasattr(style_step, "build_style_tab")
    assert hasattr(style_step, "build_filter_tab")
    assert hasattr(style_step, "build_extractor_tab")
    assert hasattr(camera_step, "build_params_tab")
    assert hasattr(camera_step, "build_camera_tab")
    assert hasattr(output_step, "build_detail_tab")


def test_step_modules_do_not_reference_widget_self_directly():
    for path in [
        Path("features/camera_builder/scene_step.py"),
        Path("features/camera_builder/style_step.py"),
        Path("features/camera_builder/camera_step.py"),
        Path("features/camera_builder/output_step.py"),
    ]:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        leaked = [node.lineno for node in ast.walk(tree) if isinstance(node, ast.Name) and node.id == "self"]
        assert leaked == [], f"{path} leaked widget self references at {leaked}"
