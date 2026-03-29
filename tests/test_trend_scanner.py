"""Tests for trend_scanner.py — Phase 3 coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import TopicOrigin, TrendSource


# ---------------------------------------------------------------------------
# Fix 1: verify the 5 new Tavily query strings
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_tavily_uses_five_diverse_queries():
    """scan_tavily should use the 5 topic-specific query strings."""
    expected_queries = [
        "Saudi Arabia business news today",
        "Saudi tech startups latest",
        "KSA economy finance update this week",
        "Riyadh entertainment events culture",
        "Saudi e-commerce digital marketing news",
    ]

    mock_client = AsyncMock()
    mock_client.search.return_value = {"results": []}

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    with (
        patch("src.trend_scanner.settings") as mock_settings,
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.trend_scanner import scan_tavily
        await scan_tavily(max_results=8)

    actual_queries = [call.kwargs.get("query") or call.args[0] for call in mock_client.search.call_args_list]
    assert actual_queries == expected_queries


# ---------------------------------------------------------------------------
# Fix 2: scan_serpapi_trends returns [] when no API key
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_scan_serpapi_trends_no_key_returns_empty():
    """scan_serpapi_trends should return [] immediately when serpapi_api_key is empty."""
    from src.trend_scanner import scan_serpapi_trends

    with patch("src.trend_scanner.settings") as mock_settings:
        mock_settings.serpapi_api_key = ""
        result = await scan_serpapi_trends()

    assert result == []


@pytest.mark.asyncio
async def test_scan_serpapi_trends_parses_results():
    """scan_serpapi_trends should return Trend objects tagged SERP_TRENDS / TREND."""
    fake_results = {
        "trending_searches": [
            {"query": "Vision 2030"},
            {"query": "Saudi AI"},
        ]
    }

    mock_search_instance = MagicMock()
    mock_search_instance.get_dict.return_value = fake_results

    mock_serpapi_module = MagicMock()
    mock_serpapi_module.GoogleSearch.return_value = mock_search_instance

    with (
        patch("src.trend_scanner.settings") as mock_settings,
        patch.dict("sys.modules", {"serpapi": mock_serpapi_module}),
    ):
        mock_settings.serpapi_api_key = "fake-serpapi-key"
        from src.trend_scanner import scan_serpapi_trends
        result = await scan_serpapi_trends(max_results=5)

    assert len(result) == 2
    for trend in result:
        assert trend.source == TrendSource.SERP_TRENDS
        assert trend.origin == TopicOrigin.TREND
