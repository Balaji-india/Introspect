"""Introspect MCP server: lets any MCP-capable AI assistant ask about your wellness data,
but ONLY the privacy-gateway facts, and ONLY if you granted the 'mcp_access' consent.

Run (stdio transport, e.g. from Claude Desktop or any MCP client):
    python mcp_server/server.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

try:  # MCP Python SDK 2.x
    from mcp.server.mcpserver import MCPServer as _Server  # noqa: E402
except ImportError:  # MCP Python SDK 1.x
    from mcp.server.fastmcp import FastMCP as _Server  # noqa: E402

from introspect import config, pipeline, privacy  # noqa: E402

mcp = _Server("introspect")


def _facts() -> dict:
    return privacy.release(pipeline.run(config.DATA_DIR)["facts"], "mcp_access")


@mcp.tool()
def get_daily_summary() -> dict:
    """Today's readiness, 7-day averages and tomorrow's forecast (aggregates only)."""
    try:
        f = _facts()
    except privacy.ConsentError as e:
        return {"error": str(e)}
    keys = ("readiness_today", "readiness_7d_avg", "readiness_forecast_tomorrow", "sleep_7d_avg_min",
            "sleep_normal_min", "resting_hr_7d_avg", "steps_7d_avg", "drift_today")
    return {k: f[k] for k in keys}


@mcp.tool()
def get_insights() -> dict:
    """Plain-language 'why' insights about what drives the user's sleep and recovery."""
    try:
        f = _facts()
    except privacy.ConsentError as e:
        return {"error": str(e)}
    return {"insights": f["insights"], "suggested_action": f["suggested_action"]}


if __name__ == "__main__":
    mcp.run()
