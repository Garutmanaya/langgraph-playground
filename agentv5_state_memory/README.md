# agentv5_state_memory

This version introduces message-based state memory inside a LangGraph run.

Graph:

```text
START → assistant → END
```

The graph is structurally simple, but the state is now richer:

```text
messages: HumanMessage + AIMessage history
```

Learning goals:

- Use message-based state
- Use `add_messages` reducer
- Preserve conversation history inside graph state
- Pass prior messages to the LLM
- Observe multi-turn context in LangSmith
- Understand the difference between in-run state and durable persistence

Important distinction:

- `agentv5_state_memory` keeps memory in the state object you pass around manually.
- `agentv6_persistence_checkpointer` should introduce durable thread persistence with a checkpointer.

## Setup

Use the root-level `.env` you already created.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Required root `.env` values:

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
agentv5_state_memory/notebook.ipynb
```

## Run CLI

From repo root, if this folder is placed directly under the repo root:

```bash
python -m agentv5_state_memory.main
```
