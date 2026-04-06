# tests/test_environment.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.environment import CodeReviewEnvironment
from models import Action


class TestEnvironment:
    def setup_method(self):
        self.env = CodeReviewEnvironment()

    def test_reset_returns_observation(self):
        obs = self.env.reset("easy")
        assert obs is not None
        assert obs.task_id == "easy"
        assert obs.done == False
        assert obs.attempt_number == 0

    def test_reset_medium(self):
        obs = self.env.reset("medium")
        assert obs.max_attempts == 3

    def test_reset_hard(self):
        obs = self.env.reset("hard")
        assert obs.max_attempts == 5

    def test_step_without_reset_raises(self):
        env = CodeReviewEnvironment()
        try:
            env.step(Action(code="def f(): pass"))
            assert False
        except RuntimeError:
            pass

    def test_step_returns_result(self):
        self.env.reset("easy")
        result = self.env.step(Action(
            code="def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"
        ))
        assert result is not None
        assert result.reward >= 0.0
        assert result.done == True

    def test_perfect_score_easy(self):
        self.env.reset("easy")
        result = self.env.step(Action(
            code="def average(lst):\n    if not lst:\n        return 0.0\n    return sum(lst)/len(lst)"
        ))
        assert result.reward == 1.0

    def test_state_updates(self):
        self.env.reset("easy")
        self.env.step(Action(code="def average(lst):\n    if not lst: return 0.0\n    return sum(lst)/len(lst)"))
        state = self.env.state()
        assert state.step_count == 1
        assert state.total_reward > 0

    def test_episode_done_after_max_attempts(self):
        self.env.reset("easy")
        result = self.env.step(Action(code="def average(lst): return 0.0"))
        assert result.done == True

    def test_reward_in_valid_range(self):
        self.env.reset("medium")
        result = self.env.step(Action(code="def fibonacci(n): return 0"))
        assert 0.0 <= result.reward <= 1.0