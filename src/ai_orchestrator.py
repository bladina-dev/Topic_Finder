"""AI Orchestrator — multi-provider AI for content angle generation."""

from __future__ import annotations

import json
from typing import Optional

from .config import settings
from .models import (
    AIProvider,
    ContentAngle,
    Platform,
    PsychTrigger,
    PsychTriggerType,
    Trend,
    TrendSource,
)
from .psychology import get_psychology_system_prompt, suggest_triggers_for_trend


ANGLE_GENERATION_PROMPT = """You are an elite creative director at a Gulf-region agency known for viral content.
You are NOT a generic content mill. You produce work that makes people stop scrolling, feel something, and hit share.

═══ BANNED PATTERNS (instant rejection) ═══
NEVER use these clichés — they are the mark of lazy, forgettable content:
English:
- "Top X tips/ways/reasons"
- "Here's how/why/what"
- "Game-changer" / "Everything you need to know"
- "The secret to..." / "Unlock the secret"
- "Don't miss out" / "You won't believe"
- "Beyond the headlines" / "The one thing everyone overlooks"
- "Take your X to the next level"
- "In today's fast-paced world"
- "What X% of [Audience] Know"
- "Trend Chasers vs. Trend Setters"
- "overcoming adversity" / "the hero entrepreneur"
- "hidden gem" / "underdog outperforms"
- "Leveraging predictive models and deep cultural insights"
Arabic:
- "إشارة خفية" (overused mystery bait)
- "3 أشياء" / "أفضل X أشياء"
- "الأرقام تقول شيء ثاني"
- "تسبح مع التيار وتصنع موجتك"
- "سر الذي خرب..." (formula headline)
- "قصة الفشل بسبب كلمة واحدة"
- "قصة اكتشاف مؤثرة عبر السوشيال ميديا"
- "يفرق بين متابع ومؤثر"
- Starting with emoji-stuffed headlines (max 1 emoji)
If you catch yourself writing ANY of these, delete it and try harder.

═══ ASSIGNMENT ═══
Generate exactly {angles_count} content angles for this trend.
Each angle MUST use a DIFFERENT creative format:

**Angle 1 — MICRO-STORY** (narrative hook)
Start with a person, a moment, a scene. Someone is doing something specific.
Then introduce the conflict/twist that connects to the trend.
Think: "محمد was about to close his laptop at 11 PM when..." or "A Riyadh café owner noticed something strange in her analytics..."
The story IS the hook. No telling, only showing.

**Angle 2 — DATA PROVOCATEUR** (contrarian stat)
Lead with a surprising, counterintuitive number or comparison.
Then challenge the audience's assumption with a fresh take.
Think: "72% of Saudi consumers do X, but the 28% who don't are winning because..."
Use real or realistic data. Make them question what they thought they knew.

**Angle 3 — CULTURAL CONNECTOR** (local resonance)
This angle MUST be written in Arabic (عربي).
Tie the trend to a Saudi/Gulf cultural moment, proverb, or shared experience.
Reference: {cultural_context}
Think: Use Arabic idioms, Ramadan energy, Eid preparations, Saudi work culture, Gulf humor.
This angle should feel like it was written BY someone from the Gulf, not ABOUT the Gulf.

═══ TREND ═══
Title: {trend_title}
Description: {trend_description}
Source: {trend_source}

═══ CULTURAL CONTEXT (today) ═══
{cultural_context}

═══ BRAND CONTEXT ═══
{brand_context}

═══ QUALITY TESTS (apply to every angle) ═══
Before submitting each angle, verify:
□ Scroll-stop test: Would YOU stop scrolling to read this? Be honest.
□ Share test: Would someone screenshot this and send it to a friend? Why?
□ Trigger test: Does the psych trigger create a PHYSICAL reaction (stomach drop, fingers itch, fear of being left behind)?
□ Uniqueness test: Could this angle be about any brand/trend? If yes, it's too generic — rewrite.
□ Cliché test: Does ANY phrase sound like something a content mill would produce? If yes, delete it.

═══ PLATFORM CONSTRAINTS ═══
- twitter: Hook must be under 280 characters. Punchy, conversational, hot-take energy.
- tiktok: Write as a script. "POV:", "What nobody tells you about...", pattern interrupt in first 2 seconds.
- linkedin: Thought leadership tone. No hashtag spam. Open with a bold statement or personal story.
- instagram: Visual-first. Describe the visual concept alongside the caption. Carousel-friendly.

Respond in this exact JSON format (no markdown, just raw JSON):
{{
  "angles": [
    {{
      "headline": "Compelling, non-cliché headline (max 1 emoji)",
      "hook": "The scroll-stopping opening that implements the psychological trigger",
      "body_outline": "2-3 sentence content body with specific details, not generic filler",
      "platform": "twitter|instagram|linkedin|tiktok|general",
      "psych_triggers": [
        {{
          "type": "zeigarnik|fomo|curiosity_gap|social_proof|gain|loss_aversion",
          "hook": "The specific hook text that creates a visceral reaction",
          "rationale": "Why this trigger works for THIS specific trend and audience"
        }}
      ],
      "brand_alignment_score": 0.85
    }}
  ]
}}"""


