from __future__ import annotations

import os
import sqlite3
import sys
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "epp_sla_demo.db"


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def initialize_database(db_path: Path = DB_PATH) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()

        cur.execute("DROP TABLE IF EXISTS epp_sla")
        cur.execute("DROP TABLE IF EXISTS epp_release")

        cur.execute("""
        CREATE TABLE epp_release (
            release_name TEXT,
            release_start TEXT,
            release_end TEXT,
            release_location TEXT
        )
        """)

        cur.execute("""
        CREATE TABLE epp_sla (
            date TEXT,
            hour INTEGER,
            command TEXT,
            tld TEXT,
            response_time REAL,
            result TEXT,
            volume INTEGER,
            client_name TEXT,
            failed_reason TEXT
        )
        """)

        releases = [
            ("R12", "2026-06-10", "2026-06-12", "us-east-1"),
            ("R13", "2026-06-20", "2026-06-22", "us-east-1"),
        ]

        sla_rows = [
            ("2026-06-17", 9, "ADD-DOMAIN", ".com", 120.0, "SUCCESS", 1200, "client_a", None),
            ("2026-06-18", 10, "ADD-DOMAIN", ".com", 128.0, "FAILURE", 40, "client_a", "AUTH_FAILED"),
            ("2026-06-19", 11, "CHECK-DOMAIN", ".net", 90.0, "FAILURE", 35, "client_b", "CONNECTION_TIMEOUT"),
            ("2026-06-20", 9, "ADD-DOMAIN", ".com", 190.0, "FAILURE", 95, "client_a", "AUTH_FAILED"),
            ("2026-06-20", 10, "CHECK-DOMAIN", ".net", 210.0, "FAILURE", 120, "client_b", "CONNECTION_TIMEOUT"),
            ("2026-06-21", 11, "CHECK-DOMAIN", ".net", 230.0, "FAILURE", 150, "client_b", "CONNECTION_TIMEOUT"),
            ("2026-06-21", 12, "RENEW-DOMAIN", ".org", 175.0, "FAILURE", 55, "client_c", "QUOTA_EXCEEDED"),
            ("2026-06-22", 13, "CHECK-DOMAIN", ".net", 240.0, "FAILURE", 180, "client_b", "CONNECTION_TIMEOUT"),
            ("2026-06-23", 10, "CHECK-DOMAIN", ".net", 160.0, "FAILURE", 70, "client_b", "CONNECTION_TIMEOUT"),
            ("2026-06-24", 10, "ADD-DOMAIN", ".com", 125.0, "SUCCESS", 1300, "client_a", None),
        ]

        cur.executemany("INSERT INTO epp_release VALUES (?, ?, ?, ?)", releases)
        cur.executemany("INSERT INTO epp_sla VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", sla_rows)

        conn.commit()

    return db_path


def is_read_only_sql(sql: str) -> bool:
    cleaned = sql.strip().lower()
    blocked = ["insert", "update", "delete", "drop", "alter", "create", "pragma", "attach", "detach", "replace", "vacuum"]
    return (cleaned.startswith("select") or cleaned.startswith("with")) and not any(word in cleaned for word in blocked)


@tool
def execute_sql(query: str) -> str:
    """Execute a read-only SQLite SELECT query against the EPP SLA demo database. Use this for analytics questions over epp_sla and epp_release."""
    initialize_database()

    if not is_read_only_sql(query):
        return "SQL rejected: only read-only SELECT/WITH queries are allowed."

    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query).fetchall()

        if not rows:
            return "No rows returned."

        result = [dict(row) for row in rows]
        return str(result[:20])
    except Exception as exc:
        return f"SQL execution error: {exc}"


TOOLS = [execute_sql]


SYSTEM_PROMPT = """You are an EPP SLA BI analyst.

You have access to a SQLite database with these tables:

epp_release(
  release_name TEXT,
  release_start TEXT,
  release_end TEXT,
  release_location TEXT
)

epp_sla(
  date TEXT,
  hour INTEGER,
  command TEXT,
  tld TEXT,
  response_time REAL,
  result TEXT,
  volume INTEGER,
  client_name TEXT,
  failed_reason TEXT
)

Rules:
- Use execute_sql for database questions.
- You may call execute_sql multiple times if needed.
- Prefer small targeted SQL queries.
- Only generate SELECT or WITH queries.
- Do not invent data.
- After enough SQL results are available, provide a concise final answer.
- When comparing before and after a release, first identify the relevant release window.
"""


def create_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(TOOLS)


def assistant_node(state: AgentState) -> AgentState:
    llm = create_llm()
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("assistant", assistant_node)
    graph_builder.add_node("tools", ToolNode(TOOLS))

    graph_builder.add_edge(START, "assistant")
    graph_builder.add_conditional_edges("assistant", tools_condition)
    graph_builder.add_edge("tools", "assistant")

    return graph_builder.compile()


def run(question: str):
    initialize_database()
    graph = build_graph()
    return graph.invoke(
        {
            "messages": [
                SystemMessage(content=SYSTEM_PROMPT),
                HumanMessage(content=question),
            ]
        },
        {"recursion_limit": 10},
    )


def final_text(state: AgentState) -> str:
    return state["messages"][-1].content


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Compare failed transactions before and after the latest release and identify the main failure reason."
    state = run(question)
    print(final_text(state))
