"""Typed YAML configuration."""
from pathlib import Path
from pydantic import BaseModel, Field
import yaml

class CompressionConfig(BaseModel):
    enabled: bool = True
    target_ratio: float = Field(2.0, gt=0)
    min_tokens: int = Field(32, ge=1)
    chunk_size_tokens: int = Field(800, ge=1)
    chunk_overlap_tokens: int = Field(80, ge=0)
    top_k_chunks: int = Field(8, ge=1)
    use_llmlingua: bool = True
    model_name: str = "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
    adaptive_control: bool = True
    tolerance: float = Field(0.15, ge=0.0)
    max_refinements: int = Field(1, ge=0)

class TokenizerConfig(BaseModel):
    encoding_name: str = "cl100k_base"

class CostConfig(BaseModel):
    input_usd_per_1k_tokens: float = Field(0.0, ge=0)
    output_usd_per_1k_tokens: float = Field(0.0, ge=0)

class BenchmarkConfig(BaseModel):
    ratios: list[float] = [1.0, 2.0, 3.0, 5.0]
    runs_per_case: int = Field(3, ge=1)
    temperature: float = 0.0

class AppConfig(BaseModel):
    compression: CompressionConfig = CompressionConfig()
    tokenizer: TokenizerConfig = TokenizerConfig()
    cost: CostConfig = CostConfig()
    benchmark: BenchmarkConfig = BenchmarkConfig()

def load_config(path: str | Path) -> AppConfig:
    with Path(path).open(encoding="utf-8") as f:
        return AppConfig.model_validate(yaml.safe_load(f) or {})
