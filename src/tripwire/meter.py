"""Token/call/$ accounting meter."""

from __future__ import annotations

import threading
from dataclasses import dataclass, field

from tripwire.pricing import estimate_cost


@dataclass
class TokenMeter:
    """Thread-safe meter that tracks token usage, call counts, and estimated cost."""

    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0
    estimated_cost: float = 0.0
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Record a call. Returns the estimated cost for this call."""
        cost = estimate_cost(model, input_tokens, output_tokens) or 0.0
        with self._lock:
            self.input_tokens += input_tokens
            self.output_tokens += output_tokens
            self.calls += 1
            self.estimated_cost += cost
        return cost

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "input_tokens": self.input_tokens,
                "output_tokens": self.output_tokens,
                "total_tokens": self.total_tokens,
                "calls": self.calls,
                "estimated_cost": round(self.estimated_cost, 6),
            }

    def reset(self) -> None:
        with self._lock:
            self.input_tokens = 0
            self.output_tokens = 0
            self.calls = 0
            self.estimated_cost = 0.0
