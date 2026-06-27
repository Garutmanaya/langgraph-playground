from __future__ import annotations

import asyncio
import json

from .a2a_streaming_client import A2AStreamingClient


def show(title: str, payload):
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)
    print(json.dumps(payload, indent=2))


async def main():
    client = A2AStreamingClient()

    show("GET /health", await client.health())
    show("GET /.well-known/agent.json", await client.get_agent_card())
    show("GET /model-card", await client.get_model_card())
    show("GET /capabilities", await client.get_capabilities())
    show("GET /skills", await client.get_skills())

    created = await client.create_task(
        input_text="Investigate CHECK-DOMAIN timeout spike after R13",
        context_id="ctx_streaming_demo",
        metadata={"source": "test_all_api_calls"},
    )
    show("POST /tasks", created)
    task_id = created["task_id"]

    print("\nStreaming task events:")
    events = await client.wait_for_completion_by_events(task_id)
    show("STREAMED EVENTS", events)

    show(f"GET /tasks/{task_id}", await client.get_task(task_id))
    show(f"GET /tasks/{task_id}/status", await client.get_task_status(task_id))
    show(f"GET /tasks/{task_id}/artifacts", await client.get_task_artifacts(task_id))
    show("GET /tasks", await client.list_tasks())

    cancel_created = await client.create_task("Long investigation to cancel", context_id="ctx_cancel_demo")
    cancel_task_id = cancel_created["task_id"]
    show("POST /tasks for cancellation test", cancel_created)
    show(f"POST /tasks/{cancel_task_id}/cancel", await client.cancel_task(cancel_task_id))
    cancel_events = await client.wait_for_completion_by_events(cancel_task_id)
    show("CANCEL STREAM EVENTS", cancel_events)

    rejected = await client.create_task("Unsupported skill test", skill_id="unsupported_skill")
    show("POST /tasks rejected unsupported skill", rejected)
    rejected_events = await client.wait_for_completion_by_events(rejected["task_id"])
    show("REJECTED STREAM EVENTS", rejected_events)


if __name__ == "__main__":
    asyncio.run(main())
