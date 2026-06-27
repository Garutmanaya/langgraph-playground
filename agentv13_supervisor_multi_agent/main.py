from __future__ import annotations

import json
import operator
import sys
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.constants import Send
from langgraph.graph import START, END, StateGraph


load_dotenv()


AgentName = Literal["sql_agent", "rag_agent", "ops_agent"]


class AgentState(TypedDict, total=False):
    input: str
    selected_agents: list[AgentName]
    agent_outputs: Annotated[list[str], operator.add]
    final_answer: str


def fallback_select_agents(text: str) -> list[AgentName]:
    normalized = text.lower()
    selected: list[AgentName] = []

    if any(term in normalized for term in ["sql", "metric", "metrics", "database", "volume", "failure", "latency", "count"]):
        selected.append("sql_agent")

    if any(term in normalized for term in ["doc", "docs", "pdf", "runbook", "release notes", "policy", "knowledge"]):
        selected.append("rag_agent")

    if any(term in normalized for term in ["ops", "operation", "restart", "service", "cloud", "aws", "endpoint", "dns", "connectivity"]):
        selected.append("ops_agent")

    if not selected:
        selected = ["sql_agent", "rag_agent", "ops_agent"]

    return selected


def supervisor_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
You are a supervisor agent.

Available specialist agents:
- sql_agent: database metrics, failure counts, latency, volume, structured analytics
- rag_agent: PDFs, runbooks, release notes, policies, document lookup
- ops_agent: operational checks, service health, AWS/cloud remediation, connectivity, DNS, endpoints

Select all agents needed to answer the user request.

Return only valid JSON:
{{"selected_agents": ["sql_agent", "rag_agent"]}}

Rules:
- Select multiple agents if the request requires multiple evidence sources.
- Select sql_agent for metrics, counts, failures, latency, volume, database analytics.
- Select rag_agent for docs, runbooks, PDFs, release notes, policy questions.
- Select ops_agent for operational checks, remediation, cloud/service investigation.
- If unclear, select all agents.

User request:
{state["input"]}
"""

    try:
        response = llm.invoke(prompt).content.strip()
        parsed = json.loads(response)
        selected = parsed.get("selected_agents", [])
        allowed = {"sql_agent", "rag_agent", "ops_agent"}
        selected = [agent for agent in selected if agent in allowed]
        if not selected:
            selected = fallback_select_agents(state["input"])
    except Exception:
        selected = fallback_select_agents(state["input"])

    return {
        "selected_agents": selected,
        "agent_outputs": [],
    }


def delegate_to_selected_agents(state: AgentState):
    return [
        Send(agent_name, {"input": state["input"]})
        for agent_name in state["selected_agents"]
    ]


def sql_agent_node(state: AgentState) -> AgentState:
    # This is a specialist-agent placeholder for v13.
    # It intentionally does not recreate the full v8 SQL tool loop.
    return {
        "agent_outputs": [
            "SQL Agent: Metrics indicate CHECK-DOMAIN timeout volume increased after release R13, with CONNECTION_TIMEOUT as the likely dominant failure reason."
        ]
    }


def rag_agent_node(state: AgentState) -> AgentState:
    # This simulates a docs specialist. The full real RAG implementation is in v12.
    return {
        "agent_outputs": [
            "RAG Agent: Release/runbook context indicates R13 introduced connection pool changes and CHECK-DOMAIN latency risk under saturation."
        ]
    }


def ops_agent_node(state: AgentState) -> AgentState:
    return {
        "agent_outputs": [
            "Ops Agent: Recommended checks are registry endpoint health, DNS resolver latency, upstream connectivity, and connection pool saturation."
        ]
    }


def supervisor_synthesis_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    outputs = "\n".join(f"- {item}" for item in state.get("agent_outputs", []))
    selected = ", ".join(state.get("selected_agents", []))

    prompt = f"""
User request:
{state["input"]}

Selected agents:
{selected}

Specialist outputs:
{outputs}

Write a concise final answer that synthesizes specialist outputs.
Include:
1. likely conclusion
2. supporting evidence by specialist
3. recommended next action
Do not mention agents that were not selected.
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("supervisor", supervisor_node)
    graph_builder.add_node("sql_agent", sql_agent_node)
    graph_builder.add_node("rag_agent", rag_agent_node)
    graph_builder.add_node("ops_agent", ops_agent_node)
    graph_builder.add_node("supervisor_synthesis", supervisor_synthesis_node)

    graph_builder.add_edge(START, "supervisor")

    graph_builder.add_conditional_edges(
        "supervisor",
        delegate_to_selected_agents,
        ["sql_agent", "rag_agent", "ops_agent"],
    )

    graph_builder.add_edge("sql_agent", "supervisor_synthesis")
    graph_builder.add_edge("rag_agent", "supervisor_synthesis")
    graph_builder.add_edge("ops_agent", "supervisor_synthesis")
    graph_builder.add_edge("supervisor_synthesis", END)

    return graph_builder.compile()


def run(text: str) -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after release R13 using metrics, docs, and operations checks."
    result = run(question)
    print("Selected agents:", result["selected_agents"])
    print()
    print(result["final_answer"])
