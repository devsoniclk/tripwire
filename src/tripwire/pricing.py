"""Bundled, overridable model pricing table."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_PRICING: dict[str, dict[str, float]] = {}
_loaded = False

_DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "pricing.json"


def load_pricing(path: Path | str | None = None) -> dict[str, dict[str, float]]:
    """Load pricing from *path* (or the bundled default) and return it."""
    global _PRICING, _loaded
    p = Path(path) if path else _DEFAULT_PATH
    with open(p) as f:
        _PRICING = json.load(f)
    _loaded = True
    return _PRICING


def _ensure_loaded() -> None:
    if not _loaded:
        load_pricing()


def get_pricing(model: str) -> dict[str, float] | None:
    """Return {input_per_1k, output_per_1k} for *model*, or ``None``."""
    _ensure_loaded()
    return _PRICING.get(model)


def override_pricing(model: str, *, input_per_1k: float, output_per_1k: float) -> None:
    """Add or override pricing for *model* at runtime."""
    _ensure_loaded()
    _PRICING[model] = {"input_per_1k": input_per_1k, "output_per_1k": output_per_1k}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float | None:
    """Return estimated USD cost, or ``None`` if model unknown."""
    pricing = get_pricing(model)
    if pricing is None:
        return None
    return (input_tokens / 1000) * pricing["input_per_1k"] + (output_tokens / 1000) * pricing["output_per_1k"]