def get_cultural_context() -> str:
    """Get current Gulf-region cultural context for content generation."""
    from datetime import datetime
    import math

    now = datetime.now()
    month, day = now.month, now.day

    context_lines = []

    # Ramadan detection (approximate for 2026: ~Feb 18 - Mar 19)
    if (month == 2 and day >= 18) or (month == 3 and day <= 19):
        ramadan_start = datetime(2026, 2, 18)
        ramadan_day = (now - ramadan_start).days + 1
        context_lines.append(f"🌙 Ramadan 2026, Day {ramadan_day} of 30")
        context_lines.append("Iftar gatherings, late-night energy, spiritual reflection, charity")
        if ramadan_day >= 25:
            context_lines.append("⚡ Last 5 nights — peak spiritual intensity, Laylat al-Qadr anticipation")
        if ramadan_day >= 28:
            context_lines.append("🎉 Eid Al-Fitr preparations underway — gift shopping, travel plans, family gatherings")

    # Eid Al-Fitr (approx March 20-22, 2026)
    elif month == 3 and 20 <= day <= 25:
        context_lines.append("🎊 Eid Al-Fitr 2026 — celebration, family, feasting, new clothes")
        context_lines.append("Gift-giving, Eid morning prayers, visiting relatives")

    # Saudi National Day (Sept 23)
    elif month == 9 and 20 <= day <= 25:
        context_lines.append("🇸🇦 Saudi National Day (Sept 23) — patriotism, Vision 2030 pride")

    # Riyadh Season (Oct-Mar typically)
    if month >= 10 or month <= 3:
        context_lines.append("🎭 Riyadh Season 2026 — entertainment, tourism, concerts, events")

    # Year-round
    context_lines.append("📐 Saudi Vision 2030 — ongoing transformation, tech, tourism, entertainment")
    context_lines.append(f"📅 Today: {now.strftime('%A, %B %d, %Y')}")

    # Weekday context (Saudi work week: Sun-Thu)
    weekday = now.weekday()  # 0=Mon
    if weekday == 3:  # Thursday
        context_lines.append("🎉 Thursday — start of Saudi weekend, going-out energy")
    elif weekday == 4:  # Friday
        context_lines.append("🕌 Friday — Jumu'ah prayer, family time, rest")
    elif weekday == 6:  # Sunday
        context_lines.append("💼 Sunday — start of Saudi work week")

    return "\n".join(context_lines)


async def generate_with_gemini(
    system_prompt: str, user_prompt: str
) -> str:
    """Generate content using Google Gemini API."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.google_api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
        ),
    )
    return response.text


async def generate_with_claude(
    system_prompt: str, user_prompt: str
) -> str:
    """Generate content using Anthropic Claude API."""
    from anthropic import AsyncAnthropic

    client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return response.content[0].text


async def generate_with_lmstudio(
    system_prompt: str, user_prompt: str
) -> str:
    """Generate content using LM Studio (OpenAI-compatible API)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(
        base_url=settings.lm_studio_base_url,
        api_key="lm-studio",  # LM Studio doesn't need a real key
    )

    response = await client.chat.completions.create(
        model=settings.lm_studio_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.8,
        max_tokens=4096,
    )

    return response.choices[0].message.content or ""


