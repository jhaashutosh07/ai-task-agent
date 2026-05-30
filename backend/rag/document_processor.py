import re
from typing import List, Tuple
from pathlib import Path


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 150) -> List[str]:
    text = re.sub(r"\n{3,}", "\n\n", text.strip())
    if len(text) <= chunk_size:
        return [text] if text else []
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        if end < len(text):
            for sep in ["\n\n", ". ", "! ", "? ", "\n"]:
                pos = text.rfind(sep, start + chunk_size // 2, end)
                if pos != -1:
                    end = pos + len(sep)
                    break
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap
        if start >= len(text):
            break
    return chunks


def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        import PyPDF2, io
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(p for p in pages if p.strip())
    except Exception as e:
        raise ValueError(f"PDF extraction failed: {e}")


def extract_text_from_html(html: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "head"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def process_document(content, filename: str, file_type: str = None) -> Tuple[str, str]:
    if not file_type:
        suffix = Path(filename).suffix.lower()
        file_type = {".pdf": "pdf", ".txt": "txt", ".md": "md",
                     ".html": "html", ".htm": "html"}.get(suffix, "txt")
    if file_type == "pdf":
        raw = content if isinstance(content, bytes) else content.encode()
        return extract_text_from_pdf(raw), "pdf"
    if file_type in ("html", "htm"):
        text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
        return extract_text_from_html(text), "html"
    text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
    return text, file_type