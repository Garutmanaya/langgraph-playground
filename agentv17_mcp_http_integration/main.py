from __future__ import annotations

import asyncio
import os
import sys
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from mcp import ClientSession
from mcp.client.sse import sse_client


load_dotenv()

MCP_HTTP_URL = os.getenv("MCP_HTTP_URL", "http://127.0.0.1:8001/sse")


class AgentState(TypedDict):
    input: str
    plan: NotRequired[str]
    metrics_context: NotRequired[str]
    runbook_context: NotRequired[str]
    final_answer: NotRequired[str]


async def call_mcp_http_tool(tool_name: str, arguments: dict) -> str:
    async with sse_client(MCP_HTTP_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(tool_name, arguments=arguments)

    return "\n".join(
        item.text for item in result.content if getattr(item, "type", None) == "text"
    )


async def planner_node(state: AgentState) -> AgentState:
    return {
        "plan": (
            "Plan: call MCP HTTP metrics tool and MCP HTTP runbook tool in parallel, "
            "then synthesize the incident analysis."
        )
    }


async def mcp_http_tools_node(state: AgentState) -> AgentState:
    metrics_task = call_mcp_http_tool("get_epp_metrics", {"issue": state["input"]})
    runbook_task = call_mcp_http_tool("get_epp_runbook", {"issue": state["input"]})

    metrics_context, runbook_context = await asyncio.gather(
        metrics_task,
        runbook_task,
    )

    return {
        "metrics_context": metrics_context,
        "runbook_context": runbook_context,
    }


async def summarize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Plan:
{state["plan"]}

MCP HTTP metrics context:
{state["metrics_context"]}

MCP HTTP runbook context:
{state["runbook_context"]}

Write a concise incident analysis with:
1. likely cause
2. supporting evidence
3. recommended next action
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("mcp_http_tools", mcp_http_tools_node)
    graph_builder.add_node("summarize", summarize_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "mcp_http_tools")
    graph_builder.add_edge("mcp_http_tools", "summarize")
    graph_builder.add_edge("summarize", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})


async def main():
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout issue after release R13."
    result = await run_async(question)
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
