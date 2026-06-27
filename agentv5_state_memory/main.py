from __future__ import annotations

from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages


load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


def assistant_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(state["messages"])
    return {"messages": [response]}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("assistant", assistant_node)

    graph_builder.add_edge(START, "assistant")
    graph_builder.add_edge("assistant", END)

    return graph_builder.compile()


def run_turn(graph, history: list[BaseMessage], user_input: str) -> list[BaseMessage]:
    state = graph.invoke({"messages": history + [HumanMessage(content=user_input)]})
    return state["messages"]


def print_conversation(messages: list[BaseMessage]) -> None:
    for msg in messages:
        role = "User" if isinstance(msg, HumanMessage) else "Assistant" if isinstance(msg, AIMessage) else type(msg).__name__
        print(f"{role}: {msg.content}")


if __name__ == "__main__":
    graph = build_graph()

    history: list[BaseMessage] = []

    history = run_turn(graph, history, "My name is Sam. Remember it for this conversation.")
    history = run_turn(graph, history, "What is my name?")

    print_conversation(history)
