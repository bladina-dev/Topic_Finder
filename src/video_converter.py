"""Video converter — transforms ContentAngle + Trend into VideoData JSON for Remotion."""

from __future__ import annotations

import json
import re
from datetime import datetime

from .models import AIProvider, ContentAngle, Trend


VIDEO_SYSTEM_PROMPT = """أنت مخرج محتوى خليجي متخصص في إنتاج فيديوهات يوتيوب شورتس للسوق السعودي.
مهمتك: تحويل فكرة محتوى إلى سكريبت فيديو جذاب باللهجة الخليجية العامية.

قواعد اللغة:
- استخدم اللهجة الخليجية/السعودية العامية (مش الفصحى الرسمية)
- أمثلة صح: "بياخد" مش "سيأخذ" ، "محدش" مش "لا أحد" ، "ليش" مش "لماذا"
- الجملة قصيرة وقوية — أقل من 8 كلمات في السطر
- استخدم \\n لتقسيم العناوين الطويلة

نمط المشاهد الإلزامي (5-6 مشاهد):
1. hook (90 frames): عنوان قوي يوقف التمرير + إيموجي كبير + كاميرا zoom
2. intro (75 frames): "معكم فهد الحربي" + "خبير مهني — SamimlyCV" + كاميرا static — هذا ثابت دائماً
3. point (120 frames): الفكرة الرئيسية + تفاصيل + كاميرا pan
4. point أو list (120-150 frames): نقطة دعم أو قائمة 3-4 عناصر + كاميرا tilt
5. (اختياري) point ثانية
6. cta (90 frames): دعوة للمتابعة + "SamimlyCV" button + كاميرا zoom

قواعد المحتوى:
- المشهد hook يخلق فضولاً أو مفاجأة — مش مجرد وصف
- استخدم الـ psychological trigger في hook scene
- الـ list scene: 3-4 عناصر فقط، كل عنصر جملة واحدة
- النوع pillar: career | workplace | ai | story | sidehustle"""

VIDEO_USER_PROMPT = """حوّل هذه الزاوية إلى سكريبت فيديو:

═══ الترند ═══
العنوان: {trend_title}
الوصف: {trend_description}

═══ الزاوية ═══
العنوان: {angle_headline}
الـ Hook: {angle_hook}
الـ Body: {angle_body}
المحفز النفسي: {psych_trigger}

═══ السياق الثقافي ═══
{cultural_context}

═══ أسلوب صح (أمثلة) ═══
Hook: "هل الذكاء الاصطناعي\\nبياخد شغلك؟"  ✓
Hook: "هل سيحل الذكاء الاصطناعي محل وظيفتك"  ✗
Point: "الحقيقة اللي محدش بيقولها:"  ✓
Point: "الحقائق التي لا يخبرك بها أحد"  ✗
CTA: "تابعني عشان نتكلم\\nعن مستقبل الشغل"  ✓

أرجع JSON فقط بدون markdown:
{{
  "id": "fahad-ep-{date_slug}-{topic_slug}",
  "title": "عنوان عربي للفيديو",
  "pillar": "career|workplace|ai|story|sidehustle",
  "bgMusic": "EleEnergetic, Social Media Creator_pre_sp109_s50_sb75_v3.mp3",
  "bgMusicVolume": 0.15,
  "scenes": [
    {{"type": "hook", "emoji": "🔥", "headline": "عنوان\\nالـ hook", "camera": "zoom", "durationInFrames": 90}},
    {{"type": "intro", "emoji": "💼", "headline": "معكم فهد الحربي", "body": "خبير مهني — SamimlyCV", "camera": "static", "durationInFrames": 75}},
    {{"type": "point", "emoji": "💡", "headline": "الفكرة الرئيسية:", "body": "تفاصيل\\nفي جملتين", "camera": "pan", "durationInFrames": 120}},
    {{"type": "list", "emoji": "✅", "headline": "النقاط:", "items": ["نقطة ١", "نقطة ٢", "نقطة ٣"], "camera": "tilt", "durationInFrames": 150}},
    {{"type": "cta", "emoji": "🚀", "headline": "تابعني عشان تعرف أكثر\\nعن مستقبل الشغل", "body": "SamimlyCV", "camera": "zoom", "durationInFrames": 90}}
  ]
}}"""


_AR_SLUG_MAP = {
    "الذكاء الاصطناعي": "ai",
    "ذكاء اصطناعي": "ai",
    "وظيف": "jobs",
    "سيرة ذاتية": "resume",
    "مهار": "skills",
    "سعودي": "ksa",
    "خليج": "gulf",
    "رمضان": "ramadan",
    "عمل": "work",
}


def _make_topic_slug(text: str) -> str:
    """Convert trend title to a URL-friendly slug."""
    for ar, en in _AR_SLUG_MAP.items():
        if ar in text:
            return en
    # Use English words if present
    words = re.sub(r"[^a-z0-9\s-]", "", text.lower()).split()
    slug = "-".join(words[:3]) if words else "content"
    return slug or "content"


