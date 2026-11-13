import pytest
import sys
from pathlib import Path

# Add benchmarks directory to path for metric imports
benchmarks_dir = Path(__file__).resolve().parent.parent / "benchmarks"
if str(benchmarks_dir) not in sys.path:
    sys.path.insert(0, str(benchmarks_dir))

from metrics import (
    exact_match,
    token_f1,
    rouge_l,
    rouge_scores,
    key_fact_recall,
    semantic_similarity,
)

def test_exact_match_normalization():
    assert exact_match("inventory-service", "inventory-service") == 1.0
    assert exact_match("  Inventory-Service!  ", "inventory-service") == 1.0
    assert exact_match("other-service", "inventory-service") == 0.0

def test_token_f1_calculation():
    pred = "database pool restored to 80"
    ref = "restoring database pool to 80 resolved issue"
    score = token_f1(pred, ref)
    assert 0.6 <= score <= 0.8
    assert token_f1("completely unrelated text", "database error") == 0.0

def test_rouge_scores():
    pred = "the database was restored and requests succeeded"
    ref = "database was restored and client requests succeeded normally"
    scores = rouge_scores(pred, ref)
    assert "rouge_1" in scores and "rouge_2" in scores and "rouge_l" in scores
    assert scores["rouge_l"] > 0.6

def test_key_fact_recall():
    pred = "service returned HTTP 503 after three retries"
    ref = "inventory-service returned HTTP 503 after 3 retries"
    recall = key_fact_recall(pred, ref)
    assert recall > 0.4
    assert key_fact_recall("", "some critical reference") == 0.0

def test_semantic_similarity_paraphrase():
    pred = "The engineer increased the connection pool limit from 20 to 60."
    ref = "The database connection pool maximum was raised from 20 to 60."
    sim = semantic_similarity(pred, ref)
    assert sim > 0.70

def test_semantic_similarity_unrelated():
    pred = "The weather in Seattle is rainy and cold."
    ref = "Kubernetes worker pod crashed due to an out of memory error."
    sim = semantic_similarity(pred, ref)
    assert sim < 0.30
