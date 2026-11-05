"""Exact Match, token F1, and ROUGE-L metrics."""
import re
from collections import Counter

def normalize_answer(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", text.lower())).strip()

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
    return rouge_scorer.RougeScorer(["rougeL"], use_stemmer=True).score(reference, prediction)["rougeL"].fmeasure
