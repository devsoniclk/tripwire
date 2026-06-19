"""Loop / rate-spike detection."""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any


@dataclass
class _CallRecord:
    tool: str
    args_hash: str
    timestamp: float


@dataclass
class LoopDetector:
    """Detects repeated near-identical tool calls and rate spikes.

    Parameters
    ----------
    repeat_threshold : int
        Number of near-identical calls within ``window_seconds`` to flag a loop.
    window_seconds : float
        Rolling window for repeat detection.
    rate_spike_per_sec : float
        Calls-per-second threshold that triggers a rate-spike warning. 0 disables.
    """

    repeat_threshold: int = 5
    window_seconds: float = 60.0
    rate_spike_per_sec: float = 0.0
    _calls: deque[_CallRecord] = field(default_factory=deque, repr=False)

    def record_call(self, tool: str, args: Any = None) -> str | None:
        """Record a tool call. Returns ``"loop"``, ``"rate_spike"``, or ``None``."""
        now = time.monotonic()
        args_hash = str(args)
        self._calls.append(_CallRecord(tool=tool, args_hash=args_hash, timestamp=now))

        # Prune old entries
        cutoff = now - self.window_seconds
        while self._calls and self._calls[0].timestamp < cutoff:
            self._calls.popleft()

        # Check for repeated identical calls
        count = sum(
            1 for c in self._calls if c.tool == tool and c.args_hash == args_hash
        )
        if count >= self.repeat_threshold:
            return "loop"

        # Check rate spike
        if self.rate_spike_per_sec > 0 and len(self._calls) >= 2:
            span = self._calls[-1].timestamp - self._calls[0].timestamp
            if span > 0:
                rate = len(self._calls) / span
                if rate >= self.rate_spike_per_sec:
                    return "rate_spike"

        return None

    def reset(self) -> None:
        self._calls.clear()
