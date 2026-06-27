# agentv24_production_deployment_pattern

This version introduces a production-style deployment wrapper for a LangGraph agent.

Earlier examples focused on graph concepts.

This version focuses on how to expose a graph as a service.

## What this version demonstrates

- FastAPI service wrapper
- `/health`
- `/ready`
- `/invoke`
- `/stream`
- typed request/response models
- correlation/request IDs
- configuration loading
- structured logging
- simple auth header check
- Dockerfile
- smoke test client
- notebook for local testing
- `NotRequired` state typing

## Graph

```text
START → classify_request → analyze → final_answer → END
```

## Service API

```text
GET  /health
GET  /ready
POST /invoke
POST /stream
```

## Run locally

Install:

```bash
pip install -U fastapi uvicorn langgraph langchain langchain-openai langsmith python-dotenv httpx ipython jupyter
```

Start API:

```bash
python -m agentv24_production_deployment_pattern.api_server
```

Invoke:

```bash
python -m agentv24_production_deployment_pattern.smoke_client
```

## Optional auth

By default, auth is disabled.

To enable:

```bash
export AGENT_API_KEY=dev-secret
```

Then send:

```text
x-api-key: dev-secret
```

## Docker build

```bash
docker build -t agentv24-production .
```

Run:

```bash
docker run --rm -p 8501:8501 \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e AGENT_API_KEY=dev-secret \
  agentv24-production
```

## Production concepts

This version shows the minimum wrapper you need before deploying an agent to:

- ECS
- Kubernetes
- Cloud Run
- Azure Container Apps
- AWS App Runner
- internal platform
- SageMaker custom endpoint pattern

## Why this matters

A graph by itself is not enough for production.

Production deployment needs:

```text
Graph
+ API boundary
+ schema validation
+ auth
+ health checks
+ logging
+ streaming
+ config
+ tests
+ containerization
```

This version introduces those deployment concerns without adding too much infrastructure.
