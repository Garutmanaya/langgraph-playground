from __future__ import annotations

import sys
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()


class AgentState(TypedDict):
    input: str
    plan: NotRequired[str]
    draft: NotRequired[str]
    review: NotRequired[str]
    final_answer: NotRequired[str]


def planner_node(state: AgentState) -> AgentState:
    return {
        "plan": (
            "Plan: identify audience, summarize incident status, explain likely impact, "
            "and provide next action."
        )
    }


def writer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
Write a concise incident update.

User request:
{state["input"]}

Plan:
{state["plan"]}
"""
    response = llm.invoke(prompt)
    return {"draft": response.content}


def reviewer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
Review this incident update for clarity and actionability.

Draft:
{state["draft"]}

Return a short review and then provide the final improved version.
"""
    response = llm.invoke(prompt)
    return {
        "review": "Reviewed for clarity and actionability.",
        "final_answer": response.content,
    }


def build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("writer", writer_node)
    graph_builder.add_node("reviewer", reviewer_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "writer")
    graph_builder.add_edge("writer", "reviewer")
    graph_builder.add_edge("reviewer", END)

    return graph_builder.compile()


def stream_updates(text: str) -> None:
    graph = build_graph()
    print("\nStreaming graph updates:\n")
    for chunk in graph.stream({"input": text}, stream_mode="updates"):
        print(chunk)


def stream_llm_tokens(text: str) -> None:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, streaming=True)
    prompt = f"Write a concise EPP incident update for this request: {text}"

    print("\nStreaming LLM tokens:\n")
    for token in llm.stream(prompt):
        print(token.content, end="", flush=True)
    print()


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Write a short incident update for EPP CHECK-DOMAIN latency."
    stream_updates(question)
    stream_llm_tokens(question)
