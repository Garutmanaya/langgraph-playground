from __future__ import annotations

import asyncio
import json
import os

import httpx


BASE_URL = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:8501")
API_KEY = os.getenv("AGENT_API_KEY")


def headers() -> dict[str, str]:
    if API_KEY:
        return {"x-api-key": API_KEY}
    return {}


async def test_health():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/health")
        response.raise_for_status()
        print("HEALTH:", response.json())


async def test_ready():
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(f"{BASE_URL}/ready")
        response.raise_for_status()
        print("READY:", response.json())


async def test_invoke():
    payload = {
        "input": "Investigate CHECK-DOMAIN timeout spike after release R13.",
        "request_id": "req_smoke_001",
        "context": {
            "command": "CHECK-DOMAIN",
            "release": "R13",
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{BASE_URL}/invoke",
            json=payload,
            headers=headers(),
        )
        response.raise_for_status()
        print("INVOKE:")
        print(json.dumps(response.json(), indent=2))


async def test_stream():
    payload = {
        "input": "Stream analysis for EPP latency incident.",
        "request_id": "req_stream_001",
        "context": {
            "command": "CHECK-DOMAIN",
        },
    }

    print("STREAM:")
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/stream",
            json=payload,
            headers=headers(),
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    print(line)


async def main():
    await test_health()
    await test_ready()
    await test_invoke()
    await test_stream()


if __name__ == "__main__":
    asyncio.run(main())
