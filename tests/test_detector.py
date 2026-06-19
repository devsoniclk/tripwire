"""Tests for tripwire.detector."""

import pytest
from tripwire.detector import LoopDetector


def test_no_detection_below_threshold():
    d = LoopDetector(repeat_threshold=5, window_seconds=60)
    for _ in range(4):
        assert d.record_call("search", {"q": "hello"}) is None


def test_detects_loop():
    d = LoopDetector(repeat_threshold=3, window_seconds=60)
    d.record_call("search", {"q": "hello"})
    d.record_call("search", {"q": "hello"})
    result = d.record_call("search", {"q": "hello"})
    assert result == "loop"


def test_different_args_no_loop():
    d = LoopDetector(repeat_threshold=3, window_seconds=60)
    d.record_call("search", {"q": "a"})
    d.record_call("search", {"q": "b"})
    result = d.record_call("search", {"q": "c"})
    assert result is None


def test_reset_clears():
    d = LoopDetector(repeat_threshold=2, window_seconds=60)
    d.record_call("tool", "x")
    d.record_call("tool", "x")
    d.reset()
    assert d.record_call("tool", "x") is None


def test_rate_spike():
    d = LoopDetector(repeat_threshold=100, window_seconds=10, rate_spike_per_sec=5)
    for i in range(20):
        result = d.record_call(f"tool_{i}", str(i))
    # With 20 calls in <1s, rate > 5/s → should spike
    assert result == "rate_spike"