async def generate_content(
    system_prompt: str,
    user_prompt: str,
    provider: AIProvider | None = None,
) -> str:
    """Generate content using the selected AI provider with fallback.

    Args:
        system_prompt: System instruction for the AI.
        user_prompt: User prompt with trend and brand data.
        provider: AI provider to use. Defaults to settings.default_ai_provider.

    Returns:
        The AI-generated text response.
    """
    if provider is None:
        provider = AIProvider(settings.default_ai_provider)

    # Try primary provider, then fallback
    providers_to_try = [provider]
    all_providers = [AIProvider.GEMINI, AIProvider.CLAUDE, AIProvider.LM_STUDIO]
    for p in all_providers:
        if p not in providers_to_try:
            providers_to_try.append(p)

    last_error = None
    for p in providers_to_try:
        try:
            if p == AIProvider.GEMINI:
                if not settings.google_api_key:
                    continue
                return await generate_with_gemini(system_prompt, user_prompt)
            elif p == AIProvider.CLAUDE:
                if not settings.anthropic_api_key:
                    continue
                return await generate_with_claude(system_prompt, user_prompt)
            elif p == AIProvider.LM_STUDIO:
                return await generate_with_lmstudio(system_prompt, user_prompt)
        except Exception as e:
            last_error = e
            print(f"[AIOrchestrator] Provider {p.value} failed: {e}")
            continue

    raise RuntimeError(
        f"All AI providers failed. Last error: {last_error}"
    )


def _parse_angles_response(
    raw_text: str, trend: Trend, angles_count: int = 3
) -> list[ContentAngle]:
    """Parse the AI response into ContentAngle objects.

    Handles JSON extraction from potentially markdown-wrapped responses.
    """
    # Try to extract JSON from the response
    text = raw_text.strip()

    # Remove markdown code fences if present (handles ```json, ```JSON, ``` etc.)
    if text.startswith("```"):
        lines = text.split("\n")
        # Skip first line (the fence + optional language tag)
        text = "\n".join(lines[1:])
        # Strip closing fence
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
        text = text.strip()

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON object in the response
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start:end])
            except json.JSONDecodeError:
                print(f"[AIOrchestrator] Parse error for '{trend.title[:40]}'. Raw: {raw_text[:500]}")
                return [ContentAngle(
                    headline=f"[Parse Error] Content for: {trend.title}",
                    hook="Generated content could not be parsed. Check AI response.",
                    trend_title=trend.title,
                    trend_source=trend.source,
                )]
        else:
            print(f"[AIOrchestrator] No JSON found for '{trend.title[:40]}'. Raw: {raw_text[:500]}")
            return [ContentAngle(
                headline=f"[Parse Error] Content for: {trend.title}",
                hook=raw_text[:200],
                trend_title=trend.title,
                trend_source=trend.source,
            )]

    angles = []
    for angle_data in data.get("angles", [])[:angles_count]:
        triggers = []
        for trig in angle_data.get("psych_triggers", []):
            try:
                triggers.append(PsychTrigger(
                    type=PsychTriggerType(trig.get("type", "curiosity_gap")),
                    hook=trig.get("hook", ""),
                    rationale=trig.get("rationale", ""),
                ))
            except (ValueError, KeyError):
                pass

        try:
            platform = Platform(angle_data.get("platform", "general"))
        except ValueError:
            platform = Platform.GENERAL

        angles.append(ContentAngle(
            headline=angle_data.get("headline", "Untitled"),
            hook=angle_data.get("hook", ""),
            body_outline=angle_data.get("body_outline", ""),
            platform=platform,
            psych_triggers=triggers,
            brand_alignment_score=float(angle_data.get("brand_alignment_score", 0.5)),
            trend_title=trend.title,
            trend_source=trend.source,
        ))

    return angles


async def generate_angles_for_trend(
    trend: Trend,
    brand_context: str = "",
    angles_count: int = 3,
    provider: AIProvider | None = None,
    feedback_context: str = "",
) -> list[ContentAngle]:
    """Generate content angles for a single trend.

    Args:
        trend: The trend to generate angles for.
        brand_context: Brand context from ChromaDB.
        angles_count: Number of angles to generate.
        provider: AI provider to use.

    Returns:
        List of ContentAngle objects.
    """
    # Get suggested triggers
    suggested = suggest_triggers_for_trend(trend.title, trend.source.value)
    psych_prompt = get_psychology_system_prompt(suggested)

    # Build the user prompt with cultural context
    cultural_ctx = get_cultural_context()
    user_prompt = ANGLE_GENERATION_PROMPT.format(
        angles_count=angles_count,
        trend_title=trend.title,
        trend_description=trend.description,
        trend_source=trend.source.value,
        cultural_context=cultural_ctx,
        brand_context=brand_context or "No brand documents uploaded. Generate general marketing angles.",
    )

    if feedback_context:
        user_prompt = user_prompt + "\n\n" + feedback_context

    # Generate
    raw_response = await generate_content(psych_prompt, user_prompt, provider)

    # Parse
    return _parse_angles_response(raw_response, trend, angles_count)
