from __future__ import annotations

import ast
import operator
import re
from datetime import datetime, timezone
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph


load_dotenv()


RouteName = Literal["math", "time", "general"]


class AgentState(TypedDict, total=False):
    input: str
    route: RouteName
    answer: str


_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_math_expr(node: ast.AST) -> float:
    if isinstance(node, ast.Expression):
        return _eval_math_expr(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_BINOPS:
        left = _eval_math_expr(node.left)
        right = _eval_math_expr(node.right)
        return _ALLOWED_BINOPS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_UNARYOPS:
        operand = _eval_math_expr(node.operand)
        return _ALLOWED_UNARYOPS[type(node.op)](operand)

    raise ValueError("Unsupported expression.")


def safe_calculate(expression: str) -> str:
    tree = ast.parse(expression, mode="eval")
    return str(_eval_math_expr(tree))


def extract_arithmetic_expression(text: str) -> str:
    match = re.search(r"[0-9\.\s\+\-\*\/\(\)%]+", text)
    if not match:
        raise ValueError("No arithmetic expression found.")
    return match.group(0).strip()


def classifier_node(state: AgentState) -> AgentState:
    text = state.get("input", "").lower()

    math_terms = ["calculate", "math", "multiply", "plus", "minus", "divide", "*", "+", "-", "/", "**"]
    time_terms = ["time", "utc", "date", "now", "today"]

    if any(term in text for term in math_terms) and re.search(r"\d", text):
        return {"route": "math"}

    if any(term in text for term in time_terms):
        return {"route": "time"}

    return {"route": "general"}


def route_selector(state: AgentState) -> RouteName:
    return state["route"]


def math_agent_node(state: AgentState) -> AgentState:
    try:
        expr = extract_arithmetic_expression(state["input"])
        result = safe_calculate(expr)
        return {"answer": f"Math route selected. {expr} = {result}"}
    except Exception as exc:
        return {"answer": f"Math route selected, but calculation failed: {exc}"}


def time_agent_node(state: AgentState) -> AgentState:
    now = datetime.now(timezone.utc).isoformat()
    return {"answer": f"Time route selected. Current UTC time is {now}"}


def general_agent_node(state: AgentState) -> AgentState:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke(state.get("input", "Explain LangGraph briefly."))
    return {"answer": f"General route selected. {response.content}"}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("classifier", classifier_node)
    graph_builder.add_node("math_agent", math_agent_node)
    graph_builder.add_node("time_agent", time_agent_node)
    graph_builder.add_node("general_agent", general_agent_node)

    graph_builder.add_edge(START, "classifier")

    graph_builder.add_conditional_edges(
        "classifier",
        route_selector,
        {
            "math": "math_agent",
            "time": "time_agent",
            "general": "general_agent",
        },
    )

    graph_builder.add_edge("math_agent", END)
    graph_builder.add_edge("time_agent", END)
    graph_builder.add_edge("general_agent", END)

    return graph_builder.compile()


def run(text: str = "Explain LangGraph briefly.") -> AgentState:
    graph = build_graph()
    return graph.invoke({"input": text})


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "Explain LangGraph briefly."
    print(run(question))
