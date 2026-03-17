"""Tests for src/video_converter.py — no LLM calls required."""

from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from src.models import ContentAngle, Trend, TrendSource
from src.video_converter import (
    _make_topic_slug,
    _mock_video_data,
    _parse_video_response,
    angle_to_video_data,
)


# ---------------------------------------------------------------------------
# _make_topic_slug
# ---------------------------------------------------------------------------


def test_make_topic_slug_arabic():
    assert _make_topic_slug("الذكاء الاصطناعي في المستقبل") == "ai"


def test_make_topic_slug_english():
    slug = _make_topic_slug("AI jobs Saudi")
    assert len(slug) > 0


def test_make_topic_slug_hello_world():
    assert _make_topic_slug("hello world") == "hello-world"


# ---------------------------------------------------------------------------
# _parse_video_response
# ---------------------------------------------------------------------------


def test_parse_video_response_clean_json():
    data = {"id": "test-id", "title": "Test", "pillar": "ai", "scenes": []}
    result = _parse_video_response(json.dumps(data))
    assert isinstance(result, dict)
    assert result["id"] == "test-id"
    assert result["title"] == "Test"
    assert result["pillar"] == "ai"
    assert "scenes" in result


def test_parse_video_response_fenced_json():
    data = {"id": "fahad-ep-test", "title": "Fenced", "pillar": "career", "scenes": []}
    fenced = f"```json\n{json.dumps(data)}\n```"
    result = _parse_video_response(fenced)
    assert isinstance(result, dict)
    assert result["id"] == "fahad-ep-test"
    assert "scenes" in result


def test_parse_video_response_invalid():
    with pytest.raises(ValueError):
        _parse_video_response("not json at all!!!")


# ---------------------------------------------------------------------------
# _mock_video_data
# ---------------------------------------------------------------------------


def test_mock_video_data():
    angle = ContentAngle(headline="Test headline", hook="Test hook")
    trend = Trend(title="AI testing", source=TrendSource.GOOGLE_TRENDS)
    result = _mock_video_data(angle, trend)

    assert "id" in result
    assert "title" in result
    assert "pillar" in result
    assert "scenes" in result

    scenes = result["scenes"]
    assert len(scenes) >= 3
    assert scenes[0]["type"] == "hook"
    assert scenes[-1]["type"] == "cta"


# ---------------------------------------------------------------------------
# angle_to_video_data
# ---------------------------------------------------------------------------


def test_angle_to_video_data():
    angle = ContentAngle(headline="Test headline", hook="Test hook")
    trend = Trend(title="AI testing", source=TrendSource.GOOGLE_TRENDS)

    # mock=True returns a dict without any LLM call
    result = asyncio.run(angle_to_video_data(angle, trend, mock=True))
    assert isinstance(result, dict)
    assert "scenes" in result

    # mock=False with patched generate_content
    valid_response = json.dumps(
        {
            "id": "fahad-ep-20260317-ai",
            "title": "Test Video",
            "pillar": "ai",
            "scenes": [{"type": "hook"}, {"type": "cta"}],
        }
    )
    mock_generate = AsyncMock(return_value=valid_response)
    with patch("src.ai_orchestrator.generate_content", mock_generate):
        result2 = asyncio.run(angle_to_video_data(angle, trend, mock=False))

    mock_generate.assert_called_once()
    assert "scenes" in result2
