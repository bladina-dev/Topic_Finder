"""FastAPI REST API for the Marketing Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from .brand_ingestion import (
    clear_brand_data,
    get_brand_profile,
    ingest_brand_pdf,
    query_brand_context,
)
from .config import settings
from .models import (
    AgentOutput,
    BrandProfile,
    BrandUploadResponse,
    GenerateRequest,
    HealthResponse,
)
from .obsidian_sync import update_angle_status
from .pipeline import run_pipeline
from .source_manager import (
    add_source,
    list_source_files,
    load_seed_keywords,
    load_sources,
)
from .trend_scanner import scan_trends

app = FastAPI(
    title="Marketing Agent API",
    description="Autonomous Marketing Agent with Psychological Triggers",
    version="0.5.1",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store for latest results
_latest_output: AgentOutput | None = None

_ENV_PATH = Path(__file__).parent.parent / ".env"

_SECRET_FIELDS = {
    "tavily_api_key",
    "serpapi_api_key",
    "google_api_key",
    "youtube_data_api_key",
    "anthropic_api_key",
    "notion_api_key",
    "telegram_bot_token",
    "elevenlabs_api_key",
    "azure_speech_key",
}


def _mask(value: str) -> str:
    if not value:
        return ""
    return f"****{value[-4:]}"


def _update_env_file(updates: dict[str, str]) -> None:
    """Read .env, update/append key=value pairs, write back preserving comments."""
    lines: list[str] = []
    if _ENV_PATH.exists():
        lines = _ENV_PATH.read_text(encoding="utf-8").splitlines()

    updated_keys: set[str] = set()
    new_lines: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            new_lines.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            new_lines.append(f"{key}={updates[key]}")
            updated_keys.add(key)
        else:
            new_lines.append(line)

    for key, value in updates.items():
        if key not in updated_keys:
            new_lines.append(f"{key}={value}")

    _ENV_PATH.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Reflect updates in the live settings object
    for key, value in updates.items():
        if hasattr(settings, key):
            # cast booleans
            field = settings.model_fields.get(key)
            if field and field.annotation is bool:
                setattr(settings, key, value.lower() in ("1", "true", "yes"))
            else:
                setattr(settings, key, value)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check with API status."""
    return HealthResponse(
        status="healthy",
        version="0.5.1",
        provider=settings.default_ai_provider,
        apis={
            "tavily": bool(settings.tavily_api_key),
            "serpapi": bool(settings.serpapi_api_key),
            "youtube": bool(settings.youtube_data_api_key or settings.google_api_key),
            "notion": bool(settings.notion_api_key),
            "telegram": bool(settings.telegram_bot_token),
        },
    )


# ---------------------------------------------------------------------------
# Scan (trends only)
# ---------------------------------------------------------------------------

