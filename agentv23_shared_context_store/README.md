# agentv23_shared_context_store

This version introduces a **shared context store**.

Earlier versions used LangGraph state only during one graph run.

This version adds durable context using SQLite:

```text
shared_context.db
```

The context survives across graph runs.

## Why this matters

LangGraph state is excellent for one execution:

```text
START → node1 → node2 → END
```

But production agents often need durable shared context:

- user preferences
- previous decisions
- incident notes
- working memory across sessions
- facts discovered by other agents
- task outputs from previous runs
- shared state between specialist agents

## Graph

```text
START
  ↓
load_context
  ↓
planner
  ├── metrics_agent
  └── runbook_agent
        ↓
    write_context
        ↓
    final_answer
        ↓
      END
```

## What this version demonstrates

- SQLite-backed context store
- durable key-value memory
- append-only event log
- shared facts table
- multiple nodes reading the same context
- multiple nodes writing shared findings
- reducer-based merge for agent outputs
- context surviving multiple runs
- `NotRequired` state typing

## Difference from checkpointing

Checkpointing stores graph execution state:

```text
thread_id → graph state
```

Shared context store stores reusable knowledge:

```text
context_id → facts, preferences, notes, events
```

Checkpointing is for resuming a graph.

Shared context is for remembering useful information across workflows.

## Tables

```sql
context_kv
context_events
context_facts
```

### context_kv

Stores latest value for a key.

Example:

```text
preferred_command = CHECK-DOMAIN
risk_threshold_ms = 220
```

### context_events

Append-only history.

Example:

```text
metrics_agent observed p95 response_time 240 ms
```

### context_facts

Structured facts discovered by agents.

Example:

```text
command=CHECK-DOMAIN
failure_reason=CONNECTION_TIMEOUT
release=R13
```

## Setup

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
agentv23_shared_context_store/notebook.ipynb
```

## Run CLI

```bash
python -m agentv23_shared_context_store.main
```

Run it multiple times. The second run will load context written by the first run.

## Production relevance

A shared context store is useful for:

- multi-agent systems
- A2A orchestration
- long-running workflows
- incident investigation
- customer support memory
- persistent project state
- audit trails
- human-in-the-loop approval records

This is the foundation for production memory that is separate from graph execution state.
