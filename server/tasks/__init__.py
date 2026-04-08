from .easy import EASY_TASKS
from .medium import MEDIUM_TASKS
from .hard import HARD_TASKS

ALL_TASKS = EASY_TASKS + MEDIUM_TASKS + HARD_TASKS


def get_task(task_id: str):
    for task in ALL_TASKS:
        if task["id"] == task_id:
            return task
    return None