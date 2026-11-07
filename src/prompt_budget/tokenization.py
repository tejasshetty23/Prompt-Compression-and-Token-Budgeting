"""Token counting and truncation."""
from functools import lru_cache

@lru_cache(maxsize=8)
def _encoding(name: str):
    try:
        import tiktoken
        return tiktoken.get_encoding(name)
    except Exception:
        return None

def count_tokens(text: str, encoding_name: str = "cl100k_base") -> int:
    enc = _encoding(encoding_name)
    if enc is not None:
        return len(enc.encode(text))
    return max(1, (len(text) + 3) // 4) if text else 0

def truncate_to_tokens(text: str, limit: int, encoding_name: str = "cl100k_base") -> str:
    if limit <= 0:
        return ""
    enc = _encoding(encoding_name)
    return enc.decode(enc.encode(text)[:limit]) if enc else text[:limit * 4]

def truncate_to_last_tokens(text: str, limit: int, encoding_name: str = "cl100k_base") -> str:
    """Keep the final tokens, for correctly carrying chunk overlap."""
    if limit <= 0 or not text:
        return ""
    enc = _encoding(encoding_name)
    if enc is not None:
        return enc.decode(enc.encode(text)[-limit:])
    return text[-limit * 4:]
