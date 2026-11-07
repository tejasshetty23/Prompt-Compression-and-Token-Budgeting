"""Chunk context and rank chunks against the question."""
from .tokenization import count_tokens, truncate_to_last_tokens

def chunk_text(
    text: str,
    chunk_size: int,
    overlap: int,
    encoding_name: str,
    tokenizer=None,
) -> list[str]:
    """Split text into bounded chunks with overlap from the previous chunk's end.

    A Hugging Face tokenizer, when supplied, defines the chunk token boundaries.
    Otherwise the configured tiktoken encoding is used.
    """
    if chunk_size < 1:
        raise ValueError("chunk_size must be positive")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and smaller than chunk_size")
    if not text.strip():
        return []

    if tokenizer is not None:
        token_ids = tokenizer.encode(text, add_special_tokens=False)
        if not token_ids:
            return []
        step = chunk_size - overlap
        chunks = []
        for start in range(0, len(token_ids), step):
            piece = tokenizer.decode(
                token_ids[start : start + chunk_size],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            ).strip()
            if piece:
                chunks.append(piece)
        return chunks

    words, chunks, current = text.split(), [], []
    for word in words:
        candidate = " ".join(current + [word])
        if current and count_tokens(candidate, encoding_name) > chunk_size:
            previous = " ".join(current)
            chunks.append(previous)
            carry = (
                truncate_to_last_tokens(previous, overlap, encoding_name).split()
                if overlap else []
            )
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
