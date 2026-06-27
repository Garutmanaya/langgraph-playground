# agentv17_mcp_http_integration

This version shows MCP integration using a local HTTP/SSE MCP server.

Unlike the earlier `agentv17_mcp_integration`, this version does **not** spawn the MCP server with stdio inside each tool call.

Instead:

```text
Terminal 1:
python -m agentv17_mcp_http_integration.mcp_http_server

Terminal 2:
python -m agentv17_mcp_http_integration.main
```

Architecture:

```text
LangGraph Agent
   ↓ HTTP/SSE
MCP Server running on localhost:8001
   ↓
MCP tools
```

## Graph

```text
START → planner → mcp_http_tools → summarize → END
```

## Why this version matters

The stdio version is useful for learning and local subprocess-based MCP.

The HTTP/SSE version is closer to production because the MCP server is a separate long-running process.

This allows:

- one server reused by multiple agent runs
- one server reused by multiple agents
- cleaner separation of agent orchestration and tool runtime
- easier deployment as a service
- future remote hosting

## Tools exposed by MCP server

The HTTP MCP server exposes:

```text
get_epp_metrics
get_epp_runbook
```

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter mcp uvicorn
```

## Run the MCP HTTP server

From repo root:

```bash
python -m agentv17_mcp_http_integration.mcp_http_server
```

Expected output should show a server listening on:

```text
http://127.0.0.1:8001
```

## Run the LangGraph client

In a second terminal:

```bash
python -m agentv17_mcp_http_integration.main
```

Or:

```bash
python -m agentv17_mcp_http_integration.main "Investigate CHECK-DOMAIN timeout issue after release R13"
```

## Run notebook

Start the MCP HTTP server first, then open:

```text
agentv17_mcp_http_integration/notebook.ipynb
```

## Important note

MCP HTTP transport APIs have changed across package versions.

This example uses MCP SSE transport:

```text
/sse
```

Client connects using:

```python
from mcp.client.sse import sse_client
```

Server runs using:

```python
mcp.run(transport="sse")
```

If your installed MCP package has changed transport names, check your installed package docs or upgrade:

```bash
pip install -U mcp
```

## Difference from stdio v17

### stdio version

```text
LangGraph node starts python mcp_server.py subprocess
communicates through stdin/stdout
server exits after call
```

Good for:
- learning
- local tool execution
- simple subprocess lifecycle

### HTTP/SSE version

```text
MCP server runs once on port 8001
LangGraph connects over HTTP/SSE
server remains alive
```

Good for:
- production-style service boundary
- shared tools
- multi-agent systems
- remote deployment

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  ├── mcp_http_tools
  └── summarize
        └── ChatOpenAI
```

The MCP server itself is outside the graph, so LangSmith sees the graph node but not the internal server process unless you instrument the server separately.
