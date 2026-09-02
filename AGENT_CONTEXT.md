# AGENT_CONTEXT

Purpose: low-context handoff notes for future agents working in `G:\PromptTool_Qt`.

## Current Project State

- App: Windows desktop Prompt tool migrated to PySide6 through a Tk-like compatibility layer.
- Entry point: `main.py` -> `features.prompt_list.widget.PromptTool`.
- Build target: `dist\PromptTool.exe` via `python -m PyInstaller --clean --noconfirm PromptTool.spec`.
- Preferred test command:

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m pytest -q
```

- Latest verified state before this file:
  - Tests: `153 passed`.
  - Build: `G:\PromptTool_Qt\dist\PromptTool.exe` (2026-05-29, rebuild after screenshot toolbar/detail changes).
  - Startup smoke: `Prompt Studio` responds on Windows.

## User Preferences

- User communicates in Chinese; reply in Chinese unless explicitly asked otherwise.
- User wants minimal back-and-forth. Make reasonable assumptions and execute.
- After code changes, normally run tests and rebuild `dist\PromptTool.exe`.
- UI target: restrained, mature, VSCode-like dark theme with very controlled blue accent.
- Do not add unrelated UI content; preserve all existing functionality.

## Important Safety Rules

- The repo has many existing dirty/untracked files from prior work and user operations. Do not revert unrelated changes.
- Do not delete or reset build/user data unless explicitly requested.
- `prompts.json` and `ai_config.json` are local working data; avoid overwriting except through app behavior or explicit task.
- Prefer `rg` / `rg --files` for search.
- Prefer `apply_patch` for small single-file edits.

## Recent High-Importance Fixes

- Screenshot analysis planning
  - Main toolbar now has primary `截图` between `提示词生成器` and `AI 优化`, with a `▾`副按钮 beside it for screenshot settings.
  - `features/screenshot_settings/widget.py` lets the user preselect screenshot reverse purpose and optional custom instruction.
  - Modes: full reverse, character, scene, cinematography, lighting/color, costume/props, composition, negative prompt, custom.
  - Detail presets: full prompt or concise direct image-generation prompt.
  - `features/screenshot_prompt/widget.py` builds the vision prompt from saved mode/detail/custom text, asks for English Prompt plus Chinese preview, and generated Prompt titles reflect the mode.
  - Config keys in `ai_config.json`: `screenshot_analysis_mode`, `screenshot_analysis_custom`, `screenshot_prompt_detail`.
  - `features/prompt_list/widget.py` hides the main window before screenshot selection, so other desktop windows can be captured normally.

- `shared/qt_compat.py`
  - Tk-like compatibility facade over PySide6.
  - Fixed white `python` ghost windows by changing widget lifecycle:
    - `destroy()` no longer calls `setParent(None)` for child widgets.
    - `pack()` no longer shows parentless non-window widgets.
    - `Toplevel` delayed `show()` now checks `_destroyed`.
  - Custom dark `messagebox` replaces native `QMessageBox`.

- `shared/ui_kit.py`
  - Global VSCode-like dark stylesheet and design tokens.
  - `make_scroll_canvas()` now parents the inner frame to the scroll area to avoid orphan top-level widgets.

- `shared/global_hotkeys.py`
  - Windows global hotkey manager based on `RegisterHotKey`.
  - Used for screenshot shortcut and per-Prompt copy shortcuts.

- `features/screenshot_prompt/widget.py`
  - Screenshot region selector.
  - `Esc` and right click cancel.
  - High-DPI crop mapping fixed.
  - Image reverse prompt uses separate screenshot model/provider config.
  - Image reverse prompt also uses the selected screenshot analysis mode/detail/custom instruction and includes a Chinese preview slot.

- `features/prompt_list/widget.py`
  - Main window.
  - Right inspector column removed; primary entries are top toolbar buttons.
  - Saved Prompts support per-Prompt shortcut copied globally to clipboard.
  - Shortcut conflicts with screenshot shortcut and other Prompt shortcuts are blocked.

- `core/domain/prompt_library.py`, `core/services/prompt_service.py`, `infrastructure/json_prompt_store.py`
  - Prompt model includes optional `shortcut`.
  - JSON storage remains backwards-compatible and omits empty shortcuts.

## Key Tests Added Recently

- `tests/test_qt_compat_lifecycle.py`
  - Prevents destroyed child widgets becoming top-level windows.
  - Prevents Prompt list refresh from creating orphan `Frame` windows.

- `tests/test_global_hotkeys.py`
  - Verifies shortcut normalization and Windows virtual key parsing.

- `tests/test_screenshot_selector.py`
  - Verifies screenshot cancel idempotence and right-click cancel.

- `tests/test_screenshot_analysis_modes.py`
  - Verifies screenshot mode prompt construction, title prefixes, and settings dialog save behavior.

- `tests/test_gui_e2e.py`
  - Covers Prompt CRUD/copy, per-Prompt shortcut save path, duplicate shortcut rejection, and CameraBuilder workflow.

## Common Workflows

### Run App From Source

```powershell
python main.py
```

### Run Tests

```powershell
$env:QT_QPA_PLATFORM='offscreen'
python -B -m pytest -q
```

### Build EXE

```powershell
python -m PyInstaller --clean --noconfirm PromptTool.spec
```

### Startup Smoke

```powershell
$exe = Resolve-Path .\dist\PromptTool.exe
$p = Start-Process -FilePath $exe -PassThru -WindowStyle Normal
Start-Sleep -Seconds 4
Get-Process PromptTool -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle,Responding,Path
Get-Process PromptTool -ErrorAction SilentlyContinue | Stop-Process -Force
Get-Item .\dist\PromptTool.exe | Format-List FullName,Length,LastWriteTime
```

## Known Architecture Notes

- This is not pure Qt code. Most UI still uses `shared.qt_compat` names (`tk.Frame`, `tk.Button`, etc.) backed by PySide6.
- Avoid introducing real `tkinter`; use `shared.qt_compat`.
- When fixing UI bugs, first check compatibility layer behavior before patching individual windows.
- Avoid parentless `QWidget` creation except true top-level windows.
- AI calls are asynchronous; callbacks must be delivered back to Qt main thread through `features/ai_optimize/client.py`.
- Screenshot AI config is separate from text AI config because text models may not support images.

## Low-Context Start Checklist

1. Read this file.
2. Read `REPO_MAP.md`.
3. Use `git status --short` to see current dirty state.
4. For UI/lifecycle bugs, inspect `shared/qt_compat.py` and `shared/ui_kit.py` first.
5. For feature bugs, find owning feature under `features/` and service logic under `core/services/`.
6. After meaningful code changes, run tests and rebuild `PromptTool.exe`.
