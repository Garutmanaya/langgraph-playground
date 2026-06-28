from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


TrustLevel = Literal["experimental", "verified", "trusted"]


class AgentRegistration(BaseModel):
    agent_id: str
    name: str
    description: str
    endpoint_url: str
    domain: str
    capabilities: list[str]
    location: dict = Field(default_factory=dict)
    trust_level: TrustLevel = "experimental"
    metadata: dict = Field(default_factory=dict)


class AgentSearchRequest(BaseModel):
    domain: str | None = None
    required_capabilities: list[str] = Field(default_factory=list)
    location: dict = Field(default_factory=dict)
    minimum_trust_level: TrustLevel = "experimental"


class ParkingSearchRequest(BaseModel):
    latitude: float
    longitude: float
    level_preference: str = "ground"
    sort_preference: str = "lowest_price"
    max_distance_meters: int = 1000


class ParkingOption(BaseModel):
    company: str
    parking_id: str
    level: str
    price_per_hour: float
    available_slots: int
    distance_meters: int
    reservation_supported: bool


class ParkingSearchResponse(BaseModel):
    agent_id: str
    options: list[ParkingOption]
