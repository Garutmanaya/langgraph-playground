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

REGISTRY_URL = os.getenv("REGISTRY_URL", "http://127.0.0.1:8600")
API_KEY = os.getenv("AGENT_API_KEY", "dev-secret")


class AgentState(TypedDict):
    input: str
    user_location: dict
    preferences: dict
    discovered_agents: NotRequired[list[dict]]
    parking_results: NotRequired[list[dict]]
    ranked_options: NotRequired[list[dict]]
    final_answer: NotRequired[str]


def headers() -> dict[str, str]:
    return {"x-api-key": API_KEY}


async def discover_agents_node(state: AgentState) -> AgentState:
    payload = {
        "domain": "parking",
        "required_capabilities": ["availability", "pricing"],
        "location": state["user_location"],
        "minimum_trust_level": "verified",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{REGISTRY_URL}/agents/search",
            json=payload,
            headers=headers(),
        )
        response.raise_for_status()
        agents = response.json()["agents"]

    return {"discovered_agents": agents}


async def call_parking_agent(agent: dict, state: AgentState) -> dict:
    payload = {
        "latitude": state["user_location"]["latitude"],
        "longitude": state["user_location"]["longitude"],
        "level_preference": state["preferences"].get("level_preference", "ground"),
        "sort_preference": state["preferences"].get("sort_preference", "lowest_price"),
        "max_distance_meters": state["preferences"].get("max_distance_meters", 1000),
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{agent['endpoint_url']}/parking/search",
            json=payload,
            headers=headers(),
        )
        response.raise_for_status()
        result = response.json()

    return {
        "agent": agent,
        "result": result,
    }


async def query_parking_agents_node(state: AgentState) -> AgentState:
    tasks = [
        call_parking_agent(agent, state)
        for agent in state.get("discovered_agents", [])
    ]

    if not tasks:
        return {"parking_results": []}

    results = await asyncio.gather(*tasks)
    return {"parking_results": results}


def rank_options_node(state: AgentState) -> AgentState:
    level_preference = state["preferences"].get("level_preference", "ground")
    options = []

    for item in state.get("parking_results", []):
        for option in item["result"]["options"]:
            if option["available_slots"] <= 0:
                continue

            level_match = option["level"] == level_preference

            score = (
                (0 if level_match else 1000)
                + option["price_per_hour"] * 10
                + option["distance_meters"] / 10
            )

            options.append(
                {
                    **option,
                    "source_agent_id": item["agent"]["agent_id"],
                    "source_agent_name": item["agent"]["name"],
                    "level_match": level_match,
                    "score": round(score, 2),
                }
            )

    options.sort(key=lambda row: row["score"])
    return {"ranked_options": options}


async def final_answer_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    prompt = f"""
User request:
{state["input"]}

User location:
{state["user_location"]}

Preferences:
{state["preferences"]}

Discovered agents:
{state["discovered_agents"]}

Ranked parking options:
{state["ranked_options"]}

Write a concise recommendation.
Explain which parking option is best and why.
Prefer ground level first, then lowest price, then distance.
"""

    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("discover_agents", discover_agents_node)
    graph_builder.add_node("query_parking_agents", query_parking_agents_node)
    graph_builder.add_node("rank_options", rank_options_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "discover_agents")
    graph_builder.add_edge("discover_agents", "query_parking_agents")
    graph_builder.add_edge("query_parking_agents", "rank_options")
    graph_builder.add_edge("rank_options", "final_answer")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile()


async def run_async(text: str) -> AgentState:
    graph = build_graph()

    return await graph.ainvoke(
        {
            "input": text,
            "user_location": {
                "latitude": 38.95,
                "longitude": -77.45,
            },
            "preferences": {
                "level_preference": "ground",
                "sort_preference": "lowest_price",
                "max_distance_meters": 1000,
            },
        }
    )


async def main():
    question = " ".join(sys.argv[1:]) or "Find ground-level parking at the lowest price near me."
    result = await run_async(question)

    print("Discovered agents:")
    for agent in result["discovered_agents"]:
        print("-", agent["name"], agent["capabilities"], agent["trust_level"])

    print("\nRanked options:")
    for option in result["ranked_options"]:
        print(option)

    print("\nFinal answer:")
    print(result["final_answer"])


if __name__ == "__main__":
    asyncio.run(main())
