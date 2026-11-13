from prompt_budget.config import AppConfig
from prompt_budget.middleware import PromptBudgetMiddleware
from prompt_budget.compressor import LLMLinguaCompressor

def test_instruction_and_question_are_preserved(tmp_path):
    config = AppConfig()
    config.compression.enabled = False
    config.compression.use_llmlingua = False
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    result = middleware.prepare("KEEP THIS", "What happened?", "The service failed.", target_ratio=1)
    assert result.prompt.startswith("KEEP THIS\n\nWhat happened?")
    assert result.system_instruction == "KEEP THIS"
    assert result.question == "What happened?"

def test_one_x_baseline_keeps_full_context(tmp_path):
    config = AppConfig()
    config.compression.chunk_size_tokens = 2
    config.compression.top_k_chunks = 1
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    context = "alpha beta gamma delta epsilon zeta"
    result = middleware.prepare("instruction", "unrelated query", context, target_ratio=1)
    assert result.context == context
    assert result.telemetry.original_tokens == result.telemetry.compressed_tokens

def test_budget_rejects_too_small_budget(tmp_path):
    config = AppConfig()
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    try:
        middleware.prepare("Long instruction", "Long question?", "Context", token_budget=1)
    except ValueError as exc:
        assert "too small" in str(exc)
    else:
        raise AssertionError("Expected token budget validation to fail")

def test_budget_is_enforced_on_complete_prompt(tmp_path):
    config = AppConfig()
    config.compression.enabled = False
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    result = middleware.prepare("Instruction", "Question?", "word " * 500, token_budget=30)
    assert result.telemetry.prompt_tokens <= 30

def test_llmlingua_rate_is_inverse_of_compression_ratio():
    class FakeModel:
        def __init__(self):
            self.rate = None
        def compress_prompt(self, context, **kwargs):
            self.rate = kwargs["rate"]
            return {"compressed_prompt": "short"}
    compressor = LLMLinguaCompressor("fake-model", enabled=True, adaptive_control=False)
    compressor._model = FakeModel()
    output, metadata = compressor.compress("long context", 4)
    assert output == "short"
    assert compressor._model.rate == 0.25
    assert metadata["target_ratio_requested"] == 4

def test_calibrated_rate_formula():
    assert LLMLinguaCompressor.calculate_calibrated_rate(1.0) == 1.0
    r2 = LLMLinguaCompressor.calculate_calibrated_rate(2.0)
    assert 0.53 <= r2 <= 0.57
    r3 = LLMLinguaCompressor.calculate_calibrated_rate(3.0)
    assert 0.37 <= r3 <= 0.41
    r5 = LLMLinguaCompressor.calculate_calibrated_rate(5.0)
    assert 0.23 <= r5 <= 0.27

def test_adaptive_control_refinement():
    calls = []
    class MockModel:
        def compress_prompt(self, context, rate, **kwargs):
            calls.append(rate)
            # On first call simulate overshoot (only 5 tokens kept out of 100)
            if len(calls) == 1:
                return {"compressed_prompt": "word " * 5}
            # On refinement return target (20 tokens)
            return {"compressed_prompt": "word " * 20}

    compressor = LLMLinguaCompressor("fake-model", enabled=True, adaptive_control=True, tolerance=0.15, max_refinements=1)
    compressor._model = MockModel()
    output, metadata = compressor.compress("word " * 100, target_ratio=5.0)
    assert len(calls) == 2
    assert metadata["refinements"] == 1
    assert calls[1] > calls[0]

def test_requested_vs_actual_compression_bounds():
    config = AppConfig()
    middleware = PromptBudgetMiddleware(config)
    context = (
        "2026-10-01 09:00:02 INFO api-gateway accepted request id R-441. "
        "2026-10-01 09:00:03 INFO auth-service validated the session. "
        "2026-10-01 09:00:04 INFO inventory-service queried warehouse stock. "
        "2026-10-01 09:00:05 WARN inventory-service retry 1 of 3 after upstream timeout. "
        "2026-10-01 09:00:06 WARN inventory-service retry 2 of 3 after upstream timeout. "
        "2026-10-01 09:00:07 ERROR inventory-service returned HTTP 503 after three retries."
    )
    for target in [1.0, 2.0, 3.0]:
        res = middleware.prepare("Inst", "Which service failed?", context, target_ratio=target)
        act = res.telemetry.original_tokens / max(1, res.telemetry.compressed_tokens)
        assert abs(act - target) / target <= 0.20


def test_chunk_overlap_uses_previous_chunk_suffix():
    from prompt_budget.chunking import chunk_text
    from prompt_budget.tokenization import count_tokens, truncate_to_last_tokens

    text = "alpha beta gamma delta epsilon zeta eta theta"
    chunks = chunk_text(text, chunk_size=4, overlap=2, encoding_name="cl100k_base")
    assert len(chunks) >= 2
    previous_words = chunks[0].split()
    next_words = chunks[1].split()
    assert next_words[:2] == previous_words[-2:]
    assert truncate_to_last_tokens("alpha beta gamma delta", 2).split() == ["gamma", "delta"]


def test_chunk_text_rejects_invalid_sizes():
    from prompt_budget.chunking import chunk_text
    import pytest

    with pytest.raises(ValueError, match="chunk_size must be positive"):
        chunk_text("some text", 0, 0, "cl100k_base")
    with pytest.raises(ValueError, match="overlap must be non-negative"):
        chunk_text("some text", 4, -1, "cl100k_base")


def test_huggingface_tokenizer_chunks_respect_limit_and_overlap():
    from prompt_budget.chunking import chunk_text

    class CharacterTokenizer:
        def encode(self, text, add_special_tokens=False):
            return [ord(char) for char in text]

        def decode(self, token_ids, **kwargs):
            return "".join(chr(token_id) for token_id in token_ids)

    chunks = chunk_text(
        "abcdefghij", chunk_size=4, overlap=2,
        encoding_name="cl100k_base", tokenizer=CharacterTokenizer()
    )
    assert chunks == ["abcd", "cdef", "efgh", "ghij"]
    assert all(len(chunk) <= 4 for chunk in chunks)
