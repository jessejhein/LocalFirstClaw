#!/usr/bin/env python3
"""Return model for pluggable model client calls."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelResult:
    """Structured result returned by a model client."""

    output_text: str
    model_name: str
    finish_reason: str | None = None
