# Repo Map

Root: `G:\PromptTool_Qt`

## `shared/qt_compat.py` (1197 lines)
- `def _app()`
- `def _parent_widget()`
- `def _font()`
- `def _parse_geometry()`
- `class Event`
- `class Variable`
- `  def __init__()`
- `  def get()`
- `  def set()`
- `  def trace_add()`

## `features/prompt_list/widget.py` (944 lines)
- `class PromptTool`
- `  def __init__()`
- `  def _build_ui()`
- `  def _build_left_pane()`
- `  def _build_right_pane()`
- `  def _build_tools_pane()`
- `  def _bind_shortcuts()`
- `  def _bind_prompt_shortcuts()`
- `  def _compact_action_bar()`
- `  def _status_pill()`

## `features/ai_optimize/widget.py` (1317 lines)
- `class AIOptimizeDialog`
- `  def __init__()`
- `  def _build_ui()`
- `  def _make_left_pane()`
- `  def _make_right_pane()`
- `  def _get_orig()`
- `  def _set_result()`
- `  def _set_status()`
- `  def _set_busy()`
- `  def _enable_apply()`

## `features/camera_builder/style_step.py` (408 lines)
- `def create_style_step()`
- `def build_preset_tab()`
- `def make_preset_grid()`
- `def build_style_tab()`
- `def fill_toggle_grid()`
- `def refresh_style_blocks()`
- `def refresh_style_toggle_colors()`
- `def build_filter_tab()`
- `def make_filter_group()`
- `def make_toggle_btn()`

## `features/ai_optimize/panels.py` (404 lines)
- `class InstructionPanel`
- `  def __init__()`
- `  def _build_options()`
- `  def _build_custom_input()`
- `class ActionBar`
- `  def __init__()`
- `  def add_group()`
- `  def action_button()`
- `class ResultPanel`
- `  def build_header()`

## `features/camera_builder/widget.py` (378 lines)
- `class CameraBuilder`
- `  def __init__()`
- `  def _build_ui()`
- `  def _build_topbar()`
- `  def _build_main_area()`
- `  def _build_notebook()`
- `  def _on_shot_change()`
- `  def _on_elevation_change()`
- `  def _on_angle_change()`
- `  def _entry_focus_in()`

## `shared/ui_kit.py` (312 lines)
- `def apply_app_theme()`
- `def bind_mousewheel()`
- `def make_btn()`
- `def make_panel()`
- `def make_scroll_canvas()`
- `def brick_text_score()`
- `def brick_span()`
- `def prepare_brick_grid()`
- `def place_brick()`
- `def make_chip_button()`

## `shared/config.py` (245 lines)
- `class AIProviderSpec`
- `def get_ai_config()`
- `def is_vision_model_name()`
- `def is_screenshot_model_name()`
- `def get_vision_models()`
- `def get_vision_provider_keys()`
- `def get_screenshot_ai_config()`
- `def load_ai_config()`
- `def save_ai_config()`
- `def _json_key()`

## `shared/global_hotkeys.py` (244 lines)
- `class MSG`
- `class GlobalHotkeyManager`
- `  def __init__()`
- `  def supported()`
- `  def register()`
- `  def unregister()`
- `  def unregister_all()`
- `  def _ensure_message_window()`
- `  def _window_proc()`
- `class WNDCLASS`

## `features/screenshot_prompt/widget.py` (237 lines)
- `def pixmap_to_png_bytes()`
- `def build_reverse_prompt_messages()`
- `def is_probable_vision_model()`
- `def resolve_reverse_prompt_config()`
- `def call_reverse_prompt()`
- `def screenshot_prompt_title()`
- `def normalize_shortcut()`
- `class ScreenshotSelector`
- `  def __init__()`
- `  def paintEvent()`

## `core/services/ai_optimize_actions.py` (209 lines)
- `def build_ai_optimize_messages()`
- `def _optimize_current()`
- `def _zh_to_en()`
- `def _generate_variants()`
- `def _score()`
- `def _extract_keywords()`
- `def _recommend_negative()`
- `def _compliance_check()`
- `def _improve_by_score()`
- `def _expand_only()`

