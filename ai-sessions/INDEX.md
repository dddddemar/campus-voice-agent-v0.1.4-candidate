# AI session 索引

- 是否使用 AI：是
- 工具、模型及可知版本：Cursor Agent（界面标识 Composer / Auto）；底层具体模型版本导出不可见，未另行记录
- 会话文件 → 用途 → 顺序/分支关系：
  1. `session-01-main.md` — **审阅正文（交付主文件）**：角色 + 消息顺序全文；含专业化提问与补充讨论；主线事实/数字/取舍与仓库代码一致
  2. `session-01-main.filtered.jsonl` — 与正文一一对应的结构化记录（55 条）
  3. `session-01-main.source.jsonl` — Cursor 原始 transcript 的**脱敏提交版**（含工具调用；已剔除出题清单 2 轮；路径已脱敏）
  - 单一线性会话，无分支/子 Agent 独立文件；审阅以 md 为准，source 供核对工具轨迹
- 关键消息位置 → 对应实现或实验（编号见 `session-01-main.md`）：
  - Msg 6–8：环境验证与 baseline 解读 → `runs/before/`
  - Msg 9–15：约束对齐、成功/失败口径、合成数据外推措辞
  - Msg 18–24：探索候选 → 主指标 **CFF** → 辅助指标约定
  - Msg 25–28：选定主问题 **A**；落地 v1（一律澄清）→ `EVAL_PLAN.md`、初版 `policy`、`evals/candidate/`
  - Msg 29–32：结果简述、取舍预审 → 初版 `REPORT.md`
  - Msg 35–38：session 收录边界约定
  - Msg 39–41：复盘 CFF 完备性
  - Msg 42–48：复盘保守性 → 敌意回归 → 落地 **v2**（`history_resolve.py`、最终 `policy.py`、`policy_always_clarify.py`、`runs/experiment_always_clarify/`、`runs/after/`）
  - Msg 49–51：P95/时延 SLO 与撤回标准
  - Msg 52–55：交付同步（除 git）
- 记录缺失与原因：
  - Cursor 导出中部分工具结果未完整内联；命令与指标以仓库 `runs/*/summary.json`、`evals/candidate/metrics_*.json`、`task.py check` 为准复核
  - 正文与 source 均已剔除「助手单方面改进问题清单」相关轮次；其后复盘反问问答保留。source 中若工具参数内嵌该清单原文的打包脚本记录亦已去掉，避免清单回流
  - 交付正文相对原始对话做过专业化扩写与讨论补充，**不改变**实验结论与代码事实；润色/加轮次元指令未纳入
- 脱敏范围（占位符，不提供原值）：
  - `[REDACTED:local-path]/...`：本机工程绝对路径（原含用户目录名）
  - `[REDACTED:cursor-path]`：本机 Cursor/agent transcript 绝对路径
  - `[REDACTED:home]`：其它 `/Users/<name>` 前缀
  - `[REDACTED:email]`：邮箱（本题未发现需替换项；规则已启用）
  - 未发现密钥、认证令牌、cookie、无关公司内部数据；未见需脱敏的个人身份信息正文
  - `session-01-main.md` / `filtered.jsonl` 本身无绝对用户路径，无需替换
