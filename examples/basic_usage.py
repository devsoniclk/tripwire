"""Basic usage: context manager and decorator modes."""

from tripwire import Budget, BudgetExceeded, get_active_budget

# --- Context manager mode ---
print("=== Context manager ===")
try:
    with Budget(max_usd=0.01, max_calls=100, warn_at=0.8,
                on_warn=lambda s: print(f"⚠ Warning: {s.estimated_cost:.6f} USD spent")):
        b = get_active_budget()
        # Simulate some LLM calls
        for i in range(5):
            b.check(model="gpt-4o-mini", input_tokens=500, output_tokens=200)
            print(f"  Call {i+1}: ${b.meter.estimated_cost:.6f}")
except BudgetExceeded as e:
    print(f"🛑 Budget exceeded: {e}")


# --- Decorator mode ---
print("\n=== Decorator ===")


@Budget(max_calls=3)
def my_agent():
    b = get_active_budget()
    for i in range(5):
        b.check(model="gpt-4o-mini", input_tokens=100, output_tokens=50)
        print(f"  Agent call {i+1}")


try:
    my_agent()
except BudgetExceeded as e:
    print(f"🛑 Budget exceeded: {e}")
