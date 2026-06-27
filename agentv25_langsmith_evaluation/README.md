# agentv25_langsmith_evaluation

This version introduces agent evaluation and regression testing.

It includes:

- `eval_cases.jsonl`
- deterministic graph under test
- local evaluators
- local regression runner
- optional LangSmith dataset upload helper
- notebook

## Run local evaluation

```bash
python -m agentv25_langsmith_evaluation.run_local_eval
```

## Optional LangSmith dataset upload

```bash
python -m agentv25_langsmith_evaluation.langsmith_dataset
```

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langsmith python-dotenv ipython jupyter
```

## Why this matters

Production agents need repeatable checks for:

- routing/classification
- required domain terms
- hallucination avoidance
- regression detection after prompt/model/tool changes
