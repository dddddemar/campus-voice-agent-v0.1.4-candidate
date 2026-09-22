# 文件与字段速查

## 两类数据

- data/history_sessions.jsonl：100 条 baseline 合成交互，一行一个 session。用于观察，不含评测 world；顺序已打散。
- data/public_scenarios.jsonl：100 条可重放场景。一行一场景，字段如下。

```json
{
  "id": "example-scene",
  "observation": {
    "request_id": "example-request", "text": "打开台灯",
    "action": "set_power", "risk": "low",
    "explicit_target": "lamp", "history": [], "interaction_mode": "normal"
  },
  "models": {
    "small": {"candidates": [{"target": "lamp", "confidence": 0.94}]},
    "standard": {"candidates": [{"target": "lamp", "confidence": 0.94}]},
    "strong": {"candidates": [{"target": "lamp", "confidence": 0.94}]}
  },
  "world": {
    "target": "lamp", "timeout": "none",
    "clarification_answered": true, "signals": []
  }
}
```

world.timeout 是 none / before_commit / after_commit，不能在策略中访问。world.signals 是与策略无关的外生观察线索，如用户改变主意后 device_manual_reversal；模拟器另根据实际错误目标产生 user_correction，根据重复非幂等操作产生 user_complaint。这些反馈发生在操作后，不传给此前的策略；修改策略后反馈依据新操作重新产生。历史反馈只是调查入口，不以所有信号都等同失败。

## 运行结果

run(scene, policy) 返回 id、observation、events、latency_ms、model_cost_usd、clarified、acknowledged、commits。

- events 按时间顺序记录模型预测、澄清回答、工具执行/超时/去重、助手回应及用户信号。
- commits 是工具实际产生的操作，每项含 target、action、key；deduplicated 不产生新操作。
- acknowledged 是是否收到回执，和 commits 可能不一致。
- clarified 标记尝试过一次澄清，不保证收到回答。

## 运行与观察

`uv run --quiet --offline --no-project python task.py run --out runs/before` 生成基础指标和完整 trace；`task.py check` 运行契约和候选人评测。入口自动切换到项目目录。CLI 的 --scenarios / --policy / --out 参数仍可用于自己的实验。

历史记录用于提出问题；public_scenarios 可对不同策略重放同一输入。先确定何种结果算改善，再选择需要看的分组。测试示例展示 API 用法，不指定最值得改的问题。

history 是按时间排序的既往对话字符串列表，含说话人前缀；text 是当前用户说法，历史不包含本次操作之后的反馈。历史中出现的目标使用与 candidates 相同的标识。重放只执行当前请求，不重放历史动作。
