import os
import json
import urllib.request
from typing import List, Optional

# Constants
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL = os.getenv("SERVER_URL", "https://tharshinidj12-code-review-env.hf.space")

def _post(url: str, payload: dict, headers: dict = None) -> dict:
    if headers is None:
        headers = {"Content-Type": "application/json"}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _get(path: str) -> dict:
    req = urllib.request.Request(f"{SERVER_URL}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _oneline(s: str) -> str:
    return s.replace("\n", "\\n").replace("\r", "").strip()

# --- Logging helpers remain the same ---
def log_start(task_id: str):
    print(f"[START] task={task_id} env=code_review_env model={MODEL_NAME}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]):
    action_safe = _oneline(action)[:200]
    done_str = "true" if done else "false"
    error_str = _oneline(error) if error else "null"
    print(f"[STEP] step={step} action={action_safe} reward={reward:.2f} done={done_str} error={error_str}", flush=True)

def log_end(success: bool, steps: int, score: float, rewards: List[float]):
    success_str = "true" if success else "false"
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={success_str} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

SYSTEM_PROMPT = """You are an expert Python engineer. You will be given a buggy Python function.
Return ONLY the complete corrected function. No explanation, no markdown, no extra text."""

def call_llm(buggy_code: str, task_description: str, feedback: str, hint: Optional[str]) -> str:
    user_msg = f"Task: {task_description}\n\nBuggy code:\n{buggy_code}\n\nPrevious feedback: {feedback or 'None'}\nHint: {hint or 'None'}\n\nReturn ONLY the corrected Python function."
    
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
        "max_tokens": 512,
        "temperature": 0.2,
    }
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        # Using urllib to avoid OpenAI dependency
        resp_data = _post(f"{API_BASE_URL}/chat/completions", payload, headers)
        code = resp_data["choices"][0]["message"]["content"].strip()
        
        # Strip markdown backticks if the model includes them
        if code.startswith("```python"):
            code = code.split("```python")[1].split("```")[0].strip()
        elif code.startswith("```"):
            code = code.split("```")[1].split("```")[0].strip()
        return code
    except Exception as e:
        return buggy_code

# --- run_task and main remain the same ---
def run_task(task_id: str) -> dict:
    log_start(task_id)
    rewards: List[float] = []
    steps = 0
    success = False
    score = 0.0
    try:
        obs_data = _post(f"{SERVER_URL}/reset", {"task_id": task_id})
        done = obs_data.get("done", False)
        buggy_code = obs_data["buggy_code"]
        task_description = obs_data["task_description"]
        feedback = obs_data.get("feedback", "")
        hint = obs_data.get("hint")
        
        while not done and steps < 5: # Added a safety cap for steps
            steps += 1
            error_str = None
            fixed_code = call_llm(buggy_code, task_description, feedback, hint)
            
            try:
                step_data = _post(f"{SERVER_URL}/step", {"code": fixed_code, "explanation": "LLM fix"})
                reward = step_data["reward"]
                done = step_data["done"]
                obs = step_data["observation"]
                feedback = obs.get("feedback", "")
                hint = obs.get("hint")
                rewards.append(reward)
                log_step(steps, fixed_code, reward, done, error_str)
            except Exception as e:
                log_step(steps, fixed_code, 0.0, True, str(e))
                done = True
                rewards.append(0.0)
        
        state_data = _get("/state")
        score = state_data.get("total_reward", sum(rewards))
        success = state_data.get("status") == "success"
    except Exception as e:
        log_step(steps + 1, "", 0.0, True, str(e))
    finally:
        log_end(success, steps, score, rewards)
    return {"task_id": task_id, "success": success, "steps": steps, "score": score}

def main():
    for task_id in ["easy", "medium", "hard"]:
        try:
            run_task(task_id)
        except Exception:
            print(f"[END] success=false steps=0 score=0.000 rewards=", flush=True)

if __name__ == "__main__":
    main()