from __future__ import annotations

import asyncio
import json
import time
import uuid
from enum import Enum
from typing import Any, Literal

import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse


class TaskState(str, Enum):
    submitted = "submitted"
    working = "working"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"
    rejected = "rejected"


class Part(BaseModel):
    type: Literal["text", "json"] = "text"
    text: str | None = None
    data: dict[str, Any] | None = None


class Artifact(BaseModel):
    artifact_id: str
    name: str
    parts: list[Part]
    created_at: float


class TaskStatus(BaseModel):
    state: TaskState
    message: str
    updated_at: float


class TaskEvent(BaseModel):
    event_id: str
    task_id: str
    event_type: str
    state: TaskState | None = None
    message: str
    timestamp: float
    data: dict[str, Any] = Field(default_factory=dict)


class TaskCreateRequest(BaseModel):
    input: str
    skill_id: str = "epp_incident_analysis"
    context_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    task_id: str
    context_id: str | None
    skill_id: str
    input: str
    status: TaskStatus
    created_at: float
    updated_at: float
    artifacts: list[Artifact] = Field(default_factory=list)
    history: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


app = FastAPI(title="A2A Streaming EPP Agent", version="1.0.0")
TASKS: dict[str, Task] = {}
EVENTS: dict[str, list[TaskEvent]] = {}


def now() -> float:
    return time.time()


def agent_card() -> dict[str, Any]:
    return {
        "name": "EPP Streaming Incident Analysis Agent",
        "description": "Analyzes EPP SLA incidents and streams task progress events.",
        "version": "1.0.0",
        "url": "http://127.0.0.1:8301",
        "provider": {"organization": "AgenticAI Learn", "url": "http://localhost"},
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
            "artifacts": True,
            "cancellation": True,
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [
            {
                "id": "epp_incident_analysis",
                "name": "EPP streaming incident analysis",
                "description": "Investigates EPP SLA failures, latency, timeout spikes, and release impact with streaming progress.",
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["text/plain", "application/json"],
                "examples": ["Investigate CHECK-DOMAIN timeout spike after R13"],
            }
        ],
        "authentication": {"schemes": ["none"]},
    }


def add_event(
    task_id: str,
    event_type: str,
    message: str,
    state: TaskState | None = None,
    data: dict[str, Any] | None = None,
) -> TaskEvent:
    event = TaskEvent(
        event_id=f"event_{uuid.uuid4().hex[:12]}",
        task_id=task_id,
        event_type=event_type,
        state=state,
        message=message,
        timestamp=now(),
        data=data or {},
    )
    EVENTS.setdefault(task_id, []).append(event)
    return event


@app.get("/health")
def health():
    return {"status": "ok", "agent": "epp_streaming_incident_analysis_agent"}


@app.get("/.well-known/agent.json")
def get_agent_json():
    return agent_card()


@app.get("/model-card")
def get_model_card_alias():
    return agent_card()


@app.get("/capabilities")
def get_capabilities():
    return agent_card()["capabilities"]


@app.get("/skills")
def get_skills():
    return {"skills": agent_card()["skills"]}


async def set_status(task_id: str, state: TaskState, message: str) -> None:
    task = TASKS[task_id]
    task.status = TaskStatus(state=state, message=message, updated_at=now())
    task.updated_at = now()
    task.history.append({"state": state.value, "message": message, "at": now()})
    add_event(task_id, "status", message, state)


