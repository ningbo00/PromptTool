# REPO_MAP

Root: `G:\PromptTool_Qt`

## Top-Level Files

- `main.py` - application entry point; creates `PromptTool` and starts Qt event loop.
- `PromptTool.spec` - PyInstaller config for `dist\PromptTool.exe`.
- `requirements.txt` - runtime/test/build dependencies.
- `prompts.json` - local Prompt data used by the app; user data, do not casually overwrite.
- `ai_config.json` - local AI provider/API config; user data, do not expose or overwrite.
- `README.md` - short project overview and commands.
- `AGENT_CONTEXT.md` - low-context working notes for future agents.
- `REPO_MAP.md` - this repository map.

## `app/`

Layout specification objects used by tests and UI code.

- `app/layout.py` - main window layout specs (`MainLayoutSpec`, sections/actions).
- `app/ai_optimize_layout.py` - AI optimize dialog layout/action group spec.
- `app/camera_builder_layout.py` - CameraBuilder four-step layout spec.

## `core/`

Domain and service logic. Keep business rules here where possible.

- `core/domain/prompt_library.py`
  - `Prompt` value object with `title`, `content`, optional `shortcut`.
  - `PromptLibrary` CRUD/search/move.
  - `PromptSelection` checked Prompt selection and joined copy text.

- `core/ports/prompt_store.py`
  - `PromptStore` protocol for persistence.

- `core/services/prompt_service.py`
  - Facade used by main UI for library CRUD, selection, persistence, action state.

- `core/services/ai_optimize_actions.py`
  - Builds AI chat messages for optimize, translate, variants, score, keywords, negative prompt, compliance, expand, etc.

- `core/services/ai_optimize_service.py`
  - Validates/normalizes AI optimize actions and parses AI result formats.

- `core/services/camera_prompt_service.py`
  - Builds final camera/scene/style/output Prompt strings and Chinese summaries.

- `core/services/camera_light_service.py`
  - Light sphere math, direction/color keyword logic.

- `core/services/camera_extractor_service.py`
  - Style extractor keyword matching and append helpers.

- `core/services/camera_negative_service.py`
  - Negative prompt preset application.

## `infrastructure/`

Persistence adapters.

- `infrastructure/json_prompt_store.py`
  - Loads/saves `Prompt` data as JSON.
  - Backwards-compatible with old records without `shortcut`.

## `shared/`

Cross-feature infrastructure, UI kit, config, compatibility layer.

- `shared/qt_compat.py`
  - Tk-like API backed by PySide6.
  - Defines `Tk`, `Toplevel`, `Frame`, `Button`, `Text`, `Entry`, `Combobox`, `ScrollArea`, `messagebox`, `simpledialog`, etc.
  - Critical for most UI bugs because feature code uses `tk.*` names from here.
  - Important lifecycle rule: child widget `destroy()` must not `setParent(None)` or it can become a visible top-level `python` window.

- `shared/ui_kit.py`
  - Global dark theme and design tokens.
  - Helpers: `apply_app_theme`, `make_panel`, `make_scroll_canvas`, `Tooltip`, brick/chip grid utilities.

- `shared/config.py`
  - AI provider specs, model lists, screenshot/text config, screenshot analysis mode/detail config, load/save for `ai_config.json`.

- `shared/global_hotkeys.py`
  - Windows `RegisterHotKey` manager for global screenshot shortcut and Prompt copy shortcuts.

- `shared/storage.py`
  - Legacy prompt storage helpers.

- `shared/constants.py`
  - Prompt keyword constants and keyword-to-Chinese helper.

## `features/prompt_list/`

Main application window.

- `features/prompt_list/widget.py`
  - `PromptTool` main UI.
  - Toolbar: primary buttons `提示词生成器`, `截图`, `▾`, `AI 优化`; utility buttons settings/help/compact/topmost.
  - Left Prompt list with search, CRUD, checked Prompt batch copy.
  - Right editor with title/content/shortcut.
  - Binds global screenshot shortcut and per-Prompt global copy shortcuts.
  - Screenshot action hides the main window before selection so other desktop windows can be captured, then restores it after selection/cancel.

## `features/screenshot_prompt/`

Screenshot reverse-prompt feature.

- `features/screenshot_prompt/widget.py`
  - Fullscreen screenshot selector.
  - `Esc` and right click cancel.
  - Converts selected pixmap to PNG bytes.
  - Defines screenshot analysis modes: full, character, scene, cinematography, lighting/color, costume/props, composition, negative, custom.
  - Supports prompt detail presets: full or concise, and asks model for English Prompt plus Chinese preview.
  - Builds vision-model chat messages and calls AI.
  - Resolves screenshot-specific provider/model config.

## `features/screenshot_settings/`

Screenshot analysis planning dialog.

- `features/screenshot_settings/widget.py`
  - Lets the user preselect screenshot reverse-prompt purpose before taking a screenshot.
  - Saves selected mode, full/concise detail, and custom instruction through `shared.config.save_ai_config()`.

## `features/ai_settings/`

