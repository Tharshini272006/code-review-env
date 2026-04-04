# CodeReviewEnv 🐛→✅

**OpenEnv RL environment** — An AI agent receives a Python function containing a deliberate bug, analyzes it, and submits a fixed version. The environment executes the fix against hidden test cases and returns partial rewards at every step.

Built for the **Meta × PyTorch × HuggingFace OpenEnv Hackathon (Scaler)**.

---

## Tasks

| ID | Name | Difficulty | Max Attempts | Bug Type |
|----|------|-----------|-------------|----------|
| `easy` | syntax_fix | ⭐ Easy | 1 | Missing empty-list guard → ZeroDivisionError |
| `medium` | logic_fix | ⭐⭐ Medium | 3 | Wrong initial values in Fibonacci → wrong output |
| `hard` | refactor_and_fix | ⭐⭐⭐ Hard | 5 | Hardcoded magic number + wrong array size in Sieve + no validation |

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
  "last_execution_output": "",
  "feedback": "✅ Code executed. Tests passed: 3/3.",
  "hint": "Think about what happens when the list is empty.",
  "reward": 1.0,
  "done": true
}
```

---

## Reward Structure

| Component | Weight | Tasks |
|-----------|--------|-------|
| Code executes without error | +0.20 | all |
| Tests passed (proportional) | +0.30–0.80 | all |
| Input validation present | +0.20 | hard |
| No magic numbers | +0.20 | hard |
| Code quality score | +0.20 | hard |

- **Attempt penalty**: ×0.90 per attempt after the first
- **Range**: clamped to [0.0, 1.0]

---

## Baseline Scores (random/no-fix agent)

| Task | Expected Score |
|------|---------------|
| easy | ~0.0 (crashes or wrong) |
| medium | ~0.0–0.10 |
| hard | ~0.0 |

A correct LLM agent should achieve **0.80–1.0** on all tasks.

---

## Setup & Run

### Local (without Docker)
```bash
# 1. Install deps
pip install -r requirements.txt
pip install -r server/requirements.txt

# 2. Start server
uvicorn server.app:app --host 0.0.0.0 --port 7860 --reload

# 3. Test endpoints
curl http://localhost:7860/health
curl -X POST http://localhost:7860/reset -H "Content-Type: application/json" -d '{"task_id":"easy"}'

# 4. Run inference
export HF_TOKEN=hf_...
python inference.py
```

### Docker
```bash
docker build -t code-review-env -f server/Dockerfile .
docker run -p 7860:7860 -e HF_TOKEN=$HF_TOKEN code-review-env
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/tasks` | List all 3 tasks |
| POST | `/reset` | Start new episode `{"task_id": "easy"}` |
| POST | `/step` | Submit fix `{"code": "...", "explanation": "..."}` |
| GET | `/state` | Current episode state |
| POST | `/grader` | Grade code without full episode |
| GET | `/docs` | Swagger UI |

---

## Inference Output Format
```
[START] task=easy env=code_review_env model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=def average(lst):... reward=1.00 done=true error=null
[END] success=true steps=1 score=1.000 rewards=1.00
```