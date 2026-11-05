"""JSONL telemetry and cost estimates."""
from dataclasses import asdict, dataclass
from pathlib import Path
import json

@dataclass
class RequestTelemetry:
    original_tokens: int
    compressed_tokens: int
    prompt_tokens: int
    compression_ratio: float
    compression_latency_ms: float
    input_cost_usd: float
    task: str = "unspecified"

    def to_dict(self):
        row = asdict(self)
        row["estimated_total_cost_usd"] = self.input_cost_usd
        return row

def append_jsonl(record: RequestTelemetry, path: str | Path):
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record.to_dict()) + "\n")
