from __future__ import annotations

import operator
import sys
from typing import Annotated, NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from .context_store import SharedContextStore


load_dotenv()

DEFAULT_CONTEXT_ID = "epp_incident_context"


class AgentState(TypedDict):
    input: str
    context_id: str
    loaded_context: NotRequired[dict]
    recent_events: NotRequired[list[dict]]
    known_facts: NotRequired[list[dict]]
    plan: NotRequired[str]
    agent_outputs: Annotated[list[str], operator.add]
    final_answer: NotRequired[str]


def load_context_node(state: AgentState) -> AgentState:
    store = SharedContextStore()
    context_id = state["context_id"]

    loaded_context = store.get_all_values(context_id)
    recent_events = store.list_events(context_id, limit=10)
    known_facts = store.list_facts(context_id, limit=20)

    return {
        "loaded_context": loaded_context,
        "recent_events": recent_events,
        "known_facts": known_facts,
        "agent_outputs": [],
    }


def planner_node(state: AgentState) -> AgentState:
    prior_command = state["loaded_context"].get("preferred_command", "CHECK-DOMAIN")
    threshold = state["loaded_context"].get("risk_threshold_ms", 220)

    plan = (
        f"Use shared context. Preferred command is {prior_command}. "
        f"Risk threshold is {threshold} ms. Ask metrics and runbook agents to analyze the incident."
    )

    return {"plan": plan}


def metrics_agent_node(state: AgentState) -> AgentState:
    store = SharedContextStore()
    context_id = state["context_id"]

    output = (
        "Metrics Agent: CHECK-DOMAIN p95 response_time is around 240 ms after R13. "
        "CONNECTION_TIMEOUT volume is elevated for client_b during peak traffic."
    )

    store.add_event(
        context_id=context_id,
        event_type="agent_observation",
        source="metrics_agent",
        message="Observed elevated CHECK-DOMAIN latency and timeout volume.",
        payload={
            "command": "CHECK-DOMAIN",
            "p95_response_time_ms": 240,
            "failure_reason": "CONNECTION_TIMEOUT",
            "client": "client_b",
        },
    )

    store.add_fact(
        context_id=context_id,
        fact_type="incident_signal",
        fact_key="primary_command",
        fact_value="CHECK-DOMAIN",
        confidence=0.95,
        source="metrics_agent",
    )

    store.add_fact(
        context_id=context_id,
        fact_type="incident_signal",
        fact_key="primary_failure_reason",
        fact_value="CONNECTION_TIMEOUT",
        confidence=0.93,
        source="metrics_agent",
    )

    return {"agent_outputs": [output]}


def runbook_agent_node(state: AgentState) -> AgentState:
    store = SharedContextStore()
    context_id = state["context_id"]

    output = (
        "Runbook Agent: For CHECK-DOMAIN timeout spikes, inspect upstream registry endpoint health, "
        "DNS resolver latency, and connection pool saturation. Rollback if elevated timeout volume "
        "persists for two consecutive hours."
    )

    store.add_event(
        context_id=context_id,
        event_type="agent_observation",
        source="runbook_agent",
        message="Loaded runbook guidance for CHECK-DOMAIN timeout incident.",
        payload={
            "recommended_checks": [
                "registry endpoint health",
                "DNS resolver latency",
                "connection pool saturation",
            ]
        },
    )

    store.add_fact(
        context_id=context_id,
        fact_type="runbook_guidance",
        fact_key="recommended_check",
        fact_value="connection pool saturation",
        confidence=0.9,
        source="runbook_agent",
    )

    return {"agent_outputs": [output]}


def write_context_node(state: AgentState) -> AgentState:
    store = SharedContextStore()
    context_id = state["context_id"]

    store.set_value(context_id, "preferred_command", "CHECK-DOMAIN")
    store.set_value(context_id, "risk_threshold_ms", 220)
    store.set_value(context_id, "last_user_request", state["input"])
    store.set_value(context_id, "last_plan", state["plan"])

    store.add_event(
        context_id=context_id,
        event_type="workflow_summary",
        source="langgraph_host",
        message="Shared context updated after incident workflow.",
        payload={"agent_outputs": state["agent_outputs"]},
    )

    return {}


def final_answer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    outputs = "\n".join(f"- {item}" for item in state["agent_outputs"])

    prompt = f"""
User request:
{state["input"]}

Loaded shared context:
{state["loaded_context"]}

Recent context events:
{state["recent_events"]}

Known facts:
{state["known_facts"]}

Plan:
{state["plan"]}

Agent outputs:
{outputs}

Write a concise final answer. Mention whether prior shared context influenced the answer.
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("load_context", load_context_node)
    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("metrics_agent", metrics_agent_node)
    graph_builder.add_node("runbook_agent", runbook_agent_node)
    graph_builder.add_node("write_context", write_context_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "load_context")
    graph_builder.add_edge("load_context", "planner")

    graph_builder.add_edge("planner", "metrics_agent")
    graph_builder.add_edge("planner", "runbook_agent")

    graph_builder.add_edge("metrics_agent", "write_context")
    graph_builder.add_edge("runbook_agent", "write_context")

    graph_builder.add_edge("write_context", "final_answer")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile()


def run(question: str, context_id: str = DEFAULT_CONTEXT_ID) -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": question, "context_id": context_id})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after release R13."
    result = run(question)

    print("Context ID:", result["context_id"])
    print()
    print(result["final_answer"])
