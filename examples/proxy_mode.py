"""Proxy mode: run an OpenAI-compatible metering proxy.

Usage:
    python proxy_mode.py
    # In another terminal:
    curl http://localhost:8787/v1/chat/completions -d '{"model":"gpt-4o","messages":[{"role":"user","content":"hi"}]}'
"""

from tripwire.proxy import create_proxy_app
from tripwire.budget import Budget


def main():
    budget = Budget(max_usd=1.0, max_calls=50)
    app = create_proxy_app(upstream="https://api.openai.com", budget=budget)

    import uvicorn
    print("tripwire proxy listening on :8787  (budget: $1.00)")
    uvicorn.run(app, host="0.0.0.0", port=8787)


if __name__ == "__main__":
    main()
