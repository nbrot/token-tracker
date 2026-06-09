from token_tracker.log_parser import TokenUsage, UsageByModel

# USD per million tokens — June 2026
_PRICING: dict[str, dict] = {
    "opus":    {"input": 15.00, "output": 75.00, "cache_write": 18.75, "cache_read": 1.50},
    "sonnet":  {"input":  3.00, "output": 15.00, "cache_write":  3.75, "cache_read": 0.30},
    "haiku":   {"input":  0.80, "output":  4.00, "cache_write":  1.00, "cache_read": 0.08},
}
_DEFAULT = _PRICING["sonnet"]


def _get_pricing(model: str) -> dict:
    model_lower = model.lower()
    for family, p in _PRICING.items():
        if family in model_lower:
            return p
    return _DEFAULT


def cost_usd(usage: UsageByModel) -> float:
    total = 0.0
    for model, u in usage.items():
        p = _get_pricing(model)
        total += (
            u.input_tokens          * p["input"]       / 1_000_000
            + u.output_tokens       * p["output"]      / 1_000_000
            + u.cache_creation_tokens * p["cache_write"] / 1_000_000
            + u.cache_read_tokens   * p["cache_read"]  / 1_000_000
        )
    return total


def format_cost(usd: float) -> str:
    if usd < 0.01:
        return f"${usd*100:.2f}¢"
    return f"${usd:.3f}"


def format_tokens(n: int) -> str:
    if n >= 1_000_000:
        return f"{n/1_000_000:.2f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}k"
    return str(n)
