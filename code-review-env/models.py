# models.py
"""
Pydantic models for CodeReviewEnv — OpenEnv spec compliant.
Action, Observation, State, StepResult
"""

from typing import Optional
from pydantic import BaseModel, Field


class Action(BaseModel):
    """Agent's submitted action: fixed code + optional explanation."""
    code: str = Field(..., description="The complete fixed Python function.")
    explanation: Optional[str] = Field(
        None,
        description="Optional explanation of what bug was found and how it was fixed.",
    )


class Observation(BaseModel):
    """What the agent sees at each step."""
    buggy_code: str = Field(..., description="The original buggy Python function.")
    task_description: str = Field(..., description="What the agent must do.")
    task_id: str = Field(..., description="Task identifier: easy | medium | hard")
    attempt_number: int = Field(..., description="Current attempt (1-based).")
    max_attempts: int = Field(..., description="Maximum allowed attempts for this task.")
    last_execution_output: str = Field(
        "", description="stdout/stderr from the last code execution."
    )
    feedback: str = Field("", description="Human-readable grader feedback.")
    hint: Optional[str] = Field(None, description="Optional hint for the agent.")
    reward: float = Field(0.0, description="Reward earned on the last step.")
    done: bool = Field(False, description="True if the episode is finished.")


class State(BaseModel):
    """Internal episode state (for /state endpoint)."""
    episode_id: str = Field(..., description="Unique episode identifier.")
    task_id: str = Field(..., description="Task identifier.")
    step_count: int = Field(0, description="Number of steps taken so far.")
    max_steps: int = Field(..., description="Maximum steps allowed.")
    total_reward: float = Field(0.0, description="Cumulative reward so far.")
    status: str = Field("running", description="running | success | failed | timeout")


class StepResult(BaseModel):
    """Result returned from /step."""
    observation: Observation
    reward: float
    done: bool