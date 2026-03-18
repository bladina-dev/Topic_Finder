"""Azure Cognitive Services TTS voiceover — Arabic speech generation via REST API."""

from __future__ import annotations

import logging
from pathlib import Path

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential
from rich.console import Console

from .config import settings

logger = logging.getLogger(__name__)
console = Console()

_AZURE_TTS_URL = "https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
_SSML_TEMPLATE = (
    "<speak version='1.0' xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='ar-SA'>"
    "<voice name='{voice}'>{text}</voice>"
    "</speak>"
)


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


@retry(
    wait=wait_exponential(multiplier=1, min=2, max=30),
    stop=stop_after_attempt(3),
    reraise=True,
)
async def _call_azure_tts(script: str, output_path: Path) -> None:
    """Call Azure TTS REST API with retry. Raises on failure after 3 attempts."""
    url = _AZURE_TTS_URL.format(region=settings.azure_speech_region)
    ssml = _SSML_TEMPLATE.format(voice=settings.azure_voice_name, text=script)
    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_speech_key,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
    }
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, content=ssml.encode("utf-8"))
        response.raise_for_status()
        output_path.write_bytes(response.content)


async def generate_voiceover(
    video_data: dict,
    output_dir: Path = Path("output/voiceovers"),
    mock: bool = False,
) -> Path | None:
    """Generate an MP3 voiceover from VideoData using Azure TTS and save to output_dir.

    Returns Path to saved file, or None if Azure is not configured.
    """
    scenes = video_data.get("scenes", [])
    logger.debug("Extracting script from %d scenes", len(scenes))
    script = _extract_script_from_video_data(video_data)
    video_id = video_data.get("id", "fahad-video")

    output_dir.mkdir(parents=True, exist_ok=True)

    if mock:
        output_path = output_dir / f"{video_id}.txt"
        output_path.write_text(script, encoding="utf-8")
        logger.info("Voiceover saved (mock): %s", output_path)
        console.print(f"[bold green]✅ Voiceover saved (mock):[/bold green] {output_path}")
        return output_path

    if not settings.azure_speech_key:
        logger.warning("AZURE_SPEECH_KEY not set — skipping voiceover")
        console.print("[yellow]⚠️ AZURE_SPEECH_KEY not set — skipping voiceover[/yellow]")
        return None

    output_path = output_dir / f"{video_id}.mp3"
    console.print(f"[cyan]🎤 Generating Arabic voiceover ({len(script)} chars) via Azure...[/cyan]")

    try:
        await _call_azure_tts(script, output_path)
        logger.info("Voiceover saved: %s", output_path)
        console.print(f"[bold green]✅ Voiceover saved:[/bold green] {output_path}")
        return output_path
    except Exception as e:
        logger.error("Azure TTS failed after retries: %s", e)
        console.print(f"[red]❌ Voiceover failed: {e}[/red]")
        return None
