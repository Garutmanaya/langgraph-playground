from __future__ import annotations

import asyncio
import sys
from typing import NotRequired, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph

from .a2a_streaming_client import A2AStreamingClient


load_dotenv()


class AgentState(TypedDict):
    input: str
    agent_card: NotRequired[dict]
    capabilities: NotRequired[dict]
    task_id: NotRequired[str]
    task: NotRequired[dict]
    events: NotRequired[list[dict]]
    artifacts: NotRequired[dict]
    final_answer: NotRequired[str]


async def discover_agent_node(state: AgentState) -> AgentState:
    client = A2AStreamingClient()
    return {
        "agent_card": await client.get_agent_card(),
        "capabilities": await client.get_capabilities(),
    }


async def submit_task_node(state: AgentState) -> AgentState:
    client = A2AStreamingClient()
    task = await client.create_task(
        input_text=state["input"],
        context_id="ctx_langgraph_streaming_host",
        metadata={"caller": "agentv20_langgraph_host"},
    )
    return {"task_id": task["task_id"], "task": task}


async def stream_task_node(state: AgentState) -> AgentState:
    client = A2AStreamingClient()
    events = []

    async for event in client.stream_task_events(state["task_id"]):
        print(f"[remote event] {event['event']}: {event['data'].get('message')}")
        events.append(event)
        if event["event"] in {"completed", "failed", "canceled", "rejected"}:
            break

    task = await client.get_task(state["task_id"])
    return {"events": events, "task": task}


async def fetch_artifacts_node(state: AgentState) -> AgentState:
    client = A2AStreamingClient()
    return {"artifacts": await client.get_task_artifacts(state["task_id"])}


async def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Remote agent:
{state["agent_card"]["name"]}

Capabilities:
{state["capabilities"]}

Streamed events:
{state["events"]}

Final task:
{state["task"]}

Artifacts:
{state["artifacts"]}

Write a concise final answer based on the streamed A2A remote agent result.
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("discover_agent", discover_agent_node)
    graph_builder.add_node("submit_task", submit_task_node)
    graph_builder.add_node("stream_task", stream_task_node)
    graph_builder.add_node("fetch_artifacts", fetch_artifacts_node)
    graph_builder.add_node("synthesize", synthesize_node)

    graph_builder.add_edge(START, "discover_agent")
    graph_builder.add_edge("discover_agent", "submit_task")
    graph_builder.add_edge("submit_task", "stream_task")
    graph_builder.add_edge("stream_task", "fetch_artifacts")
    graph_builder.add_edge("fetch_artifacts", "synthesize")
    graph_builder.add_edge("synthesize", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})


async def main():
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after R13."
    result = await run_async(question)

    print("\nRemote agent:", result["agent_card"]["name"])
    print("Task ID:", result["task_id"])
    print("Task state:", result["task"]["status"]["state"])
    print()
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
