# agentv3_tool_calling

This version introduces real tool calling with LangGraph.

Graph:

```text
START → assistant → tools → assistant → END
```

Learning goals:

- Define real tools with `@tool`
- Bind tools to `ChatOpenAI`
- Let the LLM decide whether to call a tool
- Execute tool calls through LangGraph `ToolNode`
- Route conditionally using `tools_condition`
- Visualize the graph in Jupyter
- Inspect LLM and tool-call traces in LangSmith

## Setup

From your main playground repo root:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

Create `.env` either in the repo root or inside this folder:

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
agentv3_tool_calling/notebook.ipynb
```

## Run CLI

From repo root, if this folder is placed directly under the repo root:

```bash
python -m agentv3_tool_calling.main "What is 123 * 456?"
python -m agentv3_tool_calling.main "What is the current UTC time?"
python -m agentv3_tool_calling.main "How many CPU cores are available on this machine?"
```
