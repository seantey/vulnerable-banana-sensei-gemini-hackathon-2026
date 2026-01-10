"""Story card models for vulnerability narratives."""

from typing import Literal

from pydantic import BaseModel, Field

from vulnerable_banana.models.base import ApiModel
from vulnerable_banana.models.vulnerabilities import Severity

StoryType = Literal["ACTIVE", "HISTORICAL_YOURS", "HISTORICAL_GENERAL"]


class StoryCardContent(BaseModel):
    """Quick research output for story cards.

    This is the internal model used during generation, not exposed to API.
    """

    title: str  # e.g., "The Shai-Hulud Saga"
    what_happened: list[str]  # 3-5 bullet points
    why_should_i_care: list[str]  # 2-3 bullet points
    what_should_i_do: list[str]  # 2-3 actionable items
    incident_date: str | None = None  # e.g., "2025-09"


class HistoricalIncident(BaseModel):
    """A historical security incident for a package.

    Used to check if clean packages have interesting stories worth telling.
    """

    has_incident: bool  # True if there's a notable historical incident
    package_name: str
    title: str | None = None  # Only if has_incident is True
    severity: str | None = None  # CRITICAL, HIGH, MEDIUM, LOW, INFO
    what_happened: list[str] = Field(default_factory=list)
    why_should_i_care: list[str] = Field(default_factory=list)
    what_should_i_do: list[str] = Field(default_factory=list)
    incident_date: str | None = None
    sources: list[str] = Field(default_factory=list)


class StoryCard(ApiModel):
    """A story card for a security incident.

    Combines vulnerability data with LLM-generated educational content.
    """

    id: str  # Unique identifier for the story
    title: str  # Catchy title like "The Shai-Hulud Saga"
    package_name: str
    package_version: str
    story_type: StoryType
    severity: Severity | None = None

    # Educational content from quick research
    what_happened: list[str]
    why_should_i_care: list[str]
    what_should_i_do: list[str]

    # Metadata
    incident_date: str | None = None
    sources: list[str] = Field(default_factory=list)
