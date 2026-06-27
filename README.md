# LangGraph Playground - Incremental Learning

This repository is being built version by version.

Current version:

```text
agentv1_basic_graph/
```

## Version 1: Basic Graph

Learning goals:

- Understand `StateGraph`
- Understand `START` and `END`
- Create one graph node
- Pass state into the graph
- Return updated state from a node
- Compile and invoke the graph
- Visualize the graph in Jupyter
- Enable LangSmith tracing from the beginning

## Setup

```bash
python -m venv .venv
source .venv/bin/activate

pip install -U langgraph langchain langsmith python-dotenv ipython jupyter
```

## LangSmith Setup

Create `.env` in the repository root:

```env
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=langgraph-playground
```

Then start Jupyter:

```bash
jupyter lab
```

Open:

```text
agentv1_basic_graph/notebook.ipynb
```
