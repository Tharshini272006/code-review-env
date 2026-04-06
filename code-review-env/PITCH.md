# CodeReviewEnv — 3-Minute Pitch

## The Problem

Every day, developers push buggy code that crashes in production.
Code review is slow, expensive, and inconsistent.
Current AI assistants suggest fixes but can't VERIFY them.

## Our Solution

**CodeReviewEnv** — the first RL environment where AI agents
learn to find AND verify Python bug fixes by actually executing code.

Unlike simulations that fake results, we:
- 🔥 ACTUALLY execute submitted code in a sandbox
- 🔥 ACTUALLY run hidden test cases
- 🔥 ACTUALLY measure code quality via AST analysis
- 🔥 Give REAL partial rewards at every step

## Why This Matters

| Metric | Traditional Review | CodeReviewEnv Agent |
|---|---|---|
| Speed | Hours | Seconds |
| Consistency | Variable | Deterministic |
| Coverage | ~60% | 100% of test cases |
| Learning | None | Improves with RL |

## What Makes Us Unique

### Real Code Execution Sandbox
```python
reward = executes(+0.20)
+ tests_passed(+0.30-0.80)
+ code_quality(+0.20)
× attempt_penalty(0.90)

### Proven Agent Performance
| Task | Score |
|---|---|
| easy | 1.000 ✅ |
| medium | 1.000 ✅ |
| medium2 | 1.000 ✅ |
| hard | 0.950 ✅ |
| hard2 | 1.000 ✅ |
**Average: 0.990/1.0**

## Real World Impact

- Train AI code reviewers that actually RUN the code
- Reduce production bugs by catching them in review
- Build agents that understand code correctness, not just syntax
- Direct application to GitHub Copilot, code review bots

## Technical Stack

- FastAPI + Docker + HuggingFace Spaces
- Sandboxed Python execution (blocked dangerous imports)
- AST-based code quality analysis
- OpenAI-compatible LLM interface
- Pydantic typed models — full OpenEnv spec compliance

## Live Demo
```bash
curl https://tharshinidj12-code-review-env.hf.space/health
# {"status":"ok"}

curl -X POST https://tharshinidj12-code-review-env.hf.space/reset \
  -d '{"task_id":"easy"}'
# Returns buggy code for agent to fix

curl -X POST https://tharshinidj12-code-review-env.hf.space/step \
  -d '{"code":"def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"}'
# {"reward": 1.0, "done": true}
```

## Built Solo in 5 Days 🏆

*CodeReviewEnv — Where AI learns to write correct code.*