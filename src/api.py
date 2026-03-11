"""FastAPI REST API for the Marketing Agent."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

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
from .pipeline import run_pipeline
from .trend_scanner import scan_trends

app = FastAPI(
    title="Marketing Agent API",
    description="Autonomous Marketing Agent with Psychological Triggers",
    version="0.1.0",
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


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        provider=settings.default_ai_provider,
    )


@app.get("/api/trends")
async def get_trends(mock: bool = False, max_results: int = 8):
    """Scan and return current trends."""
    try:
        trends = await scan_trends(mock=mock, max_results=max_results)
        return {"trends": [t.model_dump() for t in trends], "count": len(trends)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/angles/generate")
async def generate_angles(request: GenerateRequest):
    """Run the full pipeline — scan trends and generate angles."""
    global _latest_output
    try:
        output = await run_pipeline(
            mock=request.mock,
            max_trends=request.max_trends,
            angles_per_trend=request.angles_per_trend,
            provider=request.provider,
            platforms=request.platforms,
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


@app.post("/api/brands/upload", response_model=BrandUploadResponse)
async def upload_brand_pdf(file: UploadFile = File(...), brand_name: str = ""):
    """Upload a brand strategy/marketing plan PDF."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Save uploaded file
    upload_dir = Path(settings.brand_docs_path)
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    try:
        content = await file.read()
        file_path.write_bytes(content)

        # Ingest into ChromaDB
        result = ingest_brand_pdf(file_path, brand_name=brand_name)

        # Get updated brand profile
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
