# 改善报告

- 实际投入：约 120 分钟（含探索选题、v1/v2 实现与对照、报告与 AI session 整理）；环境准备：约 5 分钟
- 一句话成果：别人可以少被「高置信静默误执行」误导，并在可解析的序数/修订指代上少一次不必要澄清失败。

## 问题与判断

主问题 A：`explicit_target is None` 时，原策略凭 `conf≥0.8` 且 `margin≥0.4` 自动执行，会在「打开那个 / 打开刚才那个」等指代下选错设备；legacy 还会把这类错执行算成功。事实见 EVAL_PLAN；优先级对齐「先避免错误目标」。

路径：先落地「无 explicit 一律澄清」（v1，CFF→0 但真成功 −2），复盘后改为 **结构化 history 细分流（v2）**——不读 world，仅在「前一个 / 后一个 / 改好|换成」可解析时执行，其余仍澄清；**不恢复** conf/margin 盲执行。v1 未删除，作对照实验保留。

## 成果与证据

- 最终入口：`voice_agent/policy.py` + `voice_agent/history_resolve.py`
- 中间方案（保留）：`evals/candidate/policy_always_clarify.py`、`runs/experiment_always_clarify/`、`evals/candidate/metrics_always_clarify.json`
- 评测：`evals/candidate/test_ambiguous_execute.py`、`ambiguous_scenarios.jsonl`、`analyze_cff.py`；指标：`metrics_before.json` / `metrics_always_clarify.json` / `metrics_after.json`
- 对照目录：`runs/before/`（baseline）、`runs/experiment_always_clarify/`（v1）、`runs/after/`（v2 最终）
- 计划与报告：`EVAL_PLAN.md`、`REPORT.md`；AI 记录：`ai-sessions/`（见 INDEX.md）

```sh
uv run --quiet --offline --no-project python task.py run --out runs/before
uv run --quiet --offline --no-project python -m voice_agent.cli \
  --policy evals/candidate/policy_always_clarify.py --out runs/experiment_always_clarify
uv run --quiet --offline --no-project python -m voice_agent.cli --out runs/after
uv run --quiet --offline --no-project python evals/candidate/analyze_cff.py --out evals/candidate/metrics_after.json
uv run --quiet --offline --no-project python evals/candidate/analyze_cff.py \
  --policy evals/candidate/policy_always_clarify.py --out evals/candidate/metrics_always_clarify.json
uv run --quiet --offline --no-project python -m unittest discover -s evals/candidate
uv run --quiet --offline --no-project python task.py check
```

Oracle：`world.target`。主指标 CFF=`ack 且存在错误目标 commit`，分母 100。

| 指标 | before | v1 一律澄清 | after v2 细分流 |
|------|--------|-------------|-----------------|
| CFF | 2/100 | 0/100 | **0/100** |
| 真成功 | 88/100 | 86/100 | **89/100** |
| 澄清 | 43/100 | 55/100 | 50/100 |
| 高风险错目标 | 0/37 | 0/37 | 0/37 |
| legacy | 90/100 | 86/100 | 89/100 |

- 检验：原失败 2 案仍澄清且 CFF=0；无结构信号的歧义新实例仍澄清；序数/修订新实例在澄清未答时仍做对（v1 会失败）；「刚才那个」+ 高 conf 不执行；明确指令与高风险无 explicit 回归通过。`task.py check` 通过。

## 最终取舍

**保留 v2。** 相对 baseline：CFF 清零且真成功 +1；相对 v1：同安全、更高完成。v1 作为代价更大的可行方案保留实验产物。未改系统边界。

## 投入时间、未完成项与已知限制

**投入时间**
- 作答投入：约 120 分钟
- 环境准备：约 5 分钟（不计入作答时间口径时单独列出）

**未完成项**
- 未做更广的序数/修订话术敌意压测（仅有限自建场景）
- 未优化 `select_model` 路由以冲击「明确低风险 P95≤600ms」下一版目标
- 未引入 `abstain` 或 busy 模式下的交互代价对照实验
- 未做真实用户/线上分布验证（本题仅离线合成）
- 远程仓库推送与交卷链接：待打包/提交步骤完成（见交付动作）

**已知限制**
- 100 条 public 为合成且边界加重，CFF 分子/分母**不可外推**为线上错误率
- 「前一个/后一个/改好|换成」为可观测启发式，换表述可能失效；相同信号可对应不同真实意图（PRODUCT 已提示）
- 「打开那个 / 打开刚才那个」等无结构指代仍依赖澄清及用户是否回答
- CFF 只覆盖「ack 且错目标」，不是全局安全看板；非幂等重复等需并列指标（本题 public 上为 0）
- P95（after 约 1530ms）仍高于下一版简单指令 600ms 目标；**不构成撤回 v2 的理由**，但是独立未解决问题
- AI session 正文为交付润色版；`source.jsonl` 为脱敏工具轨迹，部分工具 stdout 未完整内联，数值以 `runs/` 与 `metrics_*.json` 为准

## 个人判断与 AI 交互

完整记录见 `ai-sessions/session-01-main.md`（索引：`ai-sessions/INDEX.md`）。`filtered.jsonl` 与正文对应；`source.jsonl` 为 Cursor 原始轨迹的**脱敏提交版**（含工具调用）。关键判断（润色版编号，约略）：
- 收敛易验证主指标 **CFF**，并选定主问题 **A**
- 落地 v1 一律澄清（CFF→0）后预审取舍；再经复盘落地细分流 **v2**，强制保留 v1 实验产物
- 补充讨论明确：不外推线上率、辅助指标不捆绑综合分、P95 未达 SLO 不撤回 v2
- 出题清单轮次未纳入正文；复盘反问问答已纳入