## `core/services/camera_prompt_service.py` (205 lines)
- `class PresetResolution`
- `class CameraPromptSpec`
- `def build_camera_prompt()`
- `def append_negative_as_positive()`
- `def build_negative_zh()`
- `def build_subject_scene_zh()`
- `def build_style_mood_zh()`
- `def build_detail_tech_zh()`
- `def build_prompt_zh()`
- `def resolve_preset_values()`

## `features/camera_builder/state_collector.py` (201 lines)
- `class CameraBuilderStateCollector`
- `  def __init__()`
- `  def build_prompt()`
- `  def build_prompt_zh()`
- `  def build_negative_zh()`
- `  def negative_text()`
- `  def build_subject_scene_zh()`
- `  def build_style_mood_zh()`
- `  def build_detail_tech_zh()`
- `  def _camera_terms()`

## `core/services/ai_optimize_service.py` (148 lines)
- `class AIOptimizeValidationError`
- `class AIOptimizeRequest`
- `class AIOptimizeService`
- `  def __init__()`
- `  def prepare_action()`
- `  def resolve_direction()`
- `  def parse_variants()`
- `  def parse_keywords()`
- `  def parse_negative_groups()`
- `  def build_diff()`

## `core/domain/prompt_library.py` (130 lines)
- `class Prompt`
- `  def __post_init__()`
- `  def display_label()`
- `  def to_dict()`
- `class PromptLibrary`
- `  def __post_init__()`
- `  def search()`
- `  def add_prompt()`
- `  def update_prompt()`
- `  def delete_prompt()`

## `core/services/prompt_service.py` (77 lines)
- `class PromptService`
- `  def __init__()`
- `  def prompts()`
- `  def checked_indices()`
- `  def search()`
- `  def add_prompt()`
- `  def update_prompt()`
- `  def delete_prompt()`
- `  def move_prompt()`
- `  def toggle_checked()`

## `features/camera_builder/light_panel.py` (145 lines)
- `def draw_light_sphere()`
- `def sphere_click()`
- `def sphere_drag()`
- `def sphere_release()`
- `def update_light_labels()`
- `def pick_light_color()`
- `def set_hemi()`
- `def toggle_rim_light()`

## `core/services/camera_light_service.py` (154 lines)
- `def sphere_xy_from_angles()`
- `def angles_from_sphere_xy()`
- `def normalize_hemi_azimuth()`
- `def blend_color()`
- `def light_keyword()`
- `def _direction_keyword()`
- `def _color_keyword()`

## `features/ai_settings/widget.py` (203 lines)
- `class AISettingsDialog`
- `  def __init__()`
- `  def _build_ui()`
- `  def _refresh_form()`
- `  def _refresh_screenshot_form()`
- `  def _save()`

## `features/camera_builder/camera_step.py` (229 lines)
- `def create_camera_step()`
- `def build_params_tab()`
- `def render_params()`
- `def build_camera_tab()`
- `def build_sliders_section()`

## 2026-05-29 Screenshot Analysis Settings

- Added eatures/screenshot_settings/widget.py as a dedicated screenshot planning dialog.
- Main toolbar has 截图设; screenshot action uses saved mode/custom text.
- Screenshot modes live in eatures/screenshot_prompt/widget.py and persist through shared/config.py.
- Tests: python -B -m pytest -q -> 151 passed.
- Build: python -m PyInstaller --clean --noconfirm PromptTool.spec; startup smoke passes for dist\PromptTool.exe.

## 2026-05-29 Screenshot Toolbar / Capture Fix

- Main screenshot action now hides PromptTool before showing ScreenshotSelector, waits briefly, then restores the main window after selection/cancel so other desktop windows can be captured.
- Top toolbar primary workflow is 提示词生成器 / 截图 / ▾ / AI 优化; utility buttons no longer contain screenshot.
- Screenshot settings add full vs concise prompt detail; screenshot prompts request English Prompt plus 中文预览.
- Tests: python -B -m pytest -q -> 153 passed.
