"""Pydantic models for the Marketing Agent."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# --- Enums ---

class PsychTriggerType(str, Enum):
    """Psychological trigger types for content angles."""
    ZEIGARNIK = "zeigarnik"          # Open loops
    FOMO = "fomo"                    # Fear of missing out
    CURIOSITY_GAP = "curiosity_gap"  # Information asymmetry
    SOCIAL_PROOF = "social_proof"    # Authority / bandwagon
    GAIN = "gain"                    # Promise of benefit
    LOSS_AVERSION = "loss_aversion"  # Fear of loss


class TrendSource(str, Enum):
    """Source of a trending topic."""
    TWITTER_KSA = "twitter_ksa"
    GOOGLE_TRENDS = "google_trends"
    GULF_NEWS = "gulf_news"
    CULTURAL = "cultural"
    TARGETED = "targeted"
    YOUTUBE = "youtube"


class AIProvider(str, Enum):
    """Available AI providers."""
    GEMINI = "gemini"
    CLAUDE = "claude"
    LM_STUDIO = "lmstudio"


class Platform(str, Enum):
    """Target content platform."""
    TWITTER = "twitter"
    INSTAGRAM = "instagram"
    LINKEDIN = "linkedin"
    TIKTOK = "tiktok"
    GENERAL = "general"


# --- Core Models ---

class BrandProfile(BaseModel):
    """Brand strategy profile extracted from uploaded documents."""
    name: str = ""
    industry: str = ""
    tone_of_voice: str = ""
    target_audience: str = ""
    key_messages: list[str] = Field(default_factory=list)
    values: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    summary: str = ""
    doc_ids: list[str] = Field(default_factory=list)


class SourceEntry(BaseModel):
    """A single source entry from a CSV file."""
    vertical: str = ""
    type: str = ""  # twitter, domain, instagram, etc.
    handle_or_domain: str
    label: str = ""
    youtube_handle: str = ""


class Trend(BaseModel):
    """A trending topic discovered by the scanner."""
    title: str
    description: str = ""
    source: TrendSource
    jack_potential: float = Field(default=0.0, ge=0.0, le=1.0)
    url: str = ""
    published_at: Optional[datetime] = None  # When the original content was published
    source_name: str = ""                    # Human-readable origin (channel, domain, etc.)
    region: str = "KSA"
    vertical: str = ""
    discovered_at: datetime = Field(default_factory=datetime.now)
    raw_data: dict = Field(default_factory=dict)


class PsychTrigger(BaseModel):
    """A psychological trigger applied to content."""
    type: PsychTriggerType
    hook: str            # The actual hook text
    rationale: str = ""  # Why this trigger works here


class ContentAngle(BaseModel):
    """A content angle generated from a trend + brand + psych trigger."""
    headline: str
    hook: str
    body_outline: str = ""
    platform: Platform = Platform.GENERAL
    psych_triggers: list[PsychTrigger] = Field(default_factory=list)
    brand_alignment_score: float = Field(default=0.0, ge=0.0, le=1.0)
    trend_title: str = ""
    trend_source: TrendSource = TrendSource.GOOGLE_TRENDS


class TrendWithAngles(BaseModel):
    """A trend bundled with its generated content angles."""
    trend: Trend
    angles: list[ContentAngle] = Field(default_factory=list)


class AgentOutput(BaseModel):
    """Full output from one agent run."""
    timestamp: datetime = Field(default_factory=datetime.now)
    brand_name: str = ""
    provider_used: AIProvider = AIProvider.GEMINI
    trend_count: int = 0
    angle_count: int = 0
    results: list[TrendWithAngles] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


# --- API Models ---

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "0.1.0"
    provider: str = ""
    timestamp: datetime = Field(default_factory=datetime.now)


class GenerateRequest(BaseModel):
    """Request to generate content angles."""
    provider: Optional[AIProvider] = None
    mock: bool = False
    max_trends: int = 8
    angles_per_trend: int = 3
    platforms: list[Platform] = Field(default_factory=lambda: [Platform.GENERAL])


class BrandUploadResponse(BaseModel):
    """Response after uploading a brand document."""
    filename: str
    pages_processed: int = 0
    chunks_stored: int = 0
    brand_profile: Optional[BrandProfile] = None
