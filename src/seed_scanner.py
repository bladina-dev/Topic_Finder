"""Seed Keyword Scanner — enriches topic discovery via brand pillar keywords."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from .config import settings
from .models import Trend, TrendSource, TopicOrigin
from .source_manager import load_seed_keywords
from .trend_scanner import _normalize_title, _parse_date


async def scan_seed_keywords(
    source_name: str = "seed_keywords",
    max_results: int = 6,
) -> list[Trend]:
    """Search Tavily for each seed keyword and return matching trends.

    Args:
        source_name: CSV file name (without extension) to load keywords from.
        max_results: Stop after this many trends total.

    Returns:
        Trend objects tagged as SEED_KEYWORD origin.
    """
    if not settings.tavily_api_key:
        return []

    from tavily import AsyncTavilyClient

    keywords = load_seed_keywords(source_name)
    if not keywords:
        return []

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    trends: list[Trend] = []
    seen: set[str] = set()

    for kw in keywords:
        if len(trends) >= max_results:
            break

        keyword = kw["keyword"]
        query = f"latest {keyword} 2026"

        try:
            print(f"[SeedScanner] Searching: '{query}'")
            result = await client.search(
                query=query,
                max_results=3,
                search_depth="basic",
            )
            for item in result.get("results", []):
                if len(trends) >= max_results:
                    break
                title = item.get("title", "").strip()
                normalized = _normalize_title(title)
                if normalized and normalized not in seen:
                    seen.add(normalized)
                    item_url = item.get("url", "")
                    domain = urlparse(item_url).netloc.replace("www.", "") if item_url else ""
                    pub_date = _parse_date(item.get("published_date", ""))

                    trends.append(Trend(
                        title=title,
                        description=item.get("content", "")[:300],
                        source=TrendSource.SEED_KEYWORD,
                        origin=TopicOrigin.SEED_KEYWORD,
                        url=item_url,
                        published_at=pub_date,
                        source_name=domain,
                        jack_potential=0.7,
                        vertical=kw.get("vertical", ""),
                        discovered_at=datetime.now(),
                    ))
        except Exception as e:
            print(f"[SeedScanner] Query '{query}' failed: {e}")

    return trends
