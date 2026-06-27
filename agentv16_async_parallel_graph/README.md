# agentv16_async_parallel_graph

This revised v16 demonstrates async execution with parallel graph branches.

Previous v16 was sequential:

```text
planner → async_fetch_metrics → async_fetch_logs → summarize
```

That does not reduce single-run latency because each node waits for the previous node.

Revised graph:

```text
              ┌→ async_fetch_metrics ┐
START → planner                        ├→ summarize → END
              └→ async_fetch_logs    ┘
```

## Key lesson

Async sequential graph does not reduce single-run latency much.

Async parallel graph does, when branches are independent I/O operations.

Example:

```text
metrics call = 2 sec
logs call    = 3 sec
```

Sequential total is about 5 sec.

Parallel async total is about 3 sec.

## What this version demonstrates

- async LangGraph nodes
- parallel fan-out/fan-in graph
- `graph.ainvoke(...)`
- `graph.astream(...)`
- async OpenAI call with `ainvoke`
- branch timing fields
- overlap verification
- `NotRequired` state typing

## Setup

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Use your root-level `.env`.

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv16_async_parallel_graph/notebook.ipynb
```

## Run CLI

```bash
python -m agentv16_async_parallel_graph.main
```

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  ├── async_fetch_metrics   overlaps with logs
  ├── async_fetch_logs      overlaps with metrics
  └── summarize             starts after both finish
```

Use this pattern for CloudWatch metrics + logs, multiple retrievers, MCP calls, A2A calls, and multi-source incident analysis.
