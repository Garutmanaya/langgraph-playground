# agentv15_streaming

This version introduces streaming in LangGraph.

Graph:

```text
START → planner → writer → reviewer → END
```

## What this version demonstrates

Two graph streaming modes:

```python
graph.stream(..., stream_mode="updates")
```

Streams node-level updates.

```python
graph.stream(..., stream_mode="values")
```

Streams full state snapshots after each step.

It also demonstrates direct LLM token streaming:

```python
llm.stream(prompt)
```

## Why streaming matters

Without streaming:

```text
user waits → waits → waits → final answer
```

With streaming:

```text
planner update → writer update → reviewer update → final answer
```

Streaming improves:

- UX
- debugging
- observability
- perceived latency
- trust in long-running agents

## LangGraph streaming vs LLM token streaming

LangGraph streaming shows graph execution progress.

LLM token streaming shows model output as it is generated.

Production apps often combine both.

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
agentv15_streaming/notebook.ipynb
```

## Run CLI

```bash
python -m agentv15_streaming.main
```

Or:

```bash
python -m agentv15_streaming.main "Write a short incident update for EPP CHECK-DOMAIN latency"
```

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  ├── writer
  │     └── ChatOpenAI
  └── reviewer
        └── ChatOpenAI
```

Streaming does not replace tracing. Streaming is for live user feedback; LangSmith is for post-run inspection.
