"""FFmpeg-based video assembly — merges Remotion MP4 + voiceover + background music."""

from __future__ import annotations

import shutil
import subprocess

from rich.console import Console

console = Console()


def assemble_video(
    video_path: str,
    voiceover_path: str | None,
    music_path: str | None,
    output_path: str,
) -> str:
    """Merge video, voiceover, and background music into a final MP4.

    Args:
        video_path: Path to the Remotion-rendered MP4.
        voiceover_path: Path to the ElevenLabs voiceover MP3 (or None).
        music_path: Path to the background music MP3 (or None).
        output_path: Where to write the final MP4.

    Returns:
        output_path as a string.

    Raises:
        RuntimeError: If ffmpeg is not installed.
    """
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not found — install with: brew install ffmpeg")

    console.print("[cyan]🎬 Assembling final video...[/cyan]")

    if voiceover_path and music_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-i", music_path,
            "-filter_complex",
            "[1:a]volume=1.0[voice];[2:a]volume=0.15[music];[voice][music]amix=inputs=2:duration=first[aout]",
            "-map", "0:v",
            "-map", "[aout]",
            "-c:v", "copy",
            output_path,
        ]
    elif voiceover_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", voiceover_path,
            "-c:v", "copy",
            "-c:a", "aac",
            output_path,
        ]
    elif music_path:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-i", music_path,
            "-c:v", "copy",
            "-filter:a", "volume=0.15",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", video_path,
            "-c", "copy",
            output_path,
        ]

    subprocess.run(cmd, check=True)
    console.print(f"[bold green]✅ Final video:[/bold green] {output_path}")
    return output_path
