# agentv11_human_in_loop

This version introduces **explicit human approval/rejection** before executing an action.

Graph:

```text
START → planner → approval_gate → execute_action → final_answer → END
```

The graph pauses before `approval_gate`.

The human then types:

```text
approve
```

or:

```text
reject
```

The decision is written into graph state using:

```python
graph.update_state(config, {"approval_decision": approval_decision})
```

Then the graph resumes:

```python
graph.invoke(None, config=config)
```

---

## Why this version was updated

The earlier v11 demo defaulted to approved during resume:

```python
decision = state.get("approval_decision", "approved")
```

That made the second invoke behave like auto-approval.

This version fixes that.

Now the graph does **not** auto-approve. The human decision is explicitly collected and written into checkpointed state before resume.

---

## Core flow

```text
1. Run graph
2. Graph pauses before approval_gate
3. Inspect proposed_action
4. Human enters approve/reject
5. graph.update_state(...) stores approval_decision
6. graph.invoke(None, config=config) resumes execution
7. execute_action either executes or skips
```

---

## Why checkpointer is required

Interrupts require saved state.

When the graph pauses, LangGraph must remember:

- current state
- next node
- thread ID
- checkpoint metadata

This version uses:

```python
InMemorySaver()
```

For production, use durable persistence such as SQLite/Postgres-backed checkpointing.

---

## Difference from v6

v6 used checkpointing for conversation memory:

```text
thread_id → message history
```

v11 uses checkpointing for interrupted execution:

```text
thread_id → paused workflow state + next node
```

---

## Difference from v10

v10 loops automatically:

```text
draft → critic → revise
```

v11 pauses for human judgment:

```text
planner → pause → human approves/rejects → execute or skip
```

---

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

---

## Run notebook

```bash
jupyter lab
```

Open:

```text
agentv11_human_in_loop/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv11_human_in_loop.main
```

The CLI will prompt:

```text
Approve action? Type approve or reject:
```

---

## Production relevance

This pattern is essential for:

- CloudOps remediation agents
- SQL/data modification agents
- email-sending agents
- deployment agents
- security operations agents
- approval workflows
- regulated business processes

For your AWS/CloudOps agent, the safe pattern is:

```text
diagnose → propose remediation → human approval → execute
```

Do not let an agent directly execute risky operations without an approval gate.

---

## LangSmith trace

Expected trace:

```text
Graph run
  ├── planner
  └── interrupted before approval_gate

Human:
  approve/reject

Resume:
Graph run
  ├── approval_gate
  ├── execute_action
  └── final_answer
```

LangSmith helps inspect:

- proposed action
- pause point
- human decision
- executed/skipped action
- final answer
