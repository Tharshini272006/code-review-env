# client.py
"""
EnvClient — sync wrapper around the CodeReviewEnv FastAPI server.
Handles reset/step/state with clean Python API.
"""

import requests
from typing import Optional, Dict, Any

from models import Action, Observation, State, StepResult


class CodeReviewEnvClient:
    """Synchronous HTTP client for the CodeReviewEnv server."""

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})

    def _post(self, path: str, payload: Dict) -> Dict:
        resp = self.session.post(f"{self.base_url}{path}", json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _get(self, path: str) -> Dict:
        resp = self.session.get(f"{self.base_url}{path}", timeout=10)
        resp.raise_for_status()
        return resp.json()

    def health(self) -> Dict:
        return self._get("/health")

    def tasks(self) -> list:
        return self._get("/tasks")

    def reset(self, task_id: str = "easy") -> Observation:
        data = self._post("/reset", {"task_id": task_id})
        return Observation(**data)

    def step(self, code: str, explanation: Optional[str] = None) -> StepResult:
        payload = {"code": code}
        if explanation:
            payload["explanation"] = explanation
        data = self._post("/step", payload)
        obs = Observation(**data["observation"])
        return StepResult(
            observation=obs,
            reward=data["reward"],
            done=data["done"],
        )

    def state(self) -> State:
        data = self._get("/state")
        return State(**data)

    def grade(
        self,
        task_id: str,
        code: str,
        attempt_number: int = 1,
    ) -> Dict:
        return self._post("/grader", {
            "task_id": task_id,
            "code": code,
            "attempt_number": attempt_number,
        })

    def sync(self, task_id: str, agent_fn) -> Dict[str, Any]:
        """
        Run a full episode.
        agent_fn(observation: Observation) → (code: str, explanation: str | None)
        Returns episode summary dict.
        """
        obs = self.reset(task_id=task_id)
        rewards = []

        while not obs.done:
            code, explanation = agent_fn(obs)
            result = self.step(code, explanation)
            obs = result.observation
            rewards.append(result.reward)

        s = self.state()
        return {
            "episode_id": s.episode_id,
            "task_id": task_id,
            "status": s.status,
            "total_reward": s.total_reward,
            "steps": s.step_count,
            "rewards": rewards,
        }