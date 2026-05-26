# PromptTool 工作计划（TDD + DDD）

本文档用于后续改造前的统一规划。原则是：先明确领域模型和验收标准，再写测试，再实现；每次只改一个小闭环，避免把 UI、数据、AI 调用和打包逻辑继续混在一起。

## 1. 改造目标

- 梳理混乱的 UI 布局，让用户按「管理 Prompt -> 编辑 Prompt -> 优化/生成 Prompt -> 复制/保存」的自然流程操作。
- 将业务逻辑从 Tkinter 控件中拆出，形成可测试的领域层。
- 使用 TDD 保证重构不破坏现有功能，优先覆盖数据、Prompt 组装、AI 动作编排和配置管理。
- 使用 DDD 明确边界上下文，降低 `widget.py` 巨型文件继续膨胀的风险。
- 清理仓库结构，区分源码、数据、配置、构建产物和发布包。

## 2. 工作规则

### 2.1 TDD 规则

每个功能改动都遵守 Red-Green-Refactor：

1. Red：先写一个失败测试，描述期望行为。
2. Green：用最小代码让测试通过。
3. Refactor：在测试保护下整理命名、结构和重复逻辑。

硬性要求：

- 不先写大段 UI 实现，再补测试。
- 领域逻辑必须能在无 GUI 环境下测试。
- AI 网络调用必须通过接口抽象和 mock 测试，不在单元测试中真实请求网络。
- 每个重构步骤保持可运行，避免长时间处于半成品状态。
- 每次提交只包含一个明确主题，例如「提取 PromptStore」「重排主窗口工具区」。

### 2.2 DDD 规则

优先识别业务概念，再决定代码结构。

- 使用统一语言：Prompt、PromptLibrary、PromptDraft、PromptSelection、PromptBuilder、AIOptimization、AIProviderConfig。
- 将领域规则放到 core/domain，而不是 Tkinter 回调里。
- UI 只负责展示状态和转发用户意图，不直接承担保存、排序、拼接、生成等业务规则。
- 基础设施（JSON 文件、剪贴板、AI HTTP 客户端）通过接口隔离，便于测试替换。
- 每个边界上下文只暴露清晰的应用服务，避免跨模块直接操作内部状态。

## 3. 边界上下文划分

### 3.1 Prompt Library Context

职责：

- 维护 Prompt 列表。
- 支持新建、编辑、删除、排序、搜索、批量选择。
- 支持拼接复制和当前 Prompt 复制。

核心对象：

- `Prompt`：标题和内容。
- `PromptLibrary`：Prompt 集合及排序规则。
- `PromptSelection`：单选、批量勾选和拼接规则。
- `PromptStore`：持久化接口。

优先测试：

- 加载非法 JSON 时返回空列表。
- 保存后再次加载内容一致。
- 删除 Prompt 后勾选索引正确重排。
- 上移/下移时选中项和勾选项保持一致。
- 搜索同时匹配标题和内容。
- 批量拼接使用空行分隔，并保持列表顺序。

### 3.2 Prompt Editor Context

职责：

- 管理当前编辑草稿。
- 区分预览、编辑、新建、保存、取消。

核心对象：

- `PromptDraft`：编辑中的标题和内容。
- `EditorState`：当前模式和是否有未保存变更。

优先测试：

- 新建时生成空草稿并进入编辑模式。
- 保存空标题和空内容时给出明确错误。
- 编辑已有 Prompt 时不影响原数据，直到保存。
- 取消编辑时恢复原始内容。

### 3.3 Prompt Builder Context

职责：

- 根据主体、场景、风格、镜头、技术参数和负面词生成 Prompt。
- 支持实拍模式和二次元模式。

核心对象：

- `BuilderProfile`：实拍/二次元模式。
- `SceneSpec`：主体、环境、数量、天气。
- `StyleSpec`：风格、情绪、审美、运动。
- `CameraSpec`：景别、角度、光线、镜头位置。
- `OutputSpec`：比例、渲染引擎、质量词、负面词。
- `PromptBuildResult`：英文 Prompt、中文解释、负面词。

优先测试：

- 默认参数能生成非空 Prompt。
- 未启用的参数不会出现在 Prompt 中。
- 实拍/二次元模式切换后使用对应词库。
- 自定义词会追加到正确位置。
- 负面词中文映射能正确展示。

