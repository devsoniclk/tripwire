# tripwire

> An agent in a loop can spend your entire month's budget in an afternoon. **tripwire** stops it at line 1.

A framework-agnostic budget guard that watches an agent's token spend and tool calls in real time, and kills runaway loops before they generate a catastrophic bill.

## Quickstart

```bash
pip install tripwire
```

```python
from tripwire import Budget, BudgetExceeded

with Budget(max_usd=2.00, max_calls=50, warn_at=0.8):
    run_my_agent()  # raises BudgetExceeded if cap blown
```

That's it. Three lines between you and a $34k surprise.

## Three Failure Modes tripwire Catches

### 🔄 Infinite Loop
An agent calls the same tool with the same args 200 times. tripwire's `LoopDetector` spots the pattern and trips the breaker.

### 🌊 Runaway Fan-Out
An orchestrator spawns 50 sub-agents that each call the LLM 10 times. The call counter hits `max_calls` and kills it.

### 💧 Slow Leak
A long-running agent makes small calls that individually look fine but cumulatively blow the budget. The `max_usd` ceiling catches it.

## Proxy Mode

Run an OpenAI-compatible metering proxy. Every request gets counted:

```bash
tripwire proxy --max-usd 5 --upstream https://api.openai.com
```

Then point your SDK at `http://localhost:8787`:

```python
client = OpenAI(base_url="http://localhost:8787/v1")
```

## Integration Modes

### Context Manager
```python
with Budget(max_usd=2.0, max_calls=50, warn_at=0.8,
            on_warn=lambda s: print(f"Warning: {s}")):
    run_my_agent()
```

### Decorator
```python
@Budget(max_tokens=200_000)
def nightly_agent(): ...
```

### Middleware / Callback
Feed token usage from your LLM client into `budget.check()`:
```python
budget.check(model="gpt-4o", input_tokens=1500, output_tokens=300)
```

### LangChain Adapter
```python
from tripwire.adapters.langchain import TripwireCallbackHandler

handler = TripwireCallbackHandler(budget)
llm = ChatOpenAI(callbacks=[handler])
```

## Pricing Table

tripwire bundles a pricing table in `data/pricing.json` covering GPT-4o, Claude, Gemini, and more. Override any model at runtime:

```python
from tripwire.pricing import override_pricing
override_pricing("my-custom-model", input_per_1k=0.002, output_per_1k=0.01)
```

## License

MIT
