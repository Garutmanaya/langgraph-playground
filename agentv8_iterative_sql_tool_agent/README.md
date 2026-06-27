# agentv8_iterative_sql_tool_agent

This version replaces the simpler deterministic v8 workflow with a more realistic agentic workflow:

```text
START → assistant → sql_tool → assistant → sql_tool → assistant → END
```

The LLM decides whether it needs to call the SQL tool again.

This is closer to a real Text-to-SQL BI agent.

---

## Why this version matters

In many analytics questions, one SQL query is not enough.

Example:

```text
Compare failed EPP transactions before and after the latest release and explain the root cause.
```

The agent may need multiple SQL calls:

```text
1. Find latest release window
2. Query failures before release
3. Query failures after release
4. Group failures by command/client/TLD
5. Compare results
6. Produce final explanation
```

A deterministic workflow can force these steps, but an agentic workflow lets the LLM decide:

```text
Do I have enough information?
Or should I call SQL again?
```

---

## Difference from previous v8 deterministic workflow

### Deterministic loop

```text
planner → sql_agent → evaluator → sql_agent → final_answer
```

Python decides whether to loop:

```python
if needs_more_sql:
    return "sql_agent"
else:
    return "final_answer"
```

This is useful when the workflow is predictable.

---

### LLM-controlled tool loop

```text
assistant → sql_tool → assistant → sql_tool → assistant → END
```

The LLM decides whether to call the SQL tool again.

LangGraph routing rule:

```text
If assistant returns tool_calls → go to sql_tool
If assistant returns no tool_calls → END
```

This is the standard ReAct-style agent loop:

```text
reason → act → observe → reason → act → observe → answer
```

---

## Graph

```text
START
  ↓
assistant
  ↓
tools_condition
  ├── if tool call exists → sql_tool
  │                         ↓
  │                     assistant
  │                         ↓
  │                    tools_condition
  └── if no tool call → END
```

---

## Concepts covered

- Real SQLite database
- Real SQL execution tool
- OpenAI tool calling
- LLM-controlled iterative execution
- Message state with `add_messages`
- LangGraph `ToolNode`
- LangGraph `tools_condition`
- Multi-step SQL analysis
- Safety guard for read-only SQL
- LangSmith tracing for LLM + SQL tool calls

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
agentv8_iterative_sql_tool_agent/notebook.ipynb
```

---

## Run CLI

From repo root, if this folder is placed directly under the repo root:

```bash
python -m agentv8_iterative_sql_tool_agent.main
```

Or:

```bash
python -m agentv8_iterative_sql_tool_agent.main "Compare failures before and after the latest release"
```

---

## Database schema

This version creates a local SQLite database at runtime:

```text
data/epp_sla_demo.db
```

Tables:

```sql
epp_release(
    release_name TEXT,
    release_start TEXT,
    release_end TEXT,
    release_location TEXT
)

epp_sla(
    date TEXT,
    hour INTEGER,
    command TEXT,
    tld TEXT,
    response_time REAL,
    result TEXT,
    volume INTEGER,
    client_name TEXT,
    failed_reason TEXT
)
```

The data is intentionally small but realistic enough to demonstrate iterative SQL analysis.

---

## SQL safety

The SQL tool only allows read-only queries.

Allowed:

```sql
SELECT ...
WITH ...
```

Blocked:

```sql
INSERT
UPDATE
DELETE
DROP
ALTER
CREATE
PRAGMA
ATTACH
```

This keeps the demo safer while still allowing real SQL execution.

---

## Expected behavior

Prompt:

```text
Compare failed transactions before and after the latest release and identify the main failure reason.
```

Possible agent behavior:

```text
assistant:
  I need the latest release window.
  call execute_sql("SELECT ... FROM epp_release ORDER BY release_end DESC LIMIT 1")

sql_tool:
  returns release window

assistant:
  I need failures before the release.
  call execute_sql("SELECT ... WHERE date < ...")

sql_tool:
  returns pre-release failures

assistant:
  I need failures during/after release.
  call execute_sql("SELECT ... WHERE date BETWEEN ...")

sql_tool:
  returns post-release failures

assistant:
  final answer
```

The exact sequence may vary because the LLM controls tool calls.

---

## LangSmith trace

In LangSmith, inspect project:

```text
langgraph-playground
```

Expected trace shape:

```text
Graph run
  ├── assistant
  │     └── ChatOpenAI with SQL tool schema
  ├── tools
  │     └── execute_sql
  ├── assistant
  │     └── ChatOpenAI
  ├── tools
  │     └── execute_sql
  └── assistant
        └── final answer
```

This is where LangSmith becomes very useful. You can inspect:

- model reasoning inputs
- tool call arguments
- generated SQL
- SQL results
- final answer
- token usage
- latency
- whether the model made too many SQL calls

---

## Key mental model

This version is not:

```text
one question → one SQL query → one answer
```

It is:

```text
question → LLM decides SQL query → observes result → decides next SQL query → final answer
```

That is the core pattern for BI agents, CloudOps agents, root cause analysis agents, and multi-step investigation agents.
