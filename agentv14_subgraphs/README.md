# agentv14_subgraphs

This version introduces **LangGraph subgraphs**.

A subgraph is a reusable compiled graph that can be used as a node inside a parent graph.

---

## Graph

Parent graph:

```text
START
  ↓
supervisor
  ↓
sql_subgraph
  ↓
rag_subgraph
  ↓
final_synthesis
  ↓
END
```

Each subgraph has its own internal graph.

SQL subgraph:

```text
START → sql_plan → sql_execute → sql_summary → END
```

RAG subgraph:

```text
START → rag_retrieve → rag_summary → END
```

---

## Why subgraphs matter

In v13, specialist agents were simple functions:

```text
sql_agent_node
rag_agent_node
ops_agent_node
```

That is fine for learning, but production specialists are usually not single functions.

A SQL agent may need:

```text
plan query → execute query → validate result → summarize
```

A RAG agent may need:

```text
retrieve docs → filter context → summarize evidence
```

Subgraphs let each specialist become its own workflow.

---

## Key idea

Instead of:

```python
graph_builder.add_node("sql_agent", sql_agent_node)
```

you can use:

```python
sql_graph = build_sql_subgraph()
graph_builder.add_node("sql_subgraph", sql_graph)
```

The compiled graph behaves like a node.

---

## Why this is different from v13

### v13 supervisor

```text
supervisor → simple specialist functions → synthesis
```

### v14 subgraphs

```text
parent graph → reusable specialist graphs → synthesis
```

This is closer to production architecture.

---

## State design

This version uses `NotRequired`, not `total=False`.

```python
from typing import NotRequired, TypedDict

class ParentState(TypedDict):
    input: str
    sql_summary: NotRequired[str]
    rag_summary: NotRequired[str]
    final_answer: NotRequired[str]
```

This is clearer than:

```python
class ParentState(TypedDict, total=False):
```

because `input` is required while later fields are optional.

---

## Concepts covered

- Subgraphs
- Compiled graph as node
- Parent graph
- Specialist graph
- State compatibility
- Reusable workflow units
- Cleaner production design
- LangSmith nested traces

---

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Required `.env` values:

```env
OPENAI_API_KEY=your_openai_api_key
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=langgraph-playground
```

---

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv14_subgraphs/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv14_subgraphs.main
```

Or:

```bash
python -m agentv14_subgraphs.main "Investigate CHECK-DOMAIN timeout risk after R13 using SQL and docs"
```

---

## LangSmith trace

Expected trace shape:

```text
Parent graph
  ├── supervisor
  ├── sql_subgraph
  │     ├── sql_plan
  │     ├── sql_execute
  │     └── sql_summary
  ├── rag_subgraph
  │     ├── rag_retrieve
  │     └── rag_summary
  └── final_synthesis
```

This is useful because you can debug each specialist workflow independently.

---

## Production relevance

Subgraphs are useful when:

- each agent has multiple internal steps
- you want reusable specialist workflows
- you want cleaner graph composition
- you want nested traces
- teams own different agent modules
- you want to test each specialist graph independently

This is a major step toward production multi-agent systems.
