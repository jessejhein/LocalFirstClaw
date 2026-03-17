#!/usr/bin/env python3
"""FastAPI application factory for the gateway package."""

from dataclasses import dataclass

from fastapi import FastAPI, HTTPException

from gateway.gatewayrouter import GatewayRouter
from gateway.messageinput import MessageInput


@dataclass(frozen=True)
class GatewayAppDependencies:
    """Dependencies required to construct the gateway FastAPI app."""

    router: GatewayRouter


def create_app(*, dependencies: GatewayAppDependencies) -> FastAPI:
    """
    Build the minimal FastAPI shell around the gateway routing core.

    Args:
        dependencies: Runtime objects used by the app.

    Returns:
        A configured FastAPI application.
    """
    app = FastAPI(title="LocalFirstClaw Gateway")

    @app.post("/messages")
    def post_message(message: MessageInput) -> dict[str, str | None]:
        """Route one inbound message through the gateway core."""
        result = dependencies.router.handle_message(
            endpoint_id=message.endpoint_id,
            text=message.text,
            user_id=message.user_id,
            timestamp=message.timestamp,
        )
        if result.kind == "command_error":
            raise HTTPException(status_code=400, detail=result.message)

        return result.to_dict()

    @app.get("/endpoints/{endpoint_id}")
    def get_endpoint(endpoint_id: str) -> dict[str, str | bool]:
        """Return current routing state for one endpoint."""
        status = dependencies.router.get_endpoint_status(endpoint_id=endpoint_id)
        return {
            "endpoint_id": status.endpoint_id,
            "transport": status.transport,
            "binding": status.binding,
            "primary_channel_id": status.primary_channel_id,
            "active_channel_id": status.active_channel_id,
            "default_agent_id": status.default_agent_id,
            "allow_channel_switching": status.allow_channel_switching,
        }

    return app
