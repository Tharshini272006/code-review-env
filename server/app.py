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