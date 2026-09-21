"""OPTIONAL external-AI enhancement layer.

Nothing in the product depends on this. When no API key is configured (the
default), `enhance()` returns None immediately and the deterministic engine
result is used unchanged. When a key IS configured, the model is asked only
to write a reviewer-facing narrative over findings the deterministic engine
has already computed - it never invents the score, the level, or the factors.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import List, Optional

import httpx

from app.core.config import settings
from app.risk.types import FactorResult

logger = logging.getLogger("mplad.risk.ai")

SYSTEM_PROMPT = (
    "You are assisting a government auditor reviewing MPLAD (Members of Parliament "
    "Local Area Development) works. You will be given deterministic findings that "
    "have ALREADY been computed from the project record. Write a short, factual "
    "briefing (maximum 140 words) for the reviewing officer. Rules: do not invent "
    "numbers, do not change the risk level, do not assert fraud - these are "
    "indicators flagged for investigation, not findings of wrongdoing. Plain "
    "administrative English."
)


@dataclass
class AiEnhancement:
    narrative: str
    model: str


def is_available() -> bool:
    return settings.ai_configured


def _build_user_prompt(project_title: str, risk_level: str, score: float, factors: List[FactorResult]) -> str:
    lines = [
        f"Work: {project_title}",
        f"Computed risk level: {risk_level} (score {score:.1f}/100)",
        "Deterministic findings:",
    ]
    for f in factors[:8]:
        lines.append(f"- [{f.category.value}] {f.title}. {f.detected_indicator} {f.evidence}")
    lines.append("Write the reviewing officer's briefing.")
    return "\n".join(lines)


def _call_anthropic(prompt: str) -> Optional[str]:  # pragma: no cover - network
    response = httpx.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": settings.ai_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": settings.ai_model,
            "max_tokens": 400,
            "system": SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    parts = [block.get("text", "") for block in data.get("content", []) if block.get("type") == "text"]
    return "\n".join(p for p in parts if p).strip() or None


def _call_openai(prompt: str) -> Optional[str]:  # pragma: no cover - network
    response = httpx.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {settings.ai_api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": settings.ai_model,
            "max_tokens": 400,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        },
        timeout=settings.ai_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    return (data["choices"][0]["message"]["content"] or "").strip() or None


def enhance(
    project_title: str, risk_level: str, score: float, factors: List[FactorResult]
) -> Optional[AiEnhancement]:
    """Returns None whenever external AI is unavailable or fails."""
    if not is_available():
        return None
    prompt = _build_user_prompt(project_title, risk_level, score, factors)
    try:
        if settings.ai_provider == "openai":
            text = _call_openai(prompt)
        else:
            text = _call_anthropic(prompt)
    except Exception as exc:  # network, auth, rate-limit, malformed response
        logger.warning("External AI enhancement unavailable, using deterministic result only: %s", exc)
        return None
    if not text:
        return None
    return AiEnhancement(narrative=text, model=settings.ai_model)


def describe() -> dict:
    return {
        "enabled": settings.ai_enhancement_enabled,
        "configured": settings.ai_configured,
        "provider": settings.ai_provider if settings.ai_configured else None,
        "model": settings.ai_model if settings.ai_configured else None,
    }


__all__ = ["enhance", "is_available", "describe", "AiEnhancement", "json"]
