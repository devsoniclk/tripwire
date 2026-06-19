"""Pluggable notifiers: stdout, webhook, Slack."""

from __future__ import annotations

import abc
import json
from typing import Any


class Notifier(abc.ABC):
    """Base notifier interface."""

    @abc.abstractmethod
    def notify(self, event: str, details: dict[str, Any]) -> None: ...


class StdoutNotifier(Notifier):
    """Prints events to stdout (via ``rich`` if available, else ``print``)."""

    def __init__(self, *, use_rich: bool = True) -> None:
        self._use_rich = use_rich

    def notify(self, event: str, details: dict[str, Any]) -> None:
        if self._use_rich:
            try:
                from rich.console import Console

                Console().print(f"[bold red]⚠ tripwire {event}:[/]", details)
                return
            except Exception:
                pass
        print(f"⚠ tripwire {event}: {details}")


class WebhookNotifier(Notifier):
    """POSTs a JSON payload to a URL."""

    def __init__(self, url: str) -> None:
        self.url = url

    def notify(self, event: str, details: dict[str, Any]) -> None:
        import httpx

        payload = {"event": event, **details}
        try:
            httpx.post(self.url, json=payload, timeout=10)
        except Exception as exc:
            print(f"tripwire webhook error: {exc}")


class SlackNotifier(Notifier):
    """Sends a Slack webhook message."""

    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    def notify(self, event: str, details: dict[str, Any]) -> None:
        import httpx

        text = f"⚠ *tripwire {event}*\n```{json.dumps(details, indent=2)}```"
        try:
            httpx.post(self.webhook_url, json={"text": text}, timeout=10)
        except Exception as exc:
            print(f"tripwire slack error: {exc}")
