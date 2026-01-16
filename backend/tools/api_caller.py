import json
import httpx
from typing import Dict, Any, Literal
from .base import BaseTool, ToolResult


class APICallerTool(BaseTool):
    """Make HTTP API requests"""

    def __init__(self, timeout: int = 30, max_response_size: int = 50000):
        self.timeout = timeout
        self.max_response_size = max_response_size
        self.client = httpx.AsyncClient(timeout=timeout, follow_redirects=True)

    @property
    def name(self) -> str:
        return "api_caller"

    @property
    def description(self) -> str:
        return """Make HTTP API requests (GET, POST, PUT, DELETE).
Useful for interacting with REST APIs, fetching JSON data, and webhooks."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The API endpoint URL"
                },
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "description": "HTTP method",
                    "default": "GET"
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers as key-value pairs"
                },
                "body": {
                    "type": "object",
                    "description": "Request body for POST/PUT/PATCH (will be JSON encoded)"
                },
                "params": {
                    "type": "object",
                    "description": "URL query parameters"
                }
            },
            "required": ["url"]
        }

    async def execute(
        self,
        url: str,
        method: str = "GET",
        headers: Dict[str, str] = None,
        body: Dict[str, Any] = None,
        params: Dict[str, str] = None
    ) -> ToolResult:
        try:
            # Prepare headers
            request_headers = {
                "User-Agent": "AI-Task-Agent/1.0",
                "Accept": "application/json"
            }
            if headers:
                request_headers.update(headers)

            # Make request
            method = method.upper()

            kwargs = {
                "url": url,
                "headers": request_headers,
            }

            if params:
                kwargs["params"] = params

            if body and method in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = body

            if method == "GET":
                response = await self.client.get(**kwargs)
            elif method == "POST":
                response = await self.client.post(**kwargs)
            elif method == "PUT":
                response = await self.client.put(**kwargs)
            elif method == "DELETE":
                response = await self.client.delete(**kwargs)
            elif method == "PATCH":
                response = await self.client.patch(**kwargs)
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Unsupported HTTP method: {method}"
                )

            # Process response
            status_code = response.status_code
            content_type = response.headers.get("content-type", "")

            # Limit response size
            response_text = response.text[:self.max_response_size]
            if len(response.text) > self.max_response_size:
                response_text += "\n\n[Response truncated...]"

            # Try to parse as JSON for prettier output
            try:
                if "application/json" in content_type:
                    response_data = response.json()
                    response_formatted = json.dumps(response_data, indent=2)
                else:
                    response_formatted = response_text
            except:
                response_formatted = response_text

            output = f"""**API Request**
- **URL:** {url}
- **Method:** {method}
- **Status:** {status_code} {response.reason_phrase}

**Response:**
```json
{response_formatted}
```"""

            success = 200 <= status_code < 400

            return ToolResult(
                success=success,
                output=output,
                error=None if success else f"HTTP {status_code}: {response.reason_phrase}"
            )

        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output="",
                error=f"Request timed out after {self.timeout} seconds"
            )
        except httpx.RequestError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Request failed: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"API call failed: {str(e)}"
            )

    async def close(self):
        await self.client.aclose()
