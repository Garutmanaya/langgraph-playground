# agentv12_rag_agent

This version introduces a real RAG workflow with PDF documents, embeddings, and a local Chroma vector database.

Graph:

```text
START → ingest_pdfs → retrieve_context → generate_answer → END
```

---

## Important fix in this version

The first v12 draft rebuilt the Chroma vector DB multiple times inside the notebook and inside the graph.

That can cause this error:

```text
Database error: attempt to write a readonly database
```

The cause is usually Chroma's SQLite database being reused while an earlier Chroma connection is still alive, or the notebook trying to delete/recreate `chroma_db/` while the vector DB is open.

This fixed version uses **idempotent ingestion**:

```text
if vector DB already exists:
    reuse it
else:
    create it
```

The graph no longer deletes and recreates Chroma on every run.

Manual reset is still available using:

```python
reset_vector_store()
```

---

## What this version demonstrates

- sample PDF generation
- PDF loading
- text splitting/chunking
- OpenAI embeddings
- Chroma vector database
- semantic retrieval
- answer generation with context
- LangGraph orchestration
- LangSmith tracing

---

## Why RAG matters

LLMs do not automatically know your private documents.

RAG solves this by:

```text
user question
  → retrieve relevant document chunks
  → provide chunks as context to LLM
  → generate grounded answer
```

---

## Difference from SQL agents

SQL is best for structured data:

```text
metrics, counts, rows, filters, joins
```

RAG is best for unstructured documents:

```text
PDFs, runbooks, policies, manuals, architecture docs
```

---

## Setup

Use your root-level `.env`.

Required packages:

```bash
pip install -U langgraph langchain langchain-openai langchain-community langchain-chroma chromadb pypdf reportlab langsmith python-dotenv ipython jupyter
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
agentv12_rag_agent/notebook.ipynb
```

---

## Run CLI

```bash
python -m agentv12_rag_agent.main "What should we check when CHECK-DOMAIN timeouts increase?"
```

---

## Files created at runtime

```text
docs/epp_runbook.pdf
docs/epp_release_notes.pdf
chroma_db/
```

If you need a clean reset:

```bash
rm -rf agentv12_rag_agent/chroma_db
```

or inside notebook:

```python
reset_vector_store()
```

---

## Production note

For production, do not rebuild embeddings on every request.

Use this lifecycle:

```text
ingest documents once
persist vector DB
serve retrieval queries many times
```

That is what this fixed version demonstrates.
