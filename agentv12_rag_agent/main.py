from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import START, END, StateGraph
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "docs"
CHROMA_DIR = BASE_DIR / "chroma_db"
COLLECTION_NAME = "epp_rag_docs"


class AgentState(TypedDict, total=False):
    input: str
    documents_loaded: bool
    retrieved_context: list[str]
    answer: str


def write_pdf(path: Path, title: str, paragraphs: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter

    y = height - 72
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, y, title)
    y -= 36

    c.setFont("Helvetica", 10)
    for paragraph in paragraphs:
        words = paragraph.split()
        line = ""
        for word in words:
            if len(line + " " + word) > 92:
                c.drawString(72, y, line)
                y -= 14
                line = word
                if y < 72:
                    c.showPage()
                    c.setFont("Helvetica", 10)
                    y = height - 72
            else:
                line = f"{line} {word}".strip()
        if line:
            c.drawString(72, y, line)
            y -= 20
        if y < 72:
            c.showPage()
            c.setFont("Helvetica", 10)
            y = height - 72

    c.save()


def create_sample_pdfs() -> list[Path]:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    runbook = DOCS_DIR / "epp_runbook.pdf"
    release_notes = DOCS_DIR / "epp_release_notes.pdf"

    write_pdf(
        runbook,
        "EPP SLA Operations Runbook",
        [
            "When CHECK-DOMAIN requests show elevated CONNECTION_TIMEOUT failures, first inspect upstream registry connectivity, DNS resolver latency, and client retry behavior.",
            "If response_time increases together with timeout volume, prioritize network path checks and registry endpoint health before application code changes.",
            "For ADD-DOMAIN AUTH_FAILED spikes, inspect credential rotation, client authentication configuration, and recent changes to access-control rules.",
            "Recommended incident workflow: compare failure volume before and after the release window, group failures by command and failed_reason, then identify the dominant client_name and tld.",
        ],
    )

    write_pdf(
        release_notes,
        "EPP Release R13 Notes",
        [
            "Release R13 was deployed from 2026-06-20 through 2026-06-22 in us-east-1.",
            "The release included registry connection pool changes, timeout tuning, and additional telemetry for CHECK-DOMAIN and ADD-DOMAIN commands.",
            "Known risk: CHECK-DOMAIN latency may increase if connection pool saturation occurs during peak traffic hours.",
            "Rollback criteria: sustained CONNECTION_TIMEOUT failure volume above baseline for two consecutive hours or response_time above 220 milliseconds for CHECK-DOMAIN.",
        ],
    )

    return [runbook, release_notes]


def load_and_split_pdfs(pdf_paths: list[Path]) -> list[Document]:
    docs: list[Document] = []

    for path in pdf_paths:
        loader = PyPDFLoader(str(path))
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=700,
        chunk_overlap=120,
    )

    return splitter.split_documents(docs)


def vector_store_exists() -> bool:
    return CHROMA_DIR.exists() and any(CHROMA_DIR.iterdir())


def reset_vector_store() -> None:
    if CHROMA_DIR.exists():
        shutil.rmtree(CHROMA_DIR)


def create_vector_store() -> Chroma:
    pdf_paths = create_sample_pdfs()
    chunks = load_and_split_pdfs(pdf_paths)

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    return Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )


def load_vector_store() -> Chroma:
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )


def ensure_vector_store() -> None:
    create_sample_pdfs()

    if not vector_store_exists():
        create_vector_store()


def ingest_pdfs_node(state: AgentState) -> AgentState:
    ensure_vector_store()
    return {"documents_loaded": True}


def retrieve_context_node(state: AgentState) -> AgentState:
    ensure_vector_store()
    vector_store = load_vector_store()

    docs = vector_store.similarity_search(
        state["input"],
        k=4,
    )

    context = [
        f"Source: {Path(doc.metadata.get('source', 'unknown')).name}, page {doc.metadata.get('page', 'unknown')}\n{doc.page_content}"
        for doc in docs
    ]

    return {"retrieved_context": context}


def generate_answer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    context = "\n\n---\n\n".join(state.get("retrieved_context", []))

    prompt = f"""
You are an EPP operations assistant.

Answer the user question using only the retrieved context.
If the context is insufficient, say what is missing.

User question:
{state["input"]}

Retrieved context:
{context}

Write a concise answer and mention the source PDF names when relevant.
"""

    response = llm.invoke(prompt)
    return {"answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("ingest_pdfs", ingest_pdfs_node)
    graph_builder.add_node("retrieve_context", retrieve_context_node)
    graph_builder.add_node("generate_answer", generate_answer_node)

    graph_builder.add_edge(START, "ingest_pdfs")
    graph_builder.add_edge("ingest_pdfs", "retrieve_context")
    graph_builder.add_edge("retrieve_context", "generate_answer")
    graph_builder.add_edge("generate_answer", END)

    return graph_builder.compile()


def run(question: str) -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": question})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What should we check when CHECK-DOMAIN timeouts increase?"
    result = run(question)
    print(result["answer"])
