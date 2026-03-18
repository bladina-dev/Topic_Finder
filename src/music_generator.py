"""MiniMax Audio — AI background music generation via REST API.

No MiniMax key? Returns None cleanly. video_assembler handles None music_path
by assembling video without background music.
"""

from __future__ import annotations

import base64
import logging
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console

from .config import settings

logger = logging.getLogger(__name__)
console = Console()

_MINIMAX_URL = "https://api.minimax.chat/v1/music_generation"


def _generate_music_prompt(video_data: dict) -> str:
    """Build a MiniMax music generation prompt from VideoData."""
    title = video_data.get("title", "")
    pillar = video_data.get("pillar", "career")
    topic = title[:60] if title else pillar
    return (
        f"Energetic upbeat background music for a 45-second Arabic YouTube Short "
        f"about {topic}. Modern, motivational, no vocals, suitable for {pillar} content."
    )


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _call_minimax(prompt: str, output_path: str) -> str:
    """Call MiniMax music API with retry. Raises on failure after 3 attempts."""
    headers = {
        "Authorization": f"Bearer {settings.minimax_api_key}",
        "Content-Type": "application/json",
    }
    payload = {"model": "music-01", "prompt": prompt, "refer_voice": None}

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(_MINIMAX_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    audio_bytes = base64.b64decode(data["audio_file"])
    Path(output_path).write_bytes(audio_bytes)
    return output_path


async def generate_bg_music(
    prompt: str,
    output_path: str,
    mock: bool = False,
) -> str | None:
    """Generate background music and save to output_path.

    Returns path to saved MP3, or None if MiniMax is not configured or fails.
    Caller (video_assembler) handles None by assembling video without music.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if mock:
        Path(output_path).write_bytes(b"\xff\xfb\x00\x00" * 16)
        logger.info("Music saved (mock): %s", output_path)
        console.print(f"[bold green]✅ Music saved (mock):[/bold green] {output_path}")
        return output_path

    if not getattr(settings, "minimax_api_key", ""):
        logger.warning("MINIMAX_API_KEY not set — skipping background music")
        console.print("[yellow]⚠️ MINIMAX_API_KEY not set — video will have no background music[/yellow]")
        return None

    console.print(f"[cyan]🎵 Generating background music ({len(prompt)} char prompt)...[/cyan]")
    try:
        result = await _call_minimax(prompt, output_path)
        logger.info("Music saved: %s", result)
        console.print(f"[bold green]✅ Music saved:[/bold green] {result}")
        return result
    except Exception as e:
        logger.error("MiniMax music generation failed after retries: %s", e)
        console.print(f"[red]❌ Music generation failed: {e} — continuing without music[/red]")
        return None
