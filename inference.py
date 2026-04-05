# inference.py
import os
import sys
from typing import List, Optional
import requests
from openai import OpenAI

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:7860")

client_llm = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

_session = requests.Session()
_session.headers.update({"Content-Type": "application/json"})


def _post(path: str, payload: dict) -> dict:
    r = _session.post(f"{SERVER_URL}{path}", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def _get(path: str) -> dict:
    r = _session.get(f"{SERVER_URL}{path}", timeout=10)
    r.raise_for_status()
    return r.json()


def _oneline(s: str) -> str:
    return s.replace("\n", "\\n").replace("\r", "").strip()


def log_start(task_id: str):
    print(f"[START] task={task_id} env=code_review_env model={MODEL_NAME}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    action_safe = _oneline(action)[:200]
    done_str = "true" if done else "false"
    error_str = _oneline(error) if error else "null"
    print(
        f"[STEP] step={step} action={action_safe} "
        f"reward={reward:.2f} done={done_str} error={error_str}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={success_str} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )


SYSTEM_PROMPT = """\
You are an expert Python engineer. You will be given a buggy Python function.
Your task is to identify the bug and return ONLY the complete corrected function.
Do NOT include any explanation, markdown, or extra text â€” ONLY the raw Python code.
The function must be syntactically valid and self-contained.
"""


def call_llm(buggy_code: str, task_description: str, feedback: str, hint: Optional[str]) -> str:
    user_msg = f"""\
Task: {task_description}

Buggy code:
```python
{buggy_code}
```

Previous feedback: {feedback or "None"}
Hint: {hint or "None"}

Return ONLY the corrected Python function, no explanation, no markdown fences.
"""
    try:
        response = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.2,
        )
        code = response.choices[0].message.content.strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return code
    except Exception as e:
        return f"# LLM error: {e}\n{buggy_code}"


def run_task(task_id: str) -> dict:
    log_start(task_id)
    rewards: List[float] = []
    steps = 0
    success = False
    score = 0.0

    try:
        obs_data = _post("/reset", {"task_id": task_id})
        done = obs_data.get("done", False)
        buggy_code = obs_data["buggy_code"]
        task_description = obs_data["task_description"]
        feedback = obs_data.get("feedback", "")
        hint = obs_data.get("hint")

        while not done:
            steps += 1
            error_str = None
            try:
                fixed_code = call_llm(buggy_code, task_description, feedback, hint)
            except Exception as e:
                fixed_code = buggy_code
                error_str = str(e)

            try:
                step_data = _post("/step", {"code": fixed_code, "explanation": "LLM fix"})
                reward = step_data["reward"]
                done = step_data["done"]
                obs = step_data["observation"]
                feedback = obs.get("feedback", "")
                hint = obs.get("hint")
                rewards.append(reward)
                log_step(steps, fixed_code, reward, done, error_str)
            except Exception as e:
                error_str = str(e)
                log_step(steps, fixed_code, 0.0, True, error_str)
                done = True
                rewards.append(0.0)

        try:
            state_data = _get("/state")
            score = state_data.get("total_reward", sum(rewards))
            success = state_data.get("status") == "success"
        except Exception:
            score = sum(rewards)
            success = bool(rewards) and rewards[-1] > 0.8

    except Exception as e:
        error_str = str(e)
        log_step(steps + 1, "", 0.0, True, error_str)
    finally:
        log_end(success, steps, score, rewards)

    return {"task_id": task_id, "success": success, "steps": steps, "score": score}


def main():
    task_ids = ["easy", "medium", "medium2", "hard", "hard2"]
    for task_id in task_ids:
        try:
            run_task(task_id)
        except Exception:
            print(f"[END] success=false steps=0 score=0.000 rewards=", flush=True)
        print(flush=True)


if __name__ == "__main__":
    main()