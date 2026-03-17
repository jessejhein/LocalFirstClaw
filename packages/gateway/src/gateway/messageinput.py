#!/usr/bin/env python3
"""Input model for inbound gateway messages."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class MessageInput(BaseModel):
    """Inbound message payload for the FastAPI surface."""

    model_config = ConfigDict(extra="forbid")

    endpoint_id: str
    user_id: str
    text: str
    timestamp: datetime
