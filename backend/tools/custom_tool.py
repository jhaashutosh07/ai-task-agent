"""
Custom HTTP Tool — the runtime for the Plugin SDK.

Users register a tool by pointing at an HTTP endpoint (plus a name, description
and JSON-Schema of parameters). At call time this tool forwards the arguments to
that endpoint and returns the response, so the agents can use it like any
built-in tool. This is the classic "webhook plugin" pattern.
"""
import json
import httpx
from .base import BaseTool, ToolResult


class CustomHTTPTool(BaseTool):
    def __init__(self, name: str, description: str, endpoint_url: str,
                 method: str = "POST", parameters: dict | None = None, headers: dict | None = None):
        self._name = name
        self._description = description
        self.endpoint_url = endpoint_url
        self.method = (method or "POST").upper()
        self._parameters = parameters or {"type": "object", "properties": {}}
        self._headers = headers or {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    def parameters(self) -> dict:
        return self._parameters

    async def execute(self, **kwargs) -> ToolResult:
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if self.method == "GET":
                    resp = await client.get(self.endpoint_url, params=kwargs, headers=self._headers)
                else:
                    resp = await client.request(
                        self.method, self.endpoint_url, json=kwargs, headers=self._headers
                    )
            resp.raise_for_status()
            try:
                body = json.dumps(resp.json())
            except Exception:
                body = resp.text
            return ToolResult(success=True, output=body[:4000])
        except Exception as e:
            return ToolResult(success=False, output="", error=f"{type(e).__name__}: {e}")
