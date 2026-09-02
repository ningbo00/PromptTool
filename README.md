# PromptTool

基于 **PySide6** 的本地桌面 Prompt 管理工具：管理你的 Prompt 库，调用 AI 一键优化，并通过摄影机提示词生成器快速构建画面描述。

## 功能特性

- **Prompt 库管理**：创建、编辑、分类、搜索本地 Prompt，JSON 本地存储
- **AI 优化**：接入大模型（DeepSeek / 百炼等），对 Prompt 进行润色与改写
- **AI 设置**：可视化配置 API Key、模型与服务商
- **摄影机提示词生成器**：按场景、镜头、灯光、风格分步生成摄影画面提示词
- **截图提示词**：截图选区并配合快捷键（默认 `Alt+S`）快速生成/分析提示词
- **全局快捷键**：桌面任意位置唤起工具

## 运行环境

- Windows 10/11
- Python 3.10+
- 依赖见 `requirements.txt`（核心为 PySide6）

## 快速开始

```powershell
python -m pip install -r requirements.txt
python main.py
```

首次运行后在「AI 设置」中填入你的 API Key 即可使用 AI 功能。

## 项目结构

```
main.py            # 程序入口
app/               # 应用层布局与组装
core/              # 领域模型与服务（DDD 分层）
features/          # 功能模块（prompt_list / ai_optimize / ai_settings /
                   #  camera_builder / screenshot_prompt / screenshot_settings / help）
infrastructure/    # JSON 存储等基础设施
shared/            # 配置、常量、UI 套件、全局快捷键
tests/             # pytest 测试
docs/              # 用户指南、发布清单、工作计划
```

## 开发命令

```powershell
python -m pip install -r requirements.txt
python -m pytest tests
python main.py
```

## 打包发布

```powershell
python -m PyInstaller --clean --noconfirm PromptTool.spec
```

产物输出到 `dist/PromptTool.exe`。`build/`、`dist/`、`EXE/` 等产物目录已加入 `.gitignore`，不会进入版本库。

## 文档

- 使用说明：[`docs/USER_GUIDE.md`](docs/USER_GUIDE.md)
- 发布验收：[`docs/RELEASE_CHECKLIST.md`](docs/RELEASE_CHECKLIST.md)
- TDD/DDD 工作计划：[`docs/WORK_PLAN_TDD_DDD.md`](docs/WORK_PLAN_TDD_DDD.md)

## 数据与隐私

- Prompt 数据保存在本地 `prompts.json`
- API 配置保存在本地 `ai_config.json`（已 gitignore，请勿提交真实密钥）
