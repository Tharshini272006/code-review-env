from fastapi import FastAPI
from pydantic import BaseModel
from environment import CodeReviewEnvironment

app = FastAPI()
env = CodeReviewEnvironment()


class ResetRequest(BaseModel):
    task_id: str


class StepRequest(BaseModel):
    action: str


@app.post("/reset")
def reset(req: ResetRequest):
    try:
        return env.reset(req.task_id)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.post("/step")
def step(req: StepRequest):
    try:
        return env.step(req.action)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"error": str(e)}


@app.get("/state")
def state():
    return env.get_state()