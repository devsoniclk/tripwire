"""Budget context manager, decorator, and state tracking."""

from __future__ import annotations

import functools
import threading
from dataclasses import dataclass, field
from typing import Any, Callable

from tripwire.meter import TokenMeter
from tripwire.detector import LoopDetector
from tripwire.notify import Notifier, StdoutNotifier


class BudgetExceeded(Exception):
    """Raised when a budget ceiling is breached."""

    def __init__(self, message: str, state: BudgetState | None = None):
        super().__init__(message)
        self.state = state


@dataclass
class BudgetState:
    """Snapshot of current budget consumption."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    calls: int = 0
    estimated_cost: float = 0.0
    limit_hit: str = ""


# Thread-local storage for active budget
_active_budget: threading.local = threading.local()


def get_active_budget() -> Budget | None:
    """Return the active budget for the current thread, if any."""
    return getattr(_active_budget, "current", None)


class Budget:
    """Circuit-breaker guard for agent cost.

    Can be used as a context manager or decorator::

        with Budget(max_usd=2.0) as b:
            ...

        @Budget(max_tokens=200_000)
        def agent(): ...
    """

    def __init__(
        self,
        *,
        max_usd: float | None = None,
        max_tokens: int | None = None,
        max_calls: int | None = None,
        warn_at: float = 0.8,
        on_warn: Callable[[BudgetState], Any] | None = None,
        on_trip: Callable[[BudgetState], Any] | None = None,
        notifier: Notifier | None = None,
        detector: LoopDetector | None = None,
    ):
        if max_usd is None and max_tokens is None and max_calls is None:
            raise ValueError("At least one of max_usd, max_tokens, max_calls must be set")
        self.max_usd = max_usd
        self.max_tokens = max_tokens
        self.max_calls = max_calls
        self.warn_at = warn_at
        self.on_warn = on_warn
        self.on_trip = on_trip
        self.notifier = notifier or StdoutNotifier()
        self.detector = detector
        self.meter = TokenMeter()
        self._warned = False
        self._lock = threading.Lock()

    def _make_state(self, limit_hit: str = "") -> BudgetState:
        snap = self.meter.snapshot()
        return BudgetState(
            input_tokens=snap["input_tokens"],
            output_tokens=snap["output_tokens"],
            total_tokens=snap["total_tokens"],
            calls=snap["calls"],
            estimated_cost=snap["estimated_cost"],
            limit_hit=limit_hit,
        )

    def check(self, model: str | None = None, input_tokens: int = 0, output_tokens: int = 0, tool: str | None = None, tool_args: Any = None) -> None:
        """Record usage and check limits. Raises BudgetExceeded if breached."""
        if model is not None:
            self.meter.record(model, input_tokens, output_tokens)

        # Loop detection
        if self.detector and tool is not None:
            flag = self.detector.record_call(tool, tool_args)
            if flag:
                state = self._make_state(f"detector:{flag}")
                self.notifier.notify("loop_detected", {"flag": flag, "tool": tool})
                if self.on_trip:
                    self.on_trip(state)
                raise BudgetExceeded(f"Tripwire: {flag} detected in tool '{tool}'", state)

        state = self._make_state()

        # Check ceilings
        limit_hit = ""
        if self.max_usd is not None and state.estimated_cost >= self.max_usd:
            limit_hit = f"cost ${state.estimated_cost:.4f} >= ${self.max_usd:.2f}"
        elif self.max_tokens is not None and state.total_tokens >= self.max_tokens:
            limit_hit = f"tokens {state.total_tokens} >= {self.max_tokens}"
        elif self.max_calls is not None and state.calls >= self.max_calls:
            limit_hit = f"calls {state.calls} >= {self.max_calls}"

        if limit_hit:
            state.limit_hit = limit_hit
            self.notifier.notify("budget_exceeded", {"reason": limit_hit})
            if self.on_trip:
                self.on_trip(state)
            raise BudgetExceeded(f"Tripwire: {limit_hit}", state)

        # Warn threshold
        with self._lock:
            if not self._warned:
                fraction = 0.0
                if self.max_usd and self.max_usd > 0:
                    fraction = max(fraction, state.estimated_cost / self.max_usd)
                if self.max_tokens and self.max_tokens > 0:
                    fraction = max(fraction, state.total_tokens / self.max_tokens)
                if self.max_calls and self.max_calls > 0:
                    fraction = max(fraction, state.calls / self.max_calls)
                if fraction >= self.warn_at:
                    self._warned = True
                    self.notifier.notify("budget_warning", {"fraction": round(fraction, 3)})
                    if self.on_warn:
                        self.on_warn(state)

    # --- Context manager ---

    def __enter__(self) -> Budget:
        self.meter.reset()
        self._warned = False
        _active_budget.current = self
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        _active_budget.current = None
        return False  # Don't suppress exceptions

    # --- Decorator ---

    def __call__(self, fn: Callable) -> Callable:
        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with self:
                return fn(*args, **kwargs)
        return wrapper
