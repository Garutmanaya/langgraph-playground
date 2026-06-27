# agentv21_official_a2a_sdk

This version uses the official A2A Python SDK package:

```bash
pip install "a2a-sdk[http-server]"
```

Earlier versions:

```text
v18 = custom HTTP RPC
v19 = custom A2A-style task lifecycle
v20 = custom A2A-style task lifecycle + SSE streaming
```

This version:

```text
v21 = official A2A Python SDK basics
```

## What this version demonstrates

- official `a2a-sdk`
- `AgentExecutor`
- `AgentCard`
- `AgentSkill`
- `AgentCapabilities`
- `DefaultRequestHandler`
- `InMemoryTaskStore`
- official JSON-RPC routes
- official Agent Card discovery
- official client flow
- non-streaming message call
- streaming message call
- extended agent card retrieval
- LangGraph host calling official A2A agent

## Important version note

The A2A Python SDK changed between `0.3` and `1.0`.

This example targets the current SDK style visible in the official `a2aproject/a2a-python` and `a2a-samples` repositories.

If imports fail, upgrade:

```bash
pip install -U "a2a-sdk[http-server]"
```

## Architecture

```text
Terminal 1:
python -m agentv21_official_a2a_sdk.official_a2a_server

Terminal 2:
python -m agentv21_official_a2a_sdk.official_a2a_client

Terminal 3:
python -m agentv21_official_a2a_sdk.langgraph_host
```

Runtime:

```text
LangGraph Host
   ↓
Official A2A Client
   ↓ JSON-RPC
Official A2A Server
   ↓
AgentExecutor
```

## Server port

```text
http://127.0.0.1:8401
```

## Run server

```bash
python -m agentv21_official_a2a_sdk.official_a2a_server
```

## Test official A2A APIs/client flow

```bash
python -m agentv21_official_a2a_sdk.official_a2a_client
```

This tests:

- fetch public Agent Card
- send non-streaming message
- send streaming message
- fetch extended Agent Card

## Run LangGraph host

```bash
python -m agentv21_official_a2a_sdk.langgraph_host
```

## Run notebook

Start the server first, then open:

```text
agentv21_official_a2a_sdk/notebook.ipynb
```

## Difference from v20

v20 implemented our own protocol-style server.

v21 uses the SDK primitives:

```text
AgentCard
AgentExecutor
TaskUpdater
DefaultRequestHandler
create_jsonrpc_routes
create_client
```

## Production note

Official A2A gives a standard protocol boundary.

Your business logic still lives in the executor:

```text
AgentExecutor.execute(...)
```

That is where you can connect:

- LangGraph subgraphs
- tools
- RAG
- SQL
- MCP
- cloud APIs
