import asyncio
import base64
from pathlib import Path
from .base import BaseTool, ToolResult

try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


class ScreenshotTool(BaseTool):
    """Capture screenshots of web pages"""

    def __init__(self, workspace_path: str = "./workspace"):
        self.workspace_path = Path(workspace_path).resolve()
        self.workspace_path.mkdir(parents=True, exist_ok=True)

    @property
    def name(self) -> str:
        return "screenshot"

    @property
    def description(self) -> str:
        return """Capture a screenshot of a web page.
Useful for visual documentation, debugging, and capturing dynamic content."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to screenshot"
                },
                "filename": {
                    "type": "string",
                    "description": "Output filename (default: screenshot.png)"
                },
                "full_page": {
                    "type": "boolean",
                    "description": "Capture the full scrollable page",
                    "default": False
                },
                "width": {
                    "type": "integer",
                    "description": "Viewport width in pixels",
                    "default": 1280
                },
                "height": {
                    "type": "integer",
                    "description": "Viewport height in pixels",
                    "default": 720
                },
                "wait_time": {
                    "type": "integer",
                    "description": "Wait time in ms before screenshot",
                    "default": 1000
                }
            },
            "required": ["url"]
        }

    async def execute(
        self,
        url: str,
        filename: str = "screenshot.png",
        full_page: bool = False,
        width: int = 1280,
        height: int = 720,
        wait_time: int = 1000
    ) -> ToolResult:
        if not PLAYWRIGHT_AVAILABLE:
            return ToolResult(
                success=False,
                output="",
                error="Playwright is not installed. Run: pip install playwright && playwright install chromium"
            )

        try:
            # Ensure filename has extension
            if not filename.endswith('.png'):
                filename += '.png'

            output_path = self.workspace_path / filename

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={"width": width, "height": height}
                )
                page = await context.new_page()

                # Navigate to URL
                await page.goto(url, wait_until="networkidle")

                # Wait additional time if specified
                if wait_time > 0:
                    await asyncio.sleep(wait_time / 1000)

                # Take screenshot
                await page.screenshot(
                    path=str(output_path),
                    full_page=full_page
                )

                # Get page title
                title = await page.title()

                await browser.close()

            # Get file size
            file_size = output_path.stat().st_size / 1024  # KB

            output = f"""**Screenshot Captured**
- **URL:** {url}
- **Title:** {title}
- **File:** {filename}
- **Size:** {file_size:.1f} KB
- **Dimensions:** {width}x{height}
- **Full Page:** {full_page}

Screenshot saved to: {output_path}"""

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Screenshot failed: {str(e)}"
            )
