# server/tasks.py
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from tasks import TASK_REGISTRY  # Sourced from your new tasks/ folder logic

class TestCase(BaseModel):
    """
    Standardized test case format for the Grader.
    """
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    expected: Any
    description: str = ""

class Task(BaseModel):
    """
    Standardized Task object used by the Environment and API.
    """
    task_id: str
    function_name: str
    buggy_code: str
    description: str
    hint: str
    max_attempts: int
    test_cases: List[TestCase]

def get_task(task_id: str) -> Task:
    """
    Factory function that converts the dictionary-based task definitions 
    from the tasks/ module into strict Pydantic Task objects.
    """
    raw_data = TASK_REGISTRY.get(task_id)
    if not raw_data:
        raise ValueError(f"Task '{task_id}' not found in registry.")
    
    # 1. Map test_cases and edge_cases into TestCase objects
    cases = []
    # We combine both lists so the agent must pass basic logic AND edge cases
    all_raw_cases = raw_data.get("test_cases", []) + raw_data.get("edge_cases", [])
    
    for args_data, expected in all_raw_cases:
        # Safety: Ensure args is a list. If a single string is passed as ('str',), 
        # Python might wrap it. We ensure it's a list for the *args splat.
        if isinstance(args_data, (list, tuple)):
            actual_args = list(args_data)
        else:
            actual_args = [args_data]

        cases.append(TestCase(
            args=actual_args,
            expected=expected,
            description=f"Testing {task_id} with input: {args_data}"
        ))

    # 2. Extract function name from the title
    # Logic: "logic_fix — fibonacci" -> "fibonacci"
    # Logic: "security_fix — sanitize_input" -> "sanitize_input"
    try:
        title_part = raw_data["title"].split(" — ")[-1]
        func_name = title_part.split(" ")[0].strip()
    except Exception:
        # Fallback if title format is unexpected
        func_name = "solution"

    # 3. Return the fully formed Task object
    return Task(
        task_id=raw_data["id"],
        function_name=func_name,
        buggy_code=raw_data["buggy_code"],
        description=raw_data.get("description", raw_data["title"]),
        hint=raw_data["hint"],
        max_attempts=raw_data.get("max_attempts", 3),
        test_cases=cases
    )

def list_tasks() -> List[Dict[str, str]]:
    """
    Returns a summarized list of available tasks for the UI/Client.
    """
    return [
        {"id": tid, "description": t["title"]} 
        for tid, t in TASK_REGISTRY.items()
    ]