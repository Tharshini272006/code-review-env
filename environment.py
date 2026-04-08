from typing import Dict, Any, Optional
from server.tasks import get_task
from server.grader import grade


class CodeReviewEnvironment:
    def __init__(self):
        self.task: Optional[Dict] = None
        self.current_step = 0
        self.max_steps = 0
        self.done = False

    def reset(self, task_id: str) -> Dict[str, Any]:
        task = get_task(task_id)

        if not task:
            raise ValueError(f"Task '{task_id}' not found")

        self.task = task
        self.current_step = 0
        self.done = False
        self.max_steps = task.get("max_attempts", 3)

        return {
            "task_id": task["id"],
            "description": task["title"],
            "buggy_code": task["buggy_code"],
            "hint": task["hint"],
            "max_steps": self.max_steps,
        }

    def step(self, action: str) -> Dict[str, Any]:
        if self.done:
            return {"error": "Episode finished", "done": True, "reward": 0.0}

        self.current_step += 1

        result = grade(
            task=self.task,
            submitted_code=action,
            attempt_number=self.current_step
        )

        exec_result = result.get("exec_result", {})

        tests_passed = exec_result.get("tests_passed", 0)
        total_tests = exec_result.get("total_tests", 0)
        executes = exec_result.get("executes", False)

        success = executes and (tests_passed == total_tests)

        if success or self.current_step >= self.max_steps:
            self.done = True

        return {
            "step": self.current_step,
            "reward": result.get("reward", 0.0),
            "done": self.done,
            "success": success,
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "feedback": result.get("feedback", ""),
            "exec_error": exec_result.get("exec_error"),
        }

    def get_state(self):
        return {
            "task_id": self.task["id"] if self.task else None,
            "step": self.current_step,
            "done": self.done,
        }