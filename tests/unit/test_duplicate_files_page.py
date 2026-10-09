from pathlib import Path

from PySide6.QtWidgets import QApplication

from nexus.presentation.duplicate_files_page import (
    DuplicateFilesPage,
    scan_duplicate_files,
)
from nexus.presentation.main_window import MainWindow


def test_scanner_finds_identical_content_with_different_names(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second-copy.dat"
    different = tmp_path / "different.txt"
    first.write_bytes(b"same file content")
    second.write_bytes(b"same file content")
    different.write_bytes(b"other content")

    records, errors, canceled = scan_duplicate_files([str(tmp_path)])

    assert errors == 0
    assert canceled is False
    assert len(records) == 2
    assert {Path(str(record["path"])).name for record in records} == {
        "first.txt",
        "second-copy.dat",
    }
    assert {record["copies"] for record in records} == {2}


def test_scanner_ignores_duplicate_root_entries(tmp_path: Path) -> None:
    first = tmp_path / "file.txt"
    second = tmp_path / "copy.txt"
    first.write_text("content", encoding="utf-8")
    second.write_text("content", encoding="utf-8")

    records, errors, canceled = scan_duplicate_files(
        [str(tmp_path), str(tmp_path)]
    )

    assert errors == 0
    assert canceled is False
    assert len(records) == 2


def test_duplicate_page_and_navigation() -> None:
    app = QApplication.instance() or QApplication([])
    page = DuplicateFilesPage()
    window = MainWindow()

    assert page.table.columnCount() == 5
    assert window.pages.widget(4).__class__ is DuplicateFilesPage

    page.close()
    window.close()
    app.processEvents()