@app.get("/api/scan")
async def scan(mock: bool = False, max_results: int = 15, sources: str = ""):
    """Run the pipeline in scan-only mode (no angle generation)."""
    try:
        source_names = [sources] if sources else None
        output = await run_pipeline(
            mock=mock,
            max_trends=max_results,
            angles_per_trend=0,
            source_names=source_names,
        )
        return {
            "trends": [t.trend.model_dump() for t in output.results],
            "count": len(output.results),
            "errors": output.errors,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Trends (legacy)
# ---------------------------------------------------------------------------

@app.get("/api/trends")
async def get_trends(mock: bool = False, max_results: int = 8):
    """Scan and return current trends."""
    try:
        trends = await scan_trends(mock=mock, max_results=max_results)
        return {"trends": [t.model_dump() for t in trends], "count": len(trends)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# Angles
# ---------------------------------------------------------------------------

@app.post("/api/angles/generate")
async def generate_angles(request: GenerateRequest):
    """Run the full pipeline — scan trends and generate angles."""
    global _latest_output
    try:
        source_names = [request.sources] if request.sources else None
        output = await run_pipeline(
            mock=request.mock,
            max_trends=request.max_trends,
            angles_per_trend=request.angles_per_trend,
            provider=request.provider,
            platforms=request.platforms,
            source_names=source_names,
        )
        _latest_output = output
        return output.model_dump()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/angles")
async def get_latest_angles():
    """Get the latest generated angles."""
    if _latest_output is None:
        return {"message": "No angles generated yet. Run /api/angles/generate first."}
    return _latest_output.model_dump()


@app.post("/api/angles/status")
async def set_angle_status(body: dict[str, str]):
    """Update the status of an angle in the Obsidian vault."""
    filename_stem = body.get("filename_stem", "")
    status = body.get("status", "")
    if status not in ("approved", "skipped", "new"):
        raise HTTPException(status_code=400, detail="status must be one of: approved, skipped, new")
    try:
        ok = update_angle_status(settings.obsidian_vault_path, filename_stem, status)
        if not ok:
            raise HTTPException(status_code=400, detail="Failed to update angle status")
        return {"status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------

@app.get("/api/sources")
async def get_sources():
    """List all available source CSV files."""
    return {"sources": list_source_files()}


@app.get("/api/sources/{name}")
async def get_source_entries(name: str):
    """Get entries from a source CSV file."""
    try:
        entries = load_sources(name)
        return {
            "name": name,
            "entries": [e.model_dump() for e in entries],
            "count": len(entries),
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/sources/{name}/add")
async def add_source_entry(name: str, body: dict[str, str]):
    """Add a new entry to a source CSV file."""
    vertical = body.get("vertical", "")
    source_type = body.get("source_type", "")
    handle_or_domain = body.get("handle_or_domain", "")
    label = body.get("label", "")
    if not handle_or_domain:
        raise HTTPException(status_code=400, detail="handle_or_domain is required")
    add_source(
        file_name=name,
        vertical=vertical,
        source_type=source_type,
        handle_or_domain=handle_or_domain,
        label=label,
    )
    return {"status": "added", "handle_or_domain": handle_or_domain}


@app.get("/api/sources/{name}/seeds")
async def get_seed_keywords(name: str):
    """Get seed keywords from a CSV file."""
    try:
        keywords = load_seed_keywords(name)
        return {"name": name, "keywords": keywords}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@app.get("/api/settings")
async def get_settings():
    """Return current settings with API keys masked."""
    result: dict[str, Any] = {}
    for field in _SECRET_FIELDS:
        value = getattr(settings, field, "")
        result[field] = _mask(value)
    result["default_ai_provider"] = settings.default_ai_provider
    result["agent_timezone"] = settings.agent_timezone
    result["default_sources"] = settings.default_sources
    result["youtube_scan_enabled"] = settings.youtube_scan_enabled
    result["influencer_scan_enabled"] = settings.influencer_scan_enabled
    result["google_trends_enabled"] = settings.google_trends_enabled
    result["reports_path"] = settings.reports_path
    result["obsidian_vault_path"] = settings.obsidian_vault_path
    return result


@app.post("/api/settings")
async def update_settings(body: dict[str, str]):
    """Update settings — skips masked placeholder values."""
    updates = {
        k: v for k, v in body.items()
        if not str(v).startswith("****")
    }
    if updates:
        _update_env_file(updates)
    return {"status": "updated", "keys_updated": list(updates.keys())}


# ---------------------------------------------------------------------------
# Brands
# ---------------------------------------------------------------------------

@app.post("/api/brands/upload", response_model=BrandUploadResponse)
async def upload_brand_pdf(file: UploadFile = File(...), brand_name: str = ""):
    """Upload a brand strategy/marketing plan PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    upload_dir = Path(settings.brand_docs_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    try:
        content = await file.read()
        file_path.write_bytes(content)
        result = ingest_brand_pdf(file_path, brand_name=brand_name)
        profile = get_brand_profile()
        return BrandUploadResponse(
            filename=file.filename,
            pages_processed=result["pages_processed"],
            chunks_stored=result["chunks_stored"],
            brand_profile=profile,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {e}")


@app.get("/api/brands/profile", response_model=BrandProfile)
async def get_brand():
    """Get the current brand profile."""
    return get_brand_profile()


@app.delete("/api/brands")
async def delete_brand_data():
    """Clear all brand data."""
    success = clear_brand_data()
    if success:
        return {"message": "Brand data cleared."}
    raise HTTPException(status_code=500, detail="Failed to clear brand data.")


@app.get("/api/brands/context")
async def get_context(query: str = "general brand overview"):
    """Query brand context by topic."""
    context = query_brand_context(query)
    return {"query": query, "context": context}
