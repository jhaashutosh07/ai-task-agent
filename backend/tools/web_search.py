from .base import BaseTool, ToolResult
from duckduckgo_search import DDGS


class WebSearchTool(BaseTool):
    @property
    def name(self) -> str:
        return "web_search"

    @property
    def description(self) -> str:
        return "Search the web using DuckDuckGo. Use this to find current information, articles, documentation, or answers to questions."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query"
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return (default: 5)",
                    "default": 5
                }
            },
            "required": ["query"]
        }

    async def execute(self, query: str, max_results: int = 5) -> ToolResult:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))

            if not results:
                return ToolResult(
                    success=True,
                    output="No results found for the query."
                )

            # Format results
            output_lines = []
            for i, result in enumerate(results, 1):
                title = result.get("title", "No title")
                href = result.get("href", "")
                body = result.get("body", "")
                output_lines.append(f"{i}. **{title}**\n   URL: {href}\n   {body}\n")

            return ToolResult(
                success=True,
                output="\n".join(output_lines)
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Search failed: {str(e)}"
            )
