from __future__ import annotations

import json
import logging
import uuid
from collections.abc import AsyncIterator

import uvicorn
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import StreamingResponse

from .agent_graph import build_graph
from .config import settings
from .schemas import AgentInvokeRequest, AgentInvokeResponse


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
)

logger = logging.getLogger("agentv24")


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, "request_id"):
            record.request_id = "-"
        return True


logger.addFilter(RequestIdFilter())

app = FastAPI(title=settings.app_name, version="1.0.0")
graph = build_graph()


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if settings.api_key and x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid or missing API key.")


@app.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}


@app.get("/ready")
def ready():
    return {"status": "ready", "model": settings.model_name}


@app.post("/invoke", response_model=AgentInvokeResponse)
def invoke_agent(
    request: AgentInvokeRequest,
    _: None = Depends(require_api_key),
):
    request_id = request.request_id or f"req_{uuid.uuid4().hex[:12]}"

    logger.info(
        "invoke started",
        extra={"request_id": request_id},
    )

    result = graph.invoke(
        {
            "input": request.input,
            "request_id": request_id,
            "context": request.context,
        }
    )

    logger.info(
        "invoke completed",
        extra={"request_id": request_id},
    )

    return AgentInvokeResponse(
        request_id=request_id,
        classification=result["classification"],
        answer=result["final_answer"],
        metadata={
            "model": settings.model_name,
            "context_keys": list(request.context.keys()),
        },
    )


@app.post("/stream")
async def stream_agent(
    request: AgentInvokeRequest,
    _: None = Depends(require_api_key),
):
    request_id = request.request_id or f"req_{uuid.uuid4().hex[:12]}"

    async def event_generator() -> AsyncIterator[str]:
        yield f"event: started\ndata: {json.dumps({'request_id': request_id})}\n\n"

        async for chunk in graph.astream(
            {
                "input": request.input,
                "request_id": request_id,
                "context": request.context,
            },
            stream_mode="updates",
        ):
            yield f"event: update\ndata: {json.dumps(chunk, default=str)}\n\n"

        yield f"event: completed\ndata: {json.dumps({'request_id': request_id})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


if __name__ == "__main__":
    uvicorn.run(app, host=settings.host, port=settings.port)
