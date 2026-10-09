from __future__ import annotations

import os
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

MINIMUM_AGE_SECONDS = 24 * 60 * 60


@dataclass(frozen=True)
class CleanupItem:
    path: str
    size_bytes: int
    modified_at: float


def cleanup_roots() -> list[Path]:
    """Return narrowly scoped temporary folders; never scan an entire drive."""
    candidates = [Path(tempfile.gettempdir())]
    local_temp = Path.home() / "AppData" / "Local" / "Temp"
    if local_temp.exists():
        candidates.append(local_temp)
    roots: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve(strict=True)
        except OSError:
            continue
        key = os.path.normcase(str(resolved))
        if resolved.is_dir() and key not in seen:
            roots.append(resolved)
            seen.add(key)
    return roots


def scan_temporary_files(
    roots: list[Path] | None = None,
    *,
    now: float | None = None,
    minimum_age_seconds: int = MINIMUM_AGE_SECONDS,
) -> tuple[list[CleanupItem], int]:
    """Find old regular files in approved temp roots without modifying them."""
    current_time = time.time() if now is None else now
    approved_roots = cleanup_roots() if roots is None else roots
    items: list[CleanupItem] = []
    errors = 0
    seen: set[str] = set()
    for root in approved_roots:
        try:
            base = root.resolve(strict=True)
            if not base.is_dir():
                errors += 1
                continue
        except OSError:
            errors += 1
            continue
        for current, dirs, filenames in os.walk(base, followlinks=False):
            current_path = Path(current)
            dirs[:] = [
                name for name in dirs
                if not (current_path / name).is_symlink()
            ]
            for filename in filenames:
                path = current_path / filename
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    resolved = path.resolve(strict=True)
                    resolved.relative_to(base)
                    key = os.path.normcase(str(resolved))
                    if key in seen:
                        continue
                    stat = resolved.stat()
                    if current_time - stat.st_mtime < minimum_age_seconds:
                        continue
                    seen.add(key)
                    items.append(
                        CleanupItem(str(resolved), stat.st_size, stat.st_mtime)
                    )
                except (OSError, ValueError):
                    errors += 1
    items.sort(key=lambda item: item.size_bytes, reverse=True)
    return items, errors


def delete_temporary_files(
    selected_paths: list[str],
    roots: list[Path] | None = None,
    *,
    now: float | None = None,
    minimum_age_seconds: int = MINIMUM_AGE_SECONDS,
) -> tuple[int, int, int]:
    """Delete only explicitly selected old regular files inside approved roots.

    Returns the number of deleted files, bytes freed, and skipped/failed paths.
    """
    current_time = time.time() if now is None else now
    approved_roots = cleanup_roots() if roots is None else roots
    resolved_roots: list[Path] = []
    for root in approved_roots:
        try:
            resolved_roots.append(root.resolve(strict=True))
        except OSError:
            continue

    deleted = 0
    freed = 0
    skipped = 0
    seen: set[str] = set()
    for raw_path in selected_paths:
        try:
            candidate = Path(raw_path)
            if candidate.is_symlink() or not candidate.is_file():
                skipped += 1
                continue
            resolved = candidate.resolve(strict=True)
            if not any(
                root == resolved or root in resolved.parents
                for root in resolved_roots
            ):
                skipped += 1
                continue
            key = os.path.normcase(str(resolved))
            if key in seen:
                skipped += 1
                continue
            seen.add(key)
            stat = resolved.stat()
            if current_time - stat.st_mtime < minimum_age_seconds:
                skipped += 1
                continue
            resolved.unlink()
            deleted += 1
            freed += stat.st_size
        except (OSError, ValueError):
            skipped += 1
    return deleted, freed, skipped
