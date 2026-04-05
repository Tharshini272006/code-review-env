# server/environment.py
import uuid
from typing import Optional, List, Dict, Any

from models import Action, Observation, State, StepResult
from server.tasks import get_task, Task
from server.grader import grade


class CodeReviewEnvironment:
    def __init__(self):
        self._task: Optional[Task] = None
        self._state: Optional[State] = None
        self._current_obs: Optional[Observation] = None
        self._attempt: int = 0
        self._episode_history: List[Dict] = []
        self._all_episodes: Dict[str, List[Dict]] = {}

    def reset(self, task_id: str = "easy") -> Observation:
        task = get_task(task_id)
        self._task = task
        self._attempt = 0
        self._episode_history = []

        self._state = State(
            episode_id=str(uuid.uuid4()),
            task_id=task_id,
            step_count=0,
            max_steps=task.max_attempts,
            total_reward=0.0,
            status="running",
        )

        obs = Observation(
            buggy_code=task.buggy_code,
            task_description=task.description,
            task_id=task_id,
            attempt_number=0,
            max_attempts=task.max_attempts,
            last_execution_output="",
            feedback="Episode started. Analyze the buggy code and submit a fix.",
            hint=task.hint,
            reward=0.0,
            done=False,
        )
        self._current_obs = obs

        # Store episode start
        self._episode_history.append({
            "step": 0,
            "type": "reset",
            "task_id": task_id,
            "buggy_code": task.buggy_code,
            "action": None,
            "reward": 0.0,
            "feedback": obs.feedback,
            "done": False,
        })

        return obs

    def step(self, action: Action) -> StepResult:
        if self._task is None or self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if self._state.status != "running":
            raise RuntimeError(f"Episode already ended with status '{self._state.status}'.")

        self._attempt += 1
        self._state.step_count += 1

        grade_result = grade(self._task, action.code, attempt_number=self._attempt)

        if grade_result is None:
            grade_result = {
                "reward": 0.0,
                "breakdown": "grader error",
                "exec_result": {
                    "executes": False,
                    "exec_error": "grader returned None",
                    "stdout": "",
                    "results": [],
                    "tests_passed": 0,
                    "total_tests": 0,
                },
                "quality": None,
                "feedback": "Grader error occurred.",
            }

        reward = grade_result["reward"]
        feedback = grade_result["feedback"]
        exec_result = grade_result["exec_result"]

        self._state.total_reward = round(
            min(1.0, self._state.total_reward + reward), 4
        )

        all_passed = (
            exec_result["executes"]
            and exec_result["tests_passed"] == exec_result["total_tests"]
        )
        max_reached = self._attempt >= self._task.max_attempts
        done = all_passed or max_reached

        if done:
            self._state.status = "success" if all_passed else "failed"

        obs = Observation(
            buggy_code=self._task.buggy_code,
            task_description=self._task.description,
            task_id=self._task.task_id,
            attempt_number=self._attempt,
            max_attempts=self._task.max_attempts,
            last_execution_output=exec_result.get("stdout", ""),
            feedback=feedback,
            hint=self._task.hint if not all_passed else None,
            reward=reward,
            done=done,
        )
        self._current_obs = obs

        # Store step in history
        self._episode_history.append({
            "step": self._attempt,
            "type": "step",
            "action": action.code[:200],
            "explanation": action.explanation,
            "reward": reward,
            "feedback": feedback,
            "tests_passed": exec_result["tests_passed"],
            "total_tests": exec_result["total_tests"],
            "executes": exec_result["executes"],
            "done": done,
        })

        # Save completed episode
        if done:
            self._all_episodes[self._state.episode_id] = {
                "episode_id": self._state.episode_id,
                "task_id": self._task.task_id,
                "total_reward": self._state.total_reward,
                "steps": self._state.step_count,
                "status": self._state.status,
                "history": self._episode_history.copy(),
            }

        return StepResult(observation=obs, reward=reward, done=done)

    def state(self) -> State:
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._state

    def get_episode_replay(self, episode_id: str) -> Optional[Dict]:
        return self._all_episodes.get(episode_id)

    def get_all_episodes(self) -> List[Dict]:
        return [
            {
                "episode_id": ep["episode_id"],
                "task_id": ep["task_id"],
                "total_reward": ep["total_reward"],
                "steps": ep["steps"],
                "status": ep["status"],
            }
            for ep in self._all_episodes.values()
        ]

    def get_current_replay(self) -> List[Dict]:
        return self._episode_history.copy()