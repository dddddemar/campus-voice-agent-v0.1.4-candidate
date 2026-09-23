# 自建评测

主问题 A（歧义高置信误执行）相关：

- `test_ambiguous_execute.py`：失败案 / 歧义新实例 / 序数·修订新实例 / 明确指令回归 / 高风险边界 / CFF=0 / 相对一律澄清不退步
- `ambiguous_scenarios.jsonl`：自建场景（含可解析序数与不可解析「刚才那个」反例）
- `policy_always_clarify.py`：中间方案（一律澄清），供对照，非最终策略
- `analyze_cff.py`：CFF 等分子分母指标；`metrics_before.json` / `metrics_always_clarify.json` / `metrics_after.json`
- 运行目录：`runs/before/`、`runs/experiment_always_clarify/`、`runs/after/`

```sh
uv run --quiet --offline --no-project python -m unittest discover -s evals/candidate
uv run --quiet --offline --no-project python -m voice_agent.cli \
  --policy evals/candidate/policy_always_clarify.py --out runs/experiment_always_clarify
uv run --quiet --offline --no-project python -m voice_agent.cli --out runs/after
uv run --quiet --offline --no-project python evals/candidate/analyze_cff.py --out evals/candidate/metrics_after.json
```
