# agentv13_supervisor_multi_agent

This version introduces a **Supervisor Multi-Agent** pattern.

Graph:

```text
START
  ↓
supervisor
  ├── sql_agent        if selected
  ├── rag_agent        if selected
  └── ops_agent        if selected
        ↓
    supervisor_synthesis
        ↓
      END
```

---

## Why this version matters

Earlier versions introduced related concepts:

- v7: router chooses one specialist
- v8: SQL tool agent can loop
- v9: dynamic parallel workflow selects branches
- v12: RAG agent retrieves document context

v13 combines those ideas into a supervisor-style architecture.

The supervisor decides which specialist agents should contribute, sends work to them, then synthesizes the final answer.

---

## Router vs Supervisor

### Router Agent

A router usually chooses one destination.

```text
router → sql_agent → END
```

Good for:

```text
"Route this request to the correct handler."
```

---

### Supervisor Agent

A supervisor can coordinate multiple agents.

```text
supervisor
  ├── sql_agent
  ├── rag_agent
  └── ops_agent
      ↓
  synthesis
```

Good for:

```text
"Use multiple specialists and combine their answers."
```

---

## Example

User asks:

```text
Investigate CHECK-DOMAIN timeout spike after release R13 using metrics, docs, and operations checks.
```

Supervisor may select:

```text
sql_agent
rag_agent
ops_agent
```

Each specialist returns a partial answer.

The supervisor synthesizes:

```text
- SQL metrics show increased CHECK-DOMAIN timeout volume.
- RAG docs say R13 had connection pool saturation risk.
- Ops checks recommend registry endpoint and DNS resolver validation.
- Final recommendation: inspect connection pool saturation and upstream registry connectivity.
```

---

## Concepts covered

- Supervisor agent
- Multi-agent orchestration
- Specialist agents
- Dynamic delegation
- Parallel delegation with `Send`
- Reducer-based merging
- Supervisor synthesis
- LangSmith trace for multi-agent execution

---

## How this differs from v9

v9 dynamic parallel workflow selected fixed analysis branches:

```text
failure_analysis
latency_analysis
volume_analysis
```

v13 uses named specialist agents:

```text
sql_agent
rag_agent
ops_agent
```

The architecture is closer to enterprise agent systems:

```text
Supervisor
  ├── Data/SQL Agent
  ├── RAG/Docs Agent
  ├── CloudOps Agent
  └── Security Agent
```

---

## State reducer

Multiple agents update the same field:

```python
agent_outputs: Annotated[list[str], operator.add]
```

Each specialist returns:

```python
{"agent_outputs": ["SQL Agent: ..."]}
```

LangGraph merges those outputs into one list.

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
agentv13_supervisor_multi_agent/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv13_supervisor_multi_agent.main
```

Or:

```bash
python -m agentv13_supervisor_multi_agent.main "Investigate CHECK-DOMAIN timeout spike after release R13 using docs and metrics"
```

---

## LangSmith trace

Expected trace:

```text
Graph run
  ├── supervisor
  │     └── ChatOpenAI delegation decision
  ├── sql_agent
  ├── rag_agent
  ├── ops_agent
  └── supervisor_synthesis
        └── ChatOpenAI final synthesis
```

Only selected agents should run.

---

## Production relevance

Supervisor patterns are common in:

- CloudOps agents
- BI agents
- enterprise support agents
- security investigation agents
- data + document hybrid agents
- A2A orchestration
- multi-agent assistants

This is the bridge from simple workflows to real multi-agent systems.
