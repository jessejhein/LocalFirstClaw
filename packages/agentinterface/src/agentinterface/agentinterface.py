#!/usr/bin/env python3
"""Agent execution facade over a pluggable model client."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from journal import Journal, JournalEvent, JournalLevel

from agentinterface.agentconfig import AgentConfig
from agentinterface.agentmessage import AgentMessage
from agentinterface.agentrequest import AgentRequest
from agentinterface.agentresponse import AgentResponse
from agentinterface.agentrunerror import AgentRunError
from agentinterface.modelclient import ModelClient

LOGGER = logging.getLogger(Path(__file__).stem)


class AgentInterface:
    """Execute configured agents through a model client and journal the lifecycle."""

    def __init__(
        self,
        *,
        agents: dict[str, AgentConfig],
        model_client: ModelClient,
        journal: Journal,
    ):
        """
        Create an agent execution facade.

        Args:
            agents: Configured agents keyed by agent id.
            model_client: Backend used to execute model completions.
            journal: Journal used for run lifecycle events.
        """
        self.agents = agents
        self.model_client = model_client
        self.journal = journal

    def run(self, *, request: AgentRequest) -> AgentResponse:
        """
        Execute one configured agent run.

        Args:
            request: Structured execution request.

        Returns:
            Structured response from the agent execution.

        Raises:
            AgentRunError: If the agent is unknown or the model client fails.
        """
        logger = LOGGER.getChild("run")
        agent = self._get_agent(agent_id=request.agent_id)
        correlation_id = request.correlation_id or str(uuid.uuid4())
        prepared_messages = self._prepare_messages(agent=agent, request=request)
        self._journal_run_event(
            request=request,
            correlation_id=correlation_id,
            event_type="agentinterface.run_started",
            level=JournalLevel.INFO,
            message="Agent run started",
            payload={
                "channel_id": request.channel_id,
                "endpoint_id": request.endpoint_id,
                "user_id": request.user_id,
                "model": agent.model,
                "message_count": str(len(prepared_messages)),
            },
        )

        try:
            model_result = self.model_client.complete(model=agent.model, messages=prepared_messages)
        except Exception as error:
            logger.error("Agent run failed for %s: %s", request.agent_id, error)
            self._journal_run_event(
                request=request,
                correlation_id=correlation_id,
                event_type="agentinterface.run_failed",
                level=JournalLevel.ERROR,
                message="Agent run failed",
                payload={
                    "channel_id": request.channel_id,
                    "endpoint_id": request.endpoint_id,
                    "user_id": request.user_id,
                    "model": agent.model,
                    "error": str(error),
                },
            )
            raise AgentRunError(str(error)) from error

        response = AgentResponse(
            agent_id=agent.agent_id,
            channel_id=request.channel_id,
            correlation_id=correlation_id,
            output_text=model_result.output_text,
            model_name=model_result.model_name,
            finish_reason=model_result.finish_reason,
        )
        self._journal_run_event(
            request=request,
            correlation_id=correlation_id,
            event_type="agentinterface.run_completed",
            level=JournalLevel.INFO,
            message="Agent run completed",
            payload={
                "channel_id": request.channel_id,
                "endpoint_id": request.endpoint_id,
                "user_id": request.user_id,
                "model": response.model_name,
                "finish_reason": response.finish_reason,
            },
        )

        return response

    async def run_async(self, *, request: AgentRequest) -> AgentResponse:
        """
        Expose run through an async-compatible method.

        Args:
            request: Structured execution request.

        Returns:
            Structured response from the agent execution.
        """
        return self.run(request=request)

    def _get_agent(self, *, agent_id: str) -> AgentConfig:
        """
        Return a configured agent or raise an execution error.

        Args:
            agent_id: Configured agent identifier.

        Returns:
            The matching agent configuration.

        Raises:
            AgentRunError: If the agent id is unknown.
        """
        if agent_id not in self.agents:
            raise AgentRunError(f"unknown agent: {agent_id}")

        return self.agents[agent_id]

    def _prepare_messages(self, *, agent: AgentConfig, request: AgentRequest) -> list[AgentMessage]:
        """
        Build the final message list sent to the model client.

        Args:
            agent: Configured agent definition.
            request: Current execution request.

        Returns:
            Prepared message list with the system prompt prepended.
        """
        return [AgentMessage(role="system", content=agent.system_prompt), *request.messages]

    def _journal_run_event(
        self,
        *,
        request: AgentRequest,
        correlation_id: str,
        event_type: str,
        level: JournalLevel,
        message: str,
        payload: dict[str, str | None],
    ) -> None:
        """
        Append one structured agentinterface lifecycle event to the journal.

        Args:
            request: Current execution request.
            correlation_id: Correlation id shared across the run lifecycle.
            event_type: Agentinterface event classifier.
            level: Operational level for the event.
            message: Human-readable event summary.
            payload: Structured lifecycle details.
        """
        self.journal.append_event(
            event=JournalEvent(
                timestamp=request.timestamp,
                level=level,
                event_type=event_type,
                source="agentinterface",
                agent_id=request.agent_id,
                correlation_id=correlation_id,
                tags=["agentinterface", "llm"],
                message=message,
                payload=payload,
            )
        )