### 3.4 AI Optimization Context

职责：

- 组织 AI 优化、翻译、扩写、变体、评分、负面词推荐、合规检查。
- 统一处理 busy 状态、历史记录、结果应用和另存为。

核心对象：

- `AIOptimizationRequest`：原始 Prompt、优化方向、输出长度、自定义指令。
- `AIOptimizationResult`：结果文本、变体、评分、建议。
- `AIAction`：优化、翻译、扩写、评分等动作枚举。
- `AIClient`：AI 调用接口。

优先测试：

- 不同优化动作能生成正确系统指令。
- 变体解析支持编号、分隔线和空行格式。
- AI 返回空结果时给出错误状态。
- 应用结果只修改编辑草稿，不直接保存。
- 另存为会创建新 Prompt。

### 3.5 Configuration Context

职责：

- 管理 AI 服务商、模型、API Key 和本地配置文件。
- 禁止源码内硬编码真实 Key。

核心对象：

- `AIProvider`：服务商名称、接口地址、模型列表。
- `AIConfig`：当前选择的服务商、模型和 Key。
- `ConfigStore`：配置持久化接口。

优先测试：

- 无配置文件时返回安全默认值。
- 保存配置后可重新加载。
- API Key 不出现在测试快照、日志和默认源码中。
- 不支持的服务商会返回明确错误。

## 4. 目标目录结构

```text
G:\PromptTool\
  main.py
  app\
    app.py
    theme.py
    layout.py
  core\
    domain\
      prompt.py
      prompt_library.py
      prompt_builder.py
      ai_config.py
    services\
      prompt_service.py
      builder_service.py
      ai_optimization_service.py
    ports\
      prompt_store.py
      ai_client.py
      clipboard.py
  infrastructure\
    json_prompt_store.py
    json_config_store.py
    http_ai_client.py
    system_clipboard.py
  features\
    library\
      panel.py
      editor.py
      compact_overlay.py
    builder\
      dialog.py
      scene_step.py
      style_step.py
      camera_step.py
      output_step.py
    ai_tools\
      dialog.py
      result_panel.py
      guided_create_dialog.py
      desc_to_prompt_dialog.py
  tests\
    unit\
    integration\
```

说明：

- `core` 不依赖 Tkinter。
- `infrastructure` 负责文件、网络、剪贴板等外部资源。
- `features` 只放 UI 组件和用户交互。
- 旧文件按小步迁移，不一次性重写。

## 5. 阶段计划

### Phase 0：仓库安全和开发基线

目标：先保证项目可安全迭代。

任务：

- 新增 `.gitignore`，忽略 `__pycache__/`、`*.pyc`、`build/`、`dist/`、`EXE/`、`*.rar`、`ai_config.json`。
- 移除源码中的真实 API Key，改为安全占位值或首次启动配置。
- 建立 `tests/` 目录和基础测试命令。
- 增加最小冒烟测试：导入主模块、加载 Prompt、加载配置。

验收：

- `git status` 中不再出现构建产物作为开发改动。
- 源码搜索不到真实 API Key。
- 测试命令可运行。

### Phase 1：提取 Prompt Library 领域逻辑

目标：先把主窗口最核心的 Prompt 管理规则从 UI 中拆出。

TDD 步骤：

1. 为加载、保存、搜索、排序、删除、批量拼接写测试。
2. 创建 `Prompt`、`PromptLibrary`、`PromptSelection`。
3. 将 `features/prompt_list/widget.py` 中对应逻辑迁移到领域层。
4. UI 改为调用服务，不直接处理复杂索引规则。

验收：

- 主窗口现有管理功能行为不变。
- 领域测试覆盖 Prompt 管理核心规则。

### Phase 2：重排主窗口 UI

目标：让主界面从“按钮堆叠”变成清晰的三栏工作台。

设计：

- 左侧：Prompt 库、搜索、列表、批量选择。
- 中间：当前 Prompt 编辑和预览。
- 右侧：工具入口，包括 AI 优化、描述转 Prompt、提示词生成器、设置。
- 顶部：应用标题、置顶、精简模式、帮助。

TDD/验证：

