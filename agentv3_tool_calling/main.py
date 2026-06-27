from __future__ import annotations

import ast
import operator
import os
from datetime import datetime, timezone
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.graph import START, END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition


load_dotenv()


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


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

    raise ValueError("Unsupported expression. Use only numbers and arithmetic operators.")


@tool
def calculator(expression: str) -> str:
    """Evaluate a simple arithmetic expression. Supports +, -, *, /, //, %, **, and parentheses."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _eval_math_expr(tree)
        return str(result)
    except Exception as exc:
        return f"Calculator error: {exc}"


@tool
def current_utc_time() -> str:
    """Return the current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


@tool
def machine_cpu_count() -> str:
    """Return the number of CPU cores available on this machine."""
    count = os.cpu_count()
    return str(count if count is not None else "unknown")


TOOLS = [calculator, current_utc_time, machine_cpu_count]


def create_llm():
    return ChatOpenAI(model="gpt-4o-mini", temperature=0).bind_tools(TOOLS)


def assistant_node(state: AgentState) -> AgentState:
    llm_with_tools = create_llm()
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def build_graph():
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("assistant", assistant_node)
    graph_builder.add_node("tools", ToolNode(TOOLS))

    graph_builder.add_edge(START, "assistant")
    graph_builder.add_conditional_edges("assistant", tools_condition)
    graph_builder.add_edge("tools", "assistant")
    graph_builder.add_edge("assistant", END)

    return graph_builder.compile()


def run(text: str = "What is 123 * 456?") -> AgentState:
    graph = build_graph()
    return graph.invoke({"messages": [HumanMessage(content=text)]})


def final_text(state: AgentState) -> str:
    return state["messages"][-1].content


if __name__ == "__main__":
    import sys

    question = sys.argv[1] if len(sys.argv) > 1 else "What is 123 * 456?"
    result = run(question)
    print(final_text(result))
