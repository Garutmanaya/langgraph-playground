# agentv17_mcp_integration

This version introduces MCP integration with LangGraph.

MCP = Model Context Protocol.

The goal is to show how a LangGraph agent can call tools exposed by an external MCP server instead of defining every tool directly inside the agent.

## Graph

```text
START → planner → mcp_tools → summarize → END
```

## What this version demonstrates

- local MCP server
- MCP tools
- async MCP client calls
- LangGraph async nodes
- `graph.ainvoke(...)`
- `graph.astream(...)`
- `NotRequired` state typing
- separation between agent orchestration and tool server
- production-style tool boundary

## Why MCP matters

Earlier examples defined tools directly in Python agent code.

Example:

```python
@tool
def execute_sql(...):
    ...
```

That is fine for learning.

In production, tools may live outside the agent process:

```text
LangGraph Agent
  → MCP Server
      → database tools
      → file tools
      → cloud tools
      → enterprise APIs
```

MCP gives a standard way for agents to discover and call external tools.

## Why async is natural here

MCP servers are external processes or remote services.

That means tool calls are I/O-bound.

So MCP integration should usually be async.

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter mcp
```

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv17_mcp_integration/notebook.ipynb
```

## Run CLI

```bash
python -m agentv17_mcp_integration.main
```

Or:

```bash
python -m agentv17_mcp_integration.main "Investigate CHECK-DOMAIN timeout issue"
```

## MCP server in this example

This version creates a local MCP stdio server file:

```text
mcp_server.py
```

It exposes two tools:

```text
get_epp_metrics
get_epp_runbook
```

The LangGraph agent calls those tools through the MCP client.

## Production relevance

MCP is useful for:

- enterprise tool catalogs
- shared tools across multiple agents
- database tools
- cloud operations tools
- file/document tools
- Slack/Jira/GitHub tools
- A2A systems where agents need standard tool access

## Difference from v16

v16 showed async parallel graph execution.

v17 applies async to a real integration boundary:

```text
LangGraph ↔ MCP Server
```

This is closer to production agent architecture.
