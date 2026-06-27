from __future__ import annotations

from a2a.helpers import (
    get_message_text,
    new_task_from_user_message,
    new_text_message,
    new_text_part,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.server.tasks import TaskUpdater
from a2a.types.a2a_pb2 import TaskState


class EppIncidentAgent:
    """Simple EPP incident agent business logic."""

    async def invoke(self, user_request: str) -> str:
        return (
            "Official A2A SDK Agent Response: "
            "For CHECK-DOMAIN timeout spikes after R13, likely causes include "
            "upstream registry connectivity degradation, DNS resolver latency, "
            "or connection pool saturation. Recommended next actions: inspect "
            "registry endpoint health, compare pre/post-release failure volume, "
            "check p95 response_time, and validate CONNECTION_TIMEOUT concentration "
            f"by client. Original request: {user_request}"
        )


class EppIncidentAgentExecutor(AgentExecutor):
    """Official A2A SDK AgentExecutor implementation."""

    def __init__(self) -> None:
        self.agent = EppIncidentAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Process incoming A2A request and emit task lifecycle events."""
        if context.current_task:
            task = context.current_task
        else:
            task = new_task_from_user_message(context.message)
            await event_queue.enqueue_event(task)

        task_updater = TaskUpdater(
            event_queue=event_queue,
            task_id=task.id,
            context_id=task.context_id,
        )

        await task_updater.update_status(
            state=TaskState.TASK_STATE_WORKING,
            message=new_text_message("Processing EPP incident request..."),
        )

        query = get_message_text(context.message)
        if query:
            result = await self.agent.invoke(user_request=query)
        else:
            result = "No text input was provided."

        await task_updater.add_artifact(
            parts=[
                new_text_part(
                    text=result,
                    media_type="text/plain",
                )
            ]
        )

        await task_updater.update_status(
            state=TaskState.TASK_STATE_COMPLETED,
            message=new_text_message("EPP incident analysis completed."),
        )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("Cancel is not supported in this v21 basic example.")
