# agentv11_human_in_loop

This version introduces human-in-the-loop approval.

Graph:

```text
START → planner → approval_gate → execute_action → final_answer → END
```

The graph pauses before `approval_gate`.

## Why human-in-the-loop matters

Some agent actions should not execute automatically.

Examples:

- deleting files
- sending emails
- applying infrastructure changes
- running database updates
- restarting services
- creating cloud resources
- approving financial transactions

The agent may prepare an action, but a human must approve before execution.

## Core pattern

The graph runs until it reaches an interrupt point.

```python
graph.compile(
    checkpointer=checkpointer,
    interrupt_before=["approval_gate"]
)
```

The first run pauses before `approval_gate`.

Then the user inspects the proposed action.

If approved, the graph resumes:

```python
graph.invoke(None, config=config)
```

## Why checkpointer is required

Interrupts need saved state.

When the graph pauses, LangGraph must remember:

- current state
- next node
- thread ID
- checkpoint metadata

So this version uses:

```python
InMemorySaver()
```

For production, use durable persistence such as SQLite/Postgres-backed checkpointing.

## Difference from v6

v6 used checkpointing for conversation memory:

```text
thread_id → message history
```

v11 uses checkpointing for interrupted execution:

```text
thread_id → paused workflow state + next node
```

## Difference from v10

v10 loops automatically:

```text
draft → critic → revise
```

v11 pauses for human judgment:

```text
planner → pause → human approves → execute
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
agentv11_human_in_loop/notebook.ipynb
```

## Run CLI

```bash
python -m agentv11_human_in_loop.main
```

The CLI demo auto-resumes after printing the approval checkpoint. The notebook is better for learning because you can inspect the paused state before resuming.

## Production relevance

This pattern is essential for:

- CloudOps remediation agents
- SQL/data modification agents
- email-sending agents
- deployment agents
- security operations agents
- approval workflows
- regulated business processes

For your AWS/CloudOps agent, this is the key safety pattern:

```text
diagnose → propose remediation → human approval → execute
```

Do not let an agent directly execute risky operations without an approval gate.

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  └── interrupted before approval_gate

Resume:
Graph run
  ├── approval_gate
  ├── execute_action
  └── final_answer
```
