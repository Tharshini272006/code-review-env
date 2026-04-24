"""
self_play_loop.py
=================
Master training loop for CodeReviewEnv — ties EVERYTHING together.

Components wired up:
  ┌─────────────────────┐
  │  bug_generator.py   │  ← generates fresh buggy challenge per episode
  └────────┬────────────┘
           │ challenge dict
  ┌────────▼────────────┐
  │   /reset + /step    │  ← pushes challenge into env server, runs agent
  │   (inference loop)  │
  └────────┬────────────┘
           │ reward
  ┌────────▼────────────┐
  │difficulty_escalator │  ← records reward, decides next difficulty level
  └────────┬────────────┘
           │ progress.json + reward_history.json
  ┌────────▼────────────┐
  │   reward_history    │  ← saved for dashboard.py to plot live
  └─────────────────────┘

Usage:
    python self_play_loop.py
    python self_play_loop.py --episodes 30 --server http://localhost:7860
    python self_play_loop.py --episodes 20 --resume        # resumes from progress.json
    python self_play_loop.py --episodes 10 --dry-run       # no env server needed (mock rewards)
"""

import os
import json
import time
import argparse
import urllib.request
from typing import Optional, List
from openai import OpenAI

# ── local modules ────────────────────────────────────────────────────────────
from bug_generator import generate_bug_challenge
from difficulty_escalator import DifficultyEscalator

# ── env/LLM config (mirrors inference.py) ────────────────────────────────────
API_KEY      = os.getenv("HF_TOKEN") or os.getenv("API_KEY", "")
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME   = os.getenv("MODEL_NAME",   "Qwen/Qwen2.5-72B-Instruct")
SERVER_URL   = os.getenv("SERVER_URL",   "http://localhost:7860")

client_llm = OpenAI(api_key=API_KEY, base_url=API_BASE_URL)

REWARD_HISTORY_PATH = "reward_history.json"
PROGRESS_PATH       = "progress.json"

# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers  (same pattern as inference.py)
# ─────────────────────────────────────────────────────────────────────────────

