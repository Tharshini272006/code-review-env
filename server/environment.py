# server/environment.py
import uuid
from typing import Optional

from models import Action, Observation, State, StepResult
from server.tasks import get_task, Task
from server.grader import grade


class CodeReviewEnvironment:
    def __init__(self):
        self._task: Optional[Task] = None
        self._state: Optional[State] = None
        self._current_obs: Optional[Observation] = None
        self._attempt: int = 0

    def reset(self, task_id: str = "easy") -> Observation:
        task = get_task(task_id)
        self._task = task
        self._attempt = 0

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
        return obs

    def step(self, action: Action) -> StepResult:
        if self._task is None or self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        if self._state.status != "running":
            raise RuntimeError(f"Episode already ended with status '{self._state.status}'.")

        self._attempt += 1
        self._state.step_count += 1

        grade_result = grade(self._task, action.code, attempt_number=self._attempt)

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
        return StepResult(observation=obs, reward=reward, done=done)

    def state(self) -> State:
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        return self._state