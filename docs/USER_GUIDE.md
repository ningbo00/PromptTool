# PromptTool 使用说明

PromptTool 是一个本地 Tkinter 桌面工具，用来管理 Prompt、组合 Prompt、调用 AI 优化，以及通过摄影机提示词生成器构建生图 Prompt。

## 快速启动

### 源码运行

1. 安装 Python 3.12 或兼容版本。
2. 在项目根目录安装依赖：

```powershell
python -m pip install -r requirements.txt
```

3. 启动应用：

```powershell
python main.py
```

也可以双击 `启动.bat` 启动。

### 打包版运行

发布验收后会生成：

```text
G:\PromptTool\dist\PromptTool.exe
```

双击 `PromptTool.exe` 即可运行。首次运行时如果目录下没有 `prompts.json`，应用会从空 Prompt 库开始；AI 配置会保存在同目录的 `ai_config.json`，该文件不会进入 Git。

## 主界面工作流

主界面分三列：

- 左侧：Prompt 库、搜索、勾选、排序和批量拼接复制。
- 中间：当前 Prompt 的标题和正文编辑区。
- 右侧：AI 优化、提示词生成器、AI 设置和帮助入口。

常用流程：

1. 点击 `+ 新建` 创建 Prompt。
2. 在中间编辑标题和正文。
3. 点击 `保存` 持久化到 `prompts.json`。
4. 选择 Prompt 时会自动复制正文到剪贴板。
5. 勾选多条 Prompt 后点击 `拼接复制`，会用空行拼接多条内容。

## 提示词生成器

点击右侧 `提示词生成器` 后进入 4 步结构：

1. 场景：填写主体、环境，并使用角色/天气/场景词块。
2. 风格：选择预设、风格、情绪、滤镜或二次元风格提炼器。
3. 镜头：设置基础参数、景别、俯仰角、主体方位角、主光源和轮廓光。
4. 输出：设置质量、质感、色彩、渲染引擎、比例和负面词。

右侧预览区会同步展示：

- 英文正面提示词
- 中文正面参数对照
- 英文负面提示词
- 中文负面词对照

可用操作：

- `生成`：按当前参数刷新 Prompt。
- `复制`：复制正面 Prompt。
- `插入列表`：保存为主界面 Prompt 条目。
- `转为正面排除词`：把负面词转成正面 prompt 中的排除描述。

## AI 优化

AI 优化依赖 `AI 设置` 中的 API Key 和模型配置。当前内置服务商：

- Kimi / Moonshot
- 阿里百炼 / Qwen
- 豆包 / 火山方舟
- DeepSeek 官网平台，含 `deepseek-v4-pro`、`deepseek-v4-flash`
- ChatGPT / OpenAI

使用流程：

1. 先在主界面选择一个 Prompt。
2. 点击右侧 `AI 优化`。
3. 选择优化、翻译、扩写、评分、合规修复等动作。
4. 将结果应用到当前编辑区，或另存为新 Prompt。

注意：单元测试不会真实调用 AI 网络接口；真实调用只发生在用户主动点击 AI 动作后。

## 数据和配置文件

- `prompts.json`：Prompt 库数据。
- `ai_config.json`：AI API Key、模型和服务商配置。
- `ai_config.json` 已在 `.gitignore` 中忽略，避免泄露密钥。

## 故障排查

- 应用打不开：先用 `python main.py` 查看源码运行是否正常。
- 剪贴板不可用：确认系统允许剪贴板访问，并检查 `pyperclip` 是否安装。
- 打包失败：确认已安装 `pyinstaller`，然后运行 `python -m PyInstaller --clean --noconfirm PromptTool.spec`。
- AI 无返回：检查 API Key、模型名、接口地址和网络连通性。
