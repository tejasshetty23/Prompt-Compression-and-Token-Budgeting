"""Chunk context and rank chunks against the question."""
from .tokenization import count_tokens, truncate_to_tokens

def chunk_text(text: str, chunk_size: int, overlap: int, encoding_name: str) -> list[str]:
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")
    words, chunks, current = text.split(), [], []
    for word in words:
        candidate = " ".join(current + [word])
        if current and count_tokens(candidate, encoding_name) > chunk_size:
            previous = " ".join(current)
            chunks.append(previous)
            carry = truncate_to_tokens(previous, overlap, encoding_name).split() if overlap else []
            current = carry + [word]
        else:
            current.append(word)
    if current:
        chunks.append(" ".join(current))
    return chunks

def rank_chunks(question: str, chunks: list[str], top_k: int) -> list[tuple[int, str, float]]:
    terms = {w.lower().strip(".,:;!?()[]{}") for w in question.split() if len(w) > 2}
    scored = []
    for i, chunk in enumerate(chunks):
        words = {w.lower().strip(".,:;!?()[]{}") for w in chunk.split()}
        scored.append((i, chunk, len(terms & words) / max(1, len(terms))))
    return sorted(scored, key=lambda x: (-x[2], x[0]))[:top_k]
