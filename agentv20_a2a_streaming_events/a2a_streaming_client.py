from __future__ import annotations

import asyncio
import json
import os
from typing import Any, AsyncIterator

import httpx


A2A_STREAMING_SERVER_URL = os.getenv("A2A_STREAMING_SERVER_URL", "http://127.0.0.1:8301")


class A2AStreamingClient:
    def __init__(self, base_url: str = A2A_STREAMING_SERVER_URL):
        self.base_url = base_url.rstrip("/")

    async def _get(self, path: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}{path}")
            response.raise_for_status()
            return response.json()

    async def _post(self, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{self.base_url}{path}", json=payload or {})
            response.raise_for_status()
            return response.json()

    async def health(self): return await self._get("/health")
    async def get_agent_card(self): return await self._get("/.well-known/agent.json")
    async def get_model_card(self): return await self._get("/model-card")
    async def get_capabilities(self): return await self._get("/capabilities")
    async def get_skills(self): return await self._get("/skills")
    async def list_tasks(self): return await self._get("/tasks")
    async def get_task(self, task_id: str): return await self._get(f"/tasks/{task_id}")
    async def get_task_status(self, task_id: str): return await self._get(f"/tasks/{task_id}/status")
    async def get_task_artifacts(self, task_id: str): return await self._get(f"/tasks/{task_id}/artifacts")
    async def cancel_task(self, task_id: str): return await self._post(f"/tasks/{task_id}/cancel")

    async def create_task(
        self,
        input_text: str,
        skill_id: str = "epp_incident_analysis",
        context_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        return await self._post(
            "/tasks",
            {
                "input": input_text,
                "skill_id": skill_id,
                "context_id": context_id,
                "metadata": metadata or {},
            },
        )

    async def stream_task_events(self, task_id: str) -> AsyncIterator[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", f"{self.base_url}/tasks/{task_id}/events") as response:
                response.raise_for_status()

                current_event = "message"
                current_data_lines: list[str] = []

                async for line in response.aiter_lines():
                    if line == "":
                        if current_data_lines:
                            data_text = "\n".join(current_data_lines)
                            try:
                                data = json.loads(data_text)
                            except json.JSONDecodeError:
                                data = {"raw": data_text}
                            yield {"event": current_event, "data": data}
                            current_event = "message"
                            current_data_lines = []
                        continue

                    if line.startswith("event:"):
                        current_event = line.split(":", 1)[1].strip()
                    elif line.startswith("data:"):
                        current_data_lines.append(line.split(":", 1)[1].strip())

    async def wait_for_completion_by_events(self, task_id: str) -> list[dict[str, Any]]:
        terminal_events = {"completed", "failed", "canceled", "rejected"}
        received: list[dict[str, Any]] = []

        async for event in self.stream_task_events(task_id):
            received.append(event)
            if event["event"] in terminal_events:
                break

        return received
