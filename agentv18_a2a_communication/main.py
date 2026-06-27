from __future__ import annotations

import asyncio
import os
import sys
from typing import NotRequired, TypedDict

import httpx
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()

SQL_AGENT_URL = os.getenv("SQL_AGENT_URL", "http://127.0.0.1:8101/analyze")
RAG_AGENT_URL = os.getenv("RAG_AGENT_URL", "http://127.0.0.1:8102/analyze")


class AgentState(TypedDict):
    input: str
    plan: NotRequired[str]
    sql_agent_result: NotRequired[str]
    rag_agent_result: NotRequired[str]
    final_answer: NotRequired[str]


async def planner_node(state: AgentState) -> AgentState:
    return {
        "plan": (
            "Delegate structured metrics analysis to SQL Agent and document/runbook "
            "analysis to RAG Agent, then synthesize the combined result."
        )
    }


async def call_remote_agent(url: str, task: str) -> str:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json={"task": task})
        response.raise_for_status()
        payload = response.json()

    return f"{payload['agent_name']}: {payload['analysis']}"


async def call_sql_agent_node(state: AgentState) -> AgentState:
    result = await call_remote_agent(SQL_AGENT_URL, state["input"])
    return {"sql_agent_result": result}


async def call_rag_agent_node(state: AgentState) -> AgentState:
    result = await call_remote_agent(RAG_AGENT_URL, state["input"])
    return {"rag_agent_result": result}


async def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Plan:
{state["plan"]}

SQL specialist result:
{state["sql_agent_result"]}

RAG specialist result:
{state["rag_agent_result"]}

Write a concise final incident analysis with:
1. likely cause
2. evidence from both agents
3. recommended next action
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("call_sql_agent", call_sql_agent_node)
    graph_builder.add_node("call_rag_agent", call_rag_agent_node)
    graph_builder.add_node("synthesize", synthesize_node)

    graph_builder.add_edge(START, "planner")

    # Parallel A2A calls.
    graph_builder.add_edge("planner", "call_sql_agent")
    graph_builder.add_edge("planner", "call_rag_agent")

    # Join before synthesis.
    graph_builder.add_edge("call_sql_agent", "synthesize")
    graph_builder.add_edge("call_rag_agent", "synthesize")

    graph_builder.add_edge("synthesize", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})


async def main():
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after R13 using metrics and docs."
    result = await run_async(question)
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
