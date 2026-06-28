from __future__ import annotations

import asyncio
import os

import httpx


REGISTRY_URL = os.getenv("REGISTRY_URL", "http://127.0.0.1:8600")
API_KEY = os.getenv("AGENT_API_KEY", "dev-secret")


AGENTS = [
    {
        "agent_id": "company_a_parking_agent",
        "name": "Company A Parking Agent",
        "description": "Provides availability, pricing, and reservation support for Company A parking sites.",
        "endpoint_url": "http://127.0.0.1:8601",
        "domain": "parking",
        "capabilities": ["availability", "pricing", "reservation"],
        "location": {"city": "demo-city", "zone": "north"},
        "trust_level": "trusted",
        "metadata": {"operator": "Company A"},
    },
    {
        "agent_id": "company_b_parking_agent",
        "name": "Company B Parking Agent",
        "description": "Provides availability and pricing for Company B parking sites.",
        "endpoint_url": "http://127.0.0.1:8602",
        "domain": "parking",
        "capabilities": ["availability", "pricing"],
        "location": {"city": "demo-city", "zone": "north"},
        "trust_level": "verified",
        "metadata": {"operator": "Company B"},
    },
]


async def main():
    headers = {"x-api-key": API_KEY}

    async with httpx.AsyncClient(timeout=30.0) as client:
        for agent in AGENTS:
            response = await client.post(
                f"{REGISTRY_URL}/agents/register",
                json=agent,
                headers=headers,
            )
            response.raise_for_status()
            print(response.json())

        response = await client.get(f"{REGISTRY_URL}/agents", headers=headers)
        response.raise_for_status()
        print("Registered agents:", response.json())


if __name__ == "__main__":
    asyncio.run(main())
