"""LLMLingua adapter; target_ratio is the compression multiplier."""
class LLMLinguaCompressor:
    def __init__(self, model_name: str, enabled: bool = True):
        self.model_name, self.enabled, self._model = model_name, enabled, None

    def _load(self):
        if self._model is None:
            try:
                from llmlingua import PromptCompressor
            except ImportError as exc:
                raise RuntimeError("Install LLMLingua with pip install -e .") from exc
            self._model = PromptCompressor(
                model_name=self.model_name,
                use_llmlingua2="llmlingua-2" in self.model_name.lower(),
            )
        return self._model

    def compress(self, context: str, target_ratio: float) -> tuple[str, dict]:
        if target_ratio < 1:
            raise ValueError("target_ratio must be >= 1")
        if not self.enabled or target_ratio == 1 or not context.strip():
            return context, {"method": "baseline", "target_ratio": 1.0, "retention_rate": 1.0}
        # LLMLingua rate is the retained-token fraction, not the compression multiplier.
        retention_rate = 1.0 / target_ratio
        result = self._load().compress_prompt(
            context, rate=retention_rate, force_tokens=["\\n"], drop_consecutive=True
        )
        compressed = result.get("compressed_prompt", context)
        return compressed, {
            "method": "llmlingua",
            "target_ratio_requested": target_ratio,
            "retention_rate_requested": retention_rate,
            "reported": result,
        }
