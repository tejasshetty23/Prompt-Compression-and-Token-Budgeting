from prompt_budget.config import AppConfig
from prompt_budget.middleware import PromptBudgetMiddleware

def test_instruction_and_question_are_preserved(tmp_path):
    config = AppConfig()
    config.compression.enabled = False
    config.compression.use_llmlingua = False
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    result = middleware.prepare("KEEP THIS", "What happened?", "The service failed.", target_ratio=1)
    assert result.prompt.startswith("KEEP THIS\n\nWhat happened?")
    assert result.system_instruction == "KEEP THIS"
    assert result.question == "What happened?"

def test_budget_rejects_too_small_budget(tmp_path):
    config = AppConfig()
    middleware = PromptBudgetMiddleware(config, str(tmp_path / "telemetry.jsonl"))
    try:
        middleware.prepare("Long instruction", "Long question?", "Context", token_budget=1)
    except ValueError as exc:
        assert "too small" in str(exc)
    else:
        raise AssertionError("Expected token budget validation to fail")
