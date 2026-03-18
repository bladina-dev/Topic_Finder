"""Pipeline — orchestrates the full trend-to-angles workflow."""

from __future__ import annotations

import asyncio
from datetime import datetime

from .ai_orchestrator import generate_angles_for_trend
from .brand_ingestion import query_brand_context
from .config import settings
from .models import (
    AIProvider,
    AgentOutput,
    ContentAngle,
    Platform,
    Trend,
    TrendWithAngles,
)
from .trend_scanner import scan_trends


async def run_pipeline(
    mock: bool = False,
    max_trends: int = 8,
    angles_per_trend: int = 3,
    provider: AIProvider | None = None,
    platforms: list[Platform] | None = None,
) -> AgentOutput:
    """Run the full marketing agent pipeline.

    Two-step pipeline:
    1. Scan trends from multiple sources (Tavily, Google Trends, Twitter/X KSA)
    2. For each trend, generate content angles with psychological triggers

    Args:
        mock: If True, use mock data for trends (still generates real AI angles unless provider fails).
        max_trends: Maximum number of trends to scan.
        angles_per_trend: Number of angles to generate per trend.
        provider: AI provider to use. Defaults to settings.
        platforms: Target platforms. Defaults to [GENERAL].

    Returns:
        AgentOutput with all trends and generated angles.
    """
    errors: list[str] = []
    results: list[TrendWithAngles] = []

    # Step 1: Scan trends
    print(f"[Pipeline] Scanning trends (mock={mock})...")
    try:
        trends = await scan_trends(mock=mock, max_results=max_trends)
        print(f"[Pipeline] Found {len(trends)} trends")
    except Exception as e:
        errors.append(f"Trend scanning failed: {e}")
        return AgentOutput(errors=errors)

    if not trends:
        errors.append("No trends found")
        return AgentOutput(errors=errors)

    # Step 2: Load Obsidian feedback to guide angle generation
    feedback_context = ""
    if settings.obsidian_vault_path:
        try:
            from pathlib import Path as _Path
            from .obsidian_sync import fetch_feedback, format_feedback_prompt
            feedback = fetch_feedback(_Path(settings.obsidian_vault_path))
            feedback_context = format_feedback_prompt(feedback)
            n_approved = len(feedback.get("approved", []))
            n_skipped = len(feedback.get("skipped", []))
            if feedback_context:
                print(f"[Pipeline] Loaded feedback: {n_approved} approved, {n_skipped} skipped patterns")
            else:
                print("[Pipeline] No feedback yet")
        except Exception as e:
            print(f"[Pipeline] Obsidian feedback load failed (non-fatal): {e}")

    # Step 3: Generate angles for each trend
    print(f"[Pipeline] Generating {angles_per_trend} angles per trend...")

    for trend in trends:
        try:
            # Get brand context relevant to this trend
            brand_context = query_brand_context(trend.title)

            if mock:
                # Generate mock angles without AI calls
                angles = _generate_mock_angles(trend, angles_per_trend)
            else:
                angles = await generate_angles_for_trend(
                    trend=trend,
                    brand_context=brand_context,
                    angles_count=angles_per_trend,
                    provider=provider,
                    feedback_context=feedback_context,
                )

            results.append(TrendWithAngles(trend=trend, angles=angles))
            print(f"[Pipeline] ✓ {trend.title}: {len(angles)} angles")

        except Exception as e:
            errors.append(f"Angle generation failed for '{trend.title}': {e}")
            results.append(TrendWithAngles(trend=trend, angles=[]))
            print(f"[Pipeline] ✗ {trend.title}: {e}")

    # Build output
    total_angles = sum(len(r.angles) for r in results)
    used_provider = provider or AIProvider(settings.default_ai_provider)

    output = AgentOutput(
        timestamp=datetime.now(),
        provider_used=used_provider,
        trend_count=len(trends),
        angle_count=total_angles,
        results=results,
        errors=errors,
    )

    print(f"[Pipeline] Complete: {output.trend_count} trends, {output.angle_count} angles, {len(errors)} errors")
    return output


def _generate_mock_angles(trend: Trend, count: int = 3) -> list[ContentAngle]:
    """Generate mock content angles for testing."""
    from .models import PsychTrigger, PsychTriggerType

    mock_angles = [
        ContentAngle(
            headline=f"🔥 Why {trend.title} Changes Everything for Your Brand",
            hook=f"Everyone's talking about {trend.title}. But nobody's connecting the dots to what it means for YOUR business...",
            body_outline="1. Context: What's happening. 2. The hidden opportunity. 3. Your action plan.",
            platform=Platform.LINKEDIN,
            psych_triggers=[PsychTrigger(
                type=PsychTriggerType.CURIOSITY_GAP,
                hook="Nobody's connecting the dots...",
                rationale="Creates information asymmetry — reader needs to find out what dots.",
            )],
            brand_alignment_score=0.87,
            trend_title=trend.title,
            trend_source=trend.source,
        ),
        ContentAngle(
            headline=f"⚡ {trend.title}: The 3 Things You're Missing",
            hook=f"While you were scrolling, {trend.title} just created a massive opportunity. Here's what 90% of brands won't see...",
            body_outline="1. The surface-level take. 2. The hidden angle. 3. How to act on it NOW.",
            platform=Platform.TWITTER,
            psych_triggers=[PsychTrigger(
                type=PsychTriggerType.FOMO,
                hook="While you were scrolling...",
                rationale="Implies they're already behind — urgency to catch up.",
            )],
            brand_alignment_score=0.82,
            trend_title=trend.title,
            trend_source=trend.source,
        ),
        ContentAngle(
            headline=f"📊 The Data Behind {trend.title} (And What It Means for You)",
            hook=f"We analyzed {trend.title} and found something surprising. The brands that win here do ONE thing differently...",
            body_outline="1. The data snapshot. 2. The surprising finding. 3. The one differentiator.",
            platform=Platform.INSTAGRAM,
            psych_triggers=[PsychTrigger(
                type=PsychTriggerType.ZEIGARNIK,
                hook="...found something surprising... ONE thing differently",
                rationale="Opens two loops: what's surprising? What's the one thing? Reader must resolve both.",
            )],
            brand_alignment_score=0.91,
            trend_title=trend.title,
            trend_source=trend.source,
        ),
    ]

    return mock_angles[:count]


async def run_pipeline_sync(**kwargs) -> AgentOutput:
    """Synchronous wrapper for run_pipeline."""
    return await run_pipeline(**kwargs)
