"""LangChain callback handler that integrates with tripwire metering."""

from __future__ import annotations

from typing import Any, Optional

try:
    from langchain_core.callbacks import BaseCallbackHandler
except ImportError:
    # Stub so the module can be imported without langchain installed
    class BaseCallbackHandler:  # type: ignore[no-redef]
        pass

from tripwire.budget import Budget


class TripwireCallbackHandler(BaseCallbackHandler):
    """LangChain callback that feeds token usage into a tripwire Budget.

    Usage::

        from tripwire.adapters.langchain import TripwireCallbackHandler

        budget = Budget(max_usd=2.0)
        handler = TripwireCallbackHandler(budget)
        llm.invoke("hello", config={"callbacks": [handler]})
    """

    def __init__(self, budget: Budget) -> None:
        super().__init__()
        self.budget = budget

    def on_llm_end(self, response: Any, **kwargs: Any) -> None:
        """Called when an LLM call finishes. Extracts token usage."""
        llm_output = getattr(response, "llm_output", None) or {}
        usage = llm_output.get("token_usage", {}) or llm_output.get("usage", {})

        input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0)

        # Try to get model name
        model = "unknown"
        if hasattr(response, "llm_output") and response.llm_output:
            model = response.llm_output.get("model_name", model)

        self.budget.check(model=model, input_tokens=input_tokens, output_tokens=output_tokens)

    def on_tool_start(self, serialized: dict[str, Any], input_str: str, **kwargs: Any) -> None:
        """Track tool calls for loop detection."""
        tool_name = serialized.get("name", "unknown")
        self.budget.check(tool=tool_name, tool_args=input_str)
