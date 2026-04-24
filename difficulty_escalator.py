"""
difficulty_escalator.py — Recursive Skill Amplification Engine
Tracks agent mastery per difficulty tier and escalates automatically.

Tiers:    easy → medium → hard → extreme (loops forever, LLM invents harder)
Escalate: avg reward ≥ 0.85 over 5-episode window AND 3 consecutive wins
Deescalate: avg reward < 0.30 over 5-episode window AND 3 consecutive losses
"""

import json
import os
from dataclasses import dataclass, field
from typing import List, Optional

ESCALATE_THRESHOLD   = 0.85
DEESCALATE_THRESHOLD = 0.30
WINDOW_SIZE          = 5
WIN_STREAK_NEEDED    = 3
LOSE_STREAK_NEEDED   = 3

DIFFICULTY_ORDER = ["easy", "medium", "hard", "extreme"]

DIFFICULTY_LABELS = {
    "easy":    "🟢 Easy",
    "medium":  "🟡 Medium",
    "hard":    "🔴 Hard",
    "extreme": "💀 Extreme",
}


@dataclass
class EscalatorState:
    current_difficulty: str = "easy"
    win_streak:  int = 0
    lose_streak: int = 0
    episode_count: int = 0

    rewards_easy:    List[float] = field(default_factory=list)
    rewards_medium:  List[float] = field(default_factory=list)
    rewards_hard:    List[float] = field(default_factory=list)
    rewards_extreme: List[float] = field(default_factory=list)
    reward_history:  List[dict]  = field(default_factory=list)

    def rewards_for(self, difficulty: str) -> List[float]:
        return {
            "easy":    self.rewards_easy,
            "medium":  self.rewards_medium,
            "hard":    self.rewards_hard,
            "extreme": self.rewards_extreme,
        }.get(difficulty, [])

    def avg(self, difficulty: str) -> float:
        rewards = self.rewards_for(difficulty)
        if not rewards:
            return 0.0
        window = rewards[-WINDOW_SIZE:]
        return sum(window) / len(window)

    def summary(self) -> dict:
        return {
            "current_difficulty": self.current_difficulty,
            "display_label": DIFFICULTY_LABELS[self.current_difficulty],
            "win_streak":   self.win_streak,
            "lose_streak":  self.lose_streak,
            "episode_count": self.episode_count,
            "avg_easy":    round(self.avg("easy"), 4),
            "avg_medium":  round(self.avg("medium"), 4),
            "avg_hard":    round(self.avg("hard"), 4),
            "avg_extreme": round(self.avg("extreme"), 4),
            "reward_history": list(self.reward_history),
        }


