
# agentv8_sequential_workflow

This version introduces sequential workflows with loops.

Graph:

START → planner → sql_agent → evaluator
                     ↑         ↓
                     └─────────┘
                          |
                    final_answer → END

This version is important for BI / analytics agents.

## Problem with v7 Router

v7 supports:

router → sql_agent → END

But many real-world requests need multiple SQL queries before producing a final answer.

Example:
"Compare failed EPP transactions before and after latest release and explain root cause."

This may require:
1. Query release window
2. Query failures before release
3. Query failures after release
4. Query grouped metrics
5. Final analysis

This means SQL agent may run multiple times.

## Solution

Use looping workflow with:
- planner
- sql_agent
- evaluator
- final_answer

Evaluator decides:
- stop
- continue SQL loop

## Concepts
- sequential workflow
- planner-executor pattern
- iterative SQL analysis
- loops in LangGraph
- state progression tracking
