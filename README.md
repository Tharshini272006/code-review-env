---
title: Code Review Env
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🐛→✅ CodeReviewEnv

> **An RL environment where AI agents learn to find and fix Python bugs.**  
> Built for the Meta × PyTorch × HuggingFace OpenEnv Hackathon (Scaler) — Solo submission.

[![HF Space](https://img.shields.io/badge/🤗%20HuggingFace-Space%20Live-green)](https://huggingface.co/spaces/tharshinidj12/code-review-env)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED)](https://docker.com)

---

## 🎯 What is this?

A production-grade **OpenEnv reinforcement learning environment** where an AI agent:

1. 👀 **Receives** a Python function with a deliberate bug
2. 🧠 **Analyzes** the code and identifies the problem
3. 🔧 **Submits** a fixed version
4. 🏆 **Gets rewarded** based on correctness + code quality

The environment executes submitted code in a **sandboxed namespace**, runs hidden test cases, and returns **partial rewards at every step** — giving the agent a rich RL training signal.

---

## 🚀 Live Demo
https://tharshinidj12-code-review-env.hf.space/docs

| Endpoint | Try it |
|---|---|
| Health | https://tharshinidj12-code-review-env.hf.space/health |
| Tasks | https://tharshinidj12-code-review-env.hf.space/tasks |
| Swagger UI | https://tharshinidj12-code-review-env.hf.space/docs |

---

## 📊 Agent Performance (Qwen2.5-72B)

| Task | Difficulty | Score | Result |
|------|-----------|-------|--------|
| syntax_fix | ⭐ Easy | **1.000** | ✅ Perfect |
| logic_fix | ⭐⭐ Medium | **0.800** | ✅ Success |
| refactor_and_fix | ⭐⭐⭐ Hard | **0.950** | ✅ Success |

**Average score: 0.917 / 1.0** 🏆

---

## 🧩 3 Tasks — Easy → Medium → Hard

### ⭐ Task 1 — `syntax_fix` (Easy)
```python
# Bug: crashes on empty list → ZeroDivisionError
def average(lst):
    return sum(lst) / len(lst)  # ❌

# Fix: guard for empty list
def average(lst):
    if not lst:
        return 0.0
    return sum(lst) / len(lst)  # ✅
```
- 1 attempt allowed
- 3 hidden test cases
- Max reward: 1.0

---

### ⭐⭐ Task 2 — `logic_fix` (Medium)
```python
# Bug: wrong initial values → wrong fibonacci sequence
def fibonacci(n):
    a, b = 0, 0   # ❌ should be 0, 1
    for _ in range(1, n):
        a, b = b, a + b
    return b

# Fix: correct initial values
def fibonacci(n):
    a, b = 0, 1   # ✅
    for _ in range(1, n):
        a, b = b, a + b
    return b
```
- 3 attempts with feedback
- 5 hidden test cases
- Partial reward per attempt

---

### ⭐⭐⭐ Task 3 — `refactor_and_fix` (Hard)
```python
# Bug: magic number + wrong array size + no validation
def sieve_of_eratosthenes(n):
    primes = [True] * 100        # ❌ magic number
    for j in range(i*i, 100, i): # ❌ wrong size
        primes[j] = False
    return [i for i in range(100) if primes[i]]  # ❌

# Fix: dynamic size + validation + no magic numbers
def sieve_of_eratosthenes(n):
    if n < 0:
        raise ValueError("n must be non-negative")
    if n < 2:
        return []
    primes = [True] * (n + 1)    # ✅
    primes[0] = primes[1] = False
    for i in range(2, int(n**0.5) + 1):
        if primes[i]:
            for j in range(i*i, n+1, i):  # ✅
                primes[j] = False
    return [i for i in range(n+1) if primes[i]]  # ✅
```
- 5 attempts with feedback
- 5 hidden test cases
- Graded on: correctness + validation + no magic numbers + quality

---

## 🏗️ Architecture
code_review_env/
├── inference.py          ← LLM agent [START][STEP][END] logs
├── models.py             ← Pydantic Action/Observation/State
├── client.py             ← Python client wrapper
├── openenv.yaml          ← OpenEnv spec manifest
├── requirements.txt
└── server/
├── app.py            ← FastAPI endpoints
├── environment.py    ← reset() step() state()
├── tasks.py          ← 3 task definitions
├── grader.py         ← sandbox execution + rewards
└── Dockerfile        ← HF Spaces ready

---

## 💰 Reward Design
reward = 0.0

0.20  code executes without error
0.30  basic tests pass (proportional)
0.30  edge case tests pass (proportional)
0.20  code quality score (Task 3 only)

× 0.90  attempt penalty (per attempt after first)
clamped to [0.0, 1.0]

Rich partial rewards at **every step** — not just terminal — giving the RL agent a strong learning signal throughout the episode.

---

## 🔒 Security

Submitted code runs in a **sandboxed execution environment**:
- Isolated namespace with restricted builtins
- Blocked imports: `os`, `sys`, `subprocess`, `socket` and more
- 5 second execution timeout
- Test cases hidden from agent

---

## 🛠️ Setup & Run

### Local
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r server/requirements.txt

# Start server
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860

# Test endpoints
curl http://localhost:7860/health
curl http://localhost:7860/tasks

# Run inference
export HF_TOKEN=hf_...
export API_BASE_URL=https://router.huggingface.co/v1
export MODEL_NAME=Qwen/Qwen2.5-72B-Instruct
python inference.py
```

### Docker
```bash
docker build -t code-review-env .
docker run -p 7860:7860 \
  -e HF_TOKEN=$HF_TOKEN \
  -e API_BASE_URL=https://router.huggingface.co/v1 \
  -e MODEL_NAME=Qwen/Qwen2.5-72B-Instruct \
  code-review-env
```

---

## 📡 API Reference

### POST /reset
```json
// Request
{"task_id": "easy"}

// Response
{
  "buggy_code": "def average(lst):\n    return sum(lst) / len(lst)",
  "task_description": "Fix the function...",
  "task_id": "easy",
  "attempt_number": 0,
  "max_attempts": 1,
  "feedback": "Episode started.",
  "hint": "Think about what happens when the list is empty.",
  "reward": 0.0,
  "done": false
}
```

### POST /step
```json
// Request
{
  "code": "def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst) / len(lst)",
  "explanation": "Added empty list guard"
}

// Response
{
  "observation": {
    "feedback": "✅ Code executed. Tests passed: 3/3.",
    "reward": 1.0,
    "done": true
  },
  "reward": 1.0,
  "done": true
}
```

---

## 📋 Inference Output
[START] task=easy env=code_review_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=def average(lst):... reward=1.00 done=true error=null
[END] success=true steps=1 score=1.000 rewards=1.00
[START] task=medium env=code_review_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=def fibonacci(n):... reward=0.80 done=true error=null
[END] success=true steps=1 score=0.800 rewards=0.80
[START] task=hard env=code_review_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=def sieve_of_eratosthenes(n):... reward=0.95 done=true error=null
[END] success=true steps=1 score=0.950 rewards=0.95

---

## 🌐 Environment Variables

| Variable | Default | Description |
|---|---|---|
| `HF_TOKEN` | required | HuggingFace API token |
| `API_BASE_URL` | `https://router.huggingface.co/v1` | LLM API endpoint |
| `MODEL_NAME` | `Qwen/Qwen2.5-72B-Instruct` | Model identifier |
| `SERVER_URL` | `http://localhost:7860` | Environment server URL |

---

*Built with ❤️ for the Meta × PyTorch × HuggingFace OpenEnv Hackathon*
