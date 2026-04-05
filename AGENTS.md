# AGENTS.md — CodeReviewEnv Agent Guide

## Overview

This document describes how AI agents interact with CodeReviewEnv,
what they observe, what actions they can take, and how they are rewarded.

## Agent Interface

Agents interact via HTTP REST API:
```python
import requests

BASE_URL = "https://tharshinidj12-code-review-env.hf.space"

# Start episode
obs = requests.post(f"{BASE_URL}/reset", json={"task_id": "easy"}).json()

# Submit fix
result = requests.post(f"{BASE_URL}/step", json={"code": "def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"}).json()

print(f"Reward: {result['reward']}, Done: {result['done']}")
```

## Observation Space

At each step the agent receives:
```json
{
  "buggy_code": "def average(lst):\n    return sum(lst) / len(lst)",
  "task_description": "Fix the function that crashes on empty input",
  "task_id": "easy",
  "attempt_number": 1,
  "max_attempts": 1,
  "last_execution_output": "",
  "feedback": "❌ Code failed: ZeroDivisionError on empty list",
  "hint": "Think about what happens when the list is empty.",
  "reward": 0.0,
  "done": false
}
```

## Action Space

Agent submits:
```json
{
  "code": "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst) / len(lst)",
  "explanation": "Added guard for empty list"
}
```

## Reward Structure

reward = 0.0

0.20  if code executes without error
0.80  proportional to tests passed (easy)
0.40  basic tests passed (medium)
0.40  edge case tests passed (medium)
0.20  all tests passed (hard)
0.20  input validation present (hard)
0.20  no magic numbers (hard)
0.20  code quality score (hard)
× 0.90  attempt penalty per attempt after first
→ clamped to [0.0, 1.0]

## 6 Tasks

| ID | Name | Difficulty | Bug | Max Attempts |
|---|---|---|---|---|
| easy | syntax_fix | ⭐ | ZeroDivisionError | 1 |
| medium | logic_fix | ⭐⭐ | Fibonacci wrong init | 3 |
| medium2 | string_fix | ⭐⭐ | Wrong slice step | 3 |
| hard | refactor_and_fix | ⭐⭐⭐ | Sieve + magic numbers | 5 |
| hard2 | binary_search_fix | ⭐⭐⭐ | Off-by-one + validation | 5 |
| security | security_fix | ⭐⭐⭐ | SQL injection chars | 3 |

## Agent Strategy Tips

1. Always read `feedback` from previous step before next attempt
2. Use `hint` field — it points directly at the bug location
3. For hard tasks — fix the bug AND add input validation AND remove magic numbers
4. For security task — remove `'`, `;`, and `--` characters

## Baseline Agent Performance (Qwen2.5-72B)

[END] success=true steps=1 score=1.000  ← easy
[END] success=true steps=1 score=1.000  ← medium
[END] success=true steps=1 score=1.000  ← medium2
[END] success=true steps=1 score=0.950  ← hard
[END] success=true steps=1 score=1.000  ← hard2
[END] success=true steps=1 score=1.000  ← security
Average: 0.992/1.0

## Security

Submitted code runs in a sandboxed namespace:
- Blocked imports: `os`, `sys`, `subprocess`, `socket`, `requests`
- 5 second execution timeout
- Isolated `__builtins__` — no file system access
- AST analysis before execution

## Running Inference
```bash
export HF_TOKEN=hf_...
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
export SERVER_URL=https://tharshinidj12-code-review-env.hf.space
python inference.py
```