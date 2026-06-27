# agentv18_a2a_communication

This version introduces **Agent-to-Agent communication (A2A)** using HTTP services.

The goal is to show a host/supervisor LangGraph agent calling remote specialist agents.

## Architecture

```text
Terminal 1:
python -m agentv18_a2a_communication.sql_agent_server

Terminal 2:
python -m agentv18_a2a_communication.rag_agent_server

Terminal 3:
python -m agentv18_a2a_communication.main
```

Runtime architecture:

```text
Host LangGraph Agent
   ├── HTTP call → SQL Agent Server on port 8101
   └── HTTP call → RAG Agent Server on port 8102
           ↓
      Final synthesis
```

## Graph

```text
START
  ↓
planner
  ├── call_sql_agent
  └── call_rag_agent
        ↓
    synthesize
        ↓
      END
```

The host agent uses parallel async branches, so the SQL and RAG agent calls can overlap.

## Why this version matters

Earlier versions covered:

- v13 supervisor multi-agent pattern inside one graph
- v14 subgraphs inside one process
- v16 async parallel graph
- v17 MCP tool server integration

v18 moves one level further:

```text
separate agents running as separate services
```

This is closer to production A2A systems.

## Agent vs Tool

A tool usually performs one operation:

```text
query database
retrieve document
restart service
```

An agent may have its own reasoning/workflow:

```text
receive task
decide internal steps
use tools
return analysis
```

In this example, the remote SQL and RAG agents are simple FastAPI services for learning, but the boundary is correct:

```text
host agent ↔ remote specialist agent
```

## Ports

```text
SQL Agent: http://127.0.0.1:8101/analyze
RAG Agent: http://127.0.0.1:8102/analyze
```

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter fastapi uvicorn httpx
```

## Run servers

Terminal 1:

```bash
python -m agentv18_a2a_communication.sql_agent_server
```

Terminal 2:

```bash
python -m agentv18_a2a_communication.rag_agent_server
```

## Run host agent

Terminal 3:

```bash
python -m agentv18_a2a_communication.main
```

Or:

```bash
python -m agentv18_a2a_communication.main "Investigate CHECK-DOMAIN timeout spike after R13 using metrics and docs"
```

## Run notebook

Start both servers first, then open:

```text
agentv18_a2a_communication/notebook.ipynb
```

## Environment variables

Optional:

```env
SQL_AGENT_URL=http://127.0.0.1:8101/analyze
RAG_AGENT_URL=http://127.0.0.1:8102/analyze
```

## Production relevance

A2A is useful when:

- each agent is owned by a separate team
- agents use different runtimes or languages
- agents scale independently
- specialist agents have private tools
- agents run in different security zones
- you want service boundaries

Example enterprise layout:

```text
Host/Supervisor Agent
  ├── SQL Analytics Agent
  ├── RAG Knowledge Agent
  ├── CloudOps Agent
  ├── Security Agent
  └── Ticketing Agent
```

## A2A vs MCP

MCP exposes tools.

A2A exposes agents.

```text
MCP: call tool
A2A: delegate task to another agent
```

Both are useful and often used together.

## LangSmith trace

LangSmith will show:

```text
Host graph
  ├── planner
  ├── call_sql_agent
  ├── call_rag_agent
  └── synthesize
```

The remote agent internals will not appear in the host LangSmith trace unless those services are also instrumented with LangSmith.
