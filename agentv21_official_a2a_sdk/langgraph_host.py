from __future__ import annotations

import asyncio
import sys
from typing import NotRequired, TypedDict

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import new_text_message
from a2a.types.a2a_pb2 import Role, SendMessageRequest
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()

BASE_URL = "http://127.0.0.1:8401"


class AgentState(TypedDict):
    input: str
    agent_card_text: NotRequired[str]
    a2a_chunks: NotRequired[list[str]]
    final_answer: NotRequired[str]


async def discover_agent_node(state: AgentState) -> AgentState:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BASE_URL)
        card = await resolver.get_agent_card()

    return {"agent_card_text": str(card)}


async def call_a2a_agent_node(state: AgentState) -> AgentState:
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(httpx_client=httpx_client, base_url=BASE_URL)
        card = await resolver.get_agent_card()

    client = await create_client(
        agent=card,
        client_config=ClientConfig(streaming=True),
    )

    message = new_text_message(state["input"], role=Role.ROLE_USER)
    request = SendMessageRequest(message=message)

    chunks: list[str] = []
    async for chunk in client.send_message(request):
        chunks.append(str(chunk))

    await client.close()

    return {"a2a_chunks": chunks}


async def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

Discovered official A2A agent card:
{state["agent_card_text"]}

Official A2A response chunks:
{state["a2a_chunks"]}

Write a concise final answer summarizing the official A2A agent result.
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("discover_agent", discover_agent_node)
    graph_builder.add_node("call_a2a_agent", call_a2a_agent_node)
    graph_builder.add_node("synthesize", synthesize_node)

    graph_builder.add_edge(START, "discover_agent")
    graph_builder.add_edge("discover_agent", "call_a2a_agent")
    graph_builder.add_edge("call_a2a_agent", "synthesize")
    graph_builder.add_edge("synthesize", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()
    return await graph.ainvoke({"input": text})


async def main():
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after R13."
    result = await run_async(question)
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