- 领域测试保持全部通过。
- 增加 UI smoke test：主窗口可实例化，核心按钮存在，选择 Prompt 后编辑区更新。

验收：

- 新用户能在 10 秒内识别主要操作路径。
- 主要操作按钮不超过 5 个，其余放入工具区或更多菜单。

### Phase 3：整理 AI 优化工作流

目标：把 AI 弹窗从“功能按钮墙”整理为“输入 -> 指令 -> 结果 -> 应用”。

任务：

- 抽出 AI 动作构建逻辑。
- 将默认主动作限制为：优化、中文转英文、生成变体。
- 评分、关键词、负面词、合规检查放入高级工具区。
- 统一结果操作：应用、另存为、复制。

TDD 步骤：

1. 为 prompt 指令构建写测试。
2. 为变体解析、评分解析和错误处理写测试。
3. 使用 fake AIClient 测试无网络流程。
4. 重排 UI。

验收：

- 无 API Key 时给出清晰提示，不崩溃。
- AI 结果可应用到编辑器，也可另存为新 Prompt。
- 测试不依赖真实网络。

### Phase 4：重构提示词生成器

目标：把 8 个 Tab 改造成 4 步向导。

步骤：

1. 场景：主体、环境、人数、天气、补充描述。
2. 风格：实拍/二次元、预设、风格、情绪、审美。
3. 镜头：景别、角度、机位、光线、运动。
4. 输出：质量、比例、渲染、负面词、预览、插入/复制。

TDD 步骤：

- 先为 `_build_prompt` 等组装逻辑写纯函数测试。
- 抽出 builder service。
- 再替换 UI 步骤页。

验收：

- 默认生成、切换模式、应用预设、插入列表功能保持可用。
- 生成逻辑不依赖 Tkinter 控件状态。

### Phase 5：发布和打包整理

目标：让源码仓库、用户数据和发布产物分离。

任务：

- 调整 `PromptTool.spec`。
- 明确 `prompts.json` 和 `ai_config.json` 的运行时位置。
- 打包输出到 `dist/`，不进入源码提交。
- 增加打包说明文档。

验收：

- 开发环境和打包后的 exe 都能找到正确的数据文件。
- 发布包不包含源码中的测试数据和私密配置。

## 6. 测试策略

### 6.1 单元测试

覆盖：

- Prompt 数据清洗。
- Prompt 列表排序、删除和选择状态。
- Prompt 拼接规则。
- Builder 组装规则。
- AI 指令构建和结果解析。
- 配置加载保存。

### 6.2 集成测试

覆盖：

- JSON PromptStore 读写临时文件。
- JSON ConfigStore 读写临时文件。
- PromptService 串联 store 和 domain。
- AIOptimizationService 使用 fake AIClient。

### 6.3 UI 冒烟测试

覆盖：

- 主窗口可实例化。
- 主要弹窗可实例化。
- 核心按钮和输入框存在。
- 选择 Prompt 后编辑区展示正确内容。

UI 冒烟测试不追求像素级断言，重点验证不崩溃和基础交互。

## 7. 完成定义

每个阶段完成时必须满足：

- 相关测试全部通过。
- 没有引入真实 API Key、临时文件、构建产物。
- 新增领域逻辑不依赖 Tkinter。
- UI 改动有明确前后目标，不随意增加按钮。
- 文档同步更新。
- Git 提交信息清晰。

## 8. 风险清单

- Tkinter UI 和业务逻辑耦合深，拆分时容易影响现有行为。
- `camera_builder/widget.py` 和 `ai_optimize/widget.py` 体积大，必须小步迁移。
- 现有默认配置包含敏感 Key，需要优先处理。
- 构建产物已进入首次存档提交，后续开发提交要通过 `.gitignore` 控制。
- GUI 自动化测试成本较高，初期以领域测试和 UI 冒烟测试为主。

## 9. 下一步执行建议

优先执行 Phase 0：

1. 创建 `.gitignore`。
2. 移除硬编码 API Key。
3. 引入 `pytest` 测试骨架。
4. 为 `shared/storage.py` 和 `shared/config.py` 写第一批测试。

完成 Phase 0 后再进入主窗口重排，避免在不安全、不受测试保护的状态下直接大改 UI。
