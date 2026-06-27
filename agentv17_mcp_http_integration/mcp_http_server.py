from __future__ import annotations

import os

from mcp.server.fastmcp import FastMCP


HOST = os.getenv("MCP_HOST", "127.0.0.1")
PORT = int(os.getenv("MCP_PORT", "8001"))

mcp = FastMCP(
    "epp-http-mcp-server",
    host=HOST,
    port=PORT,
)


@mcp.tool()
def get_epp_metrics(issue: str) -> str:
    """Return simulated EPP metrics for an incident investigation."""
    return (
        "EPP Metrics: CHECK-DOMAIN p95 response_time is 240 ms after R13. "
        "CONNECTION_TIMEOUT failure volume increased for client_b during peak hours. "
        f"Investigation issue: {issue}"
    )


@mcp.tool()
def get_epp_runbook(issue: str) -> str:
    """Return simulated runbook guidance for an EPP incident."""
    return (
        "Runbook Guidance: For CHECK-DOMAIN timeout spikes, inspect upstream registry "
        "connectivity, DNS resolver latency, registry endpoint health, and connection "
        "pool saturation. Rollback if timeout volume remains above baseline for two "
        "consecutive hours. "
        f"Investigation issue: {issue}"
    )


if __name__ == "__main__":
    print(f"Starting MCP HTTP/SSE server at http://{HOST}:{PORT}/sse")
    mcp.run(transport="sse")
