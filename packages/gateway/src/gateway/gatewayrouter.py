#!/usr/bin/env python3
"""In-memory routing core for channels, endpoints, and gateway commands."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

from journal import Journal, JournalEvent, JournalLevel

from gateway.channelconfig import ChannelConfig
from gateway.endpointruntimestate import EndpointRuntimeState
from gateway.endpointstatus import EndpointStatus
from gateway.gatewayresult import GatewayResult
from gateway.interfaceendpointconfig import InterfaceEndpointConfig

LOGGER = logging.getLogger(Path(__file__).stem)


class GatewayRouter:
    """Route inbound endpoint traffic to channels or gateway commands."""

    def __init__(
        self,
        *,
        channels: dict[str, ChannelConfig],
        endpoints: dict[str, InterfaceEndpointConfig],
        journal: Journal,
    ):
        """
        Create a gateway router with in-memory endpoint state.

        Args:
            channels: Known internal channels keyed by channel id.
            endpoints: Known interface endpoints keyed by endpoint id.
            journal: Journal used for operational event logging.
        """
        self.channels = channels
        self.endpoints = endpoints
        self.journal = journal
        self.runtime_states = {
            endpoint_id: EndpointRuntimeState(active_channel_id=config.primary_channel_id)
            for endpoint_id, config in endpoints.items()
        }

    def get_endpoint_status(self, *, endpoint_id: str) -> EndpointStatus:
        """
        Return the current routing status for one endpoint.

        Args:
            endpoint_id: Configured endpoint identifier.

        Returns:
            Derived endpoint status including active and primary channels.
        """
        endpoint = self._get_endpoint_config(endpoint_id=endpoint_id)
        runtime_state = self.runtime_states[endpoint_id]
        channel = self._get_channel(channel_id=runtime_state.active_channel_id)

        return EndpointStatus(
            endpoint_id=endpoint.endpoint_id,
            transport=endpoint.transport,
            binding=endpoint.binding,
            primary_channel_id=endpoint.primary_channel_id,
            active_channel_id=runtime_state.active_channel_id,
            default_agent_id=channel.default_agent_id,
            allow_channel_switching=endpoint.allow_channel_switching,
        )

    def handle_message(
        self,
        *,
        endpoint_id: str,
        text: str,
        user_id: str,
        timestamp: datetime,
    ) -> GatewayResult:
        """
        Handle one inbound message from a configured endpoint.

        Args:
            endpoint_id: Source endpoint identifier.
            text: Raw inbound message content.
            user_id: Transport-local user identifier.
            timestamp: Time the message entered the gateway.

        Returns:
            Structured routing result describing what the gateway did.
        """
        logger = LOGGER.getChild("handle_message")
        cleaned_text = text.strip()
        status = self.get_endpoint_status(endpoint_id=endpoint_id)
        logger.info("Handling message for endpoint %s", endpoint_id)
        self._journal_event(
            timestamp=timestamp,
            event_type="gateway.message_received",
            level=JournalLevel.INFO,
            agent_id="gateway",
            message="Gateway received inbound message",
            tags=["gateway", "inbound"],
            payload={
                "endpoint_id": endpoint_id,
                "user_id": user_id,
                "text": cleaned_text,
                "active_channel_id": status.active_channel_id,
            },
        )

        if cleaned_text.startswith("!"):
            return self._handle_command(
                endpoint_id=endpoint_id,
                command_text=cleaned_text,
                user_id=user_id,
                timestamp=timestamp,
            )

        if cleaned_text.startswith("@") and " " not in cleaned_text:
            return self._handle_channel_switch(
                endpoint_id=endpoint_id,
                channel_token=cleaned_text,
                user_id=user_id,
                timestamp=timestamp,
            )

        return self._route_message(
            endpoint_id=endpoint_id,
            text=cleaned_text,
            user_id=user_id,
            timestamp=timestamp,
            target_channel_id=status.active_channel_id,
        )

    def _handle_command(
        self,
        *,
        endpoint_id: str,
        command_text: str,
        user_id: str,
        timestamp: datetime,
    ) -> GatewayResult:
        """
        Parse and execute one gateway command.

        Args:
            endpoint_id: Source endpoint identifier.
            command_text: Raw command text beginning with `!`.
            user_id: Transport-local user identifier.
            timestamp: Time the command entered the gateway.

        Returns:
            Structured command result or structured command error.
        """
        endpoint = self._get_endpoint_config(endpoint_id=endpoint_id)
        runtime_state = self.runtime_states[endpoint_id]
        parts = command_text.split()
        command_name = parts[0].lower()

        if command_name == "!reset-channel":
            runtime_state.active_channel_id = endpoint.primary_channel_id
            result = GatewayResult(
                kind="command_result",
                message="Endpoint channel reset to primary",
                endpoint_id=endpoint_id,
                primary_channel_id=endpoint.primary_channel_id,
                active_channel_id=runtime_state.active_channel_id,
                target_channel_id=runtime_state.active_channel_id,
                target_agent_id=self._get_channel(channel_id=runtime_state.active_channel_id).default_agent_id,
                command_name=command_name,
            )
            self._journal_command(
                timestamp=timestamp,
                endpoint_id=endpoint_id,
                user_id=user_id,
                command_text=command_text,
                result=result,
            )
            return result

        if command_name == "!who":
            status = self.get_endpoint_status(endpoint_id=endpoint_id)
            result = GatewayResult(
                kind="command_result",
                message="Endpoint routing status returned",
                endpoint_id=endpoint_id,
                primary_channel_id=status.primary_channel_id,
                active_channel_id=status.active_channel_id,
                target_channel_id=status.active_channel_id,
                target_agent_id=status.default_agent_id,
                command_name=command_name,
            )
            self._journal_command(
                timestamp=timestamp,
                endpoint_id=endpoint_id,
                user_id=user_id,
                command_text=command_text,
                result=result,
            )
            return result

        if command_name == "!send":
            if len(parts) < 3 or not parts[1].startswith("@"):
                return self._command_error(
                    endpoint_id=endpoint_id,
                    primary_channel_id=endpoint.primary_channel_id,
                    active_channel_id=runtime_state.active_channel_id,
                    command_name=command_name,
                    timestamp=timestamp,
                    user_id=user_id,
                    command_text=command_text,
                    error_message="!send requires @channel and message text",
                )

            target_channel_id = parts[1][1:]
            routed_text = command_text.split(None, 2)[2]
            result = self._route_message(
                endpoint_id=endpoint_id,
                text=routed_text,
                user_id=user_id,
                timestamp=timestamp,
                target_channel_id=target_channel_id,
                command_name=command_name,
            )
            self._journal_command(
                timestamp=timestamp,
                endpoint_id=endpoint_id,
                user_id=user_id,
                command_text=command_text,
                result=result,
            )
            return result

        if command_name == "!channels":
            result = GatewayResult(
                kind="command_result",
                message=", ".join(sorted(self.channels.keys())),
                endpoint_id=endpoint_id,
                primary_channel_id=endpoint.primary_channel_id,
                active_channel_id=runtime_state.active_channel_id,
                command_name=command_name,
            )
            self._journal_command(
                timestamp=timestamp,
                endpoint_id=endpoint_id,
                user_id=user_id,
                command_text=command_text,
                result=result,
            )
            return result

        if command_name in {"!status", "!ping", "!help", "!recent"}:
            result = GatewayResult(
                kind="command_result",
                message=f"{command_name[1:]} handled by gateway",
                endpoint_id=endpoint_id,
                primary_channel_id=endpoint.primary_channel_id,
                active_channel_id=runtime_state.active_channel_id,
                command_name=command_name,
            )
            self._journal_command(
                timestamp=timestamp,
                endpoint_id=endpoint_id,
                user_id=user_id,
                command_text=command_text,
                result=result,
            )
            return result

        return self._command_error(
            endpoint_id=endpoint_id,
            primary_channel_id=endpoint.primary_channel_id,
            active_channel_id=runtime_state.active_channel_id,
            command_name=command_name,
            timestamp=timestamp,
            user_id=user_id,
            command_text=command_text,
            error_message="Unknown gateway command",
        )

    def _handle_channel_switch(
        self,
        *,
        endpoint_id: str,
        channel_token: str,
        user_id: str,
        timestamp: datetime,
    ) -> GatewayResult:
        """
        Switch the active channel for one endpoint when allowed.

        Args:
            endpoint_id: Source endpoint identifier.
            channel_token: Bare `@channel` token from the inbound message.
            user_id: Transport-local user identifier.
            timestamp: Time the switch request entered the gateway.

        Returns:
            Structured routing result describing the new active channel or the rejection.
        """
        endpoint = self._get_endpoint_config(endpoint_id=endpoint_id)
        runtime_state = self.runtime_states[endpoint_id]
        target_channel_id = channel_token[1:]

        if not endpoint.allow_channel_switching:
            return self._command_error(
                endpoint_id=endpoint_id,
                primary_channel_id=endpoint.primary_channel_id,
                active_channel_id=runtime_state.active_channel_id,
                command_name="@switch",
                timestamp=timestamp,
                user_id=user_id,
                command_text=channel_token,
                error_message="Endpoint does not allow channel switching",
            )

        channel = self._get_channel(channel_id=target_channel_id)
        runtime_state.active_channel_id = channel.channel_id
        result = GatewayResult(
            kind="channel_switched",
            message=f"Endpoint active channel switched to {channel.channel_id}",
            endpoint_id=endpoint_id,
            primary_channel_id=endpoint.primary_channel_id,
            active_channel_id=runtime_state.active_channel_id,
            target_channel_id=channel.channel_id,
            target_agent_id=channel.default_agent_id,
        )
        self._journal_event(
            timestamp=timestamp,
            event_type="gateway.channel_switched",
            level=JournalLevel.INFO,
            agent_id="gateway",
            message="Gateway switched endpoint active channel",
            tags=["gateway", "routing"],
            payload={
                "endpoint_id": endpoint_id,
                "user_id": user_id,
                "target_channel_id": channel.channel_id,
                "primary_channel_id": endpoint.primary_channel_id,
            },
        )

        return result

    def _route_message(
        self,
        *,
        endpoint_id: str,
        text: str,
        user_id: str,
        timestamp: datetime,
        target_channel_id: str,
        command_name: str | None = None,
    ) -> GatewayResult:
        """
        Route one message to the target channel and attached agent.

        Args:
            endpoint_id: Source endpoint identifier.
            text: Message body after any gateway syntax is removed.
            user_id: Transport-local user identifier.
            timestamp: Time the message entered the gateway.
            target_channel_id: Channel chosen for routing.
            command_name: Optional gateway command that triggered the route.

        Returns:
            Structured routing result describing the destination channel and agent.
        """
        endpoint = self._get_endpoint_config(endpoint_id=endpoint_id)
        runtime_state = self.runtime_states[endpoint_id]
        channel = self._get_channel(channel_id=target_channel_id)
        result = GatewayResult(
            kind="message_routed",
            message="Message routed to channel",
            endpoint_id=endpoint_id,
            primary_channel_id=endpoint.primary_channel_id,
            active_channel_id=runtime_state.active_channel_id,
            target_channel_id=channel.channel_id,
            target_agent_id=channel.default_agent_id,
            command_name=command_name,
        )
        self._journal_event(
            timestamp=timestamp,
            event_type="gateway.message_routed",
            level=JournalLevel.INFO,
            agent_id=channel.default_agent_id,
            message="Gateway routed inbound message to channel",
            tags=["gateway", "routing"],
            payload={
                "endpoint_id": endpoint_id,
                "user_id": user_id,
                "target_channel_id": channel.channel_id,
                "target_agent_id": channel.default_agent_id,
                "text": text,
                "active_channel_id": runtime_state.active_channel_id,
            },
        )

        return result

    def _command_error(
        self,
        *,
        endpoint_id: str,
        primary_channel_id: str,
        active_channel_id: str,
        command_name: str,
        timestamp: datetime,
        user_id: str,
        command_text: str,
        error_message: str,
    ) -> GatewayResult:
        """
        Return and journal a structured command error.

        Args:
            endpoint_id: Source endpoint identifier.
            primary_channel_id: Configured primary channel for the endpoint.
            active_channel_id: Runtime active channel for the endpoint.
            command_name: Parsed gateway command name.
            timestamp: Time the rejected command entered the gateway.
            user_id: Transport-local user identifier.
            command_text: Original raw command text.
            error_message: Human-readable rejection reason.

        Returns:
            Structured command error result.
        """
        result = GatewayResult(
            kind="command_error",
            message=error_message,
            endpoint_id=endpoint_id,
            primary_channel_id=primary_channel_id,
            active_channel_id=active_channel_id,
            command_name=command_name,
        )
        self._journal_event(
            timestamp=timestamp,
            event_type="gateway.command_rejected",
            level=JournalLevel.WARNING,
            agent_id="gateway",
            message="Gateway rejected command",
            tags=["gateway", "command"],
            payload={
                "endpoint_id": endpoint_id,
                "user_id": user_id,
                "command_text": command_text,
                "error": error_message,
            },
        )

        return result

    def _journal_command(
        self,
        *,
        timestamp: datetime,
        endpoint_id: str,
        user_id: str,
        command_text: str,
        result: GatewayResult,
    ) -> None:
        """
        Write a journal event for a successfully executed command.

        Args:
            timestamp: Time the command completed.
            endpoint_id: Source endpoint identifier.
            user_id: Transport-local user identifier.
            command_text: Original raw command text.
            result: Structured result returned to the caller.
        """
        self._journal_event(
            timestamp=timestamp,
            event_type="gateway.command_executed",
            level=JournalLevel.INFO,
            agent_id="gateway",
            message="Gateway executed command",
            tags=["gateway", "command"],
            payload={
                "endpoint_id": endpoint_id,
                "user_id": user_id,
                "command_text": command_text,
                "result_kind": result.kind,
                "active_channel_id": result.active_channel_id,
                "target_channel_id": result.target_channel_id,
            },
        )

    def _journal_event(
        self,
        *,
        timestamp: datetime,
        event_type: str,
        level: JournalLevel,
        agent_id: str,
        message: str,
        tags: list[str],
        payload: dict[str, str | None],
    ) -> None:
        """
        Append one structured gateway event to the journal.

        Args:
            timestamp: Event timestamp.
            event_type: Gateway-specific event classifier.
            level: Operational event level.
            agent_id: Logical agent or component associated with the event.
            message: Human-readable event summary.
            tags: Filterable event tags.
            payload: Structured event details.
        """
        self.journal.append_event(
            event=JournalEvent(
                timestamp=timestamp,
                level=level,
                event_type=event_type,
                source="gateway",
                agent_id=agent_id,
                tags=tags,
                message=message,
                payload=payload,
            )
        )

    def _get_endpoint_config(self, *, endpoint_id: str) -> InterfaceEndpointConfig:
        """
        Return endpoint config or raise a clear error.

        Args:
            endpoint_id: Configured endpoint identifier.

        Returns:
            The matching endpoint configuration.

        Raises:
            ValueError: If the endpoint is unknown to the router.
        """
        if endpoint_id not in self.endpoints:
            raise ValueError(f"unknown endpoint: {endpoint_id}")

        return self.endpoints[endpoint_id]

    def _get_channel(self, *, channel_id: str) -> ChannelConfig:
        """
        Return channel config or raise a clear error.

        Args:
            channel_id: Known internal channel identifier.

        Returns:
            The matching channel configuration.

        Raises:
            ValueError: If the channel is unknown to the router.
        """
        if channel_id not in self.channels:
            raise ValueError(f"unknown channel: {channel_id}")

        return self.channels[channel_id]
