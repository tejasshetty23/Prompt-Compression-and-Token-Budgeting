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
        started = perf_counter()
        original_tokens = count_tokens(context, enc)
        if cfg.enabled and context.strip():
            chunks = chunk_text(context, cfg.chunk_size_tokens, cfg.chunk_overlap_tokens, enc)
            ranked = rank_chunks(question, chunks, cfg.top_k_chunks)
            ranked.sort(key=lambda item: item[0])
            selected = "\n\n".join(item[1] for item in ranked)
            compressed, metadata = self.compressor.compress(selected, ratio)
        else:
            compressed, metadata = context, {"method": "disabled"}
        fixed = system_instruction + "\n\n" + question
        fixed_tokens = count_tokens(fixed, enc)
        if token_budget is not None:
            remaining = token_budget - fixed_tokens - count_tokens("\n\nContext:\n", enc)
            if remaining < 0:
                raise ValueError("token_budget is too small for the preserved instruction and question")
            compressed = truncate_to_tokens(compressed, remaining, enc)
        prompt = fixed + "\n\nContext:\n" + compressed
        elapsed = (perf_counter() - started) * 1000
        compressed_tokens = count_tokens(compressed, enc)
        prompt_tokens = count_tokens(prompt, enc)
        cost = prompt_tokens / 1000 * self.config.cost.input_usd_per_1k_tokens
        telemetry = RequestTelemetry(original_tokens, compressed_tokens, prompt_tokens,
            round(original_tokens / max(1, compressed_tokens), 4), round(elapsed, 3),
            round(cost, 8), task)
        append_jsonl(telemetry, self.telemetry_path)
        return CompressionResult(system_instruction, question, compressed, prompt, telemetry, metadata)
