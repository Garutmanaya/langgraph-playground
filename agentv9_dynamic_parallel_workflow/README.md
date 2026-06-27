# agentv9_dynamic_parallel_workflow

This version upgrades `agentv9_parallel_workflow` from **static parallelism** to **dynamic parallelism**.

Static v9 ran every branch for every request.

Dynamic v9 runs only the branches selected for the user request.

---

## Graph

```text
START
  ↓
planner
  ├── failure_analysis   only if selected
  ├── latency_analysis   only if selected
  └── volume_analysis    only if selected
        ↓
    synthesize
        ↓
      END
```

---

## Why this version matters

In static parallel workflow:

```text
split
 ├── failure_analysis
 ├── latency_analysis
 └── volume_analysis
```

All branches run every time.

That is useful for full health reports, but wasteful for focused questions.

Example:

```text
User: Show only latency risk for the latest release.
```

Static v9 still runs:

```text
failure_analysis
latency_analysis
volume_analysis
```

Dynamic v9 should run only:

```text
latency_analysis
```

---

## Examples

### User asks failure-only question

```text
Compare failures after the latest release.
```

Selected branches:

```text
failure_analysis
```

---

### User asks latency + volume question

```text
Check latency and traffic volume after the release.
```

Selected branches:

```text
latency_analysis
volume_analysis
```

---

### User asks full health report

```text
Create full EPP SLA health report for latest release.
```

Selected branches:

```text
failure_analysis
latency_analysis
volume_analysis
```

---

## Core LangGraph concept: Send

Dynamic parallelism uses `Send`.

```python
from langgraph.constants import Send
```

The planner returns a list of dynamic sends:

```python
return [
    Send("failure_analysis", state),
    Send("latency_analysis", state),
]
```

This means:

```text
Run only these destination nodes.
```

---

## State reducer requirement

Multiple selected branches may update the same state field.

For example:

```python
{"analysis_results": ["failure output"]}
{"analysis_results": ["latency output"]}
```

So the state uses a reducer:

```python
analysis_results: Annotated[list[str], operator.add]
```

That means:

```text
merge branch outputs by list concatenation
```

Without this reducer, parallel branches writing to the same key can conflict.

---

## Difference from v7

v7 router chooses one route:

```text
router → one specialist → END
```

Dynamic v9 can choose multiple routes:

```text
planner → selected specialists → synthesize → END
```

---

## Difference from v8

v8 iterative SQL tool agent loops because each next SQL call depends on the previous result:

```text
assistant → SQL tool → assistant → SQL tool → final answer
```

Dynamic v9 runs independent selected branches in parallel:

```text
planner → selected branches → synthesize
```

Use v8 when steps are dependent.

Use v9 dynamic parallelism when selected analyses are independent.

---

## Concepts covered

- Dynamic fan-out
- Selective branch execution
- `Send`
- Parallel branch merging
- Reducer-based state merge
- LLM-based planner
- Fallback deterministic planner
- Synthesis after selected analyses
- LangSmith tracing for selected branches only

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
agentv9_dynamic_parallel_workflow/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv9_dynamic_parallel_workflow.main
```

Or:

```bash
python -m agentv9_dynamic_parallel_workflow.main "Check latency and volume after release"
```

---

## LangSmith trace

For a latency-only request, expected trace:

```text
Graph run
  ├── planner
  ├── latency_analysis
  └── synthesize
```

For a full health request, expected trace:

```text
Graph run
  ├── planner
  ├── failure_analysis
  ├── latency_analysis
  ├── volume_analysis
  └── synthesize
```

This is useful because you can confirm unnecessary branches were skipped.

---

## Production relevance

Dynamic parallelism is useful for:

- BI agents
- CloudOps incident agents
- RAG systems with multiple retrievers
- code review agents
- security investigation agents
- multi-agent supervisors

Example:

```text
CloudOps incident:
  planner selects logs_analysis + metrics_analysis
  skips cost_analysis and config_analysis
```

This reduces:

- latency
- token usage
- tool calls
- database queries
- noise in final synthesis
