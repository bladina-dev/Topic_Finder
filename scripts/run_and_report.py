"""Run and Report — Standalone entrypoint for GitHub Actions.

Runs the full pipeline: scan trends → generate angles → benchmark → save reports → send Telegram.
Exit code 0 on success, 1 on failure.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import settings
from src.pipeline import run_pipeline
from src.report_writer import (
    format_telegram_report,
    save_html_report,
    save_json_report,
    save_markdown_report,
)
from src.telegram_bot import send_report, send_text


async def main():
    """Run the full pipeline and report."""
    print("=" * 60)
    print("🚀 Marketing Agent — Pipeline Run")
    print("=" * 60)

    try:
        # Step 1: Run the pipeline
        print("\n[1/4] Running pipeline...")
        output = await run_pipeline(mock=False)
        print(f"  → {output.trend_count} trends, {output.angle_count} angles")

        # Step 2: Benchmark (if we have angles)
        benchmark_results = None
        if output.angle_count > 0:
            print("\n[2/4] Running benchmark...")
            try:
                from src.benchmark import run_benchmark
                benchmark_results = await run_benchmark(output)
                print(f"  → Benchmarked {len(benchmark_results)} angles")
            except Exception as e:
                print(f"  → Benchmark failed (non-fatal): {e}")

        # Step 3: Save reports
        print("\n[3/4] Saving reports...")
        md_path = save_markdown_report(output, benchmark_results)
        html_path = save_html_report(output, benchmark_results)
        json_path = save_json_report(output, benchmark_results)
        print(f"  → MD:   {md_path}")
        print(f"  → HTML: {html_path}")
        print(f"  → JSON: {json_path}")

        # Step 4: Send to Telegram
        print("\n[4/4] Sending to Telegram...")
        report_text = format_telegram_report(output, benchmark_results)
        sent = await send_report(report_text)
        if sent:
            print("  → ✅ Report sent to Telegram!")
        else:
            print("  → ⚠️ Telegram send failed (check token/chat_id)")

        # Step 5: Save to Obsidian vault
        if settings.obsidian_vault_path:
            print("\n[5/5] Saving to Obsidian vault...")
            try:
                from src.obsidian_sync import ensure_vault, push_angles as obsidian_push
                vault_path = ensure_vault()
                obsidian_count = obsidian_push(output, benchmark_results)
                print(f"  → [Obsidian] {obsidian_count} angles saved to {vault_path}/angles/")
            except Exception as e:
                print(f"  → ⚠️ Obsidian save failed (non-fatal): {e}")

        # Summary
        print("\n" + "=" * 60)
        if output.errors:
            print(f"⚠️ Completed with {len(output.errors)} errors")
            for err in output.errors:
                print(f"  - {err}")
        else:
            print("✅ Pipeline completed successfully!")
        print("=" * 60)

        return 0

    except Exception as e:
        print(f"\n❌ Pipeline failed: {e}")

        # Try to notify via Telegram
        try:
            await send_text(f"❌ Marketing Agent pipeline failed:\n\n{str(e)[:500]}")
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
