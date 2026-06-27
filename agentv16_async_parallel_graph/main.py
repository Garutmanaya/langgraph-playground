from __future__ import annotations

import asyncio
import sys
import time
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
    metrics_started_at: NotRequired[float]
    metrics_finished_at: NotRequired[float]
    logs_started_at: NotRequired[float]
    logs_finished_at: NotRequired[float]
    final_answer: NotRequired[str]

async def planner_node(state: AgentState) -> AgentState:
    await asyncio.sleep(0.1)
    return {"plan": "Collect metrics and logs in parallel, then synthesize cause and next action."}

async def fetch_cloudwatch_metrics() -> str:
    await asyncio.sleep(2.0)
    return "Metrics: CHECK-DOMAIN p95 response_time increased to 240 ms after R13; timeout volume increased for client_b."

async def fetch_cloudwatch_logs() -> str:
    await asyncio.sleep(3.0)
    return "Logs: repeated CONNECTION_TIMEOUT events for upstream registry endpoint during peak traffic windows."

async def async_fetch_metrics_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    result = await fetch_cloudwatch_metrics()
    finished = time.perf_counter()
    return {"metrics_result": result, "metrics_started_at": started, "metrics_finished_at": finished}

async def async_fetch_logs_node(state: AgentState) -> AgentState:
    started = time.perf_counter()
    result = await fetch_cloudwatch_logs()
    finished = time.perf_counter()
    return {"logs_result": result, "logs_started_at": started, "logs_finished_at": finished}

async def summarize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    metrics_duration = state["metrics_finished_at"] - state["metrics_started_at"]
    logs_duration = state["logs_finished_at"] - state["logs_started_at"]
    prompt = f"""
User request:
{state["input"]}

Plan:
{state["plan"]}

Metrics:
{state["metrics_result"]}

Logs:
{state["logs_result"]}

Timing:
metrics duration = {metrics_duration:.2f} seconds
logs duration = {logs_duration:.2f} seconds

Write a concise incident analysis with likely cause and next action.
"""
    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("planner", planner_node)
    g.add_node("async_fetch_metrics", async_fetch_metrics_node)
    g.add_node("async_fetch_logs", async_fetch_logs_node)
    g.add_node("summarize", summarize_node)
    g.add_edge(START, "planner")
    g.add_edge("planner", "async_fetch_metrics")
    g.add_edge("planner", "async_fetch_logs")
    g.add_edge("async_fetch_metrics", "summarize")
    g.add_edge("async_fetch_logs", "summarize")
    g.add_edge("summarize", END)
    return g.compile()

async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})

async def main():
    question = " ".join(sys.argv[1:]) or "Investigate EPP CHECK-DOMAIN latency after release R13."
    start = time.perf_counter()
    result = await run_async(question)
    elapsed = time.perf_counter() - start
    overlap = min(result["metrics_finished_at"], result["logs_finished_at"]) - max(result["metrics_started_at"], result["logs_started_at"])
    print("Elapsed seconds:", round(elapsed, 2))
    print("Branch overlap seconds:", round(max(0, overlap), 2))
    print()
    print(result["final_answer"])

if __name__ == "__main__":
    asyncio.run(main())
