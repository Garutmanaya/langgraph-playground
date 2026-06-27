from __future__ import annotations

from pydantic import BaseModel, Field


class AgentInvokeRequest(BaseModel):
    input: str = Field(..., description="User request for the agent.")
    request_id: str | None = Field(default=None, description="Optional caller-supplied request id.")
    context: dict = Field(default_factory=dict, description="Optional request context.")


class AgentInvokeResponse(BaseModel):
    request_id: str
    classification: str
    answer: str
    metadata: dict = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    request_id: str | None = None
    error: str
    detail: str | None = None
