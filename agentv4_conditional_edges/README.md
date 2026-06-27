# agentv4_conditional_edges

This version introduces explicit conditional routing in LangGraph.

Graph:

```text
START → classifier → [math_agent | time_agent | general_agent] → END
```

Learning goals:

- Add a router/classifier node
- Store routing decision in graph state
- Use `add_conditional_edges`
- Route execution to different nodes
- Observe routing decisions in LangSmith
- Visualize branch paths in Jupyter

## Setup

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Create `.env`:

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
agentv4_conditional_edges/notebook.ipynb
```

## Run CLI

From repo root, if this folder is placed directly under the repo root:

```bash
python -m agentv4_conditional_edges.main "What is 25 * 12?"
python -m agentv4_conditional_edges.main "What is the current UTC time?"
python -m agentv4_conditional_edges.main "Explain LangGraph briefly"
```
