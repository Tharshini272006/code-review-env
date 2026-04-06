# tests/test_tasks.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from server.tasks import get_task, list_tasks, TASKS


class TestTaskRegistry:
    def test_all_tasks_exist(self):
        for task_id in ["easy", "medium", "medium2", "hard", "hard2"]:
            task = get_task(task_id)
            assert task is not None

    def test_invalid_task_raises(self):
        try:
            get_task("nonexistent")
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_list_tasks_returns_all(self):
        tasks = list_tasks()
        assert len(tasks) >= 5

    def test_each_task_has_test_cases(self):
        for task_id, task in TASKS.items():
            assert len(task.test_cases) > 0

    def test_each_task_has_buggy_code(self):
        for task_id, task in TASKS.items():
            assert len(task.buggy_code) > 0

    def test_easy_has_1_attempt(self):
        task = get_task("easy")
        assert task.max_attempts == 1

    def test_medium_has_3_attempts(self):
        task = get_task("medium")
        assert task.max_attempts == 3

    def test_hard_has_5_attempts(self):
        task = get_task("hard")
        assert task.max_attempts == 5