---
title: Code Review Env
emoji: 🐛
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
---

# CodeReviewEnv 🐛→✅

**Domain:** Real-world Code Review & Bug Fixing  
**Built for:** Meta × PyTorch × HuggingFace OpenEnv Hackathon (Scaler)

An AI agent receives a buggy Python function, identifies the bug, and submits a fixed version. The environment executes the fix against hidden test cases and returns partial rewards at every step.

---

## 3 Tasks

| ID | Name | Difficulty | Max Attempts | Bug Type |
|----|------|-----------|-------------|----------|
| `easy` | syntax_fix | ⭐ Easy | 1 | Missing empty-list guard → ZeroDivisionError |
| `medium` | logic_fix | ⭐⭐ Medium | 3 | Wrong initial values in Fibonacci |
| `hard` | refactor_and_fix | ⭐⭐⭐ Hard | 5 | Magic numbers + wrong array size + no validation |

---

## Reward Structure

| Component | Weight | Tasks |
|-----------|--------|-------|
| Code executes without error | +0.20 | all |
| Tests passed (proportional) | +0.30-0.80 | all |
| Input validation present | +0.20 | hard |
| No magic numbers | +0.20 | hard |
| Code quality score | +0.20 | hard |

- Attempt penalty: ×0.90 per attempt after the first
- Score clamped to [0.0, 1.0]

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check → `{"status":"ok"}` |
| GET | `/tasks` | List all 3 tasks |
| POST | `/reset` | Start episode `{"task_id":"easy"}` |
| POST | `/step` | Submit fix `{"code":"..."}` |
| GET | `/state` | Current episode state |
| POST | `/grader` | Grade without full episode |
| GET | `/docs` | Swagger UI |

---

## Action Space
```json
{
  "code": "def average(lst): ...",
  "explanation": "Added guard for empty list (optional)"
}
```

## Observation Space
```json
{
  "buggy_code": "def average(lst):\n    return sum(lst) / len(lst)",
  "task_description": "Fix the function...",
  "task_id": "easy",
  "attempt_number": 1,
  "max_attempts": 1,
  "feedback": "✅ Code executed. Tests passed: 3/3.",
  "hint": "Think about what happens when the list is empty.",
  "reward": 1.0,
  "done": true
}
```

---

## Baseline Scores (LLM agent)

| Task | Score |
|------|-------|
| easy | 1.000 |
| medium | 0.800 |
| hard | 0.950 |

---

## Inference Output Format