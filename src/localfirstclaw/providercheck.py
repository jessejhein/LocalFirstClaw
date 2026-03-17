#!/usr/bin/env python3
"""Provider metadata checks that avoid completion-token spend."""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class ProviderCheckResult:
    """Outcome of a metadata-only provider connectivity check."""

    provider_name: str
    api_base: str
    ok: bool
    model_count: int
    error_message: str | None = None


def check_chutes_connectivity(
    *,
    api_key: str,
    api_base: str = "https://llm.chutes.ai/v1",
    urlopen: Callable[..., object] = urllib.request.urlopen,
) -> ProviderCheckResult:
    """
    Validate Chutes connectivity using the models endpoint instead of a completion call.

    Args:
        api_key: Bearer token used for Chutes authentication.
        api_base: OpenAI-compatible Chutes API base URL.
        urlopen: Injectable urllib opener used by tests.

    Returns:
        Structured provider check result with model count on success.
    """
    models_url = api_base.rstrip("/") + "/models"
    request = urllib.request.Request(
        models_url,
        headers={"Authorization": f"Bearer {api_key}"},
    )

    try:
        with urlopen(request, timeout=30) as response:
            document = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        return ProviderCheckResult(
            provider_name="chutes",
            api_base=api_base,
            ok=False,
            model_count=0,
            error_message=str(error),
        )

    models = document.get("data", [])
    if not isinstance(models, list):
        return ProviderCheckResult(
            provider_name="chutes",
            api_base=api_base,
            ok=False,
            model_count=0,
            error_message="provider response did not include a valid models list",
        )

    return ProviderCheckResult(
        provider_name="chutes",
        api_base=api_base,
        ok=True,
        model_count=len(models),
    )
