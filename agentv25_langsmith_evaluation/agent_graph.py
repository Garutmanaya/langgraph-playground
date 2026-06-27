from __future__ import annotations

from typing import NotRequired, TypedDict
from langgraph.graph import START, END, StateGraph

class AgentState(TypedDict):
    input: str
    classification: NotRequired[str]
    answer: NotRequired[str]

def classify_node(state: AgentState) -> AgentState:
    text = state["input"].lower()
    if any(term in text for term in ["timeout", "latency", "incident", "error", "spike"]):
        classification = "incident_analysis"
    elif any(term in text for term in ["metric", "metrics", "count", "volume", "by command", "by client"]):
        classification = "analytics"
    else:
        classification = "general"
    return {"classification": classification}

def answer_node(state: AgentState) -> AgentState:
    c = state["classification"]
    if c == "incident_analysis":
        answer = (
            "This is an EPP incident analysis request. For CHECK-DOMAIN after R13, "
            "inspect CONNECTION_TIMEOUT, elevated latency, failure concentration by client, "
            "registry connectivity, DNS resolver latency, and connection pool saturation."
        )
    elif c == "analytics":
        answer = (
            "This is an EPP analytics request. Analyze metrics by command, client, "
            "failure reason, volume, response_time, and grouped failures by client and command."
        )
    else:
        answer = (
            "This agent is used for EPP SLA analysis, including incidents, metrics, "
            "latency, failure volume, release impact, and operational recommendations."
        )
    return {"answer": answer}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("classify", classify_node)
    g.add_node("answer", answer_node)
    g.add_edge(START, "classify")
    g.add_edge("classify", "answer")
    g.add_edge("answer", END)
    return g.compile()

def run(text: str) -> AgentState:
    return build_graph().invoke({"input": text})
