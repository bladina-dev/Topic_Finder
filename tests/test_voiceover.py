"""Tests for src/voiceover.py."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from src.voiceover import _extract_script_from_video_data, generate_voiceover

_VIDEO_DATA = {
    "id": "test-video",
    "scenes": [
        {"type": "hook", "headline": "هل الذكاء الاصطناعي\nبياخد شغلك؟"},
        {"type": "intro", "headline": "معكم فهد الحربي", "body": "خبير مهني — SamimlyCV"},
        {"type": "point", "headline": "الفكرة الرئيسية", "body": "تفاصيل مهمة جداً"},
        {"type": "list", "headline": "النقاط:", "items": ["نقطة ١", "نقطة ٢"]},
        {"type": "cta", "headline": "تابعني عشان تعرف أكثر", "body": "SamimlyCV"},
    ],
}


def test_extract_script_returns_arabic_text():
    script = _extract_script_from_video_data(_VIDEO_DATA)

    assert len(script) > 0
    assert "هل الذكاء الاصطناعي" in script
    assert "الفكرة الرئيسية" in script
    assert "نقطة ١" in script
    # intro scene must be skipped
    assert "معكم فهد الحربي" not in script


def test_generate_voiceover_saves_mp3(tmp_path):
    fake_audio = b"\xff\xfb\x90fake-mp3-content"

    mock_response = MagicMock()
    mock_response.content = fake_audio
    mock_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=mock_response)

    with patch.dict("os.environ", {"ELEVENLABS_API_KEY": "test-key-123"}):
        with patch("src.voiceover.httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=None)
            result = asyncio.run(generate_voiceover(_VIDEO_DATA, output_dir=tmp_path))

    assert result.is_file()
    assert result.read_bytes() == fake_audio
