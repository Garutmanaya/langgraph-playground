# agentv20_a2a_streaming_events

This version extends v19 by adding A2A-style **task event streaming**.

v19 used polling:

```text
POST /tasks
GET /tasks/{task_id}/status
GET /tasks/{task_id}/artifacts
```

v20 adds server-sent event streaming:

```text
GET /tasks/{task_id}/events
```

The host agent can subscribe to task progress events instead of only polling.

## Architecture

```text
Terminal 1:
python -m agentv20_a2a_streaming_events.a2a_streaming_server

Terminal 2:
python -m agentv20_a2a_streaming_events.test_all_api_calls

Terminal 3:
python -m agentv20_a2a_streaming_events.main
```

Runtime:

```text
Host LangGraph Agent
   ↓
A2A Streaming Client
   ↓ HTTP/SSE
Remote A2A Agent Server
   ↓
Task lifecycle + streamed events + artifacts
```

## Server endpoints

Discovery:

```text
GET /health
GET /.well-known/agent.json
GET /model-card
GET /capabilities
GET /skills
```

Task lifecycle:

```text
POST /tasks
GET /tasks
GET /tasks/{task_id}
GET /tasks/{task_id}/status
GET /tasks/{task_id}/artifacts
POST /tasks/{task_id}/cancel
```

Streaming:

```text
GET /tasks/{task_id}/events
```

## Task event stream

The event stream emits SSE messages like:

```text
event: status
data: {"task_id":"...","state":"working","message":"Collecting metrics"}

event: artifact
data: {"task_id":"...","artifact_name":"incident_analysis"}

event: completed
data: {"task_id":"...","state":"completed"}
```

## Why streaming matters

Polling works, but streaming is better for long-running tasks.

Polling:

```text
client repeatedly asks: are you done?
```

Streaming:

```text
server pushes updates as work progresses
```

Streaming is useful for:

- long-running agents
- user-visible progress
- remote agent debugging
- incident investigation
- A2A orchestration
- human-in-the-loop dashboards

## Required packages

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter fastapi uvicorn httpx sse-starlette
```

## Start server

```bash
python -m agentv20_a2a_streaming_events.a2a_streaming_server
```

Server:

```text
http://127.0.0.1:8301
```

## Test all APIs

```bash
python -m agentv20_a2a_streaming_events.test_all_api_calls
```

## Run host graph

```bash
python -m agentv20_a2a_streaming_events.main
```

## Run notebook

Start the server first, then open:

```text
agentv20_a2a_streaming_events/notebook.ipynb
```

## v19 vs v20

v19:

```text
submit task → poll until completed → fetch artifacts
```

v20:

```text
submit task → subscribe to events → fetch artifacts
```

## A2A learning progression

```text
v18: simple HTTP delegation
v19: protocol-style task lifecycle
v20: task lifecycle + streaming events
```
