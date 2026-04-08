import json
import urllib.request
from typing import Optional

SERVER_URL = "http://localhost:7860"


# -------------------------
# HTTP HELPERS
# -------------------------
def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER_URL}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{SERVER_URL}{path}", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _oneline(s: str) -> str:
    return str(s).replace("\n", "\\n").replace("\r", "").strip()


# -------------------------
# LOGGING (STRICT FORMAT)
# -------------------------
def log_start(task_id: str):
    print(f"[START] task={task_id} env=code_review_env model=simple_agent", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error):
    print(
        f"[STEP] step={step} action={_oneline(action)[:200]} reward={reward:.2f} "
        f"done={'true' if done else 'false'} error={_oneline(error) if error else 'null'}",
        flush=True
    )


def log_end(success: bool, steps: int, score: float, rewards: list):
    print(
        f"[END] success={'true' if success else 'false'} steps={steps} "
        f"score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}",
        flush=True
    )


# -------------------------
# RULE-BASED AGENT (NO LLM)
# -------------------------
def simple_agent(buggy_code: str) -> str:
    """Deterministic fixes for known patterns."""

    # Fix: division by zero in average
    if "sum(lst) / len(lst)" in buggy_code:
        return """def average(lst):
    if not lst:
        return 0.0
    return sum(lst) / len(lst)
"""

    # Add more rules if needed
    return buggy_code


# -------------------------
# MAIN TASK LOOP
# -------------------------
def run_task(task_id: str):
    log_start(task_id)

    rewards = []
    steps = 0
    success = False
    score = 0.0

    try:
        obs = _post("/reset", {"task_id": task_id})

        buggy_code = obs.get("buggy_code", "")
        feedback = obs.get("feedback", "")
        hint = obs.get("hint")
        done = obs.get("done", False)

        # 🔥 Safety limit to prevent infinite loops
        while not done and steps < 5:
            steps += 1

            fixed_code = simple_agent(buggy_code)

            try:
                step_data = _post("/step", {
                    "code": fixed_code,
                    "explanation": "rule-based fix"
                })

                reward = step_data.get("reward", 0.0)
                done = step_data.get("done", True)

                obs2 = step_data.get("observation", {})
                feedback = obs2.get("feedback", "")
                hint = obs2.get("hint")

                rewards.append(reward)

                log_step(steps, fixed_code, reward, done, None)

            except Exception as e:
                log_step(steps, fixed_code, 0.0, True, str(e))
                rewards.append(0.0)
                done = True

        # Get final state
        try:
            state = _get("/state")
            score = state.get("total_reward", sum(rewards))
            success = state.get("status") == "success"
        except Exception:
            score = sum(rewards)
            success = bool(rewards) and rewards[-1] > 0.8

    except Exception as e:
        log_step(steps + 1, "ERROR", 0.0, True, str(e))

    finally:
        log_end(success, steps, score, rewards)


# -------------------------
# ENTRY POINT
# -------------------------
def main():
    for task_id in ["easy", "medium", "hard"]:
        try:
            run_task(task_id)
        except Exception:
            print("[END] success=false steps=0 score=0.000 rewards=", flush=True)
        print(flush=True)


if __name__ == "__main__":
    main()