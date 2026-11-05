"""Core middleware: only context is compressed; instructions and question remain intact."""
from dataclasses import dataclass
from time import perf_counter
from .chunking import chunk_text, rank_chunks
from .compressor import LLMLinguaCompressor
from .config import AppConfig
from .telemetry import RequestTelemetry, append_jsonl
from .tokenization import count_tokens, truncate_to_tokens

@dataclass
class CompressionResult:
    system_instruction: str
    question: str
    context: str
    prompt: str
    telemetry: RequestTelemetry
    compressor_metadata: dict

class PromptBudgetMiddleware:
    def __init__(self, config: AppConfig, telemetry_path: str = "artifacts/telemetry.jsonl"):
        self.config, self.telemetry_path = config, telemetry_path
        c = config.compression
        self.compressor = LLMLinguaCompressor(c.model_name, c.use_llmlingua)

    def prepare(self, system_instruction: str, question: str, context: str,
                target_ratio: float | None = None, token_budget: int | None = None,
                task: str = "unspecified") -> CompressionResult:
        cfg, enc = self.config.compression, self.config.tokenizer.encoding_name
        ratio = cfg.target_ratio if target_ratio is None else target_ratio
        if ratio < 1:
            raise ValueError("target_ratio must be >= 1")
        if token_budget is not None and token_budget < 1:
            raise ValueError("token_budget must be a positive integer")

        started = perf_counter()
        original_tokens = count_tokens(context, enc)
        metadata = {"method": "baseline", "target_ratio": 1.0}
        # The 1x baseline retains the entire source context; retrieval must not
        # silently remove evidence from the baseline condition.
        if not cfg.enabled or ratio == 1 or not context.strip():
            prepared_context = context
        else:
            chunks = chunk_text(context, cfg.chunk_size_tokens, cfg.chunk_overlap_tokens, enc)
            ranked = rank_chunks(question, chunks, cfg.top_k_chunks)
            ranked.sort(key=lambda item: item[0])
            selected_context = "\\n\\n".join(item[1] for item in ranked)
            selected_tokens = count_tokens(selected_context, enc)
            if selected_tokens < cfg.min_tokens:
                prepared_context = selected_context
                metadata = {"method": "below_minimum", "selected_tokens": selected_tokens}
            else:
                prepared_context, metadata = self.compressor.compress(selected_context, ratio)

        fixed = system_instruction + "\\n\\n" + question
        prefix = fixed + "\\n\\nContext:\\n"
        if token_budget is not None:
            if count_tokens(prefix, enc) > token_budget:
                raise ValueError("token_budget is too small for the preserved instruction and question")
            prepared_context = truncate_to_tokens(
                prepared_context, max(0, token_budget - count_tokens(prefix, enc)), enc
            )
            # Tokenization across concatenation boundaries is not strictly additive.
            while prepared_context and count_tokens(prefix + prepared_context, enc) > token_budget:
                current = count_tokens(prepared_context, enc)
                prepared_context = truncate_to_tokens(prepared_context, max(0, current - 1), enc)

        prompt = prefix + prepared_context
        elapsed = (perf_counter() - started) * 1000
        compressed_tokens = count_tokens(prepared_context, enc)
        prompt_tokens = count_tokens(prompt, enc)
        cost = prompt_tokens / 1000 * self.config.cost.input_usd_per_1k_tokens
        telemetry = RequestTelemetry(
            original_tokens, compressed_tokens, prompt_tokens,
            round(original_tokens / max(1, compressed_tokens), 4),
            round(elapsed, 3), round(cost, 8), task,
        )
        append_jsonl(telemetry, self.telemetry_path)
        return CompressionResult(system_instruction, question, prepared_context, prompt, telemetry, metadata)