def _post(server: str, path: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        f"{server}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get(server: str, path: str) -> dict:
    req = urllib.request.Request(f"{server}{path}", method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


def server_alive(server: str) -> bool:
    try:
        _get(server, "/state")
        return True
    except Exception:
        return False

# ─────────────────────────────────────────────────────────────────────────────
# LLM agent  (same SYSTEM_PROMPT logic as inference.py)
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert Python engineer. You will be given a buggy Python function.
Return ONLY the complete corrected function. No explanation, no markdown, no extra text."""


def call_llm(buggy_code: str, task_description: str,
             feedback: str, hint: Optional[str]) -> str:
    user_msg = f"""Task: {task_description}

Buggy code:
{buggy_code}

Previous feedback: {feedback or 'None'}
Hint: {hint or 'None'}

Return ONLY the corrected Python function."""
    try:
        resp = client_llm.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            max_tokens=512,
            temperature=0.2,
        )
        code = resp.choices[0].message.content.strip()
        # Strip markdown fences if present
        if code.startswith("`"):
            lines = code.split("\n")
            code = "\n".join(lines[1:-1]) if lines[-1].strip() == "`" else "\n".join(lines[1:])
        return code
    except Exception as e:
        print(f"  [LLM] Error: {e}")
        return buggy_code

# ─────────────────────────────────────────────────────────────────────────────
# One episode: push challenge → run agent → return final reward
# ─────────────────────────────────────────────────────────────────────────────

def run_episode(challenge: dict, server: str, dry_run: bool = False) -> float:
    """
    Push the LLM-generated challenge into the env server and let the agent fix it.
    Returns the final cumulative reward for this episode.

    dry_run=True skips the server entirely — returns a mock reward for testing.
    """
    buggy_code       = challenge["buggy_code"]
    task_description = challenge["description"]
    hint_from_gen    = challenge.get("hint")

    if dry_run:
        import random
        mock_reward = round(random.uniform(0.2, 1.0), 3)
        print(f"  [DryRun] Skipping env server. Mock reward = {mock_reward}")
        return mock_reward

    rewards: List[float] = []

    try:
        # ── Reset env ────────────────────────────────────────────────────────
        # Pass difficulty as task_id so the server initialises the right episode.
        # If your server supports injecting custom buggy_code via /reset payload,
        # add "buggy_code": buggy_code here and update the server route.
        obs_data = _post(server, "/reset", {"task_id": challenge.get("difficulty", "easy")})

        # Prefer generated challenge values; fall back to server obs if needed
        buggy_code       = obs_data.get("buggy_code") or buggy_code
        task_description = obs_data.get("task_description") or task_description
        feedback         = obs_data.get("feedback", "")
        hint             = obs_data.get("hint") or hint_from_gen
        done             = obs_data.get("done", False)

        # ── Step loop ────────────────────────────────────────────────────────
        step = 0
        while not done:
            step += 1
            fixed_code = call_llm(buggy_code, task_description, feedback, hint)

            try:
                step_data = _post(server, "/step", {
                    "code": fixed_code,
                    "explanation": "LLM fix"
                })
                reward   = step_data["reward"]
                done     = step_data["done"]
                obs      = step_data["observation"]
                feedback = obs.get("feedback", "")
                hint     = obs.get("hint") or hint_from_gen
                rewards.append(reward)
                print(f"  [Step {step}] reward={reward:.3f}  done={done}")
            except Exception as e:
                print(f"  [Step {step}] env error: {e}")
                rewards.append(0.0)
                done = True

        # ── Final score from /state ───────────────────────────────────────────
        try:
            state_data  = _get(server, "/state")
            final_score = state_data.get("total_reward", sum(rewards))
        except Exception:
            final_score = sum(rewards) / len(rewards) if rewards else 0.0

        return round(final_score, 4)

    except Exception as e:
        print(f"  [Episode] Fatal error: {e}")
        return 0.0

# ─────────────────────────────────────────────────────────────────────────────
# Reward history persistence  (dashboard.py reads reward_history.json)
# ─────────────────────────────────────────────────────────────────────────────

def save_reward_history(history: list, path: str = REWARD_HISTORY_PATH):
    with open(path, "w") as f:
        json.dump(history, f, indent=2)


def load_reward_history(path: str = REWARD_HISTORY_PATH) -> list:
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return []

# ─────────────────────────────────────────────────────────────────────────────
# Print helpers
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════╗
║          🤖  SELF-PLAY TRAINING LOOP  🤖              ║
║          CodeReviewEnv — OpenEnv Hackathon           ║
╚══════════════════════════════════════════════════════╝"""


def print_episode_header(ep: int, total: int, challenge: dict):
    diff  = challenge.get("difficulty", "?").upper()
    fname = challenge.get("function_name", "?")
    btype = challenge.get("bug_type", "?")
    print(f"\n{'━'*56}")
    print(f"  Episode {ep}/{total}  |  {diff}  |  fn: {fname}  |  bug: {btype}")
    print(f"{'━'*56}")


def print_final_summary(escalator: DifficultyEscalator):
    summary = escalator.state.summary()
    print(f"\n{'═'*56}")
    print("  🏁  TRAINING COMPLETE")
    print(f"{'═'*56}")
    print(f"  Total Episodes  : {summary['total_episodes']}")
    print(f"  Final Difficulty: {summary['current_difficulty'].upper()}")
    print(f"  Avg Reward Easy : {summary['avg_easy']:.3f}")
    print(f"  Avg Reward Med  : {summary['avg_medium']:.3f}")
    print(f"  Avg Reward Hard : {summary['avg_hard']:.3f}")
    print(f"\n  Reward Curve:")
    for entry in summary["reward_history"]:
        bar  = "█" * int(entry["reward"] * 24)
        diff = entry["difficulty"][:3].upper()
        print(f"    Ep{entry['episode']:03d} [{diff}] {bar:<24} {entry['reward']:.3f}")
    print(f"{'═'*56}\n")

# ─────────────────────────────────────────────────────────────────────────────
# MAIN LOOP
# ─────────────────────────────────────────────────────────────────────────────

def self_play_loop(
    episodes:   int  = 20,
    server:     str  = SERVER_URL,
    resume:     bool = False,
    dry_run:    bool = False,
    save_every: int  = 5,
):
    print(BANNER)

    # ── Init escalator ────────────────────────────────────────────────────────
    escalator      = DifficultyEscalator()
    reward_history = []

    if resume:
        escalator.load_progress(PROGRESS_PATH)
        reward_history = load_reward_history(REWARD_HISTORY_PATH)
        print(f"[Loop] Resumed from episode {escalator.state.total_episodes}")

    # ── Check server ──────────────────────────────────────────────────────────
    if not dry_run:
        if server_alive(server):
            print(f"[Loop] ✅ Env server reachable at {server}")
        else:
            print(f"[Loop] ⚠️  Server at {server} is not reachable.")
            print(f"[Loop]    Start the server first, or re-run with --dry-run")
            return

    # ── Episode loop ──────────────────────────────────────────────────────────
    print(f"[Loop] Starting {episodes} episodes  |  dry_run={dry_run}\n")

    for ep in range(1, episodes + 1):

        # 1. Escalator calls bug_generator and returns the next challenge
        challenge = escalator.get_next_challenge()
        print_episode_header(ep, episodes, challenge)
        print(f"  Description : {challenge['description']}")
        print(f"  Hint        : {challenge.get('hint', 'N/A')}")

        # 2. Run agent in the env; get episode reward
        t0      = time.time()
        reward  = run_episode(challenge, server, dry_run=dry_run)
        elapsed = time.time() - t0
        print(f"  ✔ Episode reward = {reward:.4f}  ({elapsed:.1f}s)")

        # 3. Feed reward back into escalator → get escalation decision
        decision = escalator.record_reward(reward)

        # 4. Append rich entry to reward_history (dashboard reads this)
        reward_history.append({
            "episode":    escalator.state.total_episodes,
            "reward":     reward,
            "difficulty": challenge["difficulty"],
            "function":   challenge["function_name"],
            "bug_type":   challenge.get("bug_type", "unknown"),
            "action":     decision["action"],   # escalate | stay | hint | mastered
        })

        # 5. Periodic checkpoint
        if ep % save_every == 0:
            escalator.save_progress(PROGRESS_PATH)
            save_reward_history(reward_history, REWARD_HISTORY_PATH)
            print(f"  [Loop] 💾 Checkpoint saved at episode {ep}")

    # ── Final save ────────────────────────────────────────────────────────────
    escalator.save_progress(PROGRESS_PATH)
    save_reward_history(reward_history, REWARD_HISTORY_PATH)

    print_final_summary(escalator)
    print(f"[Loop] reward_history.json → ready for dashboard.py 📈")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Self-Play Training Loop — CodeReviewEnv"
    )
    parser.add_argument(
        "--episodes",   type=int, default=20,
        help="Number of training episodes (default: 20)"
    )
    parser.add_argument(
        "--server",     type=str, default=SERVER_URL,
        help="Env server URL (default: http://localhost:7860)"
    )
    parser.add_argument(
        "--resume",     action="store_true",
        help="Resume training from saved progress.json"
    )
    parser.add_argument(
        "--dry-run",    action="store_true",
        help="Skip env server, use mock rewards (safe for testing)"
    )
    parser.add_argument(
        "--save-every", type=int, default=5,
        help="Checkpoint every N episodes (default: 5)"
    )
    args = parser.parse_args()

    self_play_loop(
        episodes   = args.episodes,
        server     = args.server,
        resume     = args.resume,
        dry_run    = args.dry_run,
        save_every = args.save_every,
    )