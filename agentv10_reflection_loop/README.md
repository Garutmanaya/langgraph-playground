# agentv10_reflection_loop

This version introduces a **reflection loop**.

Graph:

```text
START
  ↓
draft_answer
  ↓
critic
  ↓
should_revise?
  ├── yes → revise_answer → critic → ...
  └── no  → final_answer → END
```

---

## Why reflection loops matter

Many agent workflows need quality control before returning a final answer.

Example:

```text
User: Write an incident analysis for EPP SLA failures after release R13.
```

A single LLM response may be incomplete.

A reflection loop adds a second step:

```text
generate → critique → revise
```

This helps catch:

- missing evidence
- weak reasoning
- unsupported claims
- unclear final answer
- missing next actions

---

## Difference from previous versions

### v8 iterative SQL tool agent

The LLM loops because it may need more tool/data calls:

```text
assistant → sql_tool → assistant → sql_tool → assistant
```

### v9 dynamic parallel workflow

The planner selects branches:

```text
planner → selected branches → synthesize
```

### v10 reflection loop

The agent loops to improve answer quality:

```text
draft → critique → revise → critique → final
```

---

## Core idea

The graph keeps these state fields:

```python
draft: str
critique: str
quality_score: int
revision_count: int
final_answer: str
```

The critic decides whether the draft is good enough.

Routing logic:

```text
if quality_score >= threshold:
    final_answer
elif revision_count >= max_revisions:
    final_answer
else:
    revise_answer
```

---

## Why max revision guard is required

Reflection loops can become infinite if not controlled.

So this version uses:

```python
MAX_REVISIONS = 2
PASS_SCORE = 8
```

The loop stops when:

```text
quality_score >= 8
```

or:

```text
revision_count >= 2
```

---

## Concepts covered

- Reflection loop
- Critic node
- Revision node
- Conditional loop routing
- Iteration guard
- Structured critique
- LangSmith trace of draft/critique/revision cycles
- Quality gate pattern

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
agentv10_reflection_loop/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv10_reflection_loop.main
```

Or:

```bash
python -m agentv10_reflection_loop.main "Write an EPP SLA incident summary after release R13"
```

---

## LangSmith trace

Expected trace:

```text
Graph run
  ├── draft_answer
  │     └── ChatOpenAI
  ├── critic
  │     └── ChatOpenAI
  ├── revise_answer
  │     └── ChatOpenAI
  ├── critic
  │     └── ChatOpenAI
  └── final_answer
```

LangSmith is useful here because you can inspect:

- original draft
- critique
- revision instructions
- improved draft
- final quality score
- number of loop iterations

---

## Production relevance

Reflection loops are useful for:

- incident reports
- executive summaries
- code review agents
- legal/contract review
- RAG answer verification
- root cause analysis
- customer support responses
- final quality gates before user-visible output

They are expensive compared with single-shot generation, so use them selectively.
