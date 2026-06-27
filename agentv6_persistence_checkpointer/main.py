from __future__ import annotations

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages


load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def assistant_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_graph(checkpointer=None):
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("assistant", assistant_node)
    graph_builder.add_edge(START, "assistant")
    graph_builder.add_edge("assistant", END)

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return graph_builder.compile(checkpointer=checkpointer)


def run_turn(graph, thread_id: str, user_input: str) -> AgentState:
    config = {"configurable": {"thread_id": thread_id}}
    return graph.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )


if __name__ == "__main__":
    graph = build_graph()
    thread_id = "demo-thread-1"

    state1 = run_turn(graph, thread_id, "My name is Sam. Remember it.")
    state2 = run_turn(graph, thread_id, "What is my name?")

    for msg in state2["messages"]:
        print(type(msg).__name__, ":", msg.content)
