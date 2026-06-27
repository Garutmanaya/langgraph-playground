from __future__ import annotations
import asyncio, os
from typing import Any
import httpx

A2A_SERVER_URL = os.getenv("A2A_SERVER_URL", "http://127.0.0.1:8201")

class A2AClient:
    def __init__(self, base_url: str = A2A_SERVER_URL):
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.get(f"{self.base_url}{path}")
            r.raise_for_status()
            return r.json()

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(f"{self.base_url}{path}", json=payload or {})
            r.raise_for_status()
            return r.json()

    async def health(self): return await self._get("/health")
    async def get_agent_card(self): return await self._get("/.well-known/agent.json")
    async def get_agent_card_alias(self): return await self._get("/.well-known/agent-card.json")
    async def get_model_card(self): return await self._get("/model-card")
    async def get_capabilities(self): return await self._get("/capabilities")
    async def get_skills(self): return await self._get("/skills")
    async def list_tasks(self): return await self._get("/tasks")
    async def get_task(self, task_id: str): return await self._get(f"/tasks/{task_id}")
    async def get_task_status(self, task_id: str): return await self._get(f"/tasks/{task_id}/status")
    async def get_task_artifacts(self, task_id: str): return await self._get(f"/tasks/{task_id}/artifacts")
    async def cancel_task(self, task_id: str): return await self._post(f"/tasks/{task_id}/cancel")

    async def create_task(self, input_text: str, skill_id: str = "epp_incident_analysis", context_id: str | None = None, metadata: dict[str, Any] | None = None):
        return await self._post("/tasks", {"input": input_text, "skill_id": skill_id, "context_id": context_id, "metadata": metadata or {}})

    async def wait_for_completion(self, task_id: str, poll_interval_seconds: float = 0.3, timeout_seconds: float = 10.0):
        deadline = asyncio.get_event_loop().time() + timeout_seconds
        while True:
            task = await self.get_task(task_id)
            if task["status"]["state"] in {"completed", "failed", "canceled", "rejected"}:
                return task
            if asyncio.get_event_loop().time() > deadline:
                raise TimeoutError(f"Timed out waiting for task {task_id}")
            await asyncio.sleep(poll_interval_seconds)
