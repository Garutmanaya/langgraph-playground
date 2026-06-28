from __future__ import annotations

import asyncio
import os

import httpx

from .host_graph import run_async


REGISTRY_URL = os.getenv("REGISTRY_URL", "http://127.0.0.1:8600")
API_KEY = os.getenv("AGENT_API_KEY", "dev-secret")


async def test_registry_health():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{REGISTRY_URL}/health")
        response.raise_for_status()
        print("Registry health:", response.json())


async def test_registry_search():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{REGISTRY_URL}/agents/search",
            json={
                "domain": "parking",
                "required_capabilities": ["availability", "pricing"],
                "minimum_trust_level": "verified",
            },
            headers={"x-api-key": API_KEY},
        )
        response.raise_for_status()
        print("Registry search:", response.json())


async def test_host_graph():
    result = await run_async("Find ground-level parking at the lowest price near me.")
    print("Best option:", result["ranked_options"][0])
    print("Answer:", result["final_answer"])


async def main():
    await test_registry_health()
    await test_registry_search()
    await test_host_graph()


if __name__ == "__main__":
    asyncio.run(main())
