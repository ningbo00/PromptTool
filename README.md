# PromptTool

本项目是一个本地桌面 Prompt 管理工具，支持 Prompt 库管理、AI 优化和摄影机提示词生成器。

- 使用说明：`docs/USER_GUIDE.md`
- 发布验收：`docs/RELEASE_CHECKLIST.md`
- TDD/DDD 工作计划：`docs/WORK_PLAN_TDD_DDD.md`

## 开发命令

```powershell
python -m pip install -r requirements.txt
python -m pytest tests
python main.py
```

## 打包命令

```powershell
python -m PyInstaller --clean --noconfirm PromptTool.spec
```

打包产物生成到 `dist/PromptTool.exe`，该目录不进入 Git。
