from __future__ import annotations
import asyncio, sys
from typing import NotRequired, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from .a2a_client import A2AClient

load_dotenv()

class AgentState(TypedDict):
    input: str
    agent_card: NotRequired[dict]
    capabilities: NotRequired[dict]
    task_id: NotRequired[str]
    task: NotRequired[dict]
    artifacts: NotRequired[dict]
    final_answer: NotRequired[str]

async def discover_agent_node(state: AgentState) -> AgentState:
    client = A2AClient()
    return {"agent_card": await client.get_agent_card(), "capabilities": await client.get_capabilities()}

async def submit_task_node(state: AgentState) -> AgentState:
    client = A2AClient()
    task = await client.create_task(state["input"], context_id="ctx_langgraph_host", metadata={"caller": "agentv19_langgraph_host"})
    return {"task_id": task["task_id"], "task": task}

async def poll_task_node(state: AgentState) -> AgentState:
    return {"task": await A2AClient().wait_for_completion(state["task_id"])}

async def fetch_artifacts_node(state: AgentState) -> AgentState:
    return {"artifacts": await A2AClient().get_task_artifacts(state["task_id"])}

async def synthesize_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    prompt = f"""
User request:
{state["input"]}

Remote agent name:
{state["agent_card"]["name"]}

Remote agent capabilities:
{state["capabilities"]}

Task:
{state["task"]}

Artifacts:
{state["artifacts"]}

Write a concise final answer based on the remote A2A agent result.
"""
    response = await llm.ainvoke(prompt)
    return {"final_answer": response.content}

def build_graph():
    g = StateGraph(AgentState)
    g.add_node("discover_agent", discover_agent_node)
    g.add_node("submit_task", submit_task_node)
    g.add_node("poll_task", poll_task_node)
    g.add_node("fetch_artifacts", fetch_artifacts_node)
    g.add_node("synthesize", synthesize_node)
    g.add_edge(START, "discover_agent")
    g.add_edge("discover_agent", "submit_task")
    g.add_edge("submit_task", "poll_task")
    g.add_edge("poll_task", "fetch_artifacts")
    g.add_edge("fetch_artifacts", "synthesize")
    g.add_edge("synthesize", END)
    return g.compile()

async def run_async(text: str) -> AgentState:
    return await build_graph().ainvoke({"input": text})

async def main():
    question = " ".join(sys.argv[1:]) or "Investigate CHECK-DOMAIN timeout spike after R13."
    result = await run_async(question)
    print("Remote agent:", result["agent_card"]["name"])
    print("Task ID:", result["task_id"])
    print("Task state:", result["task"]["status"]["state"])
    print()
    print(result["final_answer"])

if __name__ == "__main__":
    asyncio.run(main())
