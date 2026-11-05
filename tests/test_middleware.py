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
    compressor = LLMLinguaCompressor("fake-model", enabled=True)
    compressor._model = FakeModel()
    output, metadata = compressor.compress("long context", 4)
    assert output == "short"
    assert compressor._model.rate == 0.25
    assert metadata["retention_rate_requested"] == 0.25
