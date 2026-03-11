"""Trend Scanner — discovers trending topics from multiple sources."""

from __future__ import annotations

import json
from datetime import datetime

from .config import settings
from .models import Trend, TrendSource


# --- Mock Data for Testing ---

MOCK_TRENDS: list[dict] = [
    {
        "title": "Saudi Vision 2030 tech hub opens in Riyadh",
        "description": "New tech innovation center launches as part of Saudi Vision 2030, attracting global startups.",
        "source": TrendSource.GULF_NEWS,
        "jack_potential": 0.9,
        "url": "https://arabnews.com/vision-2030-tech",
    },
    {
        "title": "#SaudiTech trending on X/Twitter",
        "description": "Massive engagement around Saudi tech ecosystem and startup funding announcements.",
        "source": TrendSource.TWITTER_KSA,
        "jack_potential": 0.85,
    },
    {
        "title": "AI adoption in Gulf businesses surges 300%",
        "description": "New McKinsey report shows Gulf region leading in AI enterprise adoption.",
        "source": TrendSource.GOOGLE_TRENDS,
        "jack_potential": 0.92,
    },
    {
        "title": "Riyadh Season 2026 breaks attendance records",
        "description": "Cultural entertainment festival draws millions, boosting local economy.",
        "source": TrendSource.CULTURAL,
        "jack_potential": 0.78,
    },
    {
        "title": "E-commerce in KSA expected to hit $20B",
        "description": "Saudi e-commerce market continues rapid growth with mobile-first consumers.",
        "source": TrendSource.GULF_NEWS,
        "jack_potential": 0.88,
    },
    {
        "title": "Remote work policies reshape Gulf job market",
        "description": "Major Saudi companies announce permanent hybrid work models.",
        "source": TrendSource.GOOGLE_TRENDS,
        "jack_potential": 0.75,
    },
    {
        "title": "NEOM smart city phase 1 completion announced",
        "description": "First residential and commercial zone of NEOM opens for early residents.",
        "source": TrendSource.GULF_NEWS,
        "jack_potential": 0.95,
    },
    {
        "title": "Arabic content creators dominate social media",
        "description": "Arabic-language creators see 400% growth on TikTok and YouTube Shorts.",
        "source": TrendSource.TWITTER_KSA,
        "jack_potential": 0.82,
    },
]


async def scan_tavily(max_results: int = 8) -> list[Trend]:
    """Scan trending topics using Tavily search API.

    Searches for KSA/Gulf trending business and tech topics.
    """
    from tavily import AsyncTavilyClient

    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY not set in environment.")

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    queries = [
        "trending topics Saudi Arabia KSA today",
        "Gulf business news today",
        "Saudi Arabia X Twitter trending today",
    ]

    trends: list[Trend] = []
    seen_titles: set[str] = set()

    for query in queries:
        try:
            print(f"[TrendScanner] Tavily searching: '{query}'")
            result = await client.search(
                query=query,
                max_results=3,
                search_depth="basic",
            )
            for item in result.get("results", []):
                title = item.get("title", "").strip()
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    source = TrendSource.GULF_NEWS
                    if "twitter" in query.lower() or "x " in query.lower():
                        source = TrendSource.TWITTER_KSA

                    trends.append(Trend(
                        title=title,
                        description=item.get("content", "")[:300],
                        source=source,
                        url=item.get("url", ""),
                        jack_potential=0.7,  # Default; AI will re-score
                        discovered_at=datetime.now(),
                    ))
        except Exception as e:
            print(f"[TrendScanner] Tavily query '{query}' failed: {e}")

    return trends[:max_results]


async def scan_google_trends(max_results: int = 4) -> list[Trend]:
    """Scan Google Trends for Saudi Arabia trending searches."""
    from pytrends.request import TrendReq

    trends: list[Trend] = []
    try:
        pytrends = TrendReq(hl="ar", tz=180, timeout=(10, 25))
        trending = pytrends.trending_searches(pn="saudi_arabia")

        for i, row in trending.head(max_results).iterrows():
            title = str(row.iloc[0]).strip()
            if title:
                trends.append(Trend(
                    title=title,
                    description=f"Trending on Google in Saudi Arabia",
                    source=TrendSource.GOOGLE_TRENDS,
                    jack_potential=0.6,
                    region="KSA",
                    discovered_at=datetime.now(),
                ))
    except Exception as e:
        print(f"[TrendScanner] Google Trends failed: {e}")

    return trends


async def scan_trends(mock: bool = False, max_results: int = 8) -> list[Trend]:
    """Run all trend scanners and return combined, deduplicated results.

    Args:
        mock: If True, return mock data instead of real API calls.
        max_results: Maximum number of trends to return.

    Returns:
        List of Trend objects sorted by jack_potential (descending).
    """
    if mock:
        return [Trend(**t) for t in MOCK_TRENDS[:max_results]]

    all_trends: list[Trend] = []

    # Run scanners
    try:
        tavily_trends = await scan_tavily(max_results=max_results)
        all_trends.extend(tavily_trends)
    except Exception as e:
        print(f"[TrendScanner] Tavily scanner failed: {e}")

    try:
        google_trends = await scan_google_trends(max_results=4)
        all_trends.extend(google_trends)
    except Exception as e:
        print(f"[TrendScanner] Google Trends scanner failed: {e}")

    # Deduplicate by title similarity (simple)
    seen: set[str] = set()
    unique: list[Trend] = []
    for t in all_trends:
        key = t.title.lower().strip()[:50]
        if key not in seen:
            seen.add(key)
            unique.append(t)

    # Sort by jack_potential descending
    unique.sort(key=lambda x: x.jack_potential, reverse=True)

    return unique[:max_results]
