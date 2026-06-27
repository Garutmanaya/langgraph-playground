from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

load_dotenv()

class AgentState(TypedDict, total=False):
    input: str
    answer: str

def greet(state: AgentState) -> AgentState:
    name = state.get("input", "LangGraph learner")
    return {"answer": f"Hello, {name}. This is agentv1_basic_graph."}

def build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("greet", greet)
    graph_builder.add_edge(START, "greet")
    graph_builder.add_edge("greet", END)
    return graph_builder.compile()

def run(text: str = "Sam") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})

if __name__ == "__main__":
    import sys
    print(run(sys.argv[1] if len(sys.argv) > 1 else "Sam"))
