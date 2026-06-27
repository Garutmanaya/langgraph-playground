from __future__ import annotations

import sys
from typing import TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph


load_dotenv()


class AgentState(TypedDict, total=False):
    input: str
    proposed_action: str
    approval_decision: str
    execution_result: str
    final_answer: str


def planner_node(state: AgentState) -> AgentState:
    user_request = state["input"]
    proposed_action = (
        "Proposed action: restart the EPP health-check worker service "
        "and collect post-restart error metrics for 10 minutes. "
        f"Original request: {user_request}"
    )
    return {"proposed_action": proposed_action}


def approval_gate_node(state: AgentState) -> AgentState:
    decision = state.get("approval_decision", "approved")
    return {"approval_decision": decision}


def execute_action_node(state: AgentState) -> AgentState:
    if state.get("approval_decision") != "approved":
        return {"execution_result": "Action skipped because approval was not granted."}

    return {
        "execution_result": (
            "Executed approved action: restarted EPP health-check worker service. "
            "Post-action metrics collection started."
        )
    }


def final_answer_node(state: AgentState) -> AgentState:
    return {
        "final_answer": (
            f"{state['proposed_action']}\n\n"
            f"Approval decision: {state.get('approval_decision')}\n"
            f"Execution result: {state.get('execution_result')}"
        )
    }


def build_graph():
    checkpointer = InMemorySaver()
    graph_builder = StateGraph(AgentState)

    graph_builder.add_node("planner", planner_node)
    graph_builder.add_node("approval_gate", approval_gate_node)
    graph_builder.add_node("execute_action", execute_action_node)
    graph_builder.add_node("final_answer", final_answer_node)

    graph_builder.add_edge(START, "planner")
    graph_builder.add_edge("planner", "approval_gate")
    graph_builder.add_edge("approval_gate", "execute_action")
    graph_builder.add_edge("execute_action", "final_answer")
    graph_builder.add_edge("final_answer", END)

    return graph_builder.compile(
        checkpointer=checkpointer,
        interrupt_before=["approval_gate"],
    )


def run_demo(text: str = "Fix EPP health-check failures after latest release."):
    graph = build_graph()
    config = {"configurable": {"thread_id": "human-loop-demo"}}

    first_result = graph.invoke({"input": text}, config=config)
    paused_state = graph.get_state(config)
    resumed_result = graph.invoke(None, config=config)

    return first_result, paused_state, resumed_result


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Fix EPP health-check failures after latest release."
    first_result, paused_state, resumed_result = run_demo(question)

    print("Paused before:", paused_state.next)
    print("Proposed action:", paused_state.values.get("proposed_action"))
    print()
    print(resumed_result["final_answer"])
