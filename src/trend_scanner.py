"""Trend Scanner — discovers trending topics from multiple sources."""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from urllib.parse import urlparse

from .config import settings
from .models import Trend, TrendSource


def _parse_date(date_str: str) -> datetime | None:
    """Try to parse a date string from various formats (Tavily, RSS, etc.)."""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%a, %d %b %Y %H:%M:%S"]:
        try:
            return datetime.strptime(date_str[:len(fmt) + 5], fmt)
        except (ValueError, IndexError):
            continue
    # Try ISO format as fallback
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


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


# --- Normalization for smarter dedup ---

# Common Arabic/English stopwords to strip during dedup
_STOPWORDS = {
    "the", "a", "an", "in", "on", "at", "for", "to", "of", "and", "is", "are",
    "was", "were", "من", "في", "على", "إلى", "عن", "مع", "هذا", "هذه",
}

# Emoji pattern
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001f600-\U0001f64f"  # emoticons
    "\U0001f300-\U0001f5ff"  # symbols
    "\U0001f680-\U0001f6ff"  # transport
    "\U0001f1e0-\U0001f1ff"  # flags
    "\U00002702-\U000027b0"
    "\U000024c2-\U0001f251"
    "]+",
    flags=re.UNICODE,
)


def _normalize_title(title: str) -> str:
    """Normalize a title for deduplication.

    Strips emoji, lowercases, removes stopwords, collapses whitespace.
    """
    # Remove emoji
    cleaned = _EMOJI_PATTERN.sub("", title)
    # Lowercase
    cleaned = cleaned.lower().strip()
    # Remove common punctuation
    cleaned = re.sub(r"[#@\-_:;.,!?\"'()[\]{}]", " ", cleaned)
    # Remove stopwords
    words = [w for w in cleaned.split() if w not in _STOPWORDS]
    # Collapse whitespace
    return " ".join(words)


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

                    # Extract domain for source_name
                    item_url = item.get("url", "")
                    domain = urlparse(item_url).netloc.replace("www.", "") if item_url else ""

                    # Parse published date if available
                    pub_date = _parse_date(item.get("published_date", ""))

                    trends.append(Trend(
                        title=title,
                        description=item.get("content", "")[:300],
                        source=source,
                        url=item_url,
                        published_at=pub_date,
                        source_name=domain,
                        jack_potential=0.7,
                        discovered_at=datetime.now(),
                    ))
        except Exception as e:
            print(f"[TrendScanner] Tavily query '{query}' failed: {e}")

    return trends[:max_results]


async def scan_targeted_sources(
    domains: list[str],
    max_results: int = 10,
) -> list[Trend]:
    """Scan specific domains using Tavily include_domains.

    Args:
        domains: List of domains to scan (e.g., ["argaam.com", "magnitt.com"]).
        max_results: Maximum trends to return.

    Returns:
        List of Trend objects from targeted sources.
    """
    from tavily import AsyncTavilyClient

    if not settings.tavily_api_key:
        raise ValueError("TAVILY_API_KEY not set in environment.")

    client = AsyncTavilyClient(api_key=settings.tavily_api_key)

    trends: list[Trend] = []
    seen_titles: set[str] = set()

    # Batch domains in groups of 10 (Tavily limit)
    batch_size = 10
    for i in range(0, len(domains), batch_size):
        batch = domains[i : i + batch_size]
        try:
            print(f"[TrendScanner] Targeted scan: {batch[:3]}... ({len(batch)} domains)")
            result = await client.search(
                query="latest news trending today",
                max_results=5,
                search_depth="basic",
                include_domains=batch,
            )
            for item in result.get("results", []):
                title = item.get("title", "").strip()
                normalized = _normalize_title(title)
                if normalized and normalized not in seen_titles:
                    seen_titles.add(normalized)
                    item_url = item.get("url", "")
                    domain = urlparse(item_url).netloc.replace("www.", "") if item_url else ""
                    pub_date = _parse_date(item.get("published_date", ""))

                    trends.append(Trend(
                        title=title,
                        description=item.get("content", "")[:300],
                        source=TrendSource.TARGETED,
                        url=item_url,
                        published_at=pub_date,
                        source_name=domain,
                        jack_potential=0.75,
                        discovered_at=datetime.now(),
                    ))
        except Exception as e:
            print(f"[TrendScanner] Targeted batch failed: {e}")

        if len(trends) >= max_results:
            break

    return trends[:max_results]