async def execute_task(task_id: str) -> None:
    task = TASKS[task_id]

    if task.status.state == TaskState.canceled:
        return

    await set_status(task_id, TaskState.working, "Collecting EPP failure metrics.")
    await asyncio.sleep(0.8)

    if task.status.state == TaskState.canceled:
        return

    add_event(
        task_id,
        "progress",
        "Metrics collected: CHECK-DOMAIN p95 response_time near 240 ms; timeout volume elevated.",
        TaskState.working,
        {"step": "metrics", "p95_response_time": 240, "failure_reason": "CONNECTION_TIMEOUT"},
    )
    await asyncio.sleep(0.8)

    if task.status.state == TaskState.canceled:
        return

    add_event(
        task_id,
        "progress",
        "Runbook context retrieved: check registry endpoint, DNS resolver, and connection pool saturation.",
        TaskState.working,
        {"step": "runbook"},
    )
    await asyncio.sleep(0.8)

    if task.status.state == TaskState.canceled:
        return

    analysis_text = (
        "Likely cause: CHECK-DOMAIN timeout spike is consistent with upstream registry "
        "connectivity degradation or connection pool saturation after R13. Evidence includes "
        "p95 response_time around 240 ms, increased CONNECTION_TIMEOUT volume, and concentration "
        "around peak traffic/client_b. Recommended next action: inspect registry endpoint health, "
        "DNS resolver latency, connection pool saturation, and compare pre/post-release failure volume."
    )

    artifact = Artifact(
        artifact_id=f"artifact_{uuid.uuid4().hex[:12]}",
        name="incident_analysis",
        created_at=now(),
        parts=[
            Part(type="text", text=analysis_text),
            Part(
                type="json",
                data={
                    "likely_cause": "registry connectivity or connection pool saturation",
                    "primary_command": "CHECK-DOMAIN",
                    "primary_failure_reason": "CONNECTION_TIMEOUT",
                    "p95_response_time_ms": 240,
                    "recommended_actions": [
                        "inspect registry endpoint health",
                        "check DNS resolver latency",
                        "check connection pool saturation",
                        "compare pre/post-release failure volume",
                    ],
                },
            ),
        ],
    )
    task.artifacts.append(artifact)

    add_event(
        task_id,
        "artifact",
        "Artifact created: incident_analysis.",
        TaskState.working,
        {"artifact_id": artifact.artifact_id, "artifact_name": artifact.name},
    )

    await set_status(task_id, TaskState.completed, "Task completed successfully.")
    add_event(task_id, "completed", "Final result is ready.", TaskState.completed)


@app.post("/tasks", response_model=Task)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    valid_skill_ids = {skill["id"] for skill in agent_card()["skills"]}
    task_id = f"task_{uuid.uuid4().hex[:12]}"

    if request.skill_id not in valid_skill_ids:
        task = Task(
            task_id=task_id,
            context_id=request.context_id,
            skill_id=request.skill_id,
            input=request.input,
            created_at=now(),
            updated_at=now(),
            status=TaskStatus(state=TaskState.rejected, message=f"Unsupported skill_id: {request.skill_id}", updated_at=now()),
            metadata=request.metadata,
        )
        TASKS[task_id] = task
        add_event(task_id, "rejected", task.status.message, TaskState.rejected)
        return task

    task = Task(
        task_id=task_id,
        context_id=request.context_id,
        skill_id=request.skill_id,
        input=request.input,
        created_at=now(),
        updated_at=now(),
        status=TaskStatus(state=TaskState.submitted, message="Task submitted.", updated_at=now()),
        metadata=request.metadata,
        history=[{"state": "submitted", "message": "Task submitted.", "at": now()}],
    )
    TASKS[task_id] = task
    add_event(task_id, "status", "Task submitted.", TaskState.submitted)
    background_tasks.add_task(execute_task, task_id)
    return task


@app.get("/tasks")
def list_tasks():
    return {"tasks": list(TASKS.values())}


@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]


@app.get("/tasks/{task_id}/status", response_model=TaskStatus)
def get_task_status(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id].status


@app.get("/tasks/{task_id}/artifacts")
def get_task_artifacts(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "artifacts": TASKS[task_id].artifacts}


@app.post("/tasks/{task_id}/cancel", response_model=Task)
def cancel_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    task = TASKS[task_id]
    if task.status.state not in {TaskState.completed, TaskState.failed, TaskState.rejected}:
        task.status = TaskStatus(state=TaskState.canceled, message="Task canceled by client.", updated_at=now())
        task.updated_at = now()
        task.history.append({"state": "canceled", "message": task.status.message, "at": now()})
        add_event(task_id, "canceled", "Task canceled by client.", TaskState.canceled)

    return task


@app.get("/tasks/{task_id}/events")
async def stream_task_events(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Task not found")

    async def event_generator():
        last_index = 0
        terminal_states = {TaskState.completed, TaskState.failed, TaskState.canceled, TaskState.rejected}

        while True:
            events = EVENTS.get(task_id, [])

            while last_index < len(events):
                event = events[last_index]
                last_index += 1
                yield {
                    "event": event.event_type,
                    "id": event.event_id,
                    "data": event.model_dump_json(),
                }

            task = TASKS[task_id]
            if task.status.state in terminal_states and last_index >= len(events):
                break

            await asyncio.sleep(0.2)

    return EventSourceResponse(event_generator())


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8301)
