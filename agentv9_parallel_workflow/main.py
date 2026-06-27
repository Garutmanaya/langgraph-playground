from __future__ import annotations

import operator
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()


class AgentState(TypedDict, total=False):
    input: str
    analysis_results: Annotated[list[str], operator.add]
    final_answer: str


def split_node(state: AgentState) -> AgentState:
    return {"analysis_results": []}


def failure_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Failure analysis: CONNECTION_TIMEOUT is the dominant failure reason after the release window."
        ]
    }


def latency_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Latency analysis: response_time increased during the release window, especially for CHECK-DOMAIN."
        ]
    }


def volume_analysis_node(state: AgentState) -> AgentState:
    return {
        "analysis_results": [
            "Volume analysis: CHECK-DOMAIN failure volume increased more than other commands."
        ]
    }


def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    joined = "\\n".join(f"- {item}" for item in state["analysis_results"])

    prompt = f"""
User request:
{state["input"]}

Independent analysis results:
{joined}

Write a concise executive summary with:
1. overall health
2. likely root cause
3. recommended next action
"""

    response = llm.invoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    g = StateGraph(AgentState)

    g.add_node("split", split_node)
    g.add_node("failure_analysis", failure_analysis_node)
    g.add_node("latency_analysis", latency_analysis_node)
    g.add_node("volume_analysis", volume_analysis_node)
    g.add_node("synthesize", synthesize_node)

    g.add_edge(START, "split")

    g.add_edge("split", "failure_analysis")
    g.add_edge("split", "latency_analysis")
    g.add_edge("split", "volume_analysis")

    g.add_edge("failure_analysis", "synthesize")
    g.add_edge("latency_analysis", "synthesize")
    g.add_edge("volume_analysis", "synthesize")

    g.add_edge("synthesize", END)

    return g.compile()


def run(text: str = "Analyze EPP SLA health for the latest release.") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})


if __name__ == "__main__":
    result = run()
    print(result["final_answer"])
