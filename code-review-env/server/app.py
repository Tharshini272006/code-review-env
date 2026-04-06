# server/app.py
"""
FastAPI server — all OpenEnv mandatory endpoints.
POST /reset  POST /step  GET /state  GET /tasks  POST /grader  GET /health
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from models import Action, Observation, State, StepResult
from server.environment import CodeReviewEnvironment
from server.tasks import list_tasks, get_task
from server.grader import grade

app = FastAPI(
    title="CodeReviewEnv",
    description="RL environment: AI agent finds and fixes Python bugs.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Single environment instance (one episode at a time)
env = CodeReviewEnvironment()


# ─────────────────────────────────────────────
# Request bodies
# ─────────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: str = "easy"


class GraderRequest(BaseModel):
    task_id: str
    code: str
    attempt_number: int = 1


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "CodeReviewEnv",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
        "tasks": "/tasks"
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    """Environment metrics and statistics."""
    return {
        "environment": "code_review_env",
        "version": "1.0.0",
        "tasks": {
            "total": 6,
            "by_difficulty": {
                "easy": ["easy"],
                "medium": ["medium", "medium2"],
                "hard": ["hard", "hard2", "security"]
            }
        },
        "reward_components": {
            "code_executes": 0.20,
            "tests_passed": "0.30-0.80",
            "input_validation": 0.20,
            "no_magic_numbers": 0.20,
            "code_quality": 0.20
        },
        "attempt_penalty": 0.90,
        "sandbox": {
            "timeout_seconds": 5,
            "blocked_imports": [
                "os", "sys", "subprocess", "socket",
                "requests", "importlib", "ctypes"
            ],
            "execution": "isolated_namespace"
        },
        "baseline_scores": {
            "easy": 1.000,
            "medium": 1.000,
            "medium2": 1.000,
            "hard": 0.950,
            "hard2": 1.000,
            "security": 1.000,
            "average": 0.992
        }
    }

@app.get("/replay")
def list_replays():
    """List all completed episodes available for replay."""
    episodes = env.get_all_episodes()
    return {
        "total_episodes": len(episodes),
        "episodes": episodes
    }


@app.get("/replay/current")
def current_replay():
    """Get step-by-step replay of the current episode."""
    history = env.get_current_replay()
    return {
        "episode_id": env._state.episode_id if env._state else None,
        "task_id": env._state.task_id if env._state else None,
        "steps": len(history),
        "history": history
    }


@app.get("/replay/{episode_id}")
def get_replay(episode_id: str):
    """Get full step-by-step replay of a completed episode."""
    replay = env.get_episode_replay(episode_id)
    if replay is None:
        raise HTTPException(
            status_code=404,
            detail=f"Episode '{episode_id}' not found. Episodes are stored in memory only."
        )
    return replay

@app.get("/tasks")
def tasks():
    return list_tasks()


@app.post("/reset", response_model=Observation)
def reset(req: Optional[ResetRequest] = None):
    try:
        task_id = req.task_id if req else "easy"
        obs = env.reset(task_id=task_id)
        return obs
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(action: Action):
    try:
        result = env.step(action)
        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/state", response_model=State)
def state():
    try:
        return env.state()
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/grader")
def grader(req: GraderRequest):
    """Grade submitted code without running a full episode."""
    try:
        task = get_task(req.task_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    result = grade(task, req.code, attempt_number=req.attempt_number)
    return {
        "task_id": req.task_id,
        "reward": result["reward"],
        "breakdown": result["breakdown"],
        "feedback": result["feedback"],
        "tests_passed": result["exec_result"]["tests_passed"],
        "total_tests": result["exec_result"]["total_tests"],
        "executes": result["exec_result"]["executes"],
        "exec_error": result["exec_result"]["exec_error"],
        "quality": result["quality"],
    }
def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

if __name__ == "__main__":
    main()