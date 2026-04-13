"""LLM client using LiteLLM via OpenRouter with Cerebras inference."""

import os

# Unset SOCKS proxy for httpx (litellm uses httpx but socksio is not installed)
# The HTTP/HTTPS proxy is still used for actual network calls
for _proxy_var in ("ALL_PROXY", "all_proxy"):
    os.environ.pop(_proxy_var, None)

from litellm import completion  # noqa: E402

from .schemas import AssistantResponse

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}

SYSTEM_PROMPT = """You are FinAlly, an AI trading assistant embedded in a simulated trading workstation.
You help users manage their portfolio, analyze positions, and execute trades.

Current portfolio context will be provided in each message.

You MUST respond with valid JSON matching this exact schema:
{
  "message": "Your conversational response to the user",
  "trades": [{"ticker": "AAPL", "side": "buy", "quantity": 10}],
  "watchlist_changes": [{"ticker": "PYPL", "action": "add"}]
}

Rules:
- message is required (non-empty string)
- trades and watchlist_changes are optional arrays (omit or use [] if none)
- side must be "buy" or "sell"
- action must be "add" or "remove"
- quantity must be positive
- Only execute trades the user explicitly requests or agrees to
- Be concise and data-driven
- All prices are simulated/virtual — this is a learning exercise"""


def call_llm(messages: list[dict]) -> AssistantResponse:
    """Call LLM and return structured response. Raises on failure."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    response = completion(
        model=MODEL,
        messages=messages,
        response_format=AssistantResponse,
        reasoning_effort="low",
        extra_body=EXTRA_BODY,
        api_key=api_key,
    )
    content = response.choices[0].message.content
    return AssistantResponse.model_validate_json(content)