async def scan_google_trends(max_results: int = 4) -> list[Trend]:
    """Scan Google Trends for Saudi Arabia trending searches.

    Includes retry logic with exponential backoff for 404 errors.
    """
    from pytrends.request import TrendReq

    trends: list[Trend] = []
    max_retries = 3

    for attempt in range(max_retries):
        try:
            pytrends = TrendReq(hl="ar", tz=180, timeout=(10, 25))
            trending = pytrends.trending_searches(pn="saudi_arabia")

            for i, row in trending.head(max_results).iterrows():
                title = str(row.iloc[0]).strip()
                if title:
                    trends.append(Trend(
                        title=title,
                        description="Trending on Google in Saudi Arabia",
                        source=TrendSource.GOOGLE_TRENDS,
                        url=f"https://trends.google.com/trends/explore?q={title}&geo=SA",
                        published_at=datetime.now(),
                        source_name="Google Trends KSA",
                        jack_potential=0.6,
                        region="KSA",
                        discovered_at=datetime.now(),
                    ))
            return trends  # Success, exit retry loop

        except Exception as e:
            wait_time = 2 ** attempt
            if attempt < max_retries - 1:
                print(
                    f"[TrendScanner] Google Trends attempt {attempt + 1}/{max_retries} "
                    f"failed: {e}. Retrying in {wait_time}s..."
                )
                import asyncio
                await asyncio.sleep(wait_time)
            else:
                print(f"[TrendScanner] Google Trends failed after {max_retries} attempts: {e}")

    return trends


async def scan_trends(
    mock: bool = False,
    max_results: int = 8,
    source_names: list[str] | None = None,
) -> list[Trend]:
    """Run all trend scanners and return combined, deduplicated results.

    Args:
        mock: If True, return mock data instead of real API calls.
        max_results: Maximum number of trends to return.
        source_names: Optional CSV source list names for targeted scanning.

    Returns:
        List of Trend objects sorted by jack_potential (descending).
    """
    if mock:
        return [Trend(**t) for t in MOCK_TRENDS[:max_results]]

    all_trends: list[Trend] = []

    # Run targeted source scanning if source names provided
    if source_names:
        try:
            from .source_manager import get_domains_for_scan
            domains = get_domains_for_scan(source_names)
            if domains:
                targeted = await scan_targeted_sources(domains, max_results=max_results)
                all_trends.extend(targeted)
                print(f"[TrendScanner] Got {len(targeted)} trends from targeted sources")
                
            # Run YouTube scanning if enabled
            if settings.youtube_scan_enabled:
                from .yt_scanner import scan_youtube_sources, scan_trending_ksa
                
                # Channel-based scanning (from CSV handles)
                yt_trends = await scan_youtube_sources(source_names, max_per_channel=settings.youtube_max_per_channel)
                if yt_trends:
                    all_trends.extend(yt_trends)
                    print(f"[TrendScanner] Got {len(yt_trends)} trends from YouTube channels")
                
                # KSA trending discovery (YouTube Data API v3)
                ksa_trends = await scan_trending_ksa(max_results=3)
                if ksa_trends:
                    all_trends.extend(ksa_trends)
                    print(f"[TrendScanner] Got {len(ksa_trends)} trends from KSA YouTube trending")
                    
        except Exception as e:
            print(f"[TrendScanner] Targeted/YT scanning failed: {e}")

    # Run general scanners
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

    # Deduplicate using normalized titles
    seen: set[str] = set()
    unique: list[Trend] = []
    for t in all_trends:
        key = _normalize_title(t.title)
        if key and key not in seen:
            seen.add(key)
            unique.append(t)

    # Sort by jack_potential descending
    unique.sort(key=lambda x: x.jack_potential, reverse=True)

    return unique[:max_results]

