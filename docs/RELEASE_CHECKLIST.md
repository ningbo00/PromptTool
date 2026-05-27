# PromptTool 发布验收记录

日期：2026-05-27
平台：Windows 11 / Python 3.12.6

## 发布目标

生成可双击运行的 Windows 桌面版：

```text
G:\PromptTool\dist\PromptTool.exe
```

## 打包命令

```powershell
python -m PyInstaller --clean --noconfirm PromptTool.spec
```

本次验收结果：通过。

生成文件：

```text
G:\PromptTool\dist\PromptTool.exe
```

文件大小：约 40.21 MB。

## 启动冒烟验收

执行方式：通过 PowerShell 启动 `dist\PromptTool.exe`，等待 3 秒后确认进程仍在运行，再关闭/停止该进程。

验收结果：

- EXE 成功启动。
- 进程 3 秒后仍在运行。
- 可被正常关闭或停止。

## 自动化测试验收

完整测试命令：

```powershell
python -m pytest tests
```

当前测试覆盖：

- Prompt Library / PromptService / JsonPromptStore
- AI Optimize actions/service/layout
- CameraBuilder prompt service/light/extractor/negative/preview/state collector
- 主界面、AI 弹窗、CameraBuilder 布局规格
- Tkinter GUI 端到端关键链路

GUI E2E 单独命令：

```powershell
python -m pytest tests\test_gui_e2e.py -vv
```

本次 GUI E2E 验收结果：通过，覆盖：

- 主界面新建、保存、选择、复制、批量拼接、持久化。
- CameraBuilder 填写主体/场景、光源球体交互、负面词预设、风格提炼器应用、生成并插入 Prompt。

## 发布前检查清单

- [x] 源码完整测试通过。
- [x] GUI E2E 测试通过。
- [x] PyInstaller 打包成功。
- [x] EXE 启动冒烟通过。
- [x] `ai_config.json` 未进入 Git。
- [x] 构建产物位于 `dist/`，由 `.gitignore` 忽略。
- [x] 用户使用说明已更新。

## 已知注意事项

- PyInstaller warning 文件中包含部分 Windows 以外平台模块缺失提示，例如 `pwd`、`grp`、`AppKit` 等；这些来自标准库或 `pyperclip` 的可选平台分支，不影响本次 Windows EXE 启动验收。
- 当前发布验收为启动冒烟 + 自动化 GUI 关键链路，不等同于完整人工视觉走查。正式发给最终用户前，建议再手动点击一次主界面、AI 设置、帮助和 CameraBuilder。
