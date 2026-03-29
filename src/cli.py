"""CLI for the Marketing Agent — powered by Typer."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

app = typer.Typer(
    name="marketing-agent",
    help="🚀 Autonomous Marketing Agent with Psychological Triggers",
    rich_markup_mode="rich",
)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

console = Console()


@app.command()
def scan(
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock trend data"),
    max_results: int = typer.Option(15, "--max", "-n", help="Max trends to return"),
    sources: str = typer.Option("", "--sources", "-s", help="Comma-separated source names to scan"),
):
    """Scan current trending topics from KSA/Gulf sources (all 3 layers)."""
    from .pipeline import run_pipeline

    console.print("\n[bold cyan]🔍 Scanning Trends...[/bold cyan]\n")

    source_names = [sources] if sources else None
    output = asyncio.run(run_pipeline(
        mock=mock,
        max_trends=max_results,
        angles_per_trend=0,
        source_names=source_names,
    ))

    trends = [r.trend for r in output.results]

    if not trends:
        console.print("[yellow]No trends found.[/yellow]")
        return

    table = Table(title="📊 Trending Topics", show_lines=True)
    table.add_column("#", style="dim", width=3)
    table.add_column("Title", style="bold white", min_width=30)
    table.add_column("Source", style="cyan", width=15)
    table.add_column("Jack ⚡", justify="center", width=8)

    for i, trend in enumerate(trends, 1):
        score = f"{'🟢' if trend.jack_potential >= 0.8 else '🟡' if trend.jack_potential >= 0.6 else '🔴'} {trend.jack_potential:.0%}"
        table.add_row(str(i), trend.title, trend.source.value, score)

    console.print(table)
    console.print(f"\n[dim]Found {len(trends)} trends[/dim]\n")


@app.command()
def generate(
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock data for trends and angles"),
    max_trends: int = typer.Option(8, "--max-trends", "-t", help="Max trends"),
    angles: int = typer.Option(3, "--angles", "-a", help="Angles per trend"),
    provider: str = typer.Option("", "--provider", "-p", help="AI provider: gemini, claude, lmstudio"),
    sources: str = typer.Option("", "--sources", "-s", help="Comma-separated source names to scan"),
):
    """Run the full pipeline — scan trends → generate content angles."""
    from .models import AIProvider
    from .pipeline import run_pipeline

    console.print("\n[bold cyan]🚀 Running Marketing Agent Pipeline...[/bold cyan]\n")

    ai_provider = None
    if provider:
        try:
            ai_provider = AIProvider(provider)
        except ValueError:
            console.print(f"[red]Unknown provider: {provider}. Use: gemini, claude, lmstudio[/red]")
            raise typer.Exit(1)

    output = asyncio.run(run_pipeline(
        mock=mock,
        max_trends=max_trends,
        angles_per_trend=angles,
        provider=ai_provider,
        source_names=[sources] if sources else None,
    ))

    if output.errors:
        for err in output.errors:
            console.print(f"[red]⚠ {err}[/red]")

    for result in output.results:
        trend = result.trend
        source_emoji = {"twitter_ksa": "🐦", "google_trends": "📈", "gulf_news": "📰", "cultural": "🎭"}.get(trend.source.value, "📌")

        console.print(Panel(
            f"[bold]{trend.title}[/bold]\n"
            f"[dim]{trend.description[:100]}[/dim]",
            title=f"{source_emoji} {trend.source.value.upper()} | Jack: {trend.jack_potential:.0%}",
            border_style="cyan",
        ))

        for j, angle in enumerate(result.angles, 1):
            triggers_str = ", ".join(
                f"[magenta]{t.type.value}[/magenta]" for t in angle.psych_triggers
            ) or "[dim]none[/dim]"

            console.print(f"  [bold green]Angle {j}:[/bold green] {angle.headline}")
            console.print(f"  [yellow]Hook:[/yellow] {angle.hook}")
            console.print(f"  [dim]Platform:[/dim] {angle.platform.value} | [dim]Triggers:[/dim] {triggers_str} | [dim]Brand fit:[/dim] {angle.brand_alignment_score:.0%}")
            console.print()

    console.print(f"[bold green]✅ Done:[/bold green] {output.trend_count} trends, {output.angle_count} angles\n")


@app.command()
def upload(
    file: Path = typer.Argument(..., help="Path to brand PDF file"),
    brand_name: str = typer.Option("", "--name", "-n", help="Brand name"),
):
    """Upload a brand strategy/marketing plan PDF."""
    from .brand_ingestion import ingest_brand_pdf

    if not file.exists():
        console.print(f"[red]File not found: {file}[/red]")
        raise typer.Exit(1)

    if not str(file).lower().endswith(".pdf"):
        console.print("[red]Only PDF files are supported.[/red]")
        raise typer.Exit(1)

    console.print(f"\n[cyan]📄 Ingesting: {file.name}...[/cyan]")

    result = ingest_brand_pdf(file, brand_name=brand_name)

    console.print("[green]✅ Ingested successfully![/green]")
    console.print(f"   Pages processed: {result['pages_processed']}")
    console.print(f"   Chunks stored: {result['chunks_stored']}\n")


@app.command()
def video(
    mock: bool = typer.Option(False, "--mock", "-m", help="Use mock data"),
    max_trends: int = typer.Option(4, "--max-trends", "-t", help="Max trends"),
    angles: int = typer.Option(3, "--angles", "-a", help="Angles per trend"),
    pick: int = typer.Option(0, "--pick", "-k", help="Which angle to convert (0=best by brand_alignment_score)"),
    output_dir: Path = typer.Option(Path("output/videos"), "--output", "-o", help="Output directory"),
    provider: str = typer.Option("", "--provider", "-p", help="AI provider: gemini, claude, lmstudio"),
    sources: str = typer.Option("", "--sources", "-s", help="Comma-separated source names to scan"),
    voiceover: bool = typer.Option(False, "--voiceover", help="Generate ElevenLabs Arabic voiceover MP3"),
    mock_voiceover: bool = typer.Option(False, "--mock-voiceover", help="Generate placeholder voiceover TXT (no API key needed)"),
    voice_id: str = typer.Option("pNInz6obpgDQGcFmaJgB", "--voice-id", help="ElevenLabs voice ID"),
    bg_music: bool = typer.Option(False, "--bg-music", help="Generate AI background music via MiniMax"),
    mock_music: bool = typer.Option(False, "--mock-music", help="Use placeholder music (no API key needed)"),
    assemble: bool = typer.Option(False, "--assemble", help="Print FFmpeg assemble command after generating all assets"),
):
    """Full pipeline: scan trends → generate angles → convert best angle to video JSON."""
    import json

    from .models import AIProvider
    from .pipeline import run_pipeline
    from .video_converter import angle_to_video_data

    console.print("\n[bold cyan]🔍 Scanning Trends...[/bold cyan]\n")

    ai_provider = None
    if provider:
        try:
            ai_provider = AIProvider(provider)
        except ValueError:
            console.print(f"[red]Unknown provider: {provider}. Use: gemini, claude, lmstudio[/red]")
            raise typer.Exit(1)

    output = asyncio.run(run_pipeline(
        mock=mock,
        max_trends=max_trends,
        angles_per_trend=angles,
        provider=ai_provider,
        source_names=[sources] if sources else None,
    ))

    if output.errors:
        for err in output.errors:
            console.print(f"[red]⚠ {err}[/red]")

    # Collect all angles from all trends
    all_angles = []
    for result in output.results:
        for angle in result.angles:
            all_angles.append((angle, result.trend))

    if not all_angles:
        console.print("[yellow]No angles generated — nothing to convert.[/yellow]")
        raise typer.Exit(1)

    # Pick the angle: --pick index, or best by brand_alignment_score
    if pick > 0:
        idx = min(pick - 1, len(all_angles) - 1)
        chosen_angle, chosen_trend = all_angles[idx]
        console.print(f"[dim]Using angle #{pick} (of {len(all_angles)} total)[/dim]")
    else:
        chosen_angle, chosen_trend = max(all_angles, key=lambda x: x[0].brand_alignment_score)
        console.print(f"[dim]Best angle: {chosen_angle.headline[:60]} (score: {chosen_angle.brand_alignment_score:.0%})[/dim]")

    console.print("\n[bold cyan]🎬 Converting best angle to video script...[/bold cyan]\n")

    try:
        video_data = asyncio.run(angle_to_video_data(chosen_angle, chosen_trend, ai_provider, mock=mock))
    except Exception as e:
        console.print(f"[red]Video conversion failed: {e}[/red]")
        raise typer.Exit(1)

    # Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    video_id = video_data.get("id", "fahad-video")
    output_path = output_dir / f"{video_id}.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(video_data, f, ensure_ascii=False, indent=2)

    console.print(f"[bold green]✅ Video script saved:[/bold green] {output_path}\n")

    # Optional voiceover generation
    voiceover_path: str | None = None
    if voiceover or mock_voiceover:
        import os as _os

        from .voiceover import generate_voiceover

        if voiceover and not mock_voiceover and not _os.environ.get("ELEVENLABS_API_KEY"):
            console.print("[yellow]⚠️ ELEVENLABS_API_KEY not set — skipping voiceover[/yellow]")
        else:
            try:
                vo_result = asyncio.run(
                    generate_voiceover(
                        video_data,
                        voice_id=voice_id,
                        output_dir=Path("output/voiceovers"),
                        mock=mock_voiceover,
                    )
                )
                voiceover_path = str(vo_result)
            except Exception as e:
                console.print(f"[red]Voiceover generation failed: {e}[/red]")

    # Optional background music generation
    music_path: str | None = None
    if bg_music or mock_music:
        from .music_generator import _generate_music_prompt, generate_bg_music

        music_prompt = _generate_music_prompt(video_data)
        music_output = str(Path("output/music") / f"{video_id}_bg.mp3")
        try:
            music_path = asyncio.run(
                generate_bg_music(music_prompt, music_output, mock=mock_music)
            )
        except Exception as e:
            console.print(f"[red]Music generation failed: {e}[/red]")

    # Pipeline summary
    if assemble or bg_music or mock_music:
        vo_display = voiceover_path or "—"
        mu_display = music_path or "—"
        console.print("\n[bold]📋 Pipeline Summary:[/bold]")
        console.print(f"   📄 VideoData:  {output_path}")
        console.print(f"   🎤 Voiceover:  {vo_display}")
        console.print(f"   🎵 Music:      {mu_display}")
        if assemble:
            rendered_mp4 = f"out/{video_id}.mp4"
            final_mp4 = f"output/final/{video_id}.mp4"
            console.print(
                f"   🎬 To assemble: python -m src.cli assemble"
                f" --video {rendered_mp4}"
                f" --voiceover {vo_display}"
                f" --music {mu_display}"
                f" --output {final_mp4}"
            )

    remotion_dir = '~/Downloads/SamCV\\ /video'
    console.print("[bold]To render:[/bold]")
    console.print(f'  cd "{remotion_dir}"')
    console.print(f'  npx remotion render FahadYouTubeShort --props="$(pwd)/{output_path}" out/{video_id}.mp4\n')


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="API host"),
    port: int = typer.Option(8000, "--port", "-p", help="API port"),
):
    """Start the FastAPI server."""
    import uvicorn

    console.print("\n[bold cyan]🌐 Starting Marketing Agent API...[/bold cyan]")
    console.print(f"[dim]→ http://{host}:{port}[/dim]")
    console.print(f"[dim]→ Docs: http://{host}:{port}/docs[/dim]\n")

    uvicorn.run("src.api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    app()
