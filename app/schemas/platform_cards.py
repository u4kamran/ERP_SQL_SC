"""Shared platform card schema for marketing UIs."""

from __future__ import annotations

from pydantic import BaseModel


class PlatformCard(BaseModel):
    platform: str
    icon: str
    color: str
    label: str
    url: str
    action: str = "open"
    confidence: str = ""
    description: str = ""
