"""Report Writer — generates reports in multiple formats with simplified scoring.

Converts raw 6-dimension benchmark scores into team-friendly labels:
  🔥 Fire (≥48) — Ready to post
  ✅ Good (≥36) — Needs minor editing
  ⚠️ Weak (<36) — Skip or rework
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .config import settings


def _relative_time(dt: datetime | None) -> str:
    """Convert a datetime to a human-readable relative time string."""
    if dt is None:
        return ""
    try:
        now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
        diff = now - dt
        seconds = diff.total_seconds()
        if seconds < 0:
            return "just now"
        if seconds < 3600:
            return f"{int(seconds / 60)}m ago"
        if seconds < 86400:
            return f"{int(seconds / 3600)}h ago"
        if seconds < 604800:
            return f"{int(seconds / 86400)}d ago"
        return dt.strftime("%b %d, %Y")
    except Exception:
        return dt.strftime("%b %d") if dt else ""


def _short_domain(url: str) -> str:
    """Extract short domain from URL for display."""
    if not url:
        return ""
    try:
        domain = urlparse(url).netloc.replace("www.", "")
        return domain or url[:30]
    except Exception:
        return url[:30]


def simplified_grade(total_score: float) -> tuple[str, str]:
    """Convert a 6-dimension total score (0-60) to a simplified grade.

    Returns:
        Tuple of (emoji_label, action) e.g. ("🔥 Fire", "Ready to post")
    """
    if total_score >= 48:
        return "🔥 Fire", "Ready to post"
    elif total_score >= 36:
        return "✅ Good", "Needs minor editing"
    else:
        return "⚠️ Weak", "Skip or rework"


def _ensure_reports_dir() -> Path:
    """Ensure the reports directory exists."""
    reports_dir = Path(settings.reports_path)
    try:
        reports_dir.mkdir(parents=True, exist_ok=True)
        # Test write permission
        test_file = reports_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (PermissionError, OSError):
        # Fallback to /tmp if local dir has permission issues
        reports_dir = Path("/tmp/marketing-agent-reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        print(f"[ReportWriter] Using fallback reports dir: {reports_dir}")
    return reports_dir


def _grade_slug(total_score: float) -> str:
    """Get a slug for filenames based on grade."""
    if total_score >= 48:
        return "fire"
    elif total_score >= 36:
        return "good"
    else:
        return "weak"


def format_telegram_report(
    output: Any,
    benchmark_results: list[dict] | None = None,
) -> str:
    """Format a pipeline output as a Telegram-friendly message.

    Args:
        output: AgentOutput from the pipeline.
        benchmark_results: Optional list of benchmark score dicts.

    Returns:
        Formatted string for Telegram.
    """
    now = datetime.now()
    lines = [
        f"📊 *Marketing Agent Report*",
        f"📅 {now.strftime('%Y-%m-%d %H:%M')}",
        f"🔍 {output.trend_count} trends → {output.angle_count} angles",
        "",
    ]

    if benchmark_results:
        # Show top 3 angles
        sorted_results = sorted(
            benchmark_results,
            key=lambda x: x.get("total", 0),
            reverse=True,
        )
        lines.append("*🏆 Top Angles:*")
        lines.append("")

        for i, result in enumerate(sorted_results[:3], 1):
            total = result.get("total", 0)
            grade_emoji, action = simplified_grade(total)
            headline = result.get("headline", "Untitled")
            hook = result.get("hook", "")

            lines.append(f"*{i}. {grade_emoji} ({total}/60)*")
            lines.append(f"📌 {headline}")
            if hook:
                lines.append(f"🪝 _{hook[:150]}_")
            lines.append(f"→ {action}")
            lines.append("")

        # Summary stats
        totals = [r.get("total", 0) for r in benchmark_results]
        avg = sum(totals) / len(totals) if totals else 0
        fire_count = sum(1 for t in totals if t >= 48)
        good_count = sum(1 for t in totals if 36 <= t < 48)
        weak_count = sum(1 for t in totals if t < 36)

        lines.append("*📈 Summary:*")
        lines.append(f"  Avg: {avg:.1f}/60")
        lines.append(f"  🔥 {fire_count} fire | ✅ {good_count} good | ⚠️ {weak_count} weak")
    else:
        # No benchmark, list trends with links + dates
        for result in output.results[:5]:
            t = result.trend
            lines.append(f"📌 *{t.title}*")
            # Source link + date line
            meta_parts = []
            if t.url:
                meta_parts.append(f"🔗 {_short_domain(t.url) or t.source_name}")
            elif t.source_name:
                meta_parts.append(f"📰 {t.source_name}")
            if t.published_at:
                meta_parts.append(f"📅 {_relative_time(t.published_at)}")
            if meta_parts:
                lines.append(f"  {' · '.join(meta_parts)}")
            for angle in result.angles[:2]:
                lines.append(f"  → {angle.headline}")
            lines.append("")

    if output.errors:
        lines.append(f"\n⚠️ {len(output.errors)} errors occurred")

    return "\n".join(lines)


def save_markdown_report(
    output: Any,
    benchmark_results: list[dict] | None = None,
) -> Path:
    """Save a structured markdown report.

    Returns:
        Path to the saved file.
    """
    reports_dir = _ensure_reports_dir()
    now = datetime.now()

    # Determine grade
    avg_score = 0
    if benchmark_results:
        totals = [r.get("total", 0) for r in benchmark_results]
        avg_score = sum(totals) / len(totals) if totals else 0

    slug = _grade_slug(avg_score)
    filename = f"{now.strftime('%Y-%m-%d_%H%M')}_{slug}.md"
    filepath = reports_dir / filename

    grade_emoji, action = simplified_grade(avg_score)

    lines = [
        f"# Marketing Agent Report — {now.strftime('%Y-%m-%d %H:%M')}",
        "",
        f"**Grade:** {grade_emoji} (avg {avg_score:.1f}/60) — {action}",
        f"**Trends:** {output.trend_count} | **Angles:** {output.angle_count}",
        f"**Provider:** {output.provider_used.value}",
        "",
        "---",
        "",
    ]

    if benchmark_results:
        sorted_results = sorted(
            benchmark_results,
            key=lambda x: x.get("total", 0),
            reverse=True,
        )
        lines.append("## Top Angles")
        lines.append("")

        for i, result in enumerate(sorted_results, 1):
            total = result.get("total", 0)
            ge, ga = simplified_grade(total)
            lines.append(f"### {i}. {ge} — {result.get('headline', 'Untitled')} ({total}/60)")
            lines.append("")
            if result.get("hook"):
                lines.append(f"> {result['hook']}")
                lines.append("")
            lines.append(f"| CN | TD | VM | BA | CR | HP |")
            lines.append(f"|:--:|:--:|:--:|:--:|:--:|:--:|")
            lines.append(
                f"| {result.get('cn', '-')} | {result.get('td', '-')} | "
                f"{result.get('vm', '-')} | {result.get('ba', '-')} | "
                f"{result.get('cr', '-')} | {result.get('hp', '-')} |"
            )
            lines.append("")

    # Add discovered trends with links and dates
    if output.results:
        lines.append("## Discovered Trends")
        lines.append("")
        lines.append("| # | Source | Trend | Published | Score | Link |")
        lines.append("|:--:|:--:|:--|:--|:--:|:--|")
        for i, result in enumerate(output.results, 1):
            t = result.trend
            src = t.source_name or t.source.value
            pub = _relative_time(t.published_at) if t.published_at else "-"
            link = f"[🔗]({t.url})" if t.url else "-"
            score = f"{t.jack_potential:.0%}"
            lines.append(f"| {i} | {src} | {t.title[:50]} | {pub} | {score} | {link} |")
        lines.append("")

    if output.errors:
        lines.append("## Errors")
        for err in output.errors:
            lines.append(f"- {err}")

    filepath.write_text("\n".join(lines), encoding="utf-8")
    print(f"[ReportWriter] Saved markdown report: {filepath}")
    return filepath


def save_html_report(
    output: Any,
    benchmark_results: list[dict] | None = None,
) -> Path:
    """Save a standalone HTML report with inline CSS.

    Returns:
        Path to the saved file.
    """
    reports_dir = _ensure_reports_dir()
    now = datetime.now()

    avg_score = 0
    if benchmark_results:
        totals = [r.get("total", 0) for r in benchmark_results]
        avg_score = sum(totals) / len(totals) if totals else 0

    slug = _grade_slug(avg_score)
    filename = f"{now.strftime('%Y-%m-%d_%H%M')}_{slug}.html"
    filepath = reports_dir / filename

    grade_emoji, action = simplified_grade(avg_score)

    # Build angle rows
    angle_rows = ""
    if benchmark_results:
        sorted_results = sorted(
            benchmark_results,
            key=lambda x: x.get("total", 0),
            reverse=True,
        )
        for i, result in enumerate(sorted_results, 1):
            total = result.get("total", 0)
            ge, _ = simplified_grade(total)
            color = "#ff4444" if total < 36 else "#22c55e" if total >= 48 else "#f59e0b"
            angle_rows += f"""
            <div class="angle-card">
                <div class="angle-header">
                    <span class="rank">#{i}</span>
                    <span class="grade" style="color:{color}">{ge}</span>
                    <span class="score">{total}/60</span>
                </div>
                <h3>{result.get('headline', 'Untitled')}</h3>
                <p class="hook">{result.get('hook', '')}</p>
                <div class="dimensions">
                    <span>CN:{result.get('cn', '-')}</span>
                    <span>TD:{result.get('td', '-')}</span>
                    <span>VM:{result.get('vm', '-')}</span>
                    <span>BA:{result.get('ba', '-')}</span>
                    <span>CR:{result.get('cr', '-')}</span>
                    <span>HP:{result.get('hp', '-')}</span>
                </div>
            </div>"""

    # Build trends table for HTML
    trend_rows_html = ""
    if output.results:
        for i, result in enumerate(output.results, 1):
            t = result.trend
            src = t.source_name or t.source.value
            pub = _relative_time(t.published_at) if t.published_at else "-"
            link = f'<a href="{t.url}" target="_blank" style="color:#60a5fa;">🔗</a>' if t.url else "-"
            score_pct = f"{t.jack_potential:.0%}"
            trend_rows_html += f"""
            <tr>
                <td style="color:#888">{i}</td>
                <td>{src}</td>
                <td>{t.title[:60]}</td>
                <td style="color:#888">{pub}</td>
                <td>{score_pct}</td>
                <td>{link}</td>
            </tr>"""

    trends_table = ""
    if trend_rows_html:
        trends_table = f"""
        <h2 style="margin-top:2rem;color:#fff;">📡 Discovered Trends</h2>
        <table style="width:100%;border-collapse:collapse;margin-top:1rem;">
            <thead><tr style="border-bottom:1px solid #333;color:#888;text-align:left;">
                <th style="padding:0.5rem;">#</th>
                <th style="padding:0.5rem;">Source</th>
                <th style="padding:0.5rem;">Trend</th>
                <th style="padding:0.5rem;">Published</th>
                <th style="padding:0.5rem;">Score</th>
                <th style="padding:0.5rem;">Link</th>
            </tr></thead>
            <tbody style="font-size:0.9rem;">{trend_rows_html}</tbody>
        </table>"""

    html = f"""<!DOCTYPE html>
