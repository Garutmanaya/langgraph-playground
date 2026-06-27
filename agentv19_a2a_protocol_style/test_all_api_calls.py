from __future__ import annotations
import asyncio, json
from .a2a_client import A2AClient

def show(title: str, payload):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(json.dumps(payload, indent=2))

async def main():
    client = A2AClient()
    show("GET /health", await client.health())
    show("GET /.well-known/agent.json", await client.get_agent_card())
    show("GET /.well-known/agent-card.json", await client.get_agent_card_alias())
    show("GET /model-card", await client.get_model_card())
    show("GET /capabilities", await client.get_capabilities())
    show("GET /skills", await client.get_skills())

    created = await client.create_task("Investigate CHECK-DOMAIN timeout spike after R13", context_id="ctx_demo_001", metadata={"source": "test_all_api_calls"})
    show("POST /tasks", created)
    task_id = created["task_id"]
    show("GET /tasks", await client.list_tasks())
    show(f"GET /tasks/{task_id}", await client.get_task(task_id))
    show(f"GET /tasks/{task_id}/status", await client.get_task_status(task_id))
    show("WAIT FOR COMPLETION", await client.wait_for_completion(task_id))
    show(f"GET /tasks/{task_id}/artifacts", await client.get_task_artifacts(task_id))

    cancel_created = await client.create_task("Long investigation to cancel", context_id="ctx_cancel_demo")
    cancel_task_id = cancel_created["task_id"]
    show("POST /tasks for cancellation test", cancel_created)
    show(f"POST /tasks/{cancel_task_id}/cancel", await client.cancel_task(cancel_task_id))

    rejected = await client.create_task("Unsupported skill test", skill_id="unsupported_skill")
    show("POST /tasks rejected unsupported skill", rejected)

if __name__ == "__main__":
    asyncio.run(main())
