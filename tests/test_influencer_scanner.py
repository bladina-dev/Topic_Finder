"""Tests for influencer_scanner.py — Phase 4 coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import TopicOrigin, TrendSource


# ---------------------------------------------------------------------------
# scan_influencer_domains
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_influencer_domains_all_trends_have_influencer_origin():
    """All returned trends must have origin=INFLUENCER and source=INFLUENCER."""
    fake_results = {
        "results": [
            {"title": "Saudi tech news", "content": "desc", "url": "https://argaam.com/1"},
            {"title": "Gulf finance update", "content": "desc", "url": "https://argaam.com/2"},
        ]
    }

    mock_client = AsyncMock()
    mock_client.search.return_value = fake_results

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    with (
        patch("src.influencer_scanner.settings") as mock_settings,
        patch("src.influencer_scanner.get_domains_for_scan", return_value=["argaam.com", "magnitt.com"]),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.influencer_scanner import scan_influencer_domains
        results = await scan_influencer_domains(["saudi_general"], max_results=10)

    assert len(results) == 2
    for trend in results:
        assert trend.origin == TopicOrigin.INFLUENCER
        assert trend.source == TrendSource.INFLUENCER


@pytest.mark.asyncio
async def test_scan_influencer_domains_uses_correct_query():
    """Tavily must be called with query='latest news this week'."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {"results": []}

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    with (
        patch("src.influencer_scanner.settings") as mock_settings,
        patch("src.influencer_scanner.get_domains_for_scan", return_value=["argaam.com"]),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.influencer_scanner import scan_influencer_domains
        await scan_influencer_domains(["saudi_general"])

    call_kwargs = mock_client.search.call_args.kwargs
    assert call_kwargs["query"] == "latest news this week"
    assert call_kwargs["query"] != "trending topics"


@pytest.mark.asyncio
async def test_scan_influencer_domains_returns_empty_when_no_api_key():
    """Returns [] immediately when tavily_api_key is empty."""
    with patch("src.influencer_scanner.settings") as mock_settings:
        mock_settings.tavily_api_key = ""
        from src.influencer_scanner import scan_influencer_domains
        result = await scan_influencer_domains(["saudi_general"])

    assert result == []


@pytest.mark.asyncio
async def test_scan_influencer_domains_returns_empty_when_no_domains():
    """Returns [] when get_domains_for_scan returns no domains."""
    mock_tavily_module = MagicMock()

    with (
        patch("src.influencer_scanner.settings") as mock_settings,
        patch("src.influencer_scanner.get_domains_for_scan", return_value=[]),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.influencer_scanner import scan_influencer_domains
        result = await scan_influencer_domains(["empty_source"])

    assert result == []
    mock_tavily_module.AsyncTavilyClient.assert_not_called()


# ---------------------------------------------------------------------------
# scan_influencer_youtube
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_influencer_youtube_tags_origin_influencer():
    """All YouTube trends must be retagged with origin=INFLUENCER and source=INFLUENCER."""
    from src.models import Trend, TrendSource, TopicOrigin

    fake_yt_trends = [
        Trend(title="Trend A", source=TrendSource.YOUTUBE, origin=TopicOrigin.TREND),
        Trend(title="Trend B", source=TrendSource.YOUTUBE, origin=TopicOrigin.TREND),
    ]

    with patch("src.influencer_scanner.scan_youtube_sources", return_value=fake_yt_trends):
        from src.influencer_scanner import scan_influencer_youtube
        results = await scan_influencer_youtube(["youtube_channels"])

    assert len(results) == 2
    for trend in results:
        assert trend.origin == TopicOrigin.INFLUENCER
        assert trend.source == TrendSource.INFLUENCER