AI config dialog.

- `features/ai_settings/widget.py`
  - Text AI provider/model/API key fields.
  - Separate screenshot provider/model/API key fields.
  - Screenshot shortcut setting.
  - Saves via `shared.config.save_ai_config()`.

## `features/ai_optimize/`

AI optimize dialog and client.

- `features/ai_optimize/widget.py`
  - Large AI optimization dialog.
  - Actions: optimize, translate, variants, score, keywords, negative prompt, compliance, expand, guided create, desc-to-prompt, etc.
  - Uses service/actions for prompt construction where already migrated.

- `features/ai_optimize/panels.py`
  - Reusable panel helpers: instruction/action/result/insight UI pieces.

- `features/ai_optimize/client.py`
  - HTTP call helper.
  - Delivers success/error callbacks back to Qt main thread.

## `features/camera_builder/`

Prompt generator / CameraBuilder dialog.

- `features/camera_builder/widget.py`
  - `CameraBuilder` shell window, topbar, notebook, preview, generate/insert.

- `features/camera_builder/scene_step.py`
  - Subject/environment step and chips.

- `features/camera_builder/style_step.py`
  - Preset/style/mood/filter/anime extractor UI.
  - Watch out for Tk-style lambda captures and BooleanVar usage.

- `features/camera_builder/camera_step.py`
  - Camera shot/lens/angle/light controls.

- `features/camera_builder/output_step.py`
  - Detail/quality/render/ratio/output controls.

- `features/camera_builder/preview_panel.py`
  - Output deck / preview text areas; uses grid so text fills width.

- `features/camera_builder/light_panel.py`
  - Light sphere drawing and interactions.

- `features/camera_builder/extractor_actions.py`
  - Style extractor actions.

- `features/camera_builder/negative_panel.py`
  - Negative preset fill behavior.

- `features/camera_builder/state_collector.py`
  - Collects UI state and delegates Prompt assembly to core services.

- `features/camera_builder/presets.py`
  - Large preset constants.

## `features/help/`

- `features/help/widget.py` - help/user guide dialog.

## `docs/`

Project documentation and planning notes.

- `docs/USER_GUIDE.md` - user-facing guide; some old wording may still say Tkinter.
- `docs/RELEASE_CHECKLIST.md` - release smoke/test/build checklist.
- `docs/WORK_PLAN_TDD_DDD.md` - refactor plan.
- `docs/NEXT_2H_WORKLIST*.md` - previous incremental worklists.
- `docs/REPO_MAP.md` - older generated map; root `REPO_MAP.md` is the current low-context map.

## `tests/`

Pytest suite. Use `QT_QPA_PLATFORM=offscreen` for GUI tests.

- Prompt/domain/storage:
  - `tests/test_prompt_library.py`
  - `tests/test_prompt_service.py`
  - `tests/test_json_prompt_store.py`
  - `tests/test_storage.py`

- Main UI and lifecycle:
  - `tests/test_gui_e2e.py`
  - `tests/test_qt_compat_lifecycle.py`
  - `tests/test_main_layout_spec.py`
  - `tests/test_main_workflow_entry.py`
  - `tests/test_ui_theme.py`

- Screenshot/global shortcuts:
  - `tests/test_screenshot_selector.py`
  - `tests/test_global_hotkeys.py`

- AI:
  - `tests/test_ai_client.py`
  - `tests/test_ai_optimize_actions.py`
  - `tests/test_ai_optimize_service.py`
  - `tests/test_ai_optimize_layout_spec.py`
  - `tests/test_ai_settings.py`
  - `tests/test_config.py`

- CameraBuilder:
  - `tests/test_camera_prompt_service.py`
  - `tests/test_camera_light_service.py`
  - `tests/test_camera_aux_services.py`
  - `tests/test_camera_builder_layout_spec.py`
  - `tests/test_camera_builder_step_modules.py`
  - `tests/test_camera_builder_aux_modules.py`
  - `tests/test_camera_builder_state_collector.py`
  - `tests/test_camera_step_refreshers.py`
  - `tests/test_camera_preview_panel.py`

- Docs/release:
  - `tests/test_release_docs.py`

## Common Commands

```powershell
# Run tests
$env:QT_QPA_PLATFORM='offscreen'
python -B -m pytest -q

# Build exe
python -m PyInstaller --clean --noconfirm PromptTool.spec

# Run source app
python main.py
```

## Debugging Hints

- White `python` mini-windows usually mean a child `QWidget` became parentless/top-level. Check `shared/qt_compat.py` lifecycle and parent arguments.
- Broken scroll/layout in migrated Tk code usually means `pack`/`grid` parent or `ScrollArea` ownership is wrong.
- If AI result callbacks do not update UI, inspect `features/ai_optimize/client.py` dispatcher.
- If screenshot reverse prompt returns nothing, inspect screenshot model config in `shared/config.py` and `features/screenshot_prompt/widget.py`.
- If a shortcut works only when focused, inspect whether it uses `shared/global_hotkeys.py` or old Qt `QShortcut`.
