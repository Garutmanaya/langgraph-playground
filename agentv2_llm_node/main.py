from typing import TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI

load_dotenv()

class AgentState(TypedDict, total=False):
    input: str
    answer: str

def llm_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    user_input = state.get("input", "Explain LangGraph briefly.")
    response = llm.invoke(user_input)
    return {"answer": response.content}

def build_graph():
    graph_builder = StateGraph(AgentState)
    graph_builder.add_node("llm_node", llm_node)
    graph_builder.add_edge(START, "llm_node")
    graph_builder.add_edge("llm_node", END)
    return graph_builder.compile()

def run(text: str = "Explain LangGraph in one sentence.") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})

if __name__ == "__main__":
    import sys
    question = sys.argv[1] if len(sys.argv) > 1 else "Explain LangGraph in one sentence."
    print(run(question))
