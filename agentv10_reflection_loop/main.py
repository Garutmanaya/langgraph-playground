from __future__ import annotations

import json
import re
import sys
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()

MAX_REVISIONS = 2
PASS_SCORE = 8


class AgentState(TypedDict, total=False):
    input: str
    draft: str
    critique: str
    quality_score: int
    revision_count: int
    final_answer: str


def create_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0)


def draft_answer_node(state: AgentState) -> AgentState:
    llm = create_llm()

    prompt = f"""
Write a concise but useful answer to the user request.

User request:
{state["input"]}

For this playground, assume the domain is EPP SLA analytics and incident analysis.
Include:
- concise summary
- likely cause if applicable
- recommended next action
"""

    response = llm.invoke(prompt)
    return {
        "draft": response.content,
        "revision_count": 0,
    }


def parse_critic_response(text: str) -> tuple[int, str]:
    try:
        parsed = json.loads(text)
        score = int(parsed.get("quality_score", 0))
        critique = str(parsed.get("critique", text))
        return max(0, min(10, score)), critique
    except Exception:
        match = re.search(r"\b([0-9]|10)\b", text)
        score = int(match.group(1)) if match else 5
        return score, text


def critic_node(state: AgentState) -> AgentState:
    llm = create_llm()

    prompt = f"""
You are a strict quality critic for agent responses.

User request:
{state["input"]}

Current draft:
{state["draft"]}

Evaluate the draft on:
- correctness
- completeness
- specificity
- usefulness
- clarity
- whether it avoids unsupported claims

Return only valid JSON in this exact shape:
{{
  "quality_score": 0,
  "critique": "specific critique and missing items"
}}

Score from 0 to 10.
A score of 8 or higher means the answer is good enough.
"""

    response = llm.invoke(prompt)
    score, critique = parse_critic_response(response.content)

    return {
        "quality_score": score,
        "critique": critique,
    }


def route_after_critic(state: AgentState) -> str:
    if state.get("quality_score", 0) >= PASS_SCORE:
        return "final_answer"

    if state.get("revision_count", 0) >= MAX_REVISIONS:
        return "final_answer"

    return "revise_answer"


def revise_answer_node(state: AgentState) -> AgentState:
    llm = create_llm()

    prompt = f"""
Revise the draft based on the critique.

User request:
{state["input"]}

Current draft:
{state["draft"]}

Critique:
{state["critique"]}

Produce an improved answer.
Keep it concise, specific, and actionable.
"""

    response = llm.invoke(prompt)

    return {
        "draft": response.content,
        "revision_count": state.get("revision_count", 0) + 1,
    }


def final_answer_node(state: AgentState) -> AgentState:
    return {
        "final_answer": state["draft"]
    }


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("draft_answer", draft_answer_node)
    graph_builder.add_node("critic", critic_node)
    graph_builder.add_node("revise_answer", revise_answer_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "draft_answer")
    graph_builder.add_edge("draft_answer", "critic")

    graph_builder.add_conditional_edges(
        "critic",
        route_after_critic,
        {
            "revise_answer": "revise_answer",
            "final_answer": "final_answer",
        },
    )

    graph_builder.add_edge("revise_answer", "critic")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile()


def run(text: str = "Write an EPP SLA incident summary after release R13.") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text}, {"recursion_limit": 10})


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Write an EPP SLA incident summary after release R13."
    result = run(question)
    print("Quality score:", result.get("quality_score"))
    print("Revision count:", result.get("revision_count"))
    print()
    print(result["final_answer"])
