"""Configurable, backend-only AI provider. Never fabricates output: raises AIUnavailable instead."""
import json
import re
from typing import Any, Dict
import httpx
from app.config import settings


class AIUnavailable(Exception):
    pass


def is_configured() -> bool:
    p = settings.ai_provider.lower()
    return (p == "gemini" and bool(settings.gemini_api_key)) or (p == "anthropic" and bool(settings.anthropic_api_key))


def _extract_json(text: str) -> Dict[str, Any]:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise AIUnavailable(f"Provider returned invalid JSON: {e}")


async def generate_json(system: str, prompt: str) -> Dict[str, Any]:
    if not is_configured():
        raise AIUnavailable("No AI provider configured (set AI_PROVIDER and API key).")
    p = settings.ai_provider.lower()
    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout_seconds) as client:
            if p == "gemini":
                r = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{settings.gemini_model}:generateContent",
                    headers={"x-goog-api-key": settings.gemini_api_key},
                    json={"systemInstruction": {"parts": [{"text": system}]},
                          "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                          "generationConfig": {"responseMimeType": "application/json", "temperature": 0.3}})
                r.raise_for_status()
                return _extract_json(r.json()["candidates"][0]["content"]["parts"][0]["text"])
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": settings.anthropic_api_key, "anthropic-version": "2023-06-01"},
                json={"model": settings.anthropic_model, "max_tokens": 8000, "temperature": 0.3,
                      "system": system, "messages": [{"role": "user", "content": prompt}]})
            r.raise_for_status()
            return _extract_json(r.json()["content"][0]["text"])
    except (httpx.HTTPError, KeyError, IndexError) as e:
        raise AIUnavailable(f"AI request failed: {type(e).__name__}")
