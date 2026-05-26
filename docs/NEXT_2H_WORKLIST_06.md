# 下一轮 2 小时工作清单 06

执行原则：继续遵从 TDD 和 DDD。先扩展动作体系，再接 UI；面板拆分以降低 `widget.py` 体积为目标，保持现有功能可运行。

## 目标

1. 将 `_improve_by_score`、`_expand_only`、`_compliance_fix` 纳入 `AIOptimizeService` 动作体系。
2. 抽出 AI 优化弹窗面板辅助类：`InstructionPanel`、`ActionBar`、`ResultPanel`、`InsightsPanel`。

## 任务清单

### 1. 扩展 AI 动作构建

- 新增动作：
  - `improve_by_score`
  - `expand_only`
  - `compliance_fix`
- 先写测试，再实现。

验收：

- 三个动作 messages 有测试覆盖。
- 对依赖反馈/报告的动作有校验。

### 2. UI 接入扩展动作

- `_improve_by_score` 使用 `AIOptimizeService.prepare_action()`。
- `_expand_only` 使用 `AIOptimizeService.prepare_action()`。
- `_compliance_fix` 使用 `AIOptimizeService.prepare_action()`。

验收：

- 网络调用方式不变。
- 历史标签来自服务。

### 3. 面板辅助类

- 新增 `features/ai_optimize/panels.py`。
- 提供：
  - `InstructionPanel`
  - `ActionBar`
  - `ResultPanel`
  - `InsightsPanel`
- 本轮先抽可复用创建逻辑，避免一次性迁移全部 UI。

验收：

- `widget.py` 的部分面板创建逻辑迁移出去。
- 测试和编译通过。

## 暂不做

- 不重写整个 AI 弹窗。
- 不改真实 HTTP 客户端。
- 不动引导创作和描述转 Prompt 子弹窗内部。
