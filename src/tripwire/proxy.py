"""ASGI proxy that meters OpenAI-compatible API requests."""

from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import FastAPI, Request, Response
from fastapi.responses import StreamingResponse

from tripwire.budget import Budget, BudgetExceeded, get_active_budget
from tripwire.meter import TokenMeter

app = FastAPI(title="tripwire proxy")


def create_proxy_app(
    upstream: str = "https://api.openai.com",
    budget: Budget | None = None,
) -> FastAPI:
    """Create a FastAPI app that proxies OpenAI-compatible requests with metering."""

    _app = FastAPI(title="tripwire proxy")
    _budget = budget or Budget(max_usd=5.0)
    _client = httpx.AsyncClient(base_url=upstream, timeout=120.0)

    @_app.on_event("shutdown")
    async def _shutdown() -> None:
        await _client.aclose()

    @_app.post("/v1/chat/completions")
    async def chat_completions(request: Request) -> Response:
        body = await request.json()
        model = body.get("model", "unknown")
        stream = body.get("stream", False)

        # Estimate input tokens (rough: 1 token ≈ 4 chars)
        messages = body.get("messages", [])
        approx_input = sum(len(m.get("content", "") or "") // 4 for m in messages)

        if stream:
            return StreamingResponse(
                _stream_response(_client, request, model, approx_input, _budget),
                media_type="text/event-stream",
            )

        # Non-streaming: forward and meter
        headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
        resp = await _client.post("/v1/chat/completions", content=await request.body(), headers=headers)

        if resp.status_code == 200:
            try:
                data = resp.json()
                usage = data.get("usage", {})
                in_tok = usage.get("prompt_tokens", approx_input)
                out_tok = usage.get("completion_tokens", 0)
                _budget.check(model=model, input_tokens=in_tok, output_tokens=out_tok)
            except BudgetExceeded:
                return Response(
                    content=json.dumps({"error": {"message": "tripwire: budget exceeded", "type": "budget_exceeded"}}),
                    status_code=429,
                    media_type="application/json",
                )

        return Response(content=resp.content, status_code=resp.status_code, headers=dict(resp.headers))

    return _app


async def _stream_response(client: httpx.AsyncClient, request: Request, model: str, approx_input: int, budget: Budget):
    """Proxy a streaming response while counting tokens."""
    headers = {k: v for k, v in request.headers.items() if k.lower() not in ("host", "content-length")}
    body = await request.body()

    async with client.stream("POST", "/v1/chat/completions", content=body, headers=headers) as resp:
        output_chars = 0
        async for line in resp.aiter_lines():
            if line.startswith("data: ") and line.strip() != "data: [DONE]":
                try:
                    chunk = json.loads(line[6:])
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content", "")
                    if content:
                        output_chars += len(content)
                except json.JSONDecodeError:
                    pass
            yield line + "\n"

    # Approximate output tokens
    approx_output = output_chars // 4
    try:
        budget.check(model=model, input_tokens=approx_input, output_tokens=approx_output)
    except BudgetExceeded:
        pass  # Already streamed; next request will be blocked


# Default app for uvicorn
default_app = create_proxy_app()
