# agentv19_a2a_protocol_style

Corrected v19 notebook/package.

This version provides a protocol-style A2A learning implementation with:

- Agent Card
- model-card alias
- capabilities
- skills
- task creation
- task status polling
- artifacts
- cancellation
- unsupported skill rejection
- `test_all_api_calls.py`
- LangGraph host client
- corrected notebook that builds `graph = build_graph()` before invoking

## Start server

```bash
python -m agentv19_a2a_protocol_style.a2a_agent_server
```

Server runs at:

```text
http://127.0.0.1:8201
```

## Test all APIs

```bash
python -m agentv19_a2a_protocol_style.test_all_api_calls
```

## Run host graph

```bash
python -m agentv19_a2a_protocol_style.main
```

## Required packages

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter fastapi uvicorn httpx
```
