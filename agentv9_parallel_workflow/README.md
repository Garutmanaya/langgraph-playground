# agentv9_parallel_workflow

This version introduces **parallel workflow execution** in LangGraph.

Graph:

```text
              ┌→ failure_analysis ┐
START → split ├→ latency_analysis ├→ synthesize → END
              └→ volume_analysis  ┘
```

## Why parallel workflow matters

Some tasks have independent subtasks that can run at the same time.

Example BI request:

```text
Analyze EPP SLA health for the latest release.
```

This can be decomposed into parallel analyses:

```text
1. Failure analysis
2. Latency analysis
3. Volume analysis
```

These do not depend on each other, so they can run as separate branches and then merge into a final synthesis node.

## Difference from v8

### v8: iterative loop

```text
assistant → sql_tool → assistant → sql_tool → assistant
```

Good when each next step depends on previous SQL results.

### v9: parallel branches

```text
split → branch A
      → branch B
      → branch C
      → synthesize
```

Good when subtasks are independent.

## Concepts covered

- Fan-out / fan-in graph pattern
- Parallel branch execution
- State reducers
- Merging independent branch outputs
- Synthesis node
- LangSmith tracing for parallel execution

## Important reducer concept

When multiple branches update the same state key, LangGraph needs to know how to merge those updates.

For example, each branch returns:

```python
{"analysis_results": ["failure analysis output"]}
{"analysis_results": ["latency analysis output"]}
{"analysis_results": ["volume analysis output"]}
```

The state field uses a reducer:

```python
analysis_results: Annotated[list[str], operator.add]
```

That means:

```text
old list + branch output list
```

Without a reducer, parallel branches updating the same key can conflict.

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

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv9_parallel_workflow/notebook.ipynb
```

## Run CLI

```bash
python -m agentv9_parallel_workflow.main
```

## When to use this pattern

Use parallel workflow when:
- subtasks are independent
- each branch can analyze a separate dimension
- latency matters
- you want structured comparison before final synthesis

Examples:
- BI health report: failures + latency + volume
- CloudOps: logs + metrics + config analysis
- RAG: retrieve from multiple document collections
- Research: collect evidence from multiple sources
- Code review: security + performance + style checks
