"""Source Manager — CSV-based source list management.

Marketing teams manage sources via CSV files in sources/.
Editable in Excel, Google Sheets, or any text editor.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Optional

from .models import SourceEntry

# Default sources directory (relative to project root)
SOURCES_DIR = Path(__file__).parent.parent / "sources"


def _ensure_sources_dir() -> Path:
    """Ensure the sources directory exists."""
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)
    return SOURCES_DIR


def list_source_files() -> list[dict[str, str | int]]:
    """List available CSV source files with metadata.

    Returns:
        List of dicts with 'name', 'path', and 'count' (number of sources).
    """
    sources_dir = _ensure_sources_dir()
    files = []
    for csv_file in sorted(sources_dir.glob("*.csv")):
        try:
            count = sum(1 for _ in csv_file.open()) - 1  # minus header
            count = max(0, count)
        except Exception:
            count = 0
        files.append({
            "name": csv_file.stem,
            "path": str(csv_file),
            "count": count,
        })
    return files


def load_sources(name: str) -> list[SourceEntry]:
    """Load sources from a CSV file by name.

    Args:
        name: Name of the CSV file (without .csv extension).

    Returns:
        List of SourceEntry objects.

    Raises:
        FileNotFoundError: If the CSV file doesn't exist.
        ValueError: If the CSV is missing required columns.
    """
    csv_path = SOURCES_DIR / f"{name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(
            f"Source file '{name}.csv' not found in {SOURCES_DIR}. "
            f"Available: {[f['name'] for f in list_source_files()]}"
        )

    required_cols = {"vertical", "type", "handle_or_domain"}
    entries: list[SourceEntry] = []
    seen: set[str] = set()

    with csv_path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Validate columns
        if reader.fieldnames is None:
            raise ValueError(f"CSV file '{name}.csv' is empty.")
        missing = required_cols - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"CSV '{name}.csv' missing required columns: {missing}. "
                f"Expected: vertical, type, handle_or_domain, label"
            )

        for row_num, row in enumerate(reader, start=2):
            handle = row.get("handle_or_domain", "").strip()
            if not handle:
                continue

            # Deduplicate
            key = handle.lower().lstrip("@")
            if key in seen:
                print(f"[SourceManager] Warning: duplicate '{handle}' at row {row_num}, skipping.")
                continue
            seen.add(key)

            entries.append(SourceEntry(
                vertical=row.get("vertical", "").strip().lower(),
                type=row.get("type", "").strip().lower(),
                handle_or_domain=handle,
                label=row.get("label", "").strip(),
                youtube_handle=row.get("youtube_handle", "").strip(),
            ))

    print(f"[SourceManager] Loaded {len(entries)} sources from '{name}.csv'")
    return entries


def get_domains_for_scan(
    names: list[str],
    verticals: Optional[list[str]] = None,
) -> list[str]:
    """Get flat list of domains for Tavily include_domains.

    Args:
        names: List of source file names to load.
        verticals: Optional filter — only include these verticals.

    Returns:
        List of domain strings.
    """
    domains: list[str] = []
    for name in names:
        entries = load_sources(name)
        for entry in entries:
            if entry.type == "domain":
                if verticals is None or entry.vertical in verticals:
                    # Clean domain: remove protocol, trailing slashes
                    domain = re.sub(r"^https?://", "", entry.handle_or_domain)
                    domain = domain.rstrip("/")
                    domains.append(domain)
    return list(dict.fromkeys(domains))  # dedupe, preserve order


def get_handles_for_scan(
    names: list[str],
    verticals: Optional[list[str]] = None,
) -> list[str]:
    """Get flat list of social media handles.

    Args:
        names: List of source file names to load.
        verticals: Optional filter — only include these verticals.

    Returns:
        List of handle strings (with @ prefix).
    """
    handles: list[str] = []
    for name in names:
        entries = load_sources(name)
        for entry in entries:
            if entry.type in ("twitter", "instagram", "tiktok"):
                if verticals is None or entry.vertical in verticals:
                    handle = entry.handle_or_domain
                    if not handle.startswith("@"):
                        handle = f"@{handle}"
                    handles.append(handle)
    return list(dict.fromkeys(handles))  # dedupe, preserve order


def get_youtube_handles_for_scan(
    names: list[str],
    verticals: Optional[list[str]] = None,
) -> list[str]:
    """Get flat list of YouTube handles to scan.

    Args:
        names: List of source file names to load.
        verticals: Optional filter — only include these verticals.

    Returns:
        List of YouTube handle strings (e.g. "@ChannelName").
    """
    youtube_handles: list[str] = []
    for name in names:
        try:
            entries = load_sources(name)
            for entry in entries:
                handle = entry.youtube_handle
                if handle:
                    if verticals is None or entry.vertical in verticals:
                        if not handle.startswith("@") and not handle.startswith("UC"):
                            handle = f"@{handle}"
                        youtube_handles.append(handle)
        except Exception as e:
            print(f"[SourceManager] Error loading {name} for YouTube handles: {e}")
            
    return list(dict.fromkeys(youtube_handles))  # dedupe, preserve order


def add_source(
    file_name: str,
    vertical: str,
    source_type: str,
    handle_or_domain: str,
    label: str = "",
) -> None:
    """Append a new source to a CSV file.

    Args:
        file_name: CSV file name (without extension).
        vertical: Category (tech, finance, lifestyle, etc.).
        source_type: Type (twitter, domain, instagram, etc.).
        handle_or_domain: The handle or domain to add.
        label: Human-readable label.
    """
    csv_path = SOURCES_DIR / f"{file_name}.csv"

    # Create file with header if it doesn't exist
    if not csv_path.exists():
        _ensure_sources_dir()
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["vertical", "type", "handle_or_domain", "label"])

    # Check for duplicates
    existing = load_sources(file_name)
    key = handle_or_domain.lower().lstrip("@")
    for entry in existing:
        if entry.handle_or_domain.lower().lstrip("@") == key:
            print(f"[SourceManager] '{handle_or_domain}' already exists in '{file_name}.csv'")
            return

    # Append
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        fieldnames = ["vertical", "type", "handle_or_domain", "label", "youtube_handle"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writerow({
            "vertical": vertical.lower(),
            "type": source_type.lower(),
            "handle_or_domain": handle_or_domain,
            "label": label,
            "youtube_handle": "",
        })

    print(f"[SourceManager] Added '{handle_or_domain}' to '{file_name}.csv'")
