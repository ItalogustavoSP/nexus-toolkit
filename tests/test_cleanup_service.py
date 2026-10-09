from __future__ import annotations

import os
import time
from pathlib import Path

from nexus.services.cleanup_service import (
    MINIMUM_AGE_SECONDS,
    delete_temporary_files,
    scan_temporary_files,
)


def _set_age(path: Path, age_seconds: int) -> None:
    timestamp = time.time() - age_seconds
    os.utime(path, (timestamp, timestamp))


def test_scan_finds_only_old_files_inside_approved_root(tmp_path: Path) -> None:
    old_file = tmp_path / "old.tmp"
    old_file.write_bytes(b"old temporary data")
    recent_file = tmp_path / "recent.tmp"
    recent_file.write_bytes(b"recent")
    _set_age(old_file, MINIMUM_AGE_SECONDS + 10)

    items, errors = scan_temporary_files([tmp_path])

    assert [Path(item.path).name for item in items] == ["old.tmp"]
    assert items[0].size_bytes == len(b"old temporary data")
    assert errors == 0
    assert old_file.exists()
    assert recent_file.exists()


def test_delete_removes_only_selected_old_file(tmp_path: Path) -> None:
    selected = tmp_path / "selected.tmp"
    selected.write_bytes(b"remove me")
    other = tmp_path / "other.tmp"
    other.write_bytes(b"keep me")
    _set_age(selected, MINIMUM_AGE_SECONDS + 10)
    _set_age(other, MINIMUM_AGE_SECONDS + 10)

    deleted, freed, skipped = delete_temporary_files(
        [str(selected)], [tmp_path]
    )

    assert (deleted, freed, skipped) == (1, len(b"remove me"), 0)
    assert not selected.exists()
    assert other.exists()


def test_delete_rejects_recent_and_outside_paths(tmp_path: Path) -> None:
    approved = tmp_path / "approved"
    approved.mkdir()
    recent = approved / "recent.tmp"
    recent.write_text("recent", encoding="utf-8")
    outside = tmp_path / "outside.tmp"
    outside.write_text("outside", encoding="utf-8")
    _set_age(outside, MINIMUM_AGE_SECONDS + 10)

    deleted, freed, skipped = delete_temporary_files(
        [str(recent), str(outside)], [approved]
    )

    assert deleted == 0
    assert freed == 0
    assert skipped == 2
    assert recent.exists()
    assert outside.exists()


def test_delete_rejects_duplicate_paths(tmp_path: Path) -> None:
    old_file = tmp_path / "old.tmp"
    old_file.write_bytes(b"single")
    _set_age(old_file, MINIMUM_AGE_SECONDS + 10)

    deleted, freed, skipped = delete_temporary_files(
        [str(old_file), str(old_file)], [tmp_path]
    )

    assert deleted == 1
    assert freed == len(b"single")
    assert skipped == 1
