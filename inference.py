import subprocess, sys
subprocess.check_call([sys.executable, "-m", "pip", "install", "openai>=1.30.0", "-q"])

import os
import json
import urllib.request
from openai import OpenAI
from typing import List, Optional

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:7860")

client_llm = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)


def _post(path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{SERVER_URL}{path}", data=data,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(path: str) -> dict:
    with urllib.request.urlopen(f"{SERVER_URL}{path}", timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _oneline(s: str) -> str:
    return s.replace("\n", "\\n").replace("\r", "").strip()


def log_start(task_id: str):
    print(f"[START] task={task_id} env=code_review_env model={MODEL_NAME}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error):
    print(f"[STEP] step={step} action={_oneline(action)[:200]} reward={reward:.2f} done={'true' if done else 'false'} error={_oneline(error) if error else 'null'}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards):
    print(f"[END] success={'true' if success else 'false'} steps={steps} score={score:.3f} rewards={','.join(f'{r:.2f}' for r in rewards)}", flush=True)


SYSTEM_PROMPT = "You are an expert Python engineer. Return ONLY the complete corrected function. No explanation, no markdown."


def call_llm(buggy_code, task_description, feedback, hint):
    try:
        response = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Task: {task_description}\n\nBuggy code:\n{buggy_code}\n\nFeedback: {feedback or 'None'}\nHint: {hint or 'None'}\n\nReturn ONLY the fixed function."},
            ],
            max_tokens=512, temperature=0.2,
        )
        code = response.choices[0].message.content.strip()
        if code.startswith("`"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]) if lines[-1].strip() == "`" else "\n".join(lines[1:])
        return code
    except Exception:
        return buggy_code


def run_task(task_id):
    log_start(task_id)
    rewards, steps, success, score = [], 0, False, 0.0
    try:
        obs = _post("/reset", {"task_id": task_id})
        done = obs.get("done", False)
        buggy_code = obs["buggy_code"]
        task_description = obs["task_description"]
        feedback = obs.get("feedback", "")
        hint = obs.get("hint")
        while not done:
            steps += 1
            fixed_code = call_llm(buggy_code, task_description, feedback, hint)
            try:
                step_data = _post("/step", {"code": fixed_code, "explanation": "LLM fix"})
                reward = step_data["reward"]
                done = step_data["done"]
                obs2 = step_data["observation"]
                feedback = obs2.get("feedback", "")
                hint = obs2.get("hint")
                rewards.append(reward)
                log_step(steps, fixed_code, reward, done, None)
            except Exception as e:
                log_step(steps, fixed_code, 0.0, True, str(e))
                done = True
                rewards.append(0.0)
        try:
            state = _get("/state")
            score = state.get("total_reward", sum(rewards))
            success = state.get("status") == "success"
        except Exception:
            score = sum(rewards)
            success = bool(rewards) and rewards[-1] > 0.8
    except Exception as e:
        log_step(steps + 1, "", 0.0, True, str(e))
    finally:
        log_end(success, steps, score, rewards)


def main():
    for task_id in ["easy", "medium", "hard"]:
        try:
            run_task(task_id)
        except Exception:
            print(f"[END] success=false steps=0 score=0.000 rewards=", flush=True)
        print(flush=True)


if __name__ == "__main__":
    main()
