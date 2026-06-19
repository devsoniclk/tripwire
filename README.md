# tripwire

An agent stuck in a loop can spend your monthly budget in an afternoon. I know because it happened to me. tripwire is the thing I wish I'd had.

It's a budget guard that watches token spend and tool calls in real time. When the agent hits your cap — or starts looping the same call 40 times — it raises `BudgetExceeded` and stops.

```bash
pip install tripwire
```

```python
from tripwire import Budget, BudgetExceeded

with Budget(max_usd=2.00, max_calls=50, warn_at=0.8):
    run_my_agent()
```

That's the whole thing for most use cases.

---

## The failure modes it catches

**Infinite loops.** Agent calls the same tool with the same args over and over. The `LoopDetector` spots the repeat pattern and trips the breaker before it becomes expensive.

**Runaway fan-out.** An orchestrator spawns sub-agents that each spin up their own LLM calls. The flat call counter hits `max_calls` regardless of nesting depth.

**Slow leaks.** A long-running agent making small calls that look fine individually but add up. The `max_usd` ceiling catches cumulative spend.

---

## Other integration modes

```python
# decorator
@Budget(max_tokens=200_000)
def nightly_agent(): ...

# callback — feed usage directly from your LLM response
budget.check(model="gpt-4o", input_tokens=1500, output_tokens=300)

# langchain
from tripwire.adapters.langchain import TripwireCallbackHandler
llm = ChatOpenAI(callbacks=[TripwireCallbackHandler(budget)])
```

## Proxy mode

If you'd rather not touch application code:

```bash
tripwire proxy --max-usd 5 --upstream https://api.openai.com
```

Point your SDK at `http://localhost:8787` instead. Every request gets metered through the proxy.

## Pricing

Bundles a pricing table covering GPT-4o, Claude, Gemini, and others in `data/pricing.json`. You can override any model:

```python
from tripwire.pricing import override_pricing
override_pricing("my-finetuned-model", input_per_1k=0.002, output_per_1k=0.01)
```

## License

MIT
