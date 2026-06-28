# agentv26_agent_registry_auth_security

This version introduces an **Agent Registry + Auth/Security** pattern.

This completes the initial learning path through v26.

## What this version demonstrates

- Agent registry service
- Agent registration
- Agent discovery by capability/domain/location
- Trust level filtering
- API key authentication
- Host LangGraph agent that discovers agents dynamically
- Specialist parking agents
- Dynamic A2A-style delegation
- Security concepts for production agent systems
- Notebook-based walkthrough
- Smoke test client

## Scenario

Parking management example:

```text
Mobile Parking Agent
  ↓
Agent Registry
  ↓
Company A Parking Agent
Company B Parking Agent
  ↓
Compare price, level, distance
  ↓
Recommend best parking option
```

User preference:

```text
ground level
lowest price
near current location
```

## Architecture

Run four services:

```text
Terminal 1:
python -m agentv26_agent_registry_auth_security.registry_server

Terminal 2:
python -m agentv26_agent_registry_auth_security.parking_agent_a

Terminal 3:
python -m agentv26_agent_registry_auth_security.parking_agent_b

Terminal 4:
python -m agentv26_agent_registry_auth_security.host_graph
```

Runtime:

```text
Host LangGraph Agent
   ↓
Registry discovery
   ↓
Dynamic agent selection
   ↓
Parallel calls to discovered parking agents
   ↓
Decision and recommendation
```

## Ports

```text
Registry:        http://127.0.0.1:8600
Company A Agent: http://127.0.0.1:8601
Company B Agent: http://127.0.0.1:8602
```

## Auth

All service calls use:

```text
x-api-key: dev-secret
```

Default key:

```bash
export AGENT_API_KEY=dev-secret
```

## Required packages

```bash
pip install -U fastapi uvicorn httpx langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

## Start services

```bash
export AGENT_API_KEY=dev-secret
```

Terminal 1:

```bash
python -m agentv26_agent_registry_auth_security.registry_server
```

Terminal 2:

```bash
python -m agentv26_agent_registry_auth_security.parking_agent_a
```

Terminal 3:

```bash
python -m agentv26_agent_registry_auth_security.parking_agent_b
```

## Register agents

Terminal 4:

```bash
python -m agentv26_agent_registry_auth_security.register_agents
```

## Run host graph

```bash
python -m agentv26_agent_registry_auth_security.host_graph
```

## Test full workflow

```bash
python -m agentv26_agent_registry_auth_security.smoke_client
```

## Run notebook

Start registry and both parking agents first, then open:

```text
agentv26_agent_registry_auth_security/notebook.ipynb
```

## Security concepts introduced

This version is intentionally simple, but it introduces production security boundaries:

### 1. Authentication

Every request requires an API key.

```text
x-api-key
```

### 2. Capability filtering

Host agent asks registry for:

```text
domain = parking
capability = availability
capability = pricing
```

### 3. Trust filtering

Host can require:

```text
minimum_trust_level = verified
```

### 4. Least privilege

Host does not directly know all agents.

It asks registry for allowed agents.

### 5. Separation of concerns

Registry knows metadata.

Parking agents know parking inventory.

Host agent makes user-specific decision.

## Why this matters

Real A2A production systems need:

- discovery
- auth
- trust model
- capability metadata
- policy enforcement
- endpoint isolation
- auditability

Without a registry, clients need hardcoded URLs.

With a registry, clients can dynamically discover suitable agents.

## Learning path completed

```text
v1  basic graph
...
v17 MCP
v18 simple A2A
v19 protocol-style A2A
v20 A2A streaming
v21 official A2A SDK
v22 multimodal
v23 shared context
v24 production deployment
v25 evaluation
v26 registry + auth/security
```

Next project can combine all of these into a complete production-grade agent platform.
