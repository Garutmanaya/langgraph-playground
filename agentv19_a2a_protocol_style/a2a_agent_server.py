from __future__ import annotations

import asyncio, time, uuid
from enum import Enum
from typing import Any, Literal
import uvicorn
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

class TaskState(str, Enum):
    submitted="submitted"; working="working"; completed="completed"; failed="failed"; canceled="canceled"; rejected="rejected"

class Part(BaseModel):
    type: Literal["text","json"]="text"
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

app = FastAPI(title="A2A Protocol Style EPP Agent", version="1.0.0")
TASKS: dict[str, Task] = {}

def now() -> float:
    return time.time()

def agent_card() -> dict[str, Any]:
    return {
        "name": "EPP Incident Analysis Agent",
        "description": "Analyzes EPP SLA incidents using metrics and runbook-style reasoning.",
        "version": "1.0.0",
        "url": "http://127.0.0.1:8201",
        "provider": {"organization": "AgenticAI Learn", "url": "http://localhost"},
        "capabilities": {
            "streaming": False,
            "pushNotifications": False,
            "stateTransitionHistory": True,
            "artifacts": True,
            "cancellation": True
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [
            {
                "id": "epp_incident_analysis",
                "name": "EPP incident analysis",
                "description": "Investigates EPP SLA failures, latency, timeout spikes, and release impact.",
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["text/plain", "application/json"],
                "examples": ["Investigate CHECK-DOMAIN timeout spike after R13"]
            },
            {
                "id": "epp_release_risk_summary",
                "name": "EPP release risk summary",
                "description": "Summarizes likely release risks from incident symptoms.",
                "inputModes": ["text/plain", "application/json"],
                "outputModes": ["text/plain"],
                "examples": ["Summarize R13 risk for CHECK-DOMAIN latency"]
            }
        ],
        "authentication": {"schemes": ["none"]}
    }

@app.get("/health")
def health(): return {"status": "ok", "agent": "epp_incident_analysis_agent"}

@app.get("/.well-known/agent.json")
def get_agent_json(): return agent_card()

@app.get("/.well-known/agent-card.json")
def get_agent_card_json(): return agent_card()

@app.get("/model-card")
def get_model_card_alias(): return agent_card()

@app.get("/capabilities")
def get_capabilities(): return agent_card()["capabilities"]

@app.get("/skills")
def get_skills(): return {"skills": agent_card()["skills"]}

async def execute_task(task_id: str) -> None:
    task = TASKS[task_id]
    if task.status.state == TaskState.canceled:
        return
    task.status = TaskStatus(state=TaskState.working, message="Agent is analyzing the incident.", updated_at=now())
    task.updated_at = now()
    task.history.append({"state": "working", "message": task.status.message, "at": now()})
    await asyncio.sleep(1.5)
    if task.status.state == TaskState.canceled:
        return
    analysis_text = (
        "Likely cause: CHECK-DOMAIN timeout spike is consistent with upstream registry "
        "connectivity degradation or connection pool saturation after R13. Evidence: "
        "elevated p95 response_time around 240 ms, increased CONNECTION_TIMEOUT volume, "
        "and concentration around peak traffic/client_b. Recommended next action: inspect "
        "registry endpoint health, DNS resolver latency, connection pool saturation, and "
        "compare pre/post-release failure volume by command and client."
    )
    task.artifacts.append(Artifact(
        artifact_id=f"artifact_{uuid.uuid4().hex[:12]}",
        name="incident_analysis",
        created_at=now(),
        parts=[
            Part(type="text", text=analysis_text),
            Part(type="json", data={
                "likely_cause": "registry connectivity or connection pool saturation",
                "primary_command": "CHECK-DOMAIN",
                "primary_failure_reason": "CONNECTION_TIMEOUT",
                "recommended_actions": [
                    "inspect registry endpoint health",
                    "check DNS resolver latency",
                    "check connection pool saturation",
                    "compare pre/post-release failure volume"
                ]
            })
        ]
    ))
    task.status = TaskStatus(state=TaskState.completed, message="Task completed successfully.", updated_at=now())
    task.updated_at = now()
    task.history.append({"state": "completed", "message": task.status.message, "at": now()})

@app.post("/tasks", response_model=Task)
async def create_task(request: TaskCreateRequest, background_tasks: BackgroundTasks):
    valid_skill_ids = {skill["id"] for skill in agent_card()["skills"]}
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    if request.skill_id not in valid_skill_ids:
        task = Task(
            task_id=task_id, context_id=request.context_id, skill_id=request.skill_id,
            input=request.input, created_at=now(), updated_at=now(),
            status=TaskStatus(state=TaskState.rejected, message=f"Unsupported skill_id: {request.skill_id}", updated_at=now()),
            metadata=request.metadata
        )
        TASKS[task_id] = task
        return task
    task = Task(
        task_id=task_id, context_id=request.context_id, skill_id=request.skill_id,
        input=request.input, created_at=now(), updated_at=now(),
        status=TaskStatus(state=TaskState.submitted, message="Task submitted.", updated_at=now()),
        metadata=request.metadata,
        history=[{"state": "submitted", "message": "Task submitted.", "at": now()}]
    )
    TASKS[task_id] = task
    background_tasks.add_task(execute_task, task_id)
    return task

@app.get("/tasks")
def list_tasks(): return {"tasks": list(TASKS.values())}

@app.get("/tasks/{task_id}", response_model=Task)
def get_task(task_id: str):
    if task_id not in TASKS: raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id]

@app.get("/tasks/{task_id}/status", response_model=TaskStatus)
def get_task_status(task_id: str):
    if task_id not in TASKS: raise HTTPException(status_code=404, detail="Task not found")
    return TASKS[task_id].status

@app.get("/tasks/{task_id}/artifacts")
def get_task_artifacts(task_id: str):
    if task_id not in TASKS: raise HTTPException(status_code=404, detail="Task not found")
    return {"task_id": task_id, "artifacts": TASKS[task_id].artifacts}

@app.post("/tasks/{task_id}/cancel", response_model=Task)
def cancel_task(task_id: str):
    if task_id not in TASKS: raise HTTPException(status_code=404, detail="Task not found")
    task = TASKS[task_id]
    if task.status.state not in {TaskState.completed, TaskState.failed, TaskState.rejected}:
        task.status = TaskStatus(state=TaskState.canceled, message="Task canceled by client.", updated_at=now())
        task.updated_at = now()
        task.history.append({"state": "canceled", "message": task.status.message, "at": now()})
    return task

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8201)
