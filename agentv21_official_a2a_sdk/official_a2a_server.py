from __future__ import annotations

import uvicorn

from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.routes import create_agent_card_routes, create_jsonrpc_routes
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCapabilities, AgentCard, AgentInterface, AgentSkill
from starlette.applications import Starlette

from .agent_executor import EppIncidentAgentExecutor


HOST = "127.0.0.1"
PORT = 8401
BASE_URL = f"http://{HOST}:{PORT}"


def build_public_agent_card() -> AgentCard:
    skill = AgentSkill(
        id="epp_incident_analysis",
        name="EPP Incident Analysis",
        description=(
            "Analyzes EPP SLA incidents, timeout spikes, release impact, "
            "latency symptoms, and failure concentration."
        ),
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["a2a", "epp", "incident-analysis"],
        examples=[
            "Investigate CHECK-DOMAIN timeout spike after R13",
            "Analyze EPP latency after latest release",
        ],
    )

    return AgentCard(
        name="Official A2A EPP Incident Agent",
        description="EPP SLA incident analysis agent implemented with the official A2A Python SDK.",
        version="0.1.0",
        default_input_modes=["text/plain"],
        default_output_modes=["text/plain"],
        capabilities=AgentCapabilities(
            streaming=True,
            extended_agent_card=True,
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                url=BASE_URL,
            )
        ],
        skills=[skill],
    )


def build_extended_agent_card() -> AgentCard:
    public_card = build_public_agent_card()

    extended_skill = AgentSkill(
        id="epp_incident_analysis_debug",
        name="EPP Incident Analysis Debug",
        description="Extended/debug variant for authenticated clients.",
        input_modes=["text/plain"],
        output_modes=["text/plain"],
        tags=["a2a", "epp", "debug"],
        examples=["Debug CHECK-DOMAIN timeout spike with verbose reasoning"],
    )

    return AgentCard(
        name="Official A2A EPP Incident Agent - Extended",
        description="Extended card with additional debug skill.",
        version="0.1.0",
        default_input_modes=public_card.default_input_modes,
        default_output_modes=public_card.default_output_modes,
        capabilities=AgentCapabilities(
            streaming=True,
            extended_agent_card=True,
        ),
        supported_interfaces=[
            AgentInterface(
                protocol_binding="JSONRPC",
                url=BASE_URL,
            )
        ],
        skills=[*public_card.skills, extended_skill],
    )


def build_app() -> Starlette:
    public_agent_card = build_public_agent_card()
    extended_agent_card = build_extended_agent_card()

    request_handler = DefaultRequestHandler(
        agent_executor=EppIncidentAgentExecutor(),
        task_store=InMemoryTaskStore(),
        agent_card=public_agent_card,
        extended_agent_card=extended_agent_card,
    )

    routes = []
    routes.extend(create_agent_card_routes(public_agent_card))
    routes.extend(create_jsonrpc_routes(request_handler, "/"))

    return Starlette(routes=routes)


app = build_app()


if __name__ == "__main__":
    print(f"Starting official A2A SDK server at {BASE_URL}")
    uvicorn.run(app, host=HOST, port=PORT)
