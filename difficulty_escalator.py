"""
difficulty_escalator.py
Watches reward scores and auto-escalates difficulty.
The heart of Theme 4 - Self Improvement Loop.
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional
from bug_generator import generate_bug_challenge

# ─── Thresholds ─────────────────────────────────────────────────────────────

ESCALATE_THRESHOLD = 0.85    # reward > this → go harder
DEESCALATE_THRESHOLD = 0.3   # reward < this → give hint / stay same
PASS_STREAK_NEEDED = 2       # need 2 wins in a row to escalate

DIFFICULTY_ORDER = ["easy", "medium", "hard"]

# ─── State ──────────────────────────────────────────────────────────────────

@dataclass
class EscalatorState:
    current_difficulty: str = "easy"
    episode: int = 0
    total_episodes: int = 0

    # per-difficulty stats
    rewards_easy: List[float] = field(default_factory=list)
    rewards_medium: List[float] = field(default_factory=list)
    rewards_hard: List[float] = field(default_factory=list)

    # streak tracking
    win_streak: int = 0
    fail_streak: int = 0

    # full history for reward curve
    reward_history: List[dict] = field(default_factory=list)

    def log_reward(self, reward: float, difficulty: str):
        self.total_episodes += 1
        self.reward_history.append({
            "episode": self.total_episodes,
            "reward": reward,
            "difficulty": difficulty
        })
        if difficulty == "easy":
            self.rewards_easy.append(reward)
        elif difficulty == "medium":
            self.rewards_medium.append(reward)
        elif difficulty == "hard":
            self.rewards_hard.append(reward)

        if reward >= ESCALATE_THRESHOLD:
            self.win_streak += 1
            self.fail_streak = 0
        else:
            self.fail_streak += 1
            self.win_streak = 0

    def average_reward(self, difficulty: str = None) -> float:
        if difficulty is None:
            difficulty = self.current_difficulty
        rewards = getattr(self, f"rewards_{difficulty}", [])
        return round(sum(rewards) / len(rewards), 3) if rewards else 0.0

    def summary(self) -> dict:
        return {
            "current_difficulty": self.current_difficulty,
            "total_episodes": self.total_episodes,
            "win_streak": self.win_streak,
            "avg_easy": self.average_reward("easy"),
            "avg_medium": self.average_reward("medium"),
            "avg_hard": self.average_reward("hard"),
            "reward_history": self.reward_history,
        }


# ─── Escalator ──────────────────────────────────────────────────────────────

class DifficultyEscalator:
    """
    Watches rewards and decides:
    - escalate difficulty (agent is doing well)
    - stay same (agent needs more practice)
    - add hint (agent is struggling)
    """

    def __init__(self):
        self.state = EscalatorState()
        self._current_challenge = None

    def get_next_challenge(self) -> dict:
        """Get the next challenge based on current difficulty."""
        difficulty = self.state.current_difficulty
        print(f"\n[Escalator] 🎯 Generating {difficulty.upper()} challenge...")
        challenge = generate_bug_challenge(difficulty)
        self._current_challenge = challenge
        self.state.episode += 1
        return challenge

    def record_reward(self, reward: float) -> dict:
        """
        Record reward and decide next action.
        Returns a decision dict with: action, next_difficulty, message
        """
        difficulty = self.state.current_difficulty
        self.state.log_reward(reward, difficulty)

        decision = self._decide(reward, difficulty)
        self._apply_decision(decision)

        self._print_status(reward, decision)
        return decision

    def _decide(self, reward: float, difficulty: str) -> dict:
        current_idx = DIFFICULTY_ORDER.index(difficulty)

        # Agent is crushing it — escalate!
        if reward >= ESCALATE_THRESHOLD and self.state.win_streak >= PASS_STREAK_NEEDED:
            if current_idx < len(DIFFICULTY_ORDER) - 1:
                next_diff = DIFFICULTY_ORDER[current_idx + 1]
                return {
                    "action": "escalate",
                    "next_difficulty": next_diff,
                    "message": f"🚀 Escalating from {difficulty} → {next_diff}! Win streak: {self.state.win_streak}"
                }
            else:
                return {
                    "action": "mastered",
                    "next_difficulty": "hard",
                    "message": "🏆 Agent has MASTERED all difficulty levels!"
                }

        # Agent is doing okay — stay same level
        if reward >= ESCALATE_THRESHOLD and self.state.win_streak < PASS_STREAK_NEEDED:
            return {
                "action": "stay",
                "next_difficulty": difficulty,
                "message": f"✅ Good reward {reward:.3f}! Need {PASS_STREAK_NEEDED - self.state.win_streak} more wins to escalate."
            }

        # Agent is struggling — add hint, stay same
        if reward < DEESCALATE_THRESHOLD:
            return {
                "action": "hint",
                "next_difficulty": difficulty,
                "message": f"💡 Low reward {reward:.3f}. Providing hint and staying at {difficulty}."
            }

        # Medium performance — stay and keep trying
        return {
            "action": "stay",
            "next_difficulty": difficulty,
            "message": f"📊 Reward {reward:.3f}. Keep practicing at {difficulty} level."
        }

    def _apply_decision(self, decision: dict):
        self.state.current_difficulty = decision["next_difficulty"]

    def _print_status(self, reward: float, decision: dict):
        print(f"[Escalator] Reward: {reward:.3f} | {decision['message']}")
        print(f"[Escalator] Stats → Easy: {self.state.average_reward('easy'):.3f} | "
              f"Medium: {self.state.average_reward('medium'):.3f} | "
              f"Hard: {self.state.average_reward('hard'):.3f}")

    def get_reward_curve(self) -> List[dict]:
        """Returns full reward history for plotting."""
        return self.state.reward_history

    def save_progress(self, path: str = "progress.json"):
        """Save progress to file."""
        with open(path, "w") as f:
            json.dump(self.state.summary(), f, indent=2)
        print(f"[Escalator] 💾 Progress saved to {path}")

    def load_progress(self, path: str = "progress.json"):
        """Load progress from file."""
        if os.path.exists(path):
            with open(path) as f:
                data = json.load(f)
            self.state.current_difficulty = data.get("current_difficulty", "easy")
            self.state.total_episodes = data.get("total_episodes", 0)
            self.state.reward_history = data.get("reward_history", [])
            print(f"[Escalator] 📂 Loaded progress: {self.state.total_episodes} episodes done")


# ─── Quick test ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("📈 Testing Difficulty Escalator...\n")

    escalator = DifficultyEscalator()

    # Simulate a training run with fake rewards
    fake_rewards = [0.4, 0.6, 0.9, 0.92, 0.95, 0.88, 0.3, 0.91, 0.93, 0.96]

    for i, reward in enumerate(fake_rewards):
        print(f"\n━━━ Episode {i+1} ━━━")
        challenge = escalator.get_next_challenge()
        print(f"[Escalator] Challenge: {challenge['function_name']} ({challenge['difficulty']})")
        decision = escalator.record_reward(reward)

    print("\n━━━ FINAL SUMMARY ━━━")
    summary = escalator.state.summary()
    print(f"Total Episodes : {summary['total_episodes']}")
    print(f"Final Difficulty: {summary['current_difficulty']}")
    print(f"Avg Easy       : {summary['avg_easy']}")
    print(f"Avg Medium     : {summary['avg_medium']}")
    print(f"Avg Hard       : {summary['avg_hard']}")
    print(f"\nReward Curve:")
    for entry in summary['reward_history']:
        bar = "█" * int(entry['reward'] * 20)
        print(f"  Ep{entry['episode']:02d} [{entry['difficulty']:6s}] {bar} {entry['reward']:.3f}")

    escalator.save_progress()