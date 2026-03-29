"""Tests for seed_scanner.py — Phase 5 coverage."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.models import TopicOrigin, TrendSource


FAKE_KEYWORDS = [
    {"vertical": "tech", "keyword": "AI in Saudi Arabia", "intent": "informational", "label": "Core content pillar"},
    {"vertical": "finance", "keyword": "Tadawul stocks analysis", "intent": "commercial", "label": "Finance pillar"},
]

FAKE_SEARCH_RESULT = {
    "results": [
        {"title": "AI boom in Riyadh", "content": "desc", "url": "https://arabnews.com/1"},
    ]
}


@pytest.mark.asyncio
async def test_scan_seed_keywords_all_origin_seed_keyword():
    """All returned trends must have origin=SEED_KEYWORD and source=SEED_KEYWORD."""
    mock_client = AsyncMock()
    mock_client.search.return_value = FAKE_SEARCH_RESULT

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    with (
        patch("src.seed_scanner.settings") as mock_settings,
        patch("src.seed_scanner.load_seed_keywords", return_value=FAKE_KEYWORDS),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.seed_scanner import scan_seed_keywords
        results = await scan_seed_keywords(max_results=10)

    assert len(results) > 0
    for trend in results:
        assert trend.origin == TopicOrigin.SEED_KEYWORD
        assert trend.source == TrendSource.SEED_KEYWORD


@pytest.mark.asyncio
async def test_scan_seed_keywords_query_format():
    """Each Tavily query must be 'latest {keyword} 2026'."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {"results": []}

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    with (
        patch("src.seed_scanner.settings") as mock_settings,
        patch("src.seed_scanner.load_seed_keywords", return_value=FAKE_KEYWORDS),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.seed_scanner import scan_seed_keywords
        await scan_seed_keywords(max_results=10)

    queries = [call.kwargs.get("query") or call.args[0] for call in mock_client.search.call_args_list]
    assert queries == [
        "latest AI in Saudi Arabia 2026",
        "latest Tadawul stocks analysis 2026",
    ]


@pytest.mark.asyncio
async def test_scan_seed_keywords_returns_empty_when_no_api_key():
    """Returns [] immediately when tavily_api_key is empty."""
    with patch("src.seed_scanner.settings") as mock_settings:
        mock_settings.tavily_api_key = ""
        from src.seed_scanner import scan_seed_keywords
        result = await scan_seed_keywords()

    assert result == []


@pytest.mark.asyncio
async def test_scan_seed_keywords_respects_max_results():
    """Should not return more trends than max_results."""
    mock_client = AsyncMock()
    mock_client.search.return_value = {
        "results": [
            {"title": f"Trend {i}", "content": "desc", "url": f"https://example.com/{i}"}
            for i in range(5)
        ]
    }

    mock_tavily_module = MagicMock()
    mock_tavily_module.AsyncTavilyClient.return_value = mock_client

    many_keywords = [
        {"vertical": "tech", "keyword": f"keyword {i}", "intent": "informational", "label": ""}
        for i in range(10)
    ]

    with (
        patch("src.seed_scanner.settings") as mock_settings,
        patch("src.seed_scanner.load_seed_keywords", return_value=many_keywords),
        patch.dict("sys.modules", {"tavily": mock_tavily_module}),
    ):
        mock_settings.tavily_api_key = "fake-key"
        from src.seed_scanner import scan_seed_keywords
        results = await scan_seed_keywords(max_results=3)

    assert len(results) <= 3