def _parse_video_response(raw_text: str) -> dict:
    """Parse AI response into a VideoData dict."""
    text = raw_text.strip()

    # Strip markdown code fences
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text[:-3]
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        raise ValueError(f"Could not parse VideoData JSON: {text[:300]}")


_TRIGGER_EMOJIS = {
    "zeigarnik": "🔄",
    "fomo": "⚡",
    "curiosity_gap": "🔍",
    "social_proof": "👥",
    "gain": "📈",
    "loss_aversion": "⚠️",
}

_TOPIC_EMOJIS = {
    "ai": "🤖",
    "jobs": "💼",
    "resume": "📄",
    "skills": "🎯",
    "ksa": "🇸🇦",
    "gulf": "🌍",
    "work": "💼",
}


def _mock_video_data(angle: ContentAngle, trend: Trend) -> dict:
    """Generate a deterministic mock VideoData without an LLM call."""
    date_slug = datetime.now().strftime("%Y%m%d")
    topic_slug = _make_topic_slug(angle.trend_title or trend.title)
    hook_emoji = _TRIGGER_EMOJIS.get(
        angle.psych_triggers[0].type.value if angle.psych_triggers else "", "🎯"
    )

    # Truncate headline into two lines for hook
    hook_headline = angle.hook[:60] if angle.hook else angle.headline[:60]
    if len(hook_headline) > 30:
        mid = hook_headline.rfind(" ", 0, 35) or 30
        hook_headline = hook_headline[:mid] + "\n" + hook_headline[mid:].strip()

    return {
        "id": f"fahad-ep-{date_slug}-{topic_slug}",
        "title": angle.headline[:50],
        "pillar": "ai" if "ai" in topic_slug else "career",
        "bgMusic": "EleEnergetic, Social Media Creator_pre_sp109_s50_sb75_v3.mp3",
        "bgMusicVolume": 0.15,
        "scenes": [
            {
                "type": "hook",
                "emoji": hook_emoji,
                "headline": hook_headline,
                "camera": "zoom",
                "durationInFrames": 90,
            },
            {
                "type": "intro",
                "emoji": "💼",
                "headline": "معكم فهد الحربي",
                "body": "خبير مهني — SamimlyCV",
                "camera": "static",
                "durationInFrames": 75,
            },
            {
                "type": "point",
                "emoji": "💡",
                "headline": angle.headline[:50],
                "body": (angle.body_outline or "")[:80],
                "camera": "pan",
                "durationInFrames": 120,
            },
            {
                "type": "cta",
                "emoji": "🚀",
                "headline": "تابعني عشان تعرف أكثر\nعن مستقبل الشغل",
                "body": "SamimlyCV",
                "camera": "zoom",
                "durationInFrames": 90,
            },
        ],
    }


async def angle_to_video_data(
    angle: ContentAngle,
    trend: Trend,
    provider: AIProvider | None = None,
    mock: bool = False,
) -> dict:
    """Convert a ContentAngle into a VideoData JSON dict using LLM.

    Args:
        angle: The content angle to convert.
        trend: The trend the angle is based on.
        provider: AI provider to use (defaults to settings).

    Returns:
        VideoData dict compatible with the Remotion FahadYouTubeShort template.
    """
    if mock:
        return _mock_video_data(angle, trend)

    from .ai_orchestrator import generate_content, get_cultural_context

    cultural_ctx = get_cultural_context()
    date_slug = datetime.now().strftime("%Y%m%d")
    topic_slug = _make_topic_slug(angle.trend_title or trend.title)

    psych_trigger_text = ""
    if angle.psych_triggers:
        t = angle.psych_triggers[0]
        psych_trigger_text = f"{t.type.value}: {t.hook}"

    user_prompt = VIDEO_USER_PROMPT.format(
        trend_title=trend.title,
        trend_description=(trend.description or "")[:200],
        angle_headline=angle.headline,
        angle_hook=angle.hook,
        angle_body=(angle.body_outline or "")[:300],
        psych_trigger=psych_trigger_text,
        cultural_context=cultural_ctx,
        date_slug=date_slug,
        topic_slug=topic_slug,
    )

    raw_response = await generate_content(VIDEO_SYSTEM_PROMPT, user_prompt, provider)
    video_data = _parse_video_response(raw_response)

    # Ensure required fields with fallbacks
    if not video_data.get("id"):
        video_data["id"] = f"fahad-ep-{date_slug}-{topic_slug}"
    if "bgMusic" not in video_data:
        video_data["bgMusic"] = "EleEnergetic, Social Media Creator_pre_sp109_s50_sb75_v3.mp3"
    if "bgMusicVolume" not in video_data:
        video_data["bgMusicVolume"] = 0.15

    return video_data
