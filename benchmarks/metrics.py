"""Exact Match, token F1, ROUGE, and semantic evaluation metrics."""
import re
from collections import Counter
from functools import lru_cache

def normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", (text or "").lower())).strip()

def exact_match(prediction: str, reference: str) -> float:
    return float(normalize_answer(prediction) == normalize_answer(reference))

def token_f1(prediction: str, reference: str) -> float:
    pred, ref = normalize_answer(prediction).split(), normalize_answer(reference).split()
    if not pred or not ref:
        return float(pred == ref)
    common = sum((Counter(pred) & Counter(ref)).values())
    if not common:
        return 0.0
    precision, recall = common / len(pred), common / len(ref)
    return 2 * precision * recall / (precision + recall)

def rouge_l(prediction: str, reference: str) -> float:
    try:
        from rouge_score import rouge_scorer
    except ImportError as exc:
        raise RuntimeError("Install rouge-score to compute ROUGE-L") from exc
    scorer = rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True)
    return scorer.score(reference, prediction)["rougeL"].fmeasure

def rouge_scores(prediction: str, reference: str) -> dict:
    try:
        from rouge_score import rouge_scorer
    except ImportError as exc:
        raise RuntimeError("Install rouge-score to compute ROUGE") from exc
    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores = scorer.score(reference, prediction)
    return {
        "rouge_1": scores["rouge1"].fmeasure,
        "rouge_2": scores["rouge2"].fmeasure,
        "rouge_l": scores["rougeL"].fmeasure,
    }

def key_fact_recall(prediction: str, reference: str) -> float:
    """Measure recall of salient factual terms (numbers, entities, technical words)."""
    norm_pred = set(normalize_answer(prediction).split())
    ref_tokens = normalize_answer(reference).split()
    stopwords = {
        "the", "and", "a", "an", "in", "on", "at", "to", "for", "of", "with",
        "by", "from", "that", "this", "is", "was", "were", "are", "be", "been",
        "had", "has", "have", "it", "its", "as", "or", "which", "what", "where"
    }
    salient_ref = [tok for tok in ref_tokens if tok not in stopwords and len(tok) > 2]
    if not salient_ref:
        return 1.0 if not ref_tokens else 0.0
    matched = sum(1 for tok in salient_ref if tok in norm_pred)
    return matched / len(salient_ref)

_SEMANTIC_MODEL = None
_SEMANTIC_TOKENIZER = None

def _get_semantic_model():
    global _SEMANTIC_MODEL, _SEMANTIC_TOKENIZER
    if _SEMANTIC_MODEL is None:
        try:
            import torch
            from transformers import AutoTokenizer, AutoModel
            model_id = "sentence-transformers/all-MiniLM-L6-v2"
            _SEMANTIC_TOKENIZER = AutoTokenizer.from_pretrained(model_id, local_files_only=True)
            _SEMANTIC_MODEL = AutoModel.from_pretrained(model_id, local_files_only=True)
            _SEMANTIC_MODEL.eval()
        except Exception:
            _SEMANTIC_MODEL = False
    return _SEMANTIC_MODEL, _SEMANTIC_TOKENIZER

def semantic_similarity_details(prediction: str, reference: str) -> tuple[float, str]:
    """Return semantic score and the actual backend used; fallback is explicitly labelled."""
    if not prediction.strip() or not reference.strip():
        return float(prediction.strip() == reference.strip()), "empty-string-exact-match"
    model, tokenizer = _get_semantic_model()
    if not model or tokenizer is None:
        # Fallback to token overlap / jaccard similarity
        pred_words = set(normalize_answer(prediction).split())
        ref_words = set(normalize_answer(reference).split())
        if not pred_words or not ref_words:
            return 0.0, "token-jaccard-fallback"
        return len(pred_words & ref_words) / len(pred_words | ref_words), "token-jaccard-fallback"
    import torch
    import torch.nn.functional as F
    with torch.no_grad():
        inputs = tokenizer([prediction, reference], padding=True, truncation=True, max_length=256, return_tensors="pt")
        out = model(**inputs)
        mask = inputs["attention_mask"].unsqueeze(-1).expand(out[0].size()).float()
        sum_embeddings = torch.sum(out[0] * mask, 1)
        sum_mask = torch.clamp(mask.sum(1), min=1e-9)
        emb = F.normalize(sum_embeddings / sum_mask, p=2, dim=1)
        sim = (emb[0] @ emb[1]).item()
        return max(0.0, float(sim)), "sentence-transformers/all-MiniLM-L6-v2"


def semantic_similarity(prediction: str, reference: str) -> float:
    """Backward-compatible score-only wrapper; use details to retain provenance."""
    return semantic_similarity_details(prediction, reference)[0]
