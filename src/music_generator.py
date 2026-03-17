"""MiniMax Audio — AI background music generation via REST API."""

from __future__ import annotations

import base64
import os
from pathlib import Path

import httpx
from rich.console import Console

_MINIMAX_URL = "https://api.minimax.chat/v1/music_generation"
_DEFAULT_MUSIC_FILENAME = "EleEnergetic, Social Media Creator_pre_sp109_s50_sb75_v3.mp3"

console = Console()


def _generate_music_prompt(video_data: dict) -> str:
    """Build a MiniMax music generation prompt from VideoData."""
    title = video_data.get("title", "")
    pillar = video_data.get("pillar", "career")
    topic = title[:60] if title else pillar
    return (
        f"Energetic upbeat background music for a 45-second Arabic YouTube Short "
        f"about {topic}. Modern, motivational, no vocals, suitable for {pillar} content."
    )


async def generate_bg_music(
    prompt: str,
    output_path: str,
    mock: bool = False,
) -> str:
    """Generate background music and save to output_path.

    Args:
        prompt: Music generation prompt.
        output_path: Full path (including filename) to save the MP3.
        mock: If True, write a placeholder file without calling the API.

    Returns:
        Path to the saved audio file as a string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    if mock:
        # Write a silent placeholder so the path exists
        Path(output_path).write_bytes(b"\xff\xfb\x00\x00" * 16)  # minimal MP3-like header
        console.print(f"[bold green]✅ Music saved (mock):[/bold green] {output_path}")
        return output_path

    api_key = os.environ.get("MINIMAX_API_KEY", "")
    if not api_key:
        console.print("[yellow]⚠️ MINIMAX_API_KEY not set — using default background music[/yellow]")
        # Return path to the static default (may not exist locally; caller handles it)
        return _DEFAULT_MUSIC_FILENAME

    console.print(f"[cyan]🎵 Generating background music ({len(prompt)} char prompt)...[/cyan]")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "music-01",
        "prompt": prompt,
        "refer_voice": None,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(_MINIMAX_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    audio_b64: str = data["audio_file"]
    audio_bytes = base64.b64decode(audio_b64)
    Path(output_path).write_bytes(audio_bytes)

    console.print(f"[bold green]✅ Music saved:[/bold green] {output_path}")
    return output_path
