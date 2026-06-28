from __future__ import annotations

from fastapi import Depends, FastAPI

from .schemas import AgentRegistration, AgentSearchRequest
from .security import require_api_key


app = FastAPI(title="Agent Registry", version="1.0.0")

AGENTS: dict[str, AgentRegistration] = {}

TRUST_RANK = {
    "experimental": 0,
    "verified": 1,
    "trusted": 2,
}


@app.get("/health")
def health():
    return {"status": "ok", "service": "agent_registry"}


@app.post("/agents/register", dependencies=[Depends(require_api_key)])
def register_agent(agent: AgentRegistration):
    AGENTS[agent.agent_id] = agent
    return {"registered": True, "agent": agent}


@app.get("/agents", dependencies=[Depends(require_api_key)])
def list_agents():
    return {"agents": list(AGENTS.values())}


@app.get("/agents/{agent_id}", dependencies=[Depends(require_api_key)])
def get_agent(agent_id: str):
    return {"agent": AGENTS.get(agent_id)}


@app.post("/agents/search", dependencies=[Depends(require_api_key)])
def search_agents(request: AgentSearchRequest):
    results = []

    for agent in AGENTS.values():
        if request.domain and agent.domain != request.domain:
            continue

        if TRUST_RANK[agent.trust_level] < TRUST_RANK[request.minimum_trust_level]:
            continue

        if not set(request.required_capabilities).issubset(set(agent.capabilities)):
            continue

        results.append(agent)

    return {"agents": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8600)
