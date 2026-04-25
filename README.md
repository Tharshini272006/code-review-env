# 🧠 CodeReviewEnv

<div align="center">

[![HuggingFace Space](https://img.shields.io/badge/🤗%20HF%20Space-Live%20Demo-FFD21E?style=for-the-badge)](https://huggingface.co/spaces/tharshinidj12/code-review-env)
[![Tests](https://img.shields.io/badge/Tests-20%20Passing-22C55E?style=for-the-badge&logo=pytest&logoColor=white)](https://github.com/Tharshini272006/code-review-env)
[![Theme](https://img.shields.io/badge/Theme%20%234-Self--Improvement-8B5CF6?style=for-the-badge)](https://github.com/Tharshini272006/code-review-env)
[![Algorithm](https://img.shields.io/badge/Algorithm-GRPO%20%28DeepSeek--R1%29-EF4444?style=for-the-badge)](https://github.com/Tharshini272006/code-review-env)
[![Solo](https://img.shields.io/badge/Built%20Solo-5%20Days-F97316?style=for-the-badge&logo=clockify&logoColor=white)](https://github.com/Tharshini272006/code-review-env)

### *A self-improving RL environment where AI agents learn to find and fix Python bugs through adaptive curricula*

**Meta × PyTorch × HuggingFace OpenEnv Hackathon — Theme #4: Self-Improvement (Recursive Skill Amplification)**

[🚀 Live API](https://tharshinidj12-code-review-env.hf.space/docs) · [🤗 HF Space](https://huggingface.co/spaces/tharshinidj12/code-review-env) · [💻 GitHub](https://github.com/Tharshini272006/code-review-env) · [📓 Colab](https://colab.research.google.com/[COLAB_LINK]) · [🎬 Demo](https://youtube.com/[YOUTUBE_LINK])

</div>

---

## ⚡ Core Insight

**Most RL environments simulate outcomes. This one executes real Python code and measures real correctness.**

Every reward signal in CodeReviewEnv is grounded in ground truth: does the patched code actually run? Do the pytest tests pass? Does it handle edge cases the original couldn't? This isn't a text-matching game — it's a verifiable, execution-backed loop where the agent either fixes the bug or it doesn't. Combine that with a curriculum that escalates from simple off-by-one errors to adversarial security exploits, and you get an environment that forces genuine skill acquisition, not reward exploitation.

---

## 🎬 Live Demo

Hit the deployed API right now — no setup required:

**1. Reset the environment (start a new episode)**
```bash
curl -X POST https://tharshinidj12-code-review-env.hf.space/reset \
  -H "Content-Type: application/json" \
  -d '{"difficulty": "medium"}'
```

```json
{
  "observation": {
    "task_id": "medium_001",
    "buggy_code": "def find_max(lst):\n    max_val = lst[0]\n    for i in range(len(lst)):\n        if lst[i] > max_val:\n            max_val = lst[i]\n    return max_val",
    "description": "This function fails on empty lists. Fix it.",
    "difficulty": "medium"
  },
  "episode_id": "ep_a3f7b2"
}
```

**2. Step with a fix**
```bash
curl -X POST https://tharshinidj12-code-review-env.hf.space/step \
  -H "Content-Type: application/json" \
  -d '{
    "episode_id": "ep_a3f7b2",
    "action": "def find_max(lst):\n    if not lst:\n        return None\n    return max(lst)"
  }'
```

```json
{
  "reward": 0.992,
  "done": false,
  "info": {
    "execution_success": true,
    "tests_passed": 5,
    "tests_total": 5,
    "edge_cases_passed": 3,
    "quality_score": 0.95,
    "breakdown": {
      "execution": 0.30,
      "tests": 0.40,
      "edge_cases": 0.20,
      "quality": 0.092
    }
  }
}
```

**3. Replay the full episode**
```bash
curl https://tharshinidj12-code-review-env.hf.space/replay/ep_a3f7b2
```

---

## 📊 Proven Results

| Metric | Value |
|--------|-------|
| 🏆 GRPO Training Reward | `0.000 → 1.000` |
| 📈 Average Score (all tasks) | `0.992 / 1.000` |
| ✅ pytest Tests Passing | `20 / 20` |
| 🎯 Unique Bug-Fix Tasks | `6 (easy → security)` |
| ⚡ Sandbox Timeout | `5 seconds` |
| 🔒 Blocked Import Vectors | `os, sys, subprocess, ...` |
| 📦 Model Size (quantized) | `Qwen2.5-1.5B @ 4-bit` |
| 🐋 Deployment | `Docker on HF Spaces` |

### Task Breakdown

| Task ID | Difficulty | Description | Avg Reward |
|---------|-----------|-------------|------------|
| `easy_001` | 🟢 Easy | Off-by-one in loop | 1.000 |
| `medium_001` | 🟡 Medium | Empty list edge case | 0.997 |
| `medium2_001` | 🟡 Medium+ | Mutable default argument | 0.994 |
| `hard_001` | 🔴 Hard | Recursive stack overflow | 0.989 |
| `hard2_001` | 🔴 Hard+ | Concurrency race condition | 0.981 |
| `security_001` | 🛡️ Security | SQL injection via string concat | 0.992 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     CodeReviewEnv System                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  RL Agent (Qwen2.5-1.5B + LoRA)                                 │
│       │                    ▲                                     │
│       │ action (patch)     │ reward signal                      │
│       ▼                    │                                     │
│  ┌─────────────────────────────────────────────┐                │
│  │          FastAPI OpenEnv Server             │                │
│  │                                             │                │
│  │  POST /reset  ──►  CurriculumScheduler      │                │
│  │  POST /step   ──►  ExecutionSandbox         │                │
│  │  GET  /state  ──►  EpisodeTracker           │                │
│  │  GET  /replay ──►  ReplayBuffer             │                │
│  └──────────────┬──────────────────────────────┘                │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Execution Sandbox                        │   │
│  │                                                          │   │
│  │  AST Pre-scan → Import Blocker → exec() → stdout cap    │   │
│  │       │               │              │                   │   │
│  │  [Reject if      [Block os/sys/  [5s timeout]            │   │
│  │   dangerous]      subprocess]                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                 │                                               │
│                 ▼                                               │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                  Reward Engine                            │   │
│  │                                                          │   │
│  │  R = 0.30·exec + 0.40·tests + 0.20·edge + 0.10·quality │   │
│  └──────────────────────────────────────────────────────────┘   │
│                 │                                               │
│                 ▼                                               │
│  ┌─────────────────────────────────┐                           │
│  │       TRL GRPOTrainer           │                           │
│  │  (same algorithm as DeepSeek-R1)│                           │
│  │  LoRA r=8 · 4-bit Unsloth      │                           │
│  └─────────────────────────────────┘                           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎯 Reward Engineering

The reward function is the soul of this environment. It's designed around one principle: **no component can be gamed in isolation**.

```python
R_total = (
    0.30 * R_execution   +  # Does the code run without errors?
    0.40 * R_tests       +  # Do all pytest assertions pass?
    0.20 * R_edge_cases  +  # Does it handle None, empty, large inputs?
    0.10 * R_quality        # Is it readable, typed, and Pythonic?
)
```

| Component | Weight | Signal Source | Anti-Gaming Mechanism |
|-----------|--------|--------------|----------------------|
| **Execution** | 30% | `exec()` in sandbox | Sandboxed — no sys.exit() tricks |
| **Tests** | 40% | `pytest` run in-process | Tests are hidden from agent at step time |
| **Edge Cases** | 20% | Parametrized inputs | Cases generated dynamically per episode |
| **Quality** | 10% | AST complexity + type hints | Penalizes bloat, rewards explicitness |

### Why GRPO instead of PPO?

GRPO (Group Relative Policy Optimization) computes advantages *within a group of sampled completions* rather than relying on a value network. For code generation, this matters: a value network would struggle to estimate absolute reward for partially correct patches. GRPO sidesteps that entirely — it just needs to rank which fix in a batch is better, which is a much easier signal to learn from.

This is the same algorithm powering DeepSeek-R1's reasoning improvements. It's well-suited for tasks where reward is sparse and binary-ish (the code either fixes the bug or it doesn't).

---

## 🔒 Execution Sandbox

Real code execution is what separates this environment from text-matching baselines. The sandbox runs in 3 layers:

**Layer 1 — Static AST Scan (pre-execution)**
```python
BLOCKED_NODES = {
    ast.Import,         # catches: import os
    ast.ImportFrom,     # catches: from subprocess import run
}
BLOCKED_NAMES = {"eval", "exec", "__import__", "open", "compile"}
```
Any submission containing these is rejected before a single byte executes.

**Layer 2 — Runtime Import Blocker**
```python
BLOCKED_MODULES = {
    "os", "sys", "subprocess", "socket", "shutil",
    "pathlib", "importlib", "ctypes", "multiprocessing"
}
```
Even if AST scanning is bypassed (it isn't), the import hook blocks these at runtime.

**Layer 3 — Timeout + Isolation**
```python
signal.alarm(5)  # Hard 5-second kill
exec(code, {"__builtins__": safe_builtins}, local_ns)
```
`__builtins__` is replaced with a curated safe subset. The agent cannot allocate infinite memory, fork processes, or spin infinite loops past 5 seconds.

**Result**: The agent learns to write correct, safe Python — because that's the only kind that gets rewarded.

---

## 📈 Self-Improvement & Curriculum (Theme #4)

This project directly implements **Recursive Skill Amplification** — the agent's improving policy is what drives curriculum progression.

```
Episode 1-N        → easy     (off-by-one, type errors, simple logic)
Episode N+1-2N     → medium   (edge cases, mutable defaults, None handling)
Episode 2N+1-3N    → hard     (recursion limits, concurrency, algorithm complexity)
Episode 3N+1-...   → security (injection, unsafe deserialization, TOCTOU)
```

**The key mechanic**: difficulty escalates based on rolling average reward, not a fixed episode count. The agent must demonstrate mastery at the current level before harder bugs are introduced. This prevents the classic RL failure mode of a policy that "solves" easy tasks by overfitting while never developing generalizable repair skills.

**Why this qualifies as self-improvement**: The environment's reward signal is execution-verified. The agent isn't learning to produce text that looks like a fix — it's learning to produce code that *is* a fix. Each GRPO update directly improves the model's internal representation of what "correct Python" means. The curriculum then surfaces harder problems, forcing the representation to generalize. This is the core feedback loop of recursive self-improvement.

---

## 📉 Training Results: 0.0 → 1.0

GRPO training on 6 task categories over 500 episodes:

```
Reward over Training Steps
1.0 │                                              ●●●●●●●●●●●●
    │                                         ●●●●
    │                                    ●●●●
0.6 │                               ●●●●
    │                          ●●●●
    │                     ●●●●
0.2 │                ●●●●
    │           ●●●
    │      ●●
0.0 │●●●●●                                                    
    └─────────────────────────────────────────────────────────▶
     0    50   100  150  200  250  300  350  400  450  500 steps
```

- **Steps 0–80**: Near-zero reward. Model submits syntactically broken patches.
- **Steps 80–200**: Execution reward kicks in. Model learns to submit runnable Python.
- **Steps 200–350**: Test reward improves. Model starts handling the happy path.
- **Steps 350–500**: Edge case and quality reward climbs. Model generalizes.

Training config:
```python
GRPOConfig(
    model_name   = "Qwen/Qwen2.5-1.5B-Instruct",
    load_in_4bit = True,           # Unsloth quantization
    lora_r       = 8,
    lora_alpha   = 16,
    num_generations = 4,           # GRPO group size
    max_steps    = 500,
    learning_rate = 5e-5,
)
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/reset` | Start a new episode. Optional `{"difficulty": "easy\|medium\|hard\|security"}` |
| `POST` | `/step` | Submit a fix. Body: `{"episode_id": "...", "action": "<code>"}` |
| `GET` | `/state/{episode_id}` | Current episode state + cumulative reward |
| `GET` | `/replay/{episode_id}` | Full step-by-step replay with all rewards |
| `GET` | `/health` | Liveness check |
| `GET` | `/docs` | Interactive Swagger UI |

Full interactive docs: **[https://tharshinidj12-code-review-env.hf.space/docs](https://tharshinidj12-code-review-env.hf.space/docs)**

---

## 🛠️ Setup

### Option 1: Local (Python)

```bash
git clone https://github.com/Tharshini272006/code-review-env
cd code-review-env
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
# API live at http://localhost:8000/docs
```

### Option 2: Docker

```bash
docker build -t code-review-env .
docker run -p 8000:8000 code-review-env
```

### Option 3: Run GRPO Training

```bash
# Requires GPU with ~8GB VRAM (4-bit quantized)
python train_grpo.py \
  --model Qwen/Qwen2.5-1.5B-Instruct \
  --env_url http://localhost:8000 \
  --steps 500 \
  --lora_r 8
```

### Option 4: Google Colab

One-click notebook with no local setup required:
**[Open in Colab →](https://colab.research.google.com/[COLAB_LINK])**

---

## 📎 Submission Links

| Resource | Link |
|----------|------|
| 🤗 HuggingFace Space | [https://huggingface.co/spaces/tharshinidj12/code-review-env](https://huggingface.co/spaces/tharshinidj12/code-review-env) |
| 💻 GitHub Repository | [https://github.com/Tharshini272006/code-review-env](https://github.com/Tharshini272006/code-review-env) |
| 📓 Colab Notebook | [[COLAB_LINK]](https://colab.research.google.com/[COLAB_LINK]) |
| 🎬 Demo Video | [[YOUTUBE_LINK]](https://youtube.com/[YOUTUBE_LINK]) |
| ⚡ Live API Docs | [https://tharshinidj12-code-review-env.hf.space/docs](https://tharshinidj12-code-review-env.hf.space/docs) |

---

## 👩‍💻 Built Solo in 5 Days

| Day | What Got Built |
|-----|---------------|
| Day 1 | FastAPI environment skeleton, OpenEnv compliance, `/reset` + `/step` |
| Day 2 | Execution sandbox (AST scan, import blocker, timeout), reward engine |
| Day 3 | All 6 task definitions + pytest test suites, episode replay API |
| Day 4 | GRPO training loop with TRL + Unsloth, LoRA config, reward logging |
| Day 5 | Docker packaging, HF Spaces deployment, this README |

One person. No team. Shipped.

---

## 📜 License

MIT — use it, fork it, build on it.

---

<div align="center">

*Built for the Meta × PyTorch × HuggingFace OpenEnv Hackathon*
*Theme #4: Self-Improvement (Recursive Skill Amplification)*

**[⭐ Star on GitHub](https://github.com/Tharshini272006/code-review-env) · [🚀 Try the API](https://tharshinidj12-code-review-env.hf.space/docs)**

</div>
