"""Configuration for the Marketing Agent."""

import os
from pathlib import Path

from pydantic_settings import BaseSettings


def _find_env_file() -> str | None:
    """Find a readable .env file, handling macOS permission issues."""
    candidates = [
        Path("/tmp/.marketing-agent.env"),
        Path(".env"),
        Path(os.path.expanduser("~/.marketing-agent.env")),
    ]
    for p in candidates:
        try:
            if p.is_file():
                return str(p)
        except PermissionError:
            continue
    return None


_env_file = _find_env_file()


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""

    # AI Providers
    google_api_key: str = ""
    anthropic_api_key: str = ""
    lm_studio_base_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "default"

    # Search APIs
    tavily_api_key: str = ""

    # Agent
    agent_timezone: str = "Africa/Cairo"
    agent_schedule_hour: int = 18
    agent_schedule_minute: int = 0

    # Storage
    chromadb_path: str = "/tmp/marketing-agent-data/chromadb"
    brand_docs_path: str = "/tmp/marketing-agent-data/docs"

    # AI Provider Selection: "gemini", "claude", "lmstudio"
    default_ai_provider: str = "gemini"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Telegram
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Reports
    reports_path: str = "./reports"

    # Sources
    default_sources: str = "saudi_general"

    # Azure Speech (TTS voiceover — replaces ElevenLabs)
    azure_speech_key: str = ""
    azure_speech_region: str = "eastus"
    azure_voice_name: str = "ar-SA-HamedNeural"  # Saudi Arabic male; alt: ar-SA-ZariyahNeural

    # Notion Integration
    notion_api_key: str = ""
    notion_parent_page_id: str = ""
    notion_database_id: str = ""

    # Google Trends (disabled — pytrends returns 404 on SA endpoint as of March 2026)
    google_trends_enabled: bool = False

    # YouTube
    youtube_scan_enabled: bool = True
    youtube_max_per_channel: int = 2
    youtube_sources: str = "youtube_channels"
    youtube_data_api_key: str = ""  # Falls back to google_api_key if empty

    model_config = {
        "env_file": _env_file or "",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
