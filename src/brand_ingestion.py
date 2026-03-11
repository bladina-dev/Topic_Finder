"""Brand Ingestion — parses brand PDFs and stores in ChromaDB."""

from __future__ import annotations

import os
from pathlib import Path

from .config import settings
from .models import BrandProfile


def _ensure_dirs() -> None:
    """Ensure brand data directories exist."""
    Path(settings.chromadb_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.brand_docs_path).mkdir(parents=True, exist_ok=True)


def _get_chroma_client():
    """Get or create a ChromaDB persistent client."""
    import chromadb

    _ensure_dirs()
    return chromadb.PersistentClient(path=settings.chromadb_path)


def _get_collection(client=None):
    """Get or create the brand documents collection."""
    if client is None:
        client = _get_chroma_client()
    return client.get_or_create_collection(
        name="brand_documents",
        metadata={"description": "Brand strategy and marketing documents"},
    )


def extract_text_from_pdf(pdf_path: str | Path) -> list[str]:
    """Extract text from a PDF file, returning one string per page.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        List of strings, one per page.
    """
    from PyPDF2 import PdfReader

    reader = PdfReader(str(pdf_path))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())
    return pages


def chunk_text(pages: list[str], chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split page texts into overlapping chunks for embedding.

    Args:
        pages: List of page text strings.
        chunk_size: Target characters per chunk.
        overlap: Overlap characters between chunks.

    Returns:
        List of text chunks.
    """
    chunks = []
    for page in pages:
        words = page.split()
        current_chunk = []
        current_len = 0

        for word in words:
            current_chunk.append(word)
            current_len += len(word) + 1

            if current_len >= chunk_size:
                chunks.append(" ".join(current_chunk))
                # Keep overlap
                overlap_words = current_chunk[-(overlap // 5):]
                current_chunk = list(overlap_words)
                current_len = sum(len(w) + 1 for w in current_chunk)

        if current_chunk:
            chunks.append(" ".join(current_chunk))

    return chunks


def ingest_brand_pdf(pdf_path: str | Path, brand_name: str = "") -> dict:
    """Ingest a brand PDF into ChromaDB.

    Args:
        pdf_path: Path to the PDF file.
        brand_name: Optional brand name.

    Returns:
        Dict with ingestion stats.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Extract text
    pages = extract_text_from_pdf(pdf_path)
    if not pages:
        return {"filename": pdf_path.name, "pages_processed": 0, "chunks_stored": 0}

    # Chunk text
    chunks = chunk_text(pages)

    # Store in ChromaDB
    collection = _get_collection()
    doc_ids = [f"{pdf_path.stem}_{i}" for i in range(len(chunks))]
    metadatas = [
        {"source": pdf_path.name, "brand": brand_name, "chunk_index": i}
        for i in range(len(chunks))
    ]

    collection.add(
        documents=chunks,
        ids=doc_ids,
        metadatas=metadatas,
    )

    return {
        "filename": pdf_path.name,
        "pages_processed": len(pages),
        "chunks_stored": len(chunks),
    }


def query_brand_context(query: str, n_results: int = 5) -> str:
    """Query brand documents for relevant context.

    Args:
        query: The query string (e.g., a trend title).
        n_results: Number of results to return.

    Returns:
        Combined context string from matching chunks.
    """
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return "No brand documents have been uploaded yet."

        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
        )

        if results and results.get("documents"):
            docs = results["documents"][0]
            return "\n\n---\n\n".join(docs)

        return "No relevant brand context found."
    except Exception as e:
        return f"Brand context unavailable: {e}"


def get_brand_profile() -> BrandProfile:
    """Build a BrandProfile from stored brand documents.

    Returns a summary BrandProfile by querying stored chunks.
    """
    try:
        collection = _get_collection()
        if collection.count() == 0:
            return BrandProfile()

        # Get all documents for a holistic view
        all_docs = collection.get(limit=20)
        if not all_docs or not all_docs.get("documents"):
            return BrandProfile()

        full_text = " ".join(all_docs["documents"][:10])

        # Extract brand name from metadata if available
        brand_name = ""
        if all_docs.get("metadatas"):
            for meta in all_docs["metadatas"]:
                if meta.get("brand"):
                    brand_name = meta["brand"]
                    break

        return BrandProfile(
            name=brand_name,
            summary=full_text[:1000],
            doc_ids=[d for d in (all_docs.get("ids") or [])],
        )
    except Exception:
        return BrandProfile()


def clear_brand_data() -> bool:
    """Clear all brand data from ChromaDB."""
    try:
        client = _get_chroma_client()
        client.delete_collection("brand_documents")
        return True
    except Exception:
        return False
