"""Read supported source documents."""
from pathlib import Path

def read_text(path: str | Path) -> str:
    path = Path(path)
    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber
        except ImportError as exc:
            raise RuntimeError("Install pdfplumber to read PDFs") from exc
        with pdfplumber.open(path) as pdf:
            return "\n\n".join(f"[Page {i}]\n{p.extract_text() or ''}" for i, p in enumerate(pdf.pages, 1))
    if path.suffix.lower() in {".txt", ".log", ".md", ".csv", ".json", ".jsonl"}:
        return path.read_text(encoding="utf-8", errors="replace")
    raise ValueError(f"Unsupported file type: {path.suffix}")

def normalize_text(text: str) -> str:
    lines = [line.strip() for line in text.replace("\r", "\n").split("\n")]
    return "\n".join(line for line in lines if line)
