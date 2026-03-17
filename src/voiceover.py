"""ElevenLabs Arabic voiceover generation — uses REST API via httpx directly."""

from __future__ import annotations

import os
from pathlib import Path

import httpx
from rich.console import Console

DEFAULT_VOICE_ID = "pNInz6obpgDQGcFmaJgB"  # Adam — multilingual
_ELEVENLABS_TTS_URL = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

console = Console()


def _extract_script_from_video_data(video_data: dict) -> str:
    """Build a natural reading script from VideoData scenes.

    Skips the intro scene (always the same fixed host intro).
    Joins headline, body, and list items with periods.
    """
    parts = []
    for scene in video_data.get("scenes", []):
        if scene.get("type") == "intro":
            continue
        headline = scene.get("headline", "").replace("\n", " ").strip()
        body = scene.get("body", "").replace("\n", " ").strip()
        items: list[str] = scene.get("items", [])

        segment: list[str] = [p for p in [headline, body] if p]
        segment.extend(items)
        if segment:
            parts.append(". ".join(segment))

    return ". ".join(parts)


async def generate_voiceover(
    video_data: dict,
    voice_id: str = DEFAULT_VOICE_ID,
    output_dir: Path = Path("output/voiceovers"),
    mock: bool = False,
) -> Path:
    """Generate an MP3 voiceover from VideoData and save to output_dir.

    Args:
        video_data: VideoData dict (as produced by angle_to_video_data).
        voice_id: ElevenLabs voice ID.
        output_dir: Directory to save the output file.
        mock: If True, write a placeholder .txt file instead of calling the API.

    Returns:
        Path to the saved file.
    """
    scenes = video_data.get("scenes", [])
    console.print(f"[cyan]🎤 Extracting script from {len(scenes)} scenes...[/cyan]")

    script = _extract_script_from_video_data(video_data)
    video_id = video_data.get("id", "fahad-video")

    output_dir.mkdir(parents=True, exist_ok=True)

    if mock:
        output_path = output_dir / f"{video_id}.txt"
        output_path.write_text(script, encoding="utf-8")
        console.print(f"[bold green]✅ Voiceover saved:[/bold green] {output_path}")
        return output_path

    console.print(f"[cyan]🔊 Generating voiceover ({len(script)} chars)...[/cyan]")

    api_key = os.environ.get("ELEVENLABS_API_KEY", "")
    url = _ELEVENLABS_TTS_URL.format(voice_id=voice_id)
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75,
        },
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        audio_bytes = response.content

    output_path = output_dir / f"{video_id}.mp3"
    output_path.write_bytes(audio_bytes)
    console.print(f"[bold green]✅ Voiceover saved:[/bold green] {output_path}")

    return output_path
