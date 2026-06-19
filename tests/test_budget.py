"""Tests for tripwire.budget."""

import pytest
from tripwire.budget import Budget, BudgetExceeded, get_active_budget
from tripwire.pricing import load_pricing
from tripwire.meter import TokenMeter


@pytest.fixture(autouse=True)
def _load_pricing():
    load_pricing()


def test_context_manager_exceeded_usd():
    with pytest.raises(BudgetExceeded, match="cost"):
        with Budget(max_usd=0.001) as b:
            b.check(model="gpt-4o", input_tokens=10000, output_tokens=10000)


def test_context_manager_exceeded_calls():
    with pytest.raises(BudgetExceeded, match="calls"):
        with Budget(max_calls=2) as b:
            b.check(model="gpt-4o", input_tokens=1, output_tokens=1)
            b.check(model="gpt-4o", input_tokens=1, output_tokens=1)
            b.check(model="gpt-4o", input_tokens=1, output_tokens=1)


def test_context_manager_exceeded_tokens():
    with pytest.raises(BudgetExceeded, match="tokens"):
        with Budget(max_tokens=100) as b:
            b.check(model="gpt-4o", input_tokens=60, output_tokens=60)


def test_context_manager_within_budget():
    with Budget(max_usd=100.0, max_calls=100) as b:
        b.check(model="gpt-4o", input_tokens=10, output_tokens=10)
    # Should not raise


def test_warn_callback():
    warned = []
    # First call triggers warn (cost ~0.06 > 0.1*0.5=0.05 but < 0.1), second exceeds
    with pytest.raises(BudgetExceeded):
        with Budget(max_usd=0.1, warn_at=0.5, on_warn=lambda s: warned.append(s)) as b:
            b.check(model="gpt-4o", input_tokens=5000, output_tokens=5000)  # ~$0.0625
            b.check(model="gpt-4o", input_tokens=5000, output_tokens=5000)  # total ~$0.125 → exceeds
    assert len(warned) == 1


def test_trip_callback():
    tripped = []
    with pytest.raises(BudgetExceeded):
        with Budget(max_usd=0.001, on_trip=lambda s: tripped.append(s)) as b:
            b.check(model="gpt-4o", input_tokens=10000, output_tokens=10000)
    assert len(tripped) == 1
    assert tripped[0].limit_hit


def test_decorator():
    call_count = 0

    @Budget(max_calls=2)
    def my_agent():
        nonlocal call_count
        call_count += 1
        b = get_active_budget()
        assert b is not None
        b.check(model="gpt-4o", input_tokens=1, output_tokens=1)
        b.check(model="gpt-4o", input_tokens=1, output_tokens=1)
        b.check(model="gpt-4o", input_tokens=1, output_tokens=1)

    with pytest.raises(BudgetExceeded):
        my_agent()
    assert call_count == 1


def test_no_limits_raises():
    with pytest.raises(ValueError):
        Budget()
