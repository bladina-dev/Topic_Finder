"""Tests for src/music_generator.py."""

from __future__ import annotations

import asyncio

from src.music_generator import _generate_music_prompt, generate_bg_music

_VIDEO_DATA = {
    "id": "fahad-ep-test-ai",
    "title": "AI is changing Saudi jobs",
    "pillar": "ai",
    "scenes": [],
}


def test_generate_music_prompt_returns_string():
    prompt = _generate_music_prompt(_VIDEO_DATA)

    assert isinstance(prompt, str)
    assert len(prompt) > 0
    assert "AI is changing Saudi jobs" in prompt
    assert "ai" in prompt


def test_generate_bg_music_mock_returns_existing_file(tmp_path):
    output_path = str(tmp_path / "test_bg.mp3")

    result = asyncio.run(generate_bg_music("test prompt", output_path, mock=True))

    from pathlib import Path

    assert Path(result).is_file()
    assert Path(result).stat().st_size > 0
