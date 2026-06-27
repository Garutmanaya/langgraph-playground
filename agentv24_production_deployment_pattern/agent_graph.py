from __future__ import annotations

from typing import NotRequired, TypedDict

from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from .config import settings


class AgentState(TypedDict):
    input: str
    request_id: str
    context: NotRequired[dict]
    classification: NotRequired[str]
    analysis: NotRequired[str]
    final_answer: NotRequired[str]


def classify_request_node(state: AgentState) -> AgentState:
    text = state["input"].lower()

    if any(term in text for term in ["latency", "timeout", "failure", "incident", "error"]):
        classification = "incident_analysis"
    elif any(term in text for term in ["sql", "metric", "volume", "count"]):
        classification = "analytics"
    else:
        classification = "general"

    return {"classification": classification}


def analyze_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model=settings.model_name, temperature=settings.temperature)

    prompt = f"""
You are a production LangGraph agent.

Request id:
{state["request_id"]}

Classification:
{state["classification"]}

Optional context:
{state.get("context", {})}

User request:
{state["input"]}

Produce a concise operational analysis.
"""

    response = llm.invoke(prompt)
    return {"analysis": response.content}


def final_answer_node(state: AgentState) -> AgentState:
    return {
        "final_answer": (
            f"Classification: {state['classification']}\n\n"
            f"{state['analysis']}"
        )
    }


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("classify_request", classify_request_node)
    graph_builder.add_node("analyze", analyze_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "classify_request")
    graph_builder.add_edge("classify_request", "analyze")
    graph_builder.add_edge("analyze", "final_answer")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile()
