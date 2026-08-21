"""Reliable free-model router for Teacher Bot scene generation.

Uses the current OpenCode Zen free chat-completions endpoint first, then
OpenRouter's dynamic free-model router. Secrets are read only from env vars.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request

OPENCODE_BASE = "https://opencode.ai/zen/v1/chat/completions"
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"

# Current OpenCode Zen free models. Keep several fallbacks because free
# endpoints can be temporarily rate-limited or rotated.
OPENCODE_FREE_MODELS = [
    "hy3-free",
    "deepseek-v4-flash-free",
    "mimo-v2.5-free",
    "laguna-s-2.1-free",
    "nemotron-3.5-lightning-free",
]


def _extract_json(raw: str) -> dict:
    raw = (raw or "").strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```[a-zA-Z0-9_-]*\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw.strip())
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Some models add a short preamble. Recover the outer JSON object.
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            return json.loads(raw[start:end + 1])
        raise


def _request(url: str, model: str, key: str, messages: list[dict], headers: dict) -> dict:
    body = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": int(os.environ.get("LLM_MAX_TOKENS", "5200")),
        "temperature": 0.2,
    }).encode("utf-8")
    req_headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
        "User-Agent": "TeacherBotYT/3.0",
        **headers,
    }
    req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
    content = data["choices"][0]["message"].get("content")
    if isinstance(content, list):
        content = "".join(str(x.get("text", "")) if isinstance(x, dict) else str(x) for x in content)
    return _extract_json(str(content or ""))


def call_llm(prompt: str, api_key: str = "") -> dict:
    """Try current free routes in order; fail only after all candidates fail."""
    system = os.environ.get("LLM_SYSTEM_PROMPT", "")
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    failures = []
    opencode_key = os.environ.get("OPENCODE_API_KEY", "") or api_key
    if opencode_key:
        preferred = os.environ.get("OPENCODE_MODEL_NAME", "hy3-free")
        models = [preferred] + [m for m in OPENCODE_FREE_MODELS if m != preferred]
        for model in models:
            try:
                result = _request(OPENCODE_BASE, model, opencode_key, messages, {"Origin": "https://opencode.ai"})
                print(f"  ✅ LLM: OpenCode Zen / {model}")
                return result
            except Exception as exc:
                failures.append(f"OpenCode/{model}: {exc}")
                print(f"  ⚠ OpenCode/{model} failed: {exc}")
                time.sleep(0.4)

    openrouter_key = os.environ.get("OPENROUTER_API_KEY", "")
    if openrouter_key:
        # openrouter/free automatically selects a currently available free model.
        try:
            result = _request(
                OPENROUTER_BASE,
                os.environ.get("OPENROUTER_MODEL", "openrouter/free"),
                openrouter_key,
                messages,
                {
                    "HTTP-Referer": "https://github.com/shairo009/teacher-bot-yt",
                    "X-Title": "TeacherBotYT",
                },
            )
            print("  ✅ LLM: OpenRouter / openrouter/free")
            return result
        except Exception as exc:
            failures.append(f"OpenRouter: {exc}")
            print(f"  ⚠ OpenRouter/free failed: {exc}")

    raise RuntimeError("All free LLM routes failed: " + " | ".join(failures[-8:]))
