"""Influencer Signal Scanner — discovers trends via domain + YouTube channel signals."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlparse

from .config import settings
from .models import Trend, TrendSource, TopicOrigin
from .source_manager import get_domains_for_scan
from .trend_scanner import _normalize_title, _parse_date
from .yt_scanner import scan_youtube_sources


async def scan_influencer_domains(
    source_names: list[str],
    max_results: int = 10,
) -> list[Trend]:
    """Scan influencer/brand domains via Tavily with query 'latest news this week'.

    Args:
        source_names: CSV source file names to pull domains from.
        max_results: Maximum trends to return.

    Returns:
        Trend objects tagged as INFLUENCER origin.
    """
    if not settings.tavily_api_key:
        return []

    from tavily import AsyncTavilyClient

    domains = get_domains_for_scan(source_names)
    if not domains:
        return []

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)
    trends: list[Trend] = []
    seen: set[str] = set()

    batch_size = 10
    for i in range(0, len(domains), batch_size):
        if len(trends) >= max_results:
            break
        batch = domains[i : i + batch_size]
        try:
            print(f"[InfluencerScanner] Scanning {len(batch)} domains: {batch[:3]}...")
            result = await client.search(
                query="latest news this week",
                max_results=5,
                search_depth="basic",
                include_domains=batch,
            )
            for item in result.get("results", []):
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
                        source=TrendSource.INFLUENCER,
                        origin=TopicOrigin.INFLUENCER,
                        url=item_url,
                        published_at=pub_date,
                        source_name=domain,
                        jack_potential=0.75,
                        discovered_at=datetime.now(),
                    ))
        except Exception as e:
            print(f"[InfluencerScanner] Domain batch failed: {e}")

    return trends[:max_results]


async def scan_influencer_youtube(
    source_names: list[str],
    max_per_channel: int = 2,
) -> list[Trend]:
    """Scan YouTube channels from sources, tagging results as INFLUENCER origin.

    Args:
        source_names: CSV source file names to pull YouTube handles from.
        max_per_channel: Max videos per channel.

    Returns:
        Trend objects tagged as INFLUENCER origin.
    """
    results = await scan_youtube_sources(source_names, max_per_channel=max_per_channel)

    for trend in results:
        trend.origin = TopicOrigin.INFLUENCER
        trend.source = TrendSource.INFLUENCER

    return results