<html lang="en" dir="auto">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Marketing Report — {now.strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0f0f0f; color: #e5e5e5;
            padding: 2rem; max-width: 800px; margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            border-radius: 16px; padding: 2rem; margin-bottom: 2rem;
            border: 1px solid #333;
        }}
        .header h1 {{ font-size: 1.5rem; margin-bottom: 0.5rem; color: #fff; }}
        .meta {{ color: #888; font-size: 0.9rem; }}
        .grade-banner {{
            font-size: 1.8rem; margin: 1rem 0;
            padding: 1rem; background: #1a1a1a;
            border-radius: 12px; text-align: center;
        }}
        .angle-card {{
            background: #1a1a1a; border-radius: 12px;
            padding: 1.5rem; margin-bottom: 1rem;
            border: 1px solid #2a2a2a;
            transition: border-color 0.2s;
        }}
        .angle-card:hover {{ border-color: #444; }}
        .angle-header {{
            display: flex; align-items: center; gap: 1rem;
            margin-bottom: 0.75rem;
        }}
        .rank {{ font-size: 1.2rem; font-weight: bold; color: #666; }}
        .grade {{ font-size: 1.1rem; }}
        .score {{ color: #888; margin-left: auto; }}
        .angle-card h3 {{ font-size: 1.1rem; margin-bottom: 0.5rem; color: #fff; }}
        .hook {{ color: #999; font-style: italic; margin-bottom: 0.75rem; }}
        .dimensions {{
            display: flex; gap: 0.75rem; flex-wrap: wrap;
            font-size: 0.8rem; color: #666;
        }}
        .dimensions span {{
            background: #222; padding: 0.25rem 0.5rem;
            border-radius: 6px;
        }}
        table td {{ padding: 0.5rem; border-bottom: 1px solid #222; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Marketing Agent Report</h1>
        <p class="meta">
            {now.strftime('%Y-%m-%d %H:%M')} •
            {output.trend_count} trends • {output.angle_count} angles •
            {output.provider_used.value}
        </p>
    </div>
    <div class="grade-banner">
        {grade_emoji} Average: {avg_score:.1f}/60 — {action}
    </div>
    {angle_rows}
    {trends_table}
</body>
</html>"""

    filepath.write_text(html, encoding="utf-8")
    print(f"[ReportWriter] Saved HTML report: {filepath}")
    return filepath


def save_json_report(
    output: Any,
    benchmark_results: list[dict] | None = None,
) -> Path:
    """Save raw JSON report for programmatic use.

    Returns:
        Path to the saved file.
    """
    reports_dir = _ensure_reports_dir()
    now = datetime.now()

    avg_score = 0
    if benchmark_results:
        totals = [r.get("total", 0) for r in benchmark_results]
        avg_score = sum(totals) / len(totals) if totals else 0

    slug = _grade_slug(avg_score)
    filename = f"{now.strftime('%Y-%m-%d_%H%M')}_{slug}.json"
    filepath = reports_dir / filename

    grade_emoji, action = simplified_grade(avg_score)

    data = {
        "timestamp": now.isoformat(),
        "grade": {"emoji": grade_emoji, "action": action, "avg_score": avg_score},
        "trends": output.trend_count,
        "angles": output.angle_count,
        "provider": output.provider_used.value,
        "discovered_trends": [
            {
                "title": r.trend.title,
                "url": r.trend.url,
                "published_at": r.trend.published_at.isoformat() if r.trend.published_at else None,
                "source_name": r.trend.source_name,
                "source_type": r.trend.source.value,
                "jack_potential": r.trend.jack_potential,
            }
            for r in output.results
        ],
        "benchmark": benchmark_results or [],
        "errors": output.errors,
    }

    filepath.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[ReportWriter] Saved JSON report: {filepath}")
    return filepath
