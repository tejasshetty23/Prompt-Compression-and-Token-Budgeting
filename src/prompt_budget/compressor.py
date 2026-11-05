"""LLMLingua adapter; ratio 1 is the uncompressed baseline."""
class LLMLinguaCompressor:
    def __init__(self, model_name: str, enabled: bool = True):
        self.model_name, self.enabled, self._model = model_name, enabled, None

    def _load(self):
        if self._model is None:
            try:
                from llmlingua import PromptCompressor
            except ImportError as exc:
                raise RuntimeError("Install dependencies with pip install -e .") from exc
            self._model = PromptCompressor(
                model_name=self.model_name,
                use_llmlingua2="llmlingua-2" in self.model_name.lower(),
            )
        return self._model

    def compress(self, context: str, target_ratio: float) -> tuple[str, dict]:
        if not self.enabled or target_ratio <= 1 or not context.strip():
            return context, {"method": "baseline", "target_ratio": 1.0}
        result = self._load().compress_prompt(context, rate=target_ratio, force_tokens=["\n"], drop_consecutive=True)
        return result.get("compressed_prompt", context), {"method": "llmlingua", "result": result}
