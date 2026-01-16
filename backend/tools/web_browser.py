import httpx
from bs4 import BeautifulSoup
from .base import BaseTool, ToolResult


class WebBrowserTool(BaseTool):
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    @property
    def name(self) -> str:
        return "web_browser"

    @property
    def description(self) -> str:
        return "Fetch and read the content of a webpage. Extracts the main text content from the page."

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL of the webpage to fetch"
                },
                "extract_links": {
                    "type": "boolean",
                    "description": "Whether to extract and list links from the page",
                    "default": False
                }
            },
            "required": ["url"]
        }

    async def execute(self, url: str, extract_links: bool = False) -> ToolResult:
        try:
            response = await self.client.get(url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove script and style elements
            for element in soup(["script", "style", "nav", "footer", "header"]):
                element.decompose()

            # Get text content
            text = soup.get_text(separator="\n", strip=True)

            # Limit text length
            max_chars = 8000
            if len(text) > max_chars:
                text = text[:max_chars] + "\n\n[Content truncated...]"

            output = f"**Content from {url}:**\n\n{text}"

            # Extract links if requested
            if extract_links:
                links = []
                for a in soup.find_all("a", href=True)[:20]:
                    href = a["href"]
                    link_text = a.get_text(strip=True)[:50]
                    if href.startswith("http"):
                        links.append(f"- [{link_text}]({href})")

                if links:
                    output += "\n\n**Links found:**\n" + "\n".join(links)

            return ToolResult(success=True, output=output)

        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"HTTP error {e.response.status_code}: {str(e)}"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to fetch page: {str(e)}"
            )
