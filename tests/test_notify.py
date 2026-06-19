"""Tests for tripwire.notify."""

import pytest
from tripwire.notify import StdoutNotifier, Notifier


class CapturingNotifier(Notifier):
    def __init__(self):
        self.events = []

    def notify(self, event, details):
        self.events.append((event, details))


def test_stdout_notifier(capsys):
    n = StdoutNotifier(use_rich=False)
    n.notify("test_event", {"key": "value"})
    captured = capsys.readouterr()
    assert "tripwire test_event" in captured.out


def test_capturing_notifier():
    n = CapturingNotifier()
    n.notify("budget_exceeded", {"reason": "too much"})
    assert len(n.events) == 1
    assert n.events[0][0] == "budget_exceeded"
