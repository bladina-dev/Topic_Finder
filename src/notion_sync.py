"""Notion database sync — push ContentAngle objects to a Notion database."""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from src.models import AgentOutput, ContentAngle, Trend

NOTION_API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"
DB_NAME = "Marketing Agent Angles"

_cached_db_id: str = ""


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


async def ensure_database(parent_page_id: str) -> str:
    """Get or create the 'Marketing Agent Angles' database under parent_page_id.

    Returns the database_id.
    """
    global _cached_db_id
    from src.config import settings

    api_key = settings.notion_api_key
    print("[Notion] Checking database...")

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{NOTION_API_BASE}/blocks/{parent_page_id}/children",
            headers=_headers(api_key),
        )
        resp.raise_for_status()

        for block in resp.json().get("results", []):
            if block.get("type") == "child_database":
                title = block.get("child_database", {}).get("title", "")
                if title == DB_NAME:
                    _cached_db_id = block["id"]
                    print(f"[Notion] Database ready: {_cached_db_id}")
                    return _cached_db_id

        # Database not found — create it
        resp = await client.post(
            f"{NOTION_API_BASE}/databases",
            headers=_headers(api_key),
            json={
                "parent": {"type": "page_id", "page_id": parent_page_id},
                "title": [{"type": "text", "text": {"content": DB_NAME}}],
                "properties": {
                    "Headline": {"title": {}},
                    "Hook": {"rich_text": {}},
                    "Trend": {"rich_text": {}},
                    "Source": {
                        "select": {
                            "options": [
                                {"name": "twitter_ksa"},
                                {"name": "gulf_news"},
                                {"name": "google_trends"},
                                {"name": "youtube"},
                                {"name": "cultural"},
                                {"name": "targeted"},
                            ]
                        }
                    },
                    "Platform": {
                        "select": {
                            "options": [
                                {"name": "twitter"},
                                {"name": "instagram"},
                                {"name": "linkedin"},
                                {"name": "tiktok"},
                                {"name": "general"},
                            ]
                        }
                    },
                    "Triggers": {
                        "multi_select": {
                            "options": [
                                {"name": "zeigarnik"},
                                {"name": "fomo"},
                                {"name": "curiosity_gap"},
                                {"name": "social_proof"},
                                {"name": "gain"},
                                {"name": "loss_aversion"},
                            ]
                        }
                    },
                    "Score": {"number": {"format": "percent"}},
                    "Grade": {
                        "select": {
                            "options": [
                                {"name": "Fire"},
                                {"name": "Good"},
                                {"name": "Weak"},
                            ]
                        }
                    },
                    "Date": {"date": {}},
                    "Status": {
                        "select": {
                            "options": [
                                {"name": "New"},
                                {"name": "Approved"},
                                {"name": "Published"},
                                {"name": "Skipped"},
                            ]
                        }
                    },
                },
            },
        )
        resp.raise_for_status()
        _cached_db_id = resp.json()["id"]
        print(f"[Notion] Database ready: {_cached_db_id}")
        return _cached_db_id


def _compute_grade(total_score: float) -> str:
    if total_score >= 48:
        return "Fire"
    if total_score >= 36:
        return "Good"
    return "Weak"


async def _create_angle_page(
    database_id: str,
    angle: ContentAngle,
    trend: Trend,
    grade: str,
    total_score: float,
    api_key: str,
    client: httpx.AsyncClient,
) -> bool:
    """Create a single Notion page for one ContentAngle. Returns True on success."""
    trigger_names = [t.type.value for t in angle.psych_triggers]
    score_fraction = round(total_score / 60, 4) if total_score else 0.0

    payload = {
        "parent": {"database_id": database_id},
        "properties": {
            "Headline": {
                "title": [{"type": "text", "text": {"content": angle.headline[:2000]}}]
            },
            "Hook": {
                "rich_text": [{"type": "text", "text": {"content": angle.hook[:2000]}}]
            },
            "Trend": {
                "rich_text": [{"type": "text", "text": {"content": trend.title[:2000]}}]
            },
            "Source": {"select": {"name": trend.source.value}},
            "Platform": {"select": {"name": angle.platform.value}},
            "Triggers": {"multi_select": [{"name": t} for t in trigger_names]},
            "Score": {"number": score_fraction},
            "Grade": {"select": {"name": grade}},
            "Date": {
                "date": {"start": datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")}
            },
            "Status": {"select": {"name": "New"}},
        },
    }

    try:
        resp = await client.post(
            f"{NOTION_API_BASE}/pages",
            headers=_headers(api_key),
            json=payload,
        )
        resp.raise_for_status()
        return True
    except httpx.HTTPStatusError as e:
        print(
            f"[Notion] Warning: failed to push '{angle.headline[:40]}': "
            f"{e.response.text[:200]}"
        )
        return False


async def push_angles(
    output: AgentOutput,
    benchmark_results: list[dict] | None = None,
) -> int:
    """Push all ContentAngle objects from output to the Notion database.

    Returns the count of angles successfully pushed.
    """
    from src.config import settings

    api_key = settings.notion_api_key
    database_id = _cached_db_id or settings.notion_database_id
    if not database_id:
        database_id = await ensure_database(settings.notion_parent_page_id)

    score_map: dict[str, float] = {}
    if benchmark_results:
        for result in benchmark_results:
            headline = result.get("headline", "")
            if headline:
                score_map[headline] = float(result.get("total", 0.0))

    total_angles = sum(len(r.angles) for r in output.results)
    print(f"[Notion] Pushing {total_angles} angles...")

    count = 0
    async with httpx.AsyncClient(timeout=30) as client:
        for trend_with_angles in output.results:
            trend = trend_with_angles.trend
            for angle in trend_with_angles.angles:
                total_score = score_map.get(angle.headline, 0.0)
                grade = _compute_grade(total_score)
                success = await _create_angle_page(
                    database_id=database_id,
                    angle=angle,
                    trend=trend,
                    grade=grade,
                    total_score=total_score,
                    api_key=api_key,
                    client=client,
                )
                if success:
                    count += 1

    print(f"[Notion] Done: {count} angles synced to Notion")
    return count
