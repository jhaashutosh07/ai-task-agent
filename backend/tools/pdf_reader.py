from pathlib import Path
from .base import BaseTool, ToolResult

try:
    from PyPDF2 import PdfReader
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False


class PDFReaderTool(BaseTool):
    """Extract text from PDF documents"""

    def __init__(self, workspace_path: str = "./workspace", max_pages: int = 50):
        self.workspace_path = Path(workspace_path).resolve()
        self.max_pages = max_pages

    @property
    def name(self) -> str:
        return "pdf_reader"

    @property
    def description(self) -> str:
        return """Extract text content from PDF documents.
Can read specific pages or the entire document."""

    @property
    def parameters(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Path to the PDF file (relative to workspace)"
                },
                "start_page": {
                    "type": "integer",
                    "description": "Starting page number (1-indexed)",
                    "default": 1
                },
                "end_page": {
                    "type": "integer",
                    "description": "Ending page number (inclusive, 0 for all)"
                },
                "extract_metadata": {
                    "type": "boolean",
                    "description": "Include document metadata",
                    "default": True
                }
            },
            "required": ["path"]
        }

    async def execute(
        self,
        path: str,
        start_page: int = 1,
        end_page: int = 0,
        extract_metadata: bool = True
    ) -> ToolResult:
        if not PDF_AVAILABLE:
            return ToolResult(
                success=False,
                output="",
                error="PyPDF2 is not installed. Run: pip install PyPDF2"
            )

        try:
            # Resolve path
            file_path = (self.workspace_path / path).resolve()

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    output="",
                    error=f"File not found: {path}"
                )

            if not str(file_path).lower().endswith(".pdf"):
                return ToolResult(
                    success=False,
                    output="",
                    error="File is not a PDF"
                )

            # Read PDF
            reader = PdfReader(str(file_path))
            total_pages = len(reader.pages)

            # Validate page range
            if start_page < 1:
                start_page = 1
            if end_page <= 0 or end_page > total_pages:
                end_page = min(total_pages, self.max_pages)
            if end_page < start_page:
                end_page = start_page

            # Extract metadata
            metadata_str = ""
            if extract_metadata and reader.metadata:
                meta = reader.metadata
                metadata_str = f"""**Metadata:**
- Title: {meta.get('/Title', 'N/A')}
- Author: {meta.get('/Author', 'N/A')}
- Subject: {meta.get('/Subject', 'N/A')}
- Creator: {meta.get('/Creator', 'N/A')}
- Pages: {total_pages}

"""

            # Extract text
            text_content = []
            for page_num in range(start_page - 1, end_page):
                page = reader.pages[page_num]
                text = page.extract_text()
                if text.strip():
                    text_content.append(f"--- Page {page_num + 1} ---\n{text}")

            if not text_content:
                return ToolResult(
                    success=True,
                    output=f"{metadata_str}**Note:** No extractable text found in the PDF (may be scanned/image-based)"
                )

            full_text = "\n\n".join(text_content)

            # Truncate if too long
            max_chars = 20000
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + "\n\n[Content truncated...]"

            output = f"""**PDF: {path}**
{metadata_str}**Extracted Text (Pages {start_page}-{end_page} of {total_pages}):**

{full_text}"""

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to read PDF: {str(e)}"
            )
