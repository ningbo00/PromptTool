# 下一轮 2 小时工作清单 05

执行原则：继续遵从 TDD 和 DDD。Phase 3 继续从 AI 优化弹窗中剥离业务逻辑，先抽服务，再让 UI 只负责展示和事件转发。

## 目标

1. 抽出 `AIOptimizeService`，承接动作执行前的状态校验、请求准备和结果解析。
2. 让 `AIOptimizeDialog` 逐步减少提示词构建、方向解析和变体/关键词解析逻辑。
3. 继续按信息架构重排 AI 弹窗主体区域：上方指令、左侧输入、右侧结果、底部 insights。

## 任务清单

### 1. AIOptimizeService

- 新增服务和测试。
- 支持：
  - 空 Prompt 校验。
  - 自定义指令校验。
  - 动作请求准备。
  - temperature 选择。
  - history label 选择。
  - 变体解析。
  - 关键词解析。

验收：

- 服务测试覆盖校验和解析。
- UI 不直接解析自定义方向和变体格式。

### 2. AI 弹窗接入服务

- `_run_ai` 使用服务。
- `_score` 使用服务。
- `_zh_to_en` 使用服务。
- `_gen_variants` 使用服务。
- `_extract_keywords` 使用服务。
- `_recommend_negative` 使用服务。
- `_compliance_check` 使用服务。

验收：

- 网络调用方式不变。
- 现有按钮入口不丢失。

### 3. 主体区域重排

- 指令区显式成组。
- 主体区明确为左侧输入、右侧结果。
- 底部 insights 用于状态、变体、关键词、评分、负面词、合规结果。

验收：

- 弹窗结构和 `AIOptimizeLayoutSpec` 更一致。
- 测试通过。

## 暂不做

- 不改真实 HTTP 客户端。
- 不做 API 联网测试。
- 不重构引导创作和描述转 Prompt 子弹窗内部。
