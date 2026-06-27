from __future__ import annotations

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(title="SQL Specialist Agent", version="1.0.0")


class AgentRequest(BaseModel):
    task: str


class AgentResponse(BaseModel):
    agent_name: str
    analysis: str


@app.get("/health")
def health():
    return {"status": "ok", "agent": "sql_agent"}


@app.post("/analyze", response_model=AgentResponse)
def analyze(request: AgentRequest):
    return AgentResponse(
        agent_name="sql_agent",
        analysis=(
            "SQL Agent Analysis: Structured metrics indicate CHECK-DOMAIN timeout "
            "volume increased after release R13. The strongest signal is elevated "
            "CONNECTION_TIMEOUT failures for client_b and p95 response_time around "
            "240 ms during peak traffic. "
            f"Task: {request.task}"
        ),
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8101)
