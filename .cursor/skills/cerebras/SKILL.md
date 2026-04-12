---
name: cerebras-inference
description: >-
  Writes Python code to call LLMs via LiteLLM and OpenRouter with Cerebras as
  the inference provider, including structured outputs. Use when integrating
  Cerebras, OpenRouter, LiteLLM completions, or provider routing with
  `extra_body`.
---

# Calling an LLM via Cerebras

These instructions support writing code that calls an LLM with Cerebras as the inference provider. The flow uses LiteLLM and OpenRouter.

## Setup

Set `OPENROUTER_API_KEY` in the `.env` file and load it as an environment variable.

The uv project must include `litellm` and `pydantic`:

```bash
uv add litellm pydantic
```

## Code snippets

### Imports and constants

```python
from litellm import completion

MODEL = "openrouter/openai/gpt-oss-120b"
EXTRA_BODY = {"provider": {"order": ["cerebras"]}}
```

### Text completion

```python
response = completion(
    model=MODEL,
    messages=messages,
    reasoning_effort="low",
    extra_body=EXTRA_BODY,
)
result = response.choices[0].message.content
```

### Structured outputs

```python
response = completion(
    model=MODEL,
    messages=messages,
    response_format=MyBaseModelSubclass,
    reasoning_effort="low",
    extra_body=EXTRA_BODY,
)
result = response.choices[0].message.content
result_as_object = MyBaseModelSubclass.model_validate_json(result)
```
