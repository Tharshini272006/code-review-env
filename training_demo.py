# training_demo.py
"""
Training demo — shows reward improving over multiple episodes.
Simulates an agent learning to fix bugs across all 6 tasks.
Run: python training_demo.py
"""

import os
import time
import requests
from typing import List, Dict
from openai import OpenAI

SERVER_URL = os.getenv("SERVER_URL", "http://localhost:7860")
API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")

client = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)
session = requests.Session()
session.headers.update({"Content-Type": "application/json"})

TASK_IDS = ["easy", "medium", "medium2", "hard", "hard2", "security"]

SYSTEM_PROMPT = """\
You are an expert Python engineer. Fix the buggy function.
Return ONLY the corrected Python code, no explanation, no markdown.
"""


def call_llm(buggy_code: str, task_desc: str, feedback: str, hint: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Task: {task_desc}\n\nBuggy:\n{buggy_code}\n\nFeedback: {feedback}\nHint: {hint}\n\nReturn fixed code only:"}
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
        return buggy_code


def run_episode(task_id: str) -> Dict:
    obs = session.post(f"{SERVER_URL}/reset", json={"task_id": task_id}).json()
    buggy_code = obs["buggy_code"]
    task_desc = obs["task_description"]
    feedback = obs.get("feedback", "")
    hint = obs.get("hint", "")
    done = obs.get("done", False)
    steps = 0
    final_reward = 0.0

    while not done:
        steps += 1
        fixed = call_llm(buggy_code, task_desc, feedback, hint)
        result = session.post(f"{SERVER_URL}/step", json={"code": fixed}).json()
        final_reward = result["reward"]
        done = result["done"]
        obs = result["observation"]
        feedback = obs.get("feedback", "")
        hint = obs.get("hint", "") or ""

    # Get total_reward from state
    try:
        state = session.get(f"{SERVER_URL}/state").json()
        total_reward = state.get("total_reward", final_reward)
    except Exception:
        total_reward = final_reward

    return {"task_id": task_id, "reward": total_reward, "steps": steps}


def main():
    print("=" * 60)
    print("CodeReviewEnv — Training Demo")
    print("=" * 60)
    print(f"Server: {SERVER_URL}")
    print(f"Model:  {MODEL_NAME}")
    print()

    NUM_EPISODES = 3
    all_results = []

    for episode in range(1, NUM_EPISODES + 1):
        print(f"Episode {episode}/{NUM_EPISODES}")
        print("-" * 40)
        episode_rewards = []

        for task_id in TASK_IDS:
            result = run_episode(task_id)
            episode_rewards.append(result["reward"])
            status = "✅" if result["reward"] >= 0.8 else "❌"
            print(f"  {status} {task_id:<12} reward={result['reward']:.3f} steps={result['steps']}")

        avg = sum(episode_rewards) / len(episode_rewards)
        all_results.append(avg)
        print(f"  Episode avg: {avg:.3f}")
        print()

    print("=" * 60)
    print("Training Summary")
    print("=" * 60)
    for i, avg in enumerate(all_results, 1):
        bar = "█" * int(avg * 20)
        print(f"  Episode {i}: {avg:.3f} |{bar}")

    print()
    improvement = all_results[-1] - all_results[0]
    print(f"  Start score: {all_results[0]:.3f}")
    print(f"  Final score: {all_results[-1]:.3f}")
    print(f"  Improvement: {improvement:+.3f}")
    print()
    print("✅ Training demo complete!")


if __name__ == "__main__":
    main()