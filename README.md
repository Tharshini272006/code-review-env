---
title: Code Review Env
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# 🐛→✅ CodeReviewEnv

> **A fully executable OpenEnv environment where AI agents learn to find and fix Python bugs by actually running the code.**
> Built solo in 5 days · Meta × PyTorch × HuggingFace OpenEnv Hackathon

[![Live](https://img.shields.io/badge/🤗%20Space-Live-brightgreen)](https://huggingface.co/spaces/tharshinidj12/code-review-env)
[![Score](https://img.shields.io/badge/Avg%20Score-0.992%2F1.0-gold)](https://tharshinidj12-code-review-env.hf.space/metrics)
[![Tasks](https://img.shields.io/badge/Tasks-6-blue)](https://tharshinidj12-code-review-env.hf.space/tasks)
[![Tests](https://img.shields.io/badge/Tests-20%20passing-brightgreen)](#testing)
[![Solo](https://img.shields.io/badge/Built-Solo-purple)](#built-solo)

---

## ⚡ The Core Insight

Most RL environments **simulate** outcomes.

**CodeReviewEnv executes them.**
```python
# Not a simulation. Real execution.
exec(agent_submitted_code, isolated_namespace)

# Real test cases. Real outputs.
result = fn(*test_args)
assert result == expected  # earned, not estimated

# Real code quality analysis
tree = ast.parse(submitted_code)
```

When the agent submits a fix:
- The code **actually runs**
- Hidden test cases **actually execute**
- Rewards are **earned** — not approximated

No reward hacking. No shortcuts. Real learning signal.

---

## 🚀 Try It Live
```bash
# 1. Get a buggy function
curl -X POST https://tharshinidj12-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "easy"}'

# Returns:
# {
#   "buggy_code": "def average(lst):\n    return sum(lst) / len(lst)",
#   "hint": "Think about what happens when the list is empty.",
#   "done": false
# }

# 2. Submit your fix
curl -X POST https://tharshinidj12-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{"code": "def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"}'

# Returns:
# {
#   "reward": 1.0,
#   "done": true,
#   "observation": {
#     "feedback": "✅ Code executed. Tests passed: 3/3."
#   }
# }
```

**Swagger UI:** https://tharshinidj12-code-review-env.hf.space/docs

---

## 📊 Proven Agent Performance

Task          Score    Steps   Status
─────────────────────────────────────
easy          1.000      1     ✅ Perfect
medium        1.000      1     ✅ Perfect
medium2       1.000      1     ✅ Perfect
hard          0.950      1     ✅ Strong
hard2         1.000      5     ✅ Perfect
security      1.000      1     ✅ Perfect
─────────────────────────────────────
Average       0.992            🏆 Top tier

---

## 🧩 6 Real-World Bug Tasks

Every task is a bug that real developers actually write.

---

### ⭐ Task 1 — `syntax_fix` (Easy, 1 attempt)
```python
# The bug: crashes in production on empty input
def average(lst):
    return sum(lst) / len(lst)   # ZeroDivisionError

# The fix: guard clause
def average(lst):
    if not lst:
        return 0.0
    return sum(lst) / len(lst)   # safe
```

---

### ⭐⭐ Task 2 — `logic_fix` (Medium, 3 attempts)
```python
# The bug: wrong Fibonacci sequence forever
def fibonacci(n):
    a, b = 0, 0    # wrong — produces 0,0,0,0...

# The fix:
    a, b = 0, 1    # correct — produces 0,1,1,2,3,5...
```

---

### ⭐⭐ Task 3 — `string_fix` (Medium, 3 attempts)
```python
# The bug: reverse returns the original string
def reverse_string(s):
    return s[::1]   # step=1, returns unchanged

# The fix:
    return s[::-1]  # step=-1, actually reverses
```

---

### ⭐⭐⭐ Task 4 — `refactor_and_fix` (Hard, 5 attempts)
```python
# The bug: magic number + wrong array size
def sieve_of_eratosthenes(n):
    primes = [True] * 100          # hardcoded! breaks for n>100
    for j in range(i*i, 100, i):   # wrong upper bound

# The fix: dynamic + validated
def sieve_of_eratosthenes(n):
    if n < 0: raise ValueError("n must be non-negative")
    primes = [True] * (n + 1)      # dynamic
    for j in range(i*i, n+1, i):   # correct
```

---

### ⭐⭐⭐ Task 5 — `binary_search_fix` (Hard, 5 attempts)
```python
# The bug: off-by-one causes index out of bounds
def binary_search(arr, target):
    left, right = 0, len(arr)      # wrong — should be len-1

# The fix:
    left, right = 0, len(arr) - 1  # correct boundary
```

---

### 🔐 Task 6 — `security_fix` (Hard, 3 attempts)
```python
# The bug: SQL injection vulnerability in production code
def sanitize_input(user_input):
    return user_input.replace("'", "")  # misses ; and --
    # attacker sends: "'; DROP TABLE users--"

# The fix: block ALL dangerous chars
def sanitize_input(user_input):
    if user_input is None: return ""
    return (user_input
        .replace("'", "")
        .replace(";", "")
        .replace("--", ""))
```

This is the exact class of bug that causes **real data breaches**.

---

## 💰 Reward Engineering

Partial rewards at **every step** — rich RL signal throughout the episode:

Reward breakdown:
+0.20  code executes without error
+0.80  tests passed — proportional (easy)
+0.40  basic tests passed (medium/hard)
+0.40  edge case tests passed (medium/hard)
+0.20  input validation present (hard/security)
+0.20  no magic numbers (hard)
+0.20  code quality via AST (hard/security)
×0.90  attempt penalty after first attempt
→ clamped to [0.0, 1.0]

The agent always gets **signal** — never silence.

---

## 🔒 Execution Sandbox

Submitted code runs in a fully isolated namespace:
```python
BLOCKED_IMPORTS = {
    "os", "sys", "subprocess", "socket",
    "requests", "importlib", "ctypes",
    "multiprocessing", "threading"
}

# Safety check before execution
safety_err = _check_safety(code)  # AST scan

# Isolated execution
namespace = {"__builtins__": safe_builtins_only}
exec(compiled_code, namespace)

# 5 second timeout
# No file system access
# No network access
```

The agent cannot escape the sandbox. Rewards cannot be gamed.

---

## 🎬 Episode Replay

Every episode is recorded. Every step is replayable.
```bash
# What did the agent actually do?
GET /replay/current
GET /replay/{episode_id}
```
```json
{
  "episode_id": "abc-123",
  "task_id": "security",
  "total_reward": 0.95,
  "history": [
    {
      "step": 0,
      "type": "reset",
      "buggy_code": "def sanitize_input...",
      "reward": 0
    },
    {
      "step": 1,
      "type": "step",
      "action": "def sanitize_input(user_input):\n    ...",
      "reward": 0.95,
      "tests_passed": 5,
      "feedback": "✅ Code executed. Tests passed: 5/5."
    }
  ]
}
```

Not a black box. A **fully observable RL system**.

---

## 📈 Training Demo
```bash
python training_demo.py
```

============================================================
CodeReviewEnv — Training Demo
Episode 1/3
✅ easy         reward=1.000 steps=1
✅ medium       reward=1.000 steps=1
✅ medium2      reward=1.000 steps=1
✅ hard         reward=0.950 steps=1
✅ hard2        reward=1.000 steps=5
✅ security     reward=1.000 steps=1
Episode avg: 0.992
Training Summary
Episode 1: 0.992 |███████████████████
Episode 2: 0.992 |███████████████████
Episode 3: 0.992 |███████████████████
Average: 0.992/1.0 ✅

---

## 🧪 Testing
```bash
py -3.11 -m pytest tests/ -v
```

PASSED tests/test_grader.py::TestExecuteCode::test_correct_code_executes
PASSED tests/test_grader.py::TestExecuteCode::test_blocked_import_os
PASSED tests/test_grader.py::TestExecuteCode::test_blocked_import_subprocess
PASSED tests/test_grader.py::TestCodeQuality::test_magic_number_detected
PASSED tests/test_grader.py::TestCodeQuality::test_has_docstring
PASSED tests/test_grader.py::TestGrade::test_grade_easy_perfect
PASSED tests/test_grader.py::TestGrade::test_grade_attempt_penalty
PASSED tests/test_environment.py::TestEnvironment::test_perfect_score_easy
PASSED tests/test_environment.py::TestEnvironment::test_reward_in_valid_range
... 20 tests passing ✅

---

## 🏗️ Architecture

CodeReviewEnv/
│
├── inference.py          ← [START][STEP][END] log format
├── training_demo.py      ← RL training demonstration
├── models.py             ← Pydantic typed models
├── client.py             ← Python client wrapper
├── PITCH.md              ← Why this env matters for RL
├── AGENTS.md             ← Agent interaction guide
├── openenv.yaml          ← OpenEnv spec manifest
│
├── tests/                ← 20 pytest tests
│   ├── test_grader.py    ← sandbox + reward tests
│   ├── test_tasks.py     ← task registry tests
│   └── test_environment.py ← episode lifecycle tests
│
└── server/
├── app.py            ← FastAPI + 12 endpoints
├── environment.py    ← reset/step/state + replay
├── tasks.py          ← 6 task definitions
├── grader.py         ← execution sandbox + rewards
└── Dockerfile        ← HF Spaces ready

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Environment info |
| GET | `/health` | Health check |
| GET | `/tasks` | All 6 tasks |
| POST | `/reset` | Start episode |
| POST | `/step` | Submit fix, get reward |
| GET | `/state` | Episode state |
| POST | `/grader` | Grade without episode |
| GET | `/metrics` | Scores + sandbox stats |
| GET | `/replay` | List all episodes |
| GET | `/replay/current` | Current episode |
| GET | `/replay/{id}` | Specific episode |
| GET | `/docs` | Swagger UI |

---

## ⚙️ Setup

### Local
```bash
pip install -r requirements.txt
pip install -r server/requirements.txt
python -m uvicorn server.app:app --host 0.0.0.0 --port 7860
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

### Inference
```bash
export HF_TOKEN=hf_...
export SERVER_URL=https://tharshinidj12-code-review-env.hf.space
python inference.py
```

---

## 🔭 Vision

CodeReviewEnv is a foundation — not a ceiling.

The same architecture that trains agents to fix single functions can evolve into:

- **Autonomous PR reviewer** — agent reviews pull requests across entire repositories
- **CI/CD quality gate** — catches bugs before they reach production, automatically
- **Security scanner** — trained specifically on injection, overflow, and auth vulnerabilities
- **Pair programmer** — an agent that doesn't just suggest fixes, but verifies them

> "The difference between a code suggestion and a code fix is execution. We execute."

This is the training ground for the next generation of AI developers.

---

## 🏆 Built Solo in 5 Days

One developer. No team. Five days. A complete RL training environment that:

- Actually executes submitted code in a sandbox
- Catches SQL injection and security vulnerabilities
- Runs 20 passing unit tests
- Scores 0.992/1.0 average across 6 tasks
- Deployed live on HuggingFace Spaces
- Full episode replay for observability
- Production-ready Docker deployment

**The code doesn't lie. The rewards are earned.**

---

*CodeReviewEnv — Where AI learns to write correct, secure, production-ready code.*

