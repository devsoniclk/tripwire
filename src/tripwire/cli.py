"""CLI entry point."""

from __future__ import annotations

import click


@click.group()
def main() -> None:
    """tripwire — Agent Cost Circuit Breaker."""


@main.command()
@click.option("--host", default="0.0.0.0", help="Bind host")
@click.option("--port", default=8787, type=int, help="Bind port")
@click.option("--upstream", default="https://api.openai.com", help="Upstream API base URL")
@click.option("--max-usd", default=5.0, type=float, help="Max USD budget per session")
@click.option("--max-tokens", default=None, type=int, help="Max total tokens")
@click.option("--max-calls", default=None, type=int, help="Max API calls")
def proxy(host: str, port: int, upstream: str, max_usd: float, max_tokens: int | None, max_calls: int | None) -> None:
    """Run the metering proxy server."""
    import uvicorn
    from tripwire.proxy import create_proxy_app
    from tripwire.budget import Budget

    budget = Budget(max_usd=max_usd, max_tokens=max_tokens, max_calls=max_calls)
    application = create_proxy_app(upstream=upstream, budget=budget)
    click.echo(f"tripwire proxy → {upstream}  (budget: ${max_usd:.2f})")
    uvicorn.run(application, host=host, port=port)


if __name__ == "__main__":
    main()
