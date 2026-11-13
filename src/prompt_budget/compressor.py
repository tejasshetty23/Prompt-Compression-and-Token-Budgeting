"""LLMLingua adapter with calibrated rate mapping and target-aware control."""
import os
from .tokenization import count_tokens

class LLMLinguaCompressor:
    def __init__(
        self,
        model_name: str,
        enabled: bool = True,
        adaptive_control: bool = True,
        tolerance: float = 0.15,
        max_refinements: int = 1,
        encoding_name: str = "cl100k_base",
    ):
        self.model_name = model_name
        self.enabled = enabled
        self.adaptive_control = adaptive_control
        self.tolerance = tolerance
        self.max_refinements = max_refinements
        self.encoding_name = encoding_name
        self._model = None

    def _load(self):
        if self._model is None:
            try:
                from llmlingua import PromptCompressor
            except ImportError as exc:
                raise RuntimeError("Install LLMLingua with pip install -e .") from exc
            # Force CPU execution: the project's default PyTorch install may be
            # CPU-only, while LLMLingua otherwise defaults to CUDA.
            self._model = PromptCompressor(
                model_name=self.model_name,
                device_map="cpu",
                use_llmlingua2="llmlingua-2" in self.model_name.lower(),
            )
        return self._model

    def chunking_tokenizer(self):
        """Return LLMLingua's tokenizer and a safe content-token chunk limit."""
        model = self._load()
        tokenizer = getattr(model, "tokenizer", None)
        if tokenizer is None:
            raise RuntimeError("LLMLingua did not expose its model tokenizer")
        max_sequence = int(getattr(model, "max_seq_len", 512))
        # Reserve positions for tokenizer-added boundary tokens.
        return tokenizer, max(1, max_sequence - 2)

    @staticmethod
    def calculate_calibrated_rate(target_ratio: float) -> float:
        """Map target compression ratio R to effective LLMLingua-2 retention rate.
        Empirical calibration curve on enterprise contexts:
        rate = target_ratio^(-0.86).
        This corrects for LLMLingua-2's internal strict-percentile offset (+1)
        and subword-to-word probability expansion.
        """
        if target_ratio <= 1.0:
            return 1.0
        return max(0.05, min(1.0, float(target_ratio ** -0.86)))

    def compress(
        self,
        context: str,
        target_ratio: float,
        question: str = "",
    ) -> tuple[str, dict]:
        if target_ratio < 1:
            raise ValueError("target_ratio must be >= 1")
        if not self.enabled or target_ratio == 1 or not context.strip():
            return context, {
                "method": "baseline",
                "target_ratio": 1.0,
                "retention_rate": 1.0,
                "actual_ratio": 1.0,
                "refinements": 0,
            }

        orig_tokens = count_tokens(context, self.encoding_name)
        if orig_tokens == 0:
            return context, {
                "method": "empty",
                "actual_ratio": 1.0,
                "refinements": 0,
            }

        model = self._load()
        if self.adaptive_control:
            rate = self.calculate_calibrated_rate(target_ratio)
        else:
            rate = 1.0 / target_ratio

        result = model.compress_prompt(
            context,
            rate=rate,
            question=question,
            force_tokens=["\n"],
            drop_consecutive=True,
        )
        compressed = result.get("compressed_prompt", context)
        comp_tokens = count_tokens(compressed, self.encoding_name)
        actual_ratio = orig_tokens / max(1, comp_tokens)

        refinements = 0
        if self.adaptive_control and self.max_refinements > 0:
            rel_error = abs(actual_ratio - target_ratio) / target_ratio
            if rel_error > self.tolerance:
                # Proportional feedback adjustment
                adjusted_rate = max(0.05, min(1.0, rate * (actual_ratio / target_ratio)))
                ref_result = model.compress_prompt(
                    context,
                    rate=adjusted_rate,
                    question=question,
                    force_tokens=["\n"],
                    drop_consecutive=True,
                )
                ref_compressed = ref_result.get("compressed_prompt", context)
                ref_comp_tokens = count_tokens(ref_compressed, self.encoding_name)
                ref_actual_ratio = orig_tokens / max(1, ref_comp_tokens)

                # Keep refinement if it brought ratio closer to target
                if abs(ref_actual_ratio - target_ratio) <= abs(actual_ratio - target_ratio):
                    compressed = ref_compressed
                    actual_ratio = ref_actual_ratio
                    result = ref_result
                    rate = adjusted_rate
                refinements = 1

        return compressed, {
            "method": "llmlingua",
            "target_ratio_requested": target_ratio,
            "calibrated_rate_used": rate,
            "actual_ratio": round(actual_ratio, 4),
            "refinements": refinements,
            "reported": result,
        }
