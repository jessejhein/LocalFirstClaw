#!/usr/bin/env python3
"""Protocol for pluggable model execution clients."""

from typing import Protocol

from agentinterface.agentmessage import AgentMessage
from agentinterface.modelresult import ModelResult


class ModelClient(Protocol):
    """Structural protocol implemented by model execution backends."""

    def complete(self, *, model: str, messages: list[AgentMessage]) -> ModelResult:
        """
        Execute a model completion call for the provided messages.

        Args:
            model: Provider-qualified model name.
            messages: Prepared message list in execution order.

        Returns:
            Structured model result.
        """
