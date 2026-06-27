# agentv16_async_graph

This version introduces async LangGraph execution.

Graph:

```text
START → planner → async_fetch_metrics → async_fetch_logs → summarize → END
```

## What this version demonstrates

- async node functions
- `await`
- `graph.ainvoke(...)`
- `graph.astream(...)`
- async LLM calls with `ainvoke`
- concurrent async work inside a node using `asyncio.gather`
- `NotRequired` state typing

## Why async matters

Many real agent tools are I/O-bound:

- HTTP APIs
- database calls
- vector DB calls
- cloud APIs
- MCP tool calls
- log queries
- metrics queries

Async execution lets the application wait on I/O without blocking the event loop.

## Sync vs async

Synchronous graph:

```python
result = graph.invoke(input_state)
```

Async graph:

```python
result = await graph.ainvoke(input_state)
```

Synchronous stream:

```python
for chunk in graph.stream(...):
    ...
```

Async stream:

```python
async for chunk in graph.astream(...):
    ...
```

## Important notebook note

Jupyter already runs an event loop, so you can directly use:

```python
await graph.ainvoke(...)
```

In a normal Python script, use:

```python
asyncio.run(main())
```

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv16_async_graph/notebook.ipynb
```

## Run CLI

```bash
python -m agentv16_async_graph.main
```

Or:

```bash
python -m agentv16_async_graph.main "Investigate EPP CHECK-DOMAIN latency after release R13"
```

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  ├── async_fetch_metrics
  ├── async_fetch_logs
  └── summarize
        └── ChatOpenAI async call
```

## Production relevance

Use async patterns for:

- CloudOps agents calling AWS APIs
- RAG agents querying multiple retrievers
- MCP agents calling remote tools
- multi-source incident analysis
- dashboard/report agents
- external SaaS integrations

Async becomes especially important when tools are slow but independent.
