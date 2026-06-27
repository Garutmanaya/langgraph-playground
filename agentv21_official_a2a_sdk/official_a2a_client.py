from __future__ import annotations

import asyncio

import httpx
from a2a.client import A2ACardResolver, ClientConfig, create_client
from a2a.helpers import display_agent_card, new_text_message
from a2a.types.a2a_pb2 import GetExtendedAgentCardRequest, Role, SendMessageRequest


BASE_URL = "http://127.0.0.1:8401"


async def get_agent_card():
    async with httpx.AsyncClient() as httpx_client:
        resolver = A2ACardResolver(
            httpx_client=httpx_client,
            base_url=BASE_URL,
        )
        return await resolver.get_agent_card()


async def show_agent_card():
    card = await get_agent_card()
    print("\nPUBLIC AGENT CARD")
    print("=" * 80)
    display_agent_card(card)
    return card


async def send_message(text_query: str, streaming: bool = False):
    card = await get_agent_card()
    config = ClientConfig(streaming=streaming)
    client = await create_client(agent=card, client_config=config)

    message = new_text_message(text_query, role=Role.ROLE_USER)
    request = SendMessageRequest(message=message)

    print("\nSTREAMING" if streaming else "\nNON-STREAMING")
    print("=" * 80)

    chunks = []
    async for chunk in client.send_message(request):
        print(chunk)
        chunks.append(chunk)

    await client.close()
    return chunks


async def show_extended_agent_card():
    card = await get_agent_card()
    config = ClientConfig(streaming=False)
    client = await create_client(agent=card, client_config=config)

    extended_card = await client.get_extended_agent_card(GetExtendedAgentCardRequest())

    print("\nEXTENDED AGENT CARD")
    print("=" * 80)
    display_agent_card(extended_card)

    await client.close()
    return extended_card


async def main():
    await show_agent_card()
    await send_message("Investigate CHECK-DOMAIN timeout spike after R13.", streaming=False)
    await send_message("Investigate CHECK-DOMAIN timeout spike after R13.", streaming=True)
    await show_extended_agent_card()


if __name__ == "__main__":
    asyncio.run(main())
