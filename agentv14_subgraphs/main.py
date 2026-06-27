from __future__ import annotations

import sys
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()


class ParentState(TypedDict):
    input: str
    route_note: NotRequired[str]
    sql_plan: NotRequired[str]
    sql_result: NotRequired[str]
    sql_summary: NotRequired[str]
    rag_context: NotRequired[str]
    rag_summary: NotRequired[str]
    final_answer: NotRequired[str]


class SqlState(TypedDict):
    input: str
    sql_plan: NotRequired[str]
    sql_result: NotRequired[str]
    sql_summary: NotRequired[str]


class RagState(TypedDict):
    input: str
    rag_context: NotRequired[str]
    rag_summary: NotRequired[str]


def supervisor_node(state: ParentState) -> ParentState:
    return {
        "route_note": "Supervisor selected SQL and RAG subgraphs for metrics plus document evidence."
    }


def sql_plan_node(state: SqlState) -> SqlState:
    return {
        "sql_plan": (
            "Plan: query failure volume and average response_time for CHECK-DOMAIN "
            "during and after release R13."
        )
    }


def sql_execute_node(state: SqlState) -> SqlState:
    return {
        "sql_result": (
            "SQL result: CHECK-DOMAIN CONNECTION_TIMEOUT volume increased after R13; "
            "average response_time exceeded 220 ms during peak windows."
        )
    }


def sql_summary_node(state: SqlState) -> SqlState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
Summarize this SQL analysis for an EPP SLA incident.

User request:
{state["input"]}

SQL plan:
{state["sql_plan"]}

SQL result:
{state["sql_result"]}
"""

    response = llm.invoke(prompt)
    return {"sql_summary": response.content}


def build_sql_subgraph():
    graph_builder = StateGraph(SqlState)

    graph_builder.add_node("sql_plan", sql_plan_node)
    graph_builder.add_node("sql_execute", sql_execute_node)
    graph_builder.add_node("sql_summary", sql_summary_node)

    graph_builder.add_edge(START, "sql_plan")
    graph_builder.add_edge("sql_plan", "sql_execute")
    graph_builder.add_edge("sql_execute", "sql_summary")
    graph_builder.add_edge("sql_summary", END)

    return graph_builder.compile()


def rag_retrieve_node(state: RagState) -> RagState:
    return {
        "rag_context": (
            "Retrieved docs: R13 release notes mention connection pool changes and a known "
            "CHECK-DOMAIN latency risk under saturation. Runbook recommends registry endpoint, "
            "DNS resolver, and upstream connectivity checks."
        )
    }


def rag_summary_node(state: RagState) -> RagState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
Summarize this retrieved document context for an EPP SLA incident.

User request:
{state["input"]}

Retrieved context:
{state["rag_context"]}
"""

    response = llm.invoke(prompt)
    return {"rag_summary": response.content}


def build_rag_subgraph():
    graph_builder = StateGraph(RagState)

    graph_builder.add_node("rag_retrieve", rag_retrieve_node)
    graph_builder.add_node("rag_summary", rag_summary_node)

    graph_builder.add_edge(START, "rag_retrieve")
    graph_builder.add_edge("rag_retrieve", "rag_summary")
    graph_builder.add_edge("rag_summary", END)

    return graph_builder.compile()


def final_synthesis_node(state: ParentState) -> ParentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Supervisor note:
{state.get("route_note", "")}

SQL summary:
{state.get("sql_summary", "")}

RAG summary:
{state.get("rag_summary", "")}

Write a concise final incident analysis with:
1. likely cause
2. supporting evidence
3. recommended next action
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_parent_graph():
    sql_subgraph = build_sql_subgraph()
    rag_subgraph = build_rag_subgraph()

    graph_builder = StateGraph(ParentState)

    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("sql_subgraph", sql_subgraph)
    graph_builder.add_node("rag_subgraph", rag_subgraph)
    graph_builder.add_node("final_synthesis", final_synthesis_node)

    graph_builder.add_edge(START, "supervisor")
    graph_builder.add_edge("supervisor", "sql_subgraph")
    graph_builder.add_edge("sql_subgraph", "rag_subgraph")
    graph_builder.add_edge("rag_subgraph", "final_synthesis")
    graph_builder.add_edge("final_synthesis", END)

    return graph_builder.compile()


def run(text: str) -> ParentState:
    graph = build_parent_graph()
    return graph.invoke({"input": text})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout risk after R13 using SQL and docs."
    result = run(question)
    print(result["final_answer"])
