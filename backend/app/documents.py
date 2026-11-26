import io

from pypdf import PdfReader

SUPPORTED_EXTENSIONS = (".txt", ".md", ".pdf")


def extract_text(filename: str, data: bytes) -> str:
    """Return the plain text of an uploaded file."""
    name = filename.lower()
    if name.endswith(".pdf"):
        reader = PdfReader(io.BytesIO(data))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if name.endswith((".txt", ".md")):
        return data.decode("utf-8", errors="replace")
    raise ValueError(f"Unsupported file type. Use one of: {', '.join(SUPPORTED_EXTENSIONS)}")


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    """Split text into chunks of `size` characters, each overlapping the previous by `overlap`."""
    if size <= 0:
        raise ValueError("size must be positive")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be at least 0 and smaller than size")

    text = " ".join(text.split())
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunks.append(text[start : start + size])
        if start + size >= len(text):
            break
        start += size - overlap
    return chunks
