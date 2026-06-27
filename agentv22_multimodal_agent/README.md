# agentv22_multimodal_agent

This version introduces a **multimodal LangGraph agent**.

The agent accepts:

```text
text question + image
```

and uses a vision-capable OpenAI model to inspect the image and answer.

## Graph

```text
START → prepare_image → vision_analysis → final_answer → END
```

## What this version demonstrates

- image input
- base64 image encoding
- OpenAI vision message format
- LangGraph state for multimodal inputs
- structured visual analysis
- final answer generation
- notebook-based testing
- `NotRequired` state typing

## Why multimodal agents matter

Many production agents need to inspect:

- screenshots
- diagrams
- charts
- receipts
- documents
- monitoring dashboards
- architecture images
- incident screenshots
- logs captured as images

Text-only agents cannot handle these well.

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter pillow
```

Required `.env`:

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
agentv22_multimodal_agent/notebook.ipynb
```

## Run CLI

```bash
python -m agentv22_multimodal_agent.main
```

Or:

```bash
python -m agentv22_multimodal_agent.main "What does this monitoring dashboard show?"
```

The CLI creates a sample monitoring dashboard image automatically.

## Files created at runtime

```text
sample_dashboard.png
```

## Production relevance

For your future CloudOps / AI-BI agent, this is useful for:

```text
User uploads CloudWatch screenshot
Agent reads chart visually
Agent summarizes incident signal
Agent recommends next action
```

For enterprise agents, multimodal input is common because users often share screenshots instead of structured data.