class DifficultyEscalator:
    """
    Tracks rewards per difficulty and decides escalate / deescalate / stay.
    At 'extreme', the loop never ends — LLM keeps inventing harder problems.
    """

    def __init__(self, save_path: str = "progress.json"):
        self.save_path = save_path
        self.state = EscalatorState()
        self._load()

    # ── Public API ────────────────────────────────────────────────────────────

    def get_next_challenge(self) -> dict:
        """Return a freshly LLM-generated challenge at current difficulty."""
        from bug_generator import generate_bug_challenge
        return generate_bug_challenge(self.state.current_difficulty)

    def record_reward(self, reward: float) -> dict:
        """
        Record episode reward, update streaks, decide next difficulty.
        Returns a decision dict for the dashboard to display.
        """
        diff = self.state.current_difficulty
        self.state.episode_count += 1
        ep = self.state.episode_count

        # Append to per-difficulty history
        self.state.rewards_for(diff).append(reward)
        self.state.reward_history.append({
            "episode":    ep,
            "reward":     round(reward, 4),
            "difficulty": diff,
        })

        avg = self.state.avg(diff)
        decision = self._decide(reward, avg, diff)
        self.save()
        return decision

    def save(self, path: Optional[str] = None):
        path = path or self.save_path
        try:
            with open(path, "w") as f:
                json.dump({
                    "current_difficulty": self.state.current_difficulty,
                    "win_streak":   self.state.win_streak,
                    "lose_streak":  self.state.lose_streak,
                    "episode_count": self.state.episode_count,
                    "rewards_easy":    self.state.rewards_easy,
                    "rewards_medium":  self.state.rewards_medium,
                    "rewards_hard":    self.state.rewards_hard,
                    "rewards_extreme": self.state.rewards_extreme,
                    "reward_history":  self.state.reward_history,
                }, f, indent=2)
        except Exception as e:
            print(f"⚠️  Could not save progress: {e}")

    # ── Internal ──────────────────────────────────────────────────────────────

    def _decide(self, reward: float, avg: float, diff: str) -> dict:
        idx = DIFFICULTY_ORDER.index(diff)

        # Update streaks
        if reward >= ESCALATE_THRESHOLD:
            self.state.win_streak  += 1
            self.state.lose_streak  = 0
        elif reward < DEESCALATE_THRESHOLD:
            self.state.lose_streak += 1
            self.state.win_streak   = 0
        else:
            self.state.win_streak  = 0
            self.state.lose_streak = 0

        # ESCALATE
        if avg >= ESCALATE_THRESHOLD and self.state.win_streak >= WIN_STREAK_NEEDED:
            self.state.win_streak = 0
            if idx < len(DIFFICULTY_ORDER) - 1:
                new = DIFFICULTY_ORDER[idx + 1]
                self.state.current_difficulty = new
                return {
                    "action": "escalate",
                    "message": f"🚀 Mastered {diff.upper()}! Escalating → {new.upper()}",
                    "new_difficulty": new,
                    "avg": avg,
                }
            else:
                # Already extreme — recursive amplification
                return {
                    "action": "amplify",
                    "message": "🧠 EXTREME mastered! LLM inventing ultra-hard custom challenge...",
                    "new_difficulty": "extreme",
                    "avg": avg,
                }

        # DE-ESCALATE
        if avg < DEESCALATE_THRESHOLD and self.state.lose_streak >= LOSE_STREAK_NEEDED:
            self.state.lose_streak = 0
            if idx > 0:
                new = DIFFICULTY_ORDER[idx - 1]
                self.state.current_difficulty = new
                return {
                    "action": "deescalate",
                    "message": f"📉 Struggling at {diff.upper()}. Stepping back → {new.upper()}",
                    "new_difficulty": new,
                    "avg": avg,
                }

        # HINT (very low reward)
        if reward < 0.4:
            return {
                "action": "hint",
                "message": f"💡 Low reward {reward:.3f}. Check the hint and try again.",
                "new_difficulty": diff,
                "avg": avg,
            }

        # STAY
        return {
            "action": "stay",
            "message": f"📊 Reward {reward:.3f} (avg {avg:.3f}). Keep pushing at {diff.upper()}.",
            "new_difficulty": diff,
            "avg": avg,
        }

    def _load(self):
        if not os.path.exists(self.save_path):
            return
        try:
            with open(self.save_path) as f:
                data = json.load(f)
            self.state.current_difficulty = data.get("current_difficulty", "easy")
            self.state.win_streak         = data.get("win_streak", 0)
            self.state.lose_streak        = data.get("lose_streak", 0)
            self.state.episode_count      = data.get("episode_count", 0)
            self.state.rewards_easy       = data.get("rewards_easy", [])
            self.state.rewards_medium     = data.get("rewards_medium", [])
            self.state.rewards_hard       = data.get("rewards_hard", [])
            self.state.rewards_extreme    = data.get("rewards_extreme", [])
            self.state.reward_history     = data.get("reward_history", [])
            print(f"✅ Progress loaded — currently at {self.state.current_difficulty.upper()}")
        except Exception as e:
            print(f"⚠️  Could not load progress: {e}")