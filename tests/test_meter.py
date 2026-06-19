"""Tests for tripwire.meter."""

import pytest
from tripwire.meter import TokenMeter
from tripwire.pricing import load_pricing


@pytest.fixture(autouse=True)
def _load_pricing():
    load_pricing()


def test_record_tracks_tokens():
    m = TokenMeter()
    m.record("gpt-4o", 1000, 500)
    assert m.input_tokens == 1000
    assert m.output_tokens == 500
    assert m.total_tokens == 1500
    assert m.calls == 1
    assert m.estimated_cost > 0


def test_record_accumulates():
    m = TokenMeter()
    m.record("gpt-4o", 1000, 500)
    m.record("gpt-4o", 2000, 1000)
    assert m.input_tokens == 3000
    assert m.output_tokens == 1500
    assert m.calls == 2


def test_unknown_model_costs_zero():
    m = TokenMeter()
    cost = m.record("nonexistent-model", 1000, 1000)
    assert cost == 0.0
    assert m.estimated_cost == 0.0


def test_snapshot():
    m = TokenMeter()
    m.record("gpt-4o", 1000, 500)
    snap = m.snapshot()
    assert snap["input_tokens"] == 1000
    assert snap["calls"] == 1


def test_reset():
    m = TokenMeter()
    m.record("gpt-4o", 1000, 500)
    m.reset()
    assert m.input_tokens == 0
    assert m.calls == 0
    assert m.estimated_cost == 0.0
