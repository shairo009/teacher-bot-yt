"""Reliable free-model router for Teacher Bot scene generation.

Prefers OpenRouter's dynamic free router when a key is configured, then falls
back to OpenCode's current free inference endpoint. Secrets stay in env vars.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
OPENCODE_BASE = "https://opencode.ai/inference/openai/v1/chat/completions"

# Current OpenCode free models supported by the OpenAI-compatible inference API.
OPENCODE_FREE_MODELS = [
    "mimo-v2.5-free",
    "hy3-free",
    "nemotron-3-super-free",
    "big-pickle",
]


def _extract_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
        raise


def _request(url: str, model: str, key: str, messages: list[dict], headers: dict | None = None) -> dict:
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "5200")),
        "temperature": 0.2,
    }).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "User-Agent": "TeacherBotYT/3.1",
    }
    if key:
        req_headers["Authorization"] = f"Bearer {key}"
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"].get("content")
    if isinstance(content, list):
        content = "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
    return _extract_json(str(content or ""))


def _try_openrouter(messages: list[dict], failures: list[str]) -> dict | None:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        return None
    model = os.environ.get("OPENROUTER_MODEL", "openrouter/free").strip() or "openrouter/free"
    try:
        result = _request(
            OPENROUTER_BASE,
            model,
            key,
            messages,
            {
                "HTTP-Referer": "https://github.com/shairo009/teacher-bot-yt",
                "X-Title": "TeacherBotYT",
            },
        )
        print(f"  ✅ LLM: OpenRouter / {model}")
        return result
    except Exception as exc:
        failures.append(f"OpenRouter/{model}: {exc}")
        print(f"  ⚠ OpenRouter/{model} failed: {exc}")
        return None


def _try_opencode(messages: list[dict], failures: list[str]) -> dict | None:
    # OpenCode's current inference endpoint allows free models without auth.
    configured_key = os.environ.get("OPENCODE_API_KEY", "").strip()
    preferred = os.environ.get("OPENCODE_MODEL_NAME", "mimo-v2.5-free").strip()
    models = [preferred] + [m for m in OPENCODE_FREE_MODELS if m != preferred]
    for model in models:
        try:
            result = _request(OPENCODE_BASE, model, configured_key, messages)
            print(f"  ✅ LLM: OpenCode inference / {model}")
            return result
        except Exception as exc:
            failures.append(f"OpenCode/{model}: {exc}")
            print(f"  ⚠ OpenCode/{model} failed: {exc}")
            time.sleep(0.25)
    return None


def call_llm(prompt: str, api_key: str = "") -> dict:
    """Try current free routes and fail only after every configured route fails."""
    system = os.environ.get("LLM_SYSTEM_PROMPT", "")
    messages: list[dict] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    failures: list[str] = []

    # OpenRouter is the primary route when its secret exists; unlike hard-coded
    # model IDs, openrouter/free dynamically selects an available free model.
    result = _try_openrouter(messages, failures)
    if result is not None:
        return result

    # OpenCode free inference is the no-key fallback. This avoids treating an
    # expired OpenCode Zen billing key as the only path to free generation.
    result = _try_opencode(messages, failures)
    if result is not None:
        return result

    raise RuntimeError("All free LLM routes failed: " + " | ".join(failures[-10:]))
