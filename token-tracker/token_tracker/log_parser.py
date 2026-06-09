import json
from datetime import date
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Optional


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0

    @property
    def total(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )

    def add(self, other: "TokenUsage") -> None:
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens
        self.cache_creation_tokens += other.cache_creation_tokens
        self.cache_read_tokens += other.cache_read_tokens


UsageByModel = Dict[str, TokenUsage]


def _parse_file(
    path: Path,
    start_date: Optional[date],
    end_date: Optional[date],
    seen_ids: set,
) -> UsageByModel:
    result: UsageByModel = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if data.get("type") != "assistant":
                    continue

                message = data.get("message") or {}
                usage = message.get("usage")
                if not usage:
                    continue

                # Deduplicate by message id (same API call appears N times in JSONL)
                msg_id = message.get("id")
                if msg_id:
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)

                # Filter by date
                ts_str = data.get("timestamp", "")
                if ts_str:
                    try:
                        # "2026-06-09T12:33:30.842Z" → date
                        entry_date = date.fromisoformat(ts_str[:10])
                        if start_date and entry_date < start_date:
                            continue
                        if end_date and entry_date > end_date:
                            continue
                    except ValueError:
                        pass

                model = message.get("model") or "unknown"
                if model not in result:
                    result[model] = TokenUsage()

                u = result[model]
                u.input_tokens += usage.get("input_tokens", 0)
                u.output_tokens += usage.get("output_tokens", 0)
                u.cache_creation_tokens += usage.get("cache_creation_input_tokens", 0)
                u.cache_read_tokens += usage.get("cache_read_input_tokens", 0)
    except (IOError, PermissionError):
        pass
    return result


def parse_usage(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
) -> UsageByModel:
    projects_dir = Path.home() / ".claude" / "projects"
    if not projects_dir.exists():
        return {}

    seen_ids: set = set()
    combined: UsageByModel = {}

    for jsonl_file in projects_dir.rglob("*.jsonl"):
        file_usage = _parse_file(jsonl_file, start_date, end_date, seen_ids)
        for model, usage in file_usage.items():
            if model not in combined:
                combined[model] = TokenUsage()
            combined[model].add(usage)

    return combined


def total_tokens(usage: UsageByModel) -> int:
    return sum(u.total for u in usage.values())
