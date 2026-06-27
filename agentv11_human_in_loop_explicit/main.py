from __future__ import annotations

import sys
from typing import Literal, TypedDict

from dotenv import load_dotenv
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph


load_dotenv()


ApprovalDecision = Literal["approved", "rejected"]


class AgentState(TypedDict, total=False):
    input: str
    proposed_action: str
    approval_decision: ApprovalDecision
    execution_result: str
    final_answer: str


def normalize_decision(raw: str) -> ApprovalDecision:
    value = raw.strip().lower()
    if value in {"approve", "approved", "yes", "y"}:
        return "approved"
    return "rejected"


def planner_node(state: AgentState) -> AgentState:
    user_request = state["input"]

    proposed_action = (
        "Proposed action: restart the EPP health-check worker service "
        "and collect post-restart error metrics for 10 minutes. "
        f"Original request: {user_request}"
    )

    return {"proposed_action": proposed_action}


def approval_gate_node(state: AgentState) -> AgentState:
    decision = state.get("approval_decision")

    if decision not in {"approved", "rejected"}:
        return {"approval_decision": "rejected"}

    return {"approval_decision": decision}


def execute_action_node(state: AgentState) -> AgentState:
    if state.get("approval_decision") != "approved":
        return {"execution_result": "Action skipped because approval was rejected or missing."}

    # This is intentionally a safe simulated execution.
    # In production, this node could call AWS, SQL update, email send, deployment APIs, etc.
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


def run_interactive(text: str = "Fix EPP health-check failures after latest release."):
    graph = build_graph()
    config = {"configurable": {"thread_id": "human-loop-demo"}}

    graph.invoke({"input": text}, config=config)

    paused_state = graph.get_state(config)
    print("\nGraph paused before:", paused_state.next)
    print("\nProposed action:")
    print(paused_state.values.get("proposed_action"))

    raw_decision = input("\nApprove action? Type approve or reject: ")
    approval_decision = normalize_decision(raw_decision)

    graph.update_state(
        config,
        {"approval_decision": approval_decision},
    )

    resumed_result = graph.invoke(None, config=config)
    return resumed_result


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Fix EPP health-check failures after latest release."
    result = run_interactive(question)
    print("\nFinal answer:")
    print(result["final_answer"])
