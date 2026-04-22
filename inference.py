# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
import os
import json
import urllib.request
from typing import List, Optional

API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",  "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("SERVER_URL", "https://tharshinidj12-code-review-env.hf.space")

# ✅ No openai import at all — everything uses urllib (stdlib only)


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

def log_start(task_id: str):
    print(f"[START] task={task_id} env=code_review_env model={MODEL_NAME}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error):
    print(
        f"[STEP] step={step} action={_oneline(action)[:200]} reward={reward:.2f} "
        f"done={'true' if done else 'false'} error={_oneline(error) if error else 'null'}",
        flush=True
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    print(
        f"[END] success={'true' if success else 'false'} steps={steps} "
        f"score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}",
        flush=True
    )

SYSTEM_PROMPT = """You are an expert Python engineer doing code review. You will be given a buggy Python function. Fix ALL bugs including logic errors, off-by-one errors, and security issues. Remove BUG comments and fix the actual code. Return ONLY the complete corrected Python function with no explanation, no markdown, no backticks."""

Rules:
- Fix every bug. Do NOT return the same code. Do NOT keep BUG comments. Return ONLY the fixed function."""
- No explanation, no markdown, no extra text
- No code fences or backticks
- Keep the same function name and signature
- Fix ALL bugs you find
- Always add a clear docstring
- Never use magic numbers"""

def call_llm(buggy_code: str, task_description: str, feedback: str, hint: Optional[str]) -> str:
    user_msg = f"""Task: {task_description}

Buggy code to fix:
{buggy_code}

Previous attempt feedback: {feedback or "None"}
Hint: {hint or "None"}

Fix every bug. Do NOT return the same code. Return ONLY the fixed function."""

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        "max_tokens": 512,
        "temperature": 0.1,
    }
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{API_BASE_URL}/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        code = result["choices"][0]["message"]["content"].strip()
        if code.startswith("```"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return code.strip()
    except Exception:
        return buggy_code

def run_task(task_id: str) -> dict:
    log_start(task_id)
    rewards: List[float] = []
    steps = 0
    success = False
    score = 0.0
    try:
        obs = _post("/reset", {"task_id": task_id})
        buggy_code       = obs.get("buggy_code", "")
        task_description = obs.get("task_description", "Fix the buggy function.")
        feedback         = obs.get("feedback", "")
        hint             = obs.get("hint")
        done             = obs.get("done", False)

        while not done and steps < 10:
            steps += 1
            error_str = None
            try:
                fixed_code = call_llm(buggy_code, task_description, feedback, hint)
            except Exception as e:
                fixed_code = buggy_code
                error_str  = str(e)
            try:
                step_data = _post("/step", {"code": fixed_code, "explanation": "LLM fix"})
                reward   = step_data.get("reward", 0.0)
                done     = step_data.get("done", True)
                obs2     = step_data.get("observation", {})
                feedback = obs2.get("feedback", "")
                hint     = obs2.get("hint")
                rewards.append(reward)
                log_step(steps, fixed_code, reward, done, error_str)
                if not done:
                    buggy_code = fixed_code
            except Exception as e:
                log_step(steps, fixed_code, 0.0, True, str(e))
                rewards.append(0.0)
                done = True
        try:
            state   = _get("/state")
            score   = state.get("total_reward", sum(rewards))
            success = state.get("status") == "success"
        except Exception:
            score   = sum(rewards)
            success = bool(rewards) and rewards[-1] > 0.8
    except Exception as e:
        log_step(steps + 1, "ERROR", 0.0, True, str(e))
    finally:
        log_end(success, steps, score, rewards)
    return {"task_id": task_id, "success": success, "steps": steps, "score": score}

def main():
    for task_id in ["easy", "medium", "medium2", "hard", "hard2", "security"]:
        try:
            run_task(task_id)
        except Exception:
            print("[END] success=false steps=0 score=0.000 rewards=", flush=True)
        print(flush=True)

if __name__ == "__main__":
    main()