from __future__ import annotations

import asyncio
import sys
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()


class AgentState(TypedDict):
    input: str
    plan: NotRequired[str]
    metrics_result: NotRequired[str]
    logs_result: NotRequired[str]
    final_answer: NotRequired[str]


async def planner_node(state: AgentState) -> AgentState:
    await asyncio.sleep(0.1)
    return {
        "plan": (
            "Plan: collect metrics, collect logs, then synthesize the likely cause "
            "and next action."
        )
    }


async def fetch_cloudwatch_metrics() -> str:
    await asyncio.sleep(1.0)
    return (
        "Metrics: CHECK-DOMAIN p95 response_time increased to 240 ms after R13; "
        "timeout volume increased for client_b."
    )


async def fetch_cloudwatch_logs() -> str:
    await asyncio.sleep(1.0)
    return (
        "Logs: repeated CONNECTION_TIMEOUT events for upstream registry endpoint "
        "during peak traffic windows."
    )


async def async_fetch_metrics_node(state: AgentState) -> AgentState:
    result = await fetch_cloudwatch_metrics()
    return {"metrics_result": result}


async def async_fetch_logs_node(state: AgentState) -> AgentState:
    result = await fetch_cloudwatch_logs()
    return {"logs_result": result}


async def summarize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Plan:
{state["plan"]}

Metrics:
{state["metrics_result"]}

Logs:
{state["logs_result"]}

Write a concise incident analysis with likely cause and next action.
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("async_fetch_metrics", async_fetch_metrics_node)
    graph_builder.add_node("async_fetch_logs", async_fetch_logs_node)
    graph_builder.add_node("summarize", summarize_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "async_fetch_metrics")
    graph_builder.add_edge("async_fetch_metrics", "async_fetch_logs")
    graph_builder.add_edge("async_fetch_logs", "summarize")
    graph_builder.add_edge("summarize", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})


async def stream_async(text: str) -> None:
    graph = build_graph()

    async for chunk in graph.astream(
        {"input": text},
        stream_mode="updates",
    ):
        print(chunk)


async def main():
    question = " ".join(sys.argv[1:]) or "Investigate EPP CHECK-DOMAIN latency after release R13."
    print("Streaming async graph updates:")
    await stream_async(question)

    print("\nFinal result:")
    result = await run_async(question)
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
