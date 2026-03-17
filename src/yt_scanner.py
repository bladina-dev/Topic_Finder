"""YouTube Transcript Scanner — pulls text from YT videos to extract trends via Gemini."""

from __future__ import annotations

import json
from datetime import datetime

import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi

from .config import settings
from .models import Trend, TrendSource

def get_latest_video_ids(channel_handle: str, count: int = 2) -> list[str]:
    """Get the latest N video IDs from a YouTube channel using yt-dlp."""
    if not channel_handle.startswith("@") and not channel_handle.startswith("UC"):
        channel_handle = f"@{channel_handle}"
        
    url = f"https://www.youtube.com/{channel_handle}/videos"
    
    ydl_opts = {
        "extract_flat": "in_playlist",
        "playlistend": count,
        "quiet": True,
        "no_warnings": True,
        # Prevent yt-dlp from downloading full playlists if it hits a channel
        "playlist_items": f"1-{count}", 
    }
    
    video_ids = []
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print(f"[YT Scanner] Fetching latest videos from {channel_handle}...")
            info = ydl.extract_info(url, download=False)
            if info and "entries" in info:
                for entry in info["entries"]:
                    if entry and "id" in entry:
                        video_ids.append(entry["id"])
    except Exception as e:
        print(f"[YT Scanner] Error getting videos for {channel_handle}: {e}")
        
    return video_ids


def get_transcript(video_id: str, langs: list[str] = None) -> str | None:
    """Fetch the transcript for a video, combining all text."""
    if langs is None:
        langs = ["ar", "en"]
        
    try:
        # In youtube-transcript-api 1.x or 0.x, there might be get_transcript or fetch
        if hasattr(YouTubeTranscriptApi, "get_transcript"):
            # Older versions or if the class method exists
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=langs)
            if transcript_list and isinstance(transcript_list[0], dict):
                return " ".join([t["text"] for t in transcript_list])
            
        # 1.2+ version using object instance
        api = YouTubeTranscriptApi()
        if hasattr(api, "fetch"):
            fetched = api.fetch(video_id, languages=langs)
            # handle FetchedTranscriptSnippet objects or dicts
            lines = []
            for item in fetched:
                if hasattr(item, "text"):
                    lines.append(item.text)
                elif isinstance(item, dict) and "text" in item:
                    lines.append(item["text"])
            return " ".join(lines)
            
        return None
    except Exception as e:
        print(f"[YT Scanner] No transcript for video {video_id} ({e})")
        return None


def extract_marketing_insights(transcript: str, video_url: str) -> dict | None:
    """Use Gemini Flash to extract a topic, description, and marketing angles from transcript."""
    if not settings.google_api_key:
        print("[YT Scanner] GOOGLE_API_KEY missing.")
        return None
        
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=settings.google_api_key)

        prompt = f"""You are a marketing analyst. Here is a transcript from a recent YouTube video from Saudi/Gulf region.
Link: {video_url}
Transcript (may be auto-generated with no punctuation):
{transcript[:15000]}

Extract the core meaning of this video to figure out if it's a "trending topic" or useful marketing insight.
Return ONLY a JSON object with this exact schema:
{{
    "is_trend": true/false,
    "title": "A short 5-6 word title summarizing the core topic",
    "description": "2-3 sentences explaining what this is about and why people are watching it",
    "jack_potential": 0.0 to 1.0 float showing how viral or useful this is for marketing (e.g. 0.85)
}}"""

        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                safety_settings=[
                    types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                    types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                ],
            ),
        )

        text = response.text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
            if text.rstrip().endswith("```"):
                text = text.rstrip()[:-3]
            text = text.strip()

        data = json.loads(text)
        return data

    except Exception as e:
        print(f"[YT Scanner] Error extracting insights with Gemini: {e}")
        return None


async def scan_youtube_sources(
    source_names: list[str], 
    max_per_channel: int = 2
) -> list[Trend]:
    """Scan YouTube sources to extract trending themes from video content."""
    from .source_manager import get_youtube_handles_for_scan
    
    trends: list[Trend] = []
    
    handles = get_youtube_handles_for_scan(source_names)
    if not handles:
        print("[YT Scanner] No YouTube handles found in sources.")
        return trends
        
    print(f"[YT Scanner] Scanning {len(handles)} YouTube channels...")
    
    for handle in handles:
        video_ids = get_latest_video_ids(handle, count=max_per_channel)
        for vid in video_ids:
            transcript = get_transcript(vid)
            if not transcript:
                continue
                
            # If transcript is too short, skip
            if len(transcript) < 200:
                continue
                
            url = f"https://youtube.com/watch?v={vid}"
            insights = extract_marketing_insights(transcript, url)
            
            if insights and insights.get("is_trend"):
                trends.append(Trend(
                    title=f"[YT {handle}] {insights.get('title', 'Unknown Title')}",
                    description=insights.get("description", ""),
                    source=TrendSource.YOUTUBE,
                    jack_potential=insights.get("jack_potential", 0.7),
                    url=url,
                    published_at=datetime.now(),
                    source_name=handle,
                    discovered_at=datetime.now()
                ))
                print(f"[YT Scanner] Added trend from {handle}: '{insights.get('title')}'")

    return trends


# --- YouTube Data API v3: KSA Trending Discovery ---

