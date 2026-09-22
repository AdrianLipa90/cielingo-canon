"""Concrete stdio MCP transport for the CIELingo -> GREMLIN full bridge.

The MCP dependency is imported lazily so CIELingo remains importable without
GREMLIN installed. Runtime connection fails loudly when the dependency or
server entrypoint is unavailable.
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from collections.abc import Mapping, Sequence
from typing import Any


class GremlinTransportError(RuntimeError):
    pass


def _extract_mapping(result: Any) -> dict[str, Any]:
    if getattr(result, "is_error", False):
        raise GremlinTransportError("GREMLIN MCP tool call returned an error")
    structured = getattr(result, "structured_content", None)
    if isinstance(structured, Mapping):
        return dict(structured)
    for block in getattr(result, "content", ()):
        text = getattr(block, "text", None)
        if not isinstance(text, str):
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, Mapping):
            return dict(value)
    raise GremlinTransportError("GREMLIN MCP result contained no structured mapping")


class GremlinStdioTransport:
    """Discover and call the complete GREMLIN `server_with_hive` MCP surface.

    The default command follows GREMLIN v0.5.0's canonical entrypoint. Each
    operation uses a fresh MCP session; callers that need a persistent session
    can provide another object implementing the GremlinTransport protocol.
    """

    def __init__(
        self,
        *,
        command: str | None = None,
        args: Sequence[str] | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.command = command or sys.executable
        self.args = list(args or ("-m", "gremlin_mcp.server_with_hive", "--transport", "stdio"))
        self.env = dict(os.environ)
        if env:
            self.env.update({str(k): str(v) for k, v in env.items()})

    @staticmethod
    def _run(coro):
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            return asyncio.run(coro)
        raise GremlinTransportError(
            "synchronous GremlinStdioTransport cannot be called from an active asyncio loop; "
            "use a dedicated thread or an async transport"
        )

    async def _list_tools(self) -> list[str]:
        try:
            from mcp import Client, StdioServerParameters
        except ImportError as exc:
            raise GremlinTransportError("MCP dependency is unavailable") from exc
        params = StdioServerParameters(command=self.command, args=self.args, env=self.env)
        async with Client(params) as client:
            listed = await client.list_tools()
            return sorted(tool.name for tool in listed.tools)

    async def _call_tool(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        try:
            from mcp import Client, StdioServerParameters
        except ImportError as exc:
            raise GremlinTransportError("MCP dependency is unavailable") from exc
        params = StdioServerParameters(command=self.command, args=self.args, env=self.env)
        async with Client(params) as client:
            result = await client.call_tool(name, dict(arguments))
            return _extract_mapping(result)

    def list_tools(self) -> list[str]:
        return self._run(self._list_tools())

    def call_tool(self, name: str, arguments: Mapping[str, Any]) -> dict[str, Any]:
        return self._run(self._call_tool(name, arguments))
