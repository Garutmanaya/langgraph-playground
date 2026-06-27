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


AnalysisName = Literal["failure_analysis", "latency_analysis", "volume_analysis"]


class AgentState(TypedDict, total=False):
    input: str
    selected_analyses: list[AnalysisName]
    analysis_results: Annotated[list[str], operator.add]
    final_answer: str


def fallback_select_analyses(text: str) -> list[AnalysisName]:
    normalized = text.lower()
    selected: list[AnalysisName] = []

    if any(term in normalized for term in ["failure", "failures", "failed", "error", "timeout", "reason"]):
        selected.append("failure_analysis")

    if any(term in normalized for term in ["latency", "response time", "slow", "performance"]):
        selected.append("latency_analysis")

    if any(term in normalized for term in ["volume", "traffic", "load", "count", "throughput"]):
        selected.append("volume_analysis")

    if not selected or any(term in normalized for term in ["full", "health", "overall", "summary", "release report"]):
        selected = ["failure_analysis", "latency_analysis", "volume_analysis"]

    return selected


def planner_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
You are a planner for an EPP SLA analysis workflow.

Available analysis branches:
- failure_analysis: failure counts, failed_reason, errors, timeout issues
- latency_analysis: response_time, slow performance, latency trends
- volume_analysis: volume, traffic, throughput, transaction counts

Select only the branches needed for the user request.

Return only valid JSON in this exact shape:
{{"selected_analyses": ["failure_analysis", "latency_analysis"]}}

Rules:
- If the user asks for full health, overall summary, or release report, select all branches.
- If the user asks only about latency, select latency_analysis only.
- If the user asks only about failures, select failure_analysis only.
- If the user asks only about volume or traffic, select volume_analysis only.

User request:
{state["input"]}
"""

    try:
        response = llm.invoke(prompt).content.strip()
        parsed = json.loads(response)
        selected = parsed.get("selected_analyses", [])
        allowed = {"failure_analysis", "latency_analysis", "volume_analysis"}
        selected = [item for item in selected if item in allowed]
        if not selected:
            selected = fallback_select_analyses(state["input"])
    except Exception:
        selected = fallback_select_analyses(state["input"])

    return {
        "selected_analyses": selected,
        "analysis_results": [],
    }


def dynamic_fanout(state: AgentState):
    return [
        Send(analysis_name, {"input": state["input"]})
        for analysis_name in state["selected_analyses"]
    ]


def failure_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Failure analysis: failure volume is concentrated in CHECK-DOMAIN, with CONNECTION_TIMEOUT as the dominant failed_reason."
        ]
    }


def latency_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Latency analysis: response_time increased during the release window, especially for CHECK-DOMAIN transactions."
        ]
    }


def volume_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Volume analysis: CHECK-DOMAIN transaction volume increased significantly compared with other commands."
        ]
    }


def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    selected = ", ".join(state.get("selected_analyses", []))
    results = "\n".join(f"- {item}" for item in state.get("analysis_results", []))

    prompt = f"""
User request:
{state["input"]}

Selected analyses:
{selected}

Analysis results:
{results}

Write a concise final response. Do not mention analyses that were not selected.
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("failure_analysis", failure_analysis_node)
    graph_builder.add_node("latency_analysis", latency_analysis_node)
    graph_builder.add_node("volume_analysis", volume_analysis_node)
    graph_builder.add_node("synthesize", synthesize_node)

    graph_builder.add_edge(START, "planner")

    graph_builder.add_conditional_edges(
        "planner",
        dynamic_fanout,
        ["failure_analysis", "latency_analysis", "volume_analysis"],
    )

    graph_builder.add_edge("failure_analysis", "synthesize")
    graph_builder.add_edge("latency_analysis", "synthesize")
    graph_builder.add_edge("volume_analysis", "synthesize")

    graph_builder.add_edge("synthesize", END)

    return graph_builder.compile()


def run(text: str = "Create full EPP SLA health report for latest release.") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Create full EPP SLA health report for latest release."
    result = run(question)
    print("Selected analyses:", result["selected_analyses"])
    print()
    print(result["final_answer"])