# YouTube video category IDs relevant for marketing in Saudi Arabia
# See: https://developers.google.com/youtube/v3/docs/videoCategories/list
KSA_CATEGORY_IDS = {
    "1": "Film & Animation",
    "2": "Autos & Vehicles",
    "10": "Music",
    "17": "Sports",
    "20": "Gaming",
    "22": "People & Blogs",
    "24": "Entertainment",
    "25": "News & Politics",
    "26": "Howto & Style",
    "27": "Education",
    "28": "Science & Technology",
}

# Default categories to scan (most relevant for marketing)
DEFAULT_TRENDING_CATEGORIES = ["24", "25", "28", "22", "26"]  # Entertainment, News, Tech, People, Howto


async def scan_trending_ksa(
    category_ids: list[str] | None = None,
    max_results: int = 5,
) -> list[Trend]:
    """Discover trending YouTube videos in Saudi Arabia using YouTube Data API v3.

    Uses `videos.list(chart=mostPopular, regionCode=SA)` to find what's trending,
    then extracts transcripts and marketing insights.

    Args:
        category_ids: YouTube category IDs to scan. Defaults to entertainment, news, tech.
        max_results: Max videos per category.

    Returns:
        List of Trend objects from trending KSA videos.
    """
    # Get API key — prefer dedicated YouTube key, fall back to Google API key
    api_key = getattr(settings, "youtube_data_api_key", "") or settings.google_api_key
    if not api_key:
        print("[YT Trending] No API key available (set YOUTUBE_DATA_API_KEY or GOOGLE_API_KEY)")
        return []

    try:
        from googleapiclient.discovery import build
    except ImportError:
        print("[YT Trending] google-api-python-client not installed. Run: pip install google-api-python-client")
        return []

    if category_ids is None:
        category_ids = DEFAULT_TRENDING_CATEGORIES

    trends: list[Trend] = []
    seen_ids: set[str] = set()

    try:
        youtube = build("youtube", "v3", developerKey=api_key)

        for cat_id in category_ids:
            cat_name = KSA_CATEGORY_IDS.get(cat_id, f"Category {cat_id}")
            print(f"[YT Trending] Scanning KSA trending: {cat_name}...")

            try:
                request = youtube.videos().list(
                    part="snippet,statistics",
                    chart="mostPopular",
                    regionCode="SA",
                    videoCategoryId=cat_id,
                    maxResults=max_results,
                )
                response = request.execute()

                for item in response.get("items", []):
                    video_id = item["id"]
                    if video_id in seen_ids:
                        continue
                    seen_ids.add(video_id)

                    snippet = item.get("snippet", {})
                    stats = item.get("statistics", {})

                    title = snippet.get("title", "")
                    channel = snippet.get("channelTitle", "")
                    views = int(stats.get("viewCount", 0))
                    likes = int(stats.get("likeCount", 0))
                    published = snippet.get("publishedAt", "")

                    # Calculate view velocity (views per hour since publish)
                    velocity = 0.0
                    if published:
                        try:
                            pub_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
                            hours_since = max(1, (datetime.now(pub_dt.tzinfo) - pub_dt).total_seconds() / 3600)
                            velocity = views / hours_since
                        except Exception:
                            pass

                    # Try to get transcript for deeper analysis
                    transcript = get_transcript(video_id)
                    description = snippet.get("description", "")[:300]

                    # If we have a transcript, use Gemini for richer insights
                    jack_potential = 0.7
                    if transcript and len(transcript) > 200:
                        url = f"https://youtube.com/watch?v={video_id}"
                        insights = extract_marketing_insights(transcript, url)
                        if insights:
                            description = insights.get("description", description)
                            jack_potential = insights.get("jack_potential", 0.7)

                    # Boost jack_potential based on engagement signals
                    if velocity > 10000:  # >10K views/hour
                        jack_potential = min(1.0, jack_potential + 0.15)
                    elif velocity > 1000:
                        jack_potential = min(1.0, jack_potential + 0.05)

                    like_ratio = likes / max(1, views)
                    if like_ratio > 0.05:  # >5% like ratio = high engagement
                        jack_potential = min(1.0, jack_potential + 0.05)

                    # Parse publish date
                    pub_dt_parsed = None
                    if published:
                        try:
                            pub_dt_parsed = datetime.fromisoformat(published.replace("Z", "+00:00"))
                        except Exception:
                            pass

                    trends.append(Trend(
                        title=f"[KSA Trending] {title}",
                        description=f"{description} | 👁 {views:,} views | ⚡ {velocity:,.0f} views/hr | 📺 {channel}",
                        source=TrendSource.YOUTUBE,
                        jack_potential=round(jack_potential, 2),
                        url=f"https://youtube.com/watch?v={video_id}",
                        published_at=pub_dt_parsed,
                        source_name=channel,
                        vertical=cat_name.lower(),
                        discovered_at=datetime.now(),
                    ))
                    print(f"[YT Trending] {cat_name}: '{title}' ({views:,} views, {velocity:,.0f} v/hr)")

            except Exception as e:
                print(f"[YT Trending] Error scanning category {cat_name}: {e}")

    except Exception as e:
        print(f"[YT Trending] Failed to build YouTube client: {e}")

    # Sort by jack_potential
    trends.sort(key=lambda t: t.jack_potential, reverse=True)
    return trends

