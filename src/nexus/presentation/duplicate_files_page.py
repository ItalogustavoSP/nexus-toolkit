from __future__ import annotations

import csv
import hashlib
import os
import threading
from collections import defaultdict
from pathlib import Path
from typing import Callable

from PySide6.QtCore import QSettings, QThread, Qt, Signal
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


DuplicateRecord = dict[str, str | int]


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


def scan_duplicate_files(
    roots: list[str],
    cancel_event: threading.Event | None = None,
    progress_callback: Callable[[str], None] | None = None,
) -> tuple[list[DuplicateRecord], int, bool]:
    """Find byte-identical files below the selected roots without modifying them."""
    cancel_event = cancel_event or threading.Event()
    progress_callback = progress_callback or (lambda _message: None)
    candidates: dict[int, list[Path]] = defaultdict(list)
    seen_paths: set[str] = set()
    errors = 0

    for root in roots:
        if cancel_event.is_set():
            return [], errors, True
        base = Path(root)
        if not base.is_dir():
            errors += 1
            continue
        for current, dirs, files in os.walk(base, followlinks=False):
            if cancel_event.is_set():
                return [], errors, True
            dirs[:] = [
                name for name in dirs
                if not (Path(current) / name).is_symlink()
            ]
            for filename in files:
                if cancel_event.is_set():
                    return [], errors, True
                path = Path(current) / filename
                try:
                    if path.is_symlink() or not path.is_file():
                        continue
                    normalized = str(path.resolve())
                    if normalized in seen_paths:
                        continue
                    seen_paths.add(normalized)
                    candidates[path.stat().st_size].append(path)
                except OSError:
                    errors += 1

    size_groups = [paths for paths in candidates.values() if len(paths) > 1]
    total_groups = len(size_groups)
    hashed: dict[str, list[tuple[Path, int]]] = defaultdict(list)
    for group_index, paths in enumerate(size_groups, start=1):
        if cancel_event.is_set():
            return [], errors, True
        progress_callback(
            f"Comparando conteúdo dos arquivos ({group_index}/{total_groups})..."
        )
        for path in paths:
            if cancel_event.is_set():
                return [], errors, True
            try:
                digest = hashlib.sha256()
                with path.open("rb") as file_handle:
                    for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                        if cancel_event.is_set():
                            return [], errors, True
                        digest.update(chunk)
                hashed[digest.hexdigest()].append((path, path.stat().st_size))
            except OSError:
                errors += 1

    records: list[DuplicateRecord] = []
    duplicate_group = 0
    for digest, matches in sorted(hashed.items()):
        if len(matches) < 2:
            continue
        duplicate_group += 1
        for path, size in sorted(matches, key=lambda item: str(item[0]).casefold()):
            records.append(
                {
                    "group": duplicate_group,
                    "name": path.name,
                    "path": str(path),
                    "size": size,
                    "hash": digest,
                    "copies": len(matches),
                }
            )
    return records, errors, False


class _DuplicateScanThread(QThread):
    progress = Signal(str)
    completed = Signal(object, int, bool)

    def __init__(self, roots: list[str]) -> None:
        super().__init__()
        self.roots = roots
        self.cancel_event = threading.Event()

    def cancel(self) -> None:
        self.cancel_event.set()

    def run(self) -> None:
        records, errors, canceled = scan_duplicate_files(
            self.roots,
            self.cancel_event,
            self.progress.emit,
        )
        self.completed.emit(records, errors, canceled)


class DuplicateFilesPage(QWidget):
    """Find duplicate files by SHA-256 while keeping files untouched."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("duplicateFilesPage")
        self._scan_thread: _DuplicateScanThread | None = None
        self._records: list[DuplicateRecord] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(15)

        title = QLabel("Arquivos duplicados")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Encontre arquivos com conteúdo idêntico em pastas escolhidas por você."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        folder_panel = QFrame()
        folder_panel.setObjectName("panel")
        folder_layout = QVBoxLayout(folder_panel)
        folder_layout.setContentsMargins(14, 14, 14, 14)
        folder_layout.setSpacing(10)
        folder_title = QLabel("Pastas para analisar")
        folder_title.setStyleSheet("font-weight: 600;")
        folder_layout.addWidget(folder_title)

        folder_actions = QHBoxLayout()
        self.add_folder_button = QPushButton("Adicionar pasta")
        self.add_folder_button.setObjectName("secondaryButton")
        self.add_folder_button.clicked.connect(self.add_folder)
        folder_actions.addWidget(self.add_folder_button)
        self.remove_folder_button = QPushButton("Remover selecionada")
        self.remove_folder_button.setObjectName("secondaryButton")
        self.remove_folder_button.clicked.connect(self.remove_selected_folder)
        folder_actions.addWidget(self.remove_folder_button)
        folder_actions.addStretch()
        folder_layout.addLayout(folder_actions)

        self.folder_list = QListWidget()
        self.folder_list.setMinimumHeight(85)
        self.folder_list.setAlternatingRowColors(True)
        folder_layout.addWidget(self.folder_list)
        layout.addWidget(folder_panel)

        scan_actions = QHBoxLayout()
        self.scan_button = QPushButton("Analisar duplicados")
        self.scan_button.setObjectName("primaryButton")
        self.scan_button.clicked.connect(self.start_scan)
        scan_actions.addWidget(self.scan_button)
        self.cancel_button = QPushButton("Cancelar análise")
        self.cancel_button.setObjectName("secondaryButton")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_scan)
        scan_actions.addWidget(self.cancel_button)
        self.export_button = QPushButton("Exportar CSV")
        self.export_button.setObjectName("secondaryButton")
        self.export_button.setEnabled(False)
        self.export_button.clicked.connect(self.export_results)
        scan_actions.addWidget(self.export_button)
        scan_actions.addStretch()
        layout.addLayout(scan_actions)

        results_panel = QFrame()
        results_panel.setObjectName("panel")
        results_layout = QVBoxLayout(results_panel)
        results_layout.setContentsMargins(12, 12, 12, 12)
        results_layout.setSpacing(8)
        self.summary = QLabel("Adicione uma ou mais pastas e inicie a análise.")
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        results_layout.addWidget(self.summary)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Grupo", "Arquivo", "Localização", "Tamanho", "Cópias"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        for column in (0, 1, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        results_layout.addWidget(self.table, 1)
        layout.addWidget(results_panel, 1)

        note = QLabel(
            "Seguro por padrão: a análise é somente leitura. "
            "Arquivos não são apagados, movidos nem modificados. "
            "Pastas de sistema podem exigir permissões adicionais."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

    def add_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Escolher pasta para analisar")
        if not folder:
            return
        normalized = str(Path(folder).resolve())
        existing = {
            str(Path(self.folder_list.item(index).text()).resolve())
            for index in range(self.folder_list.count())
        }
        if normalized not in existing:
            self.folder_list.addItem(normalized)

    def remove_selected_folder(self) -> None:
        row = self.folder_list.currentRow()
        if row >= 0:
            self.folder_list.takeItem(row)

    def start_scan(self) -> None:
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return
        roots = [
            self.folder_list.item(index).text()
            for index in range(self.folder_list.count())
        ]
        if not roots:
            QMessageBox.information(
                self,
                "Escolha uma pasta",
                "Adicione pelo menos uma pasta antes de iniciar a análise.",
            )
            return
        self.table.setRowCount(0)
        self._records = []
        self.summary.setText("Preparando análise...")
        self.scan_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self._scan_thread = _DuplicateScanThread(roots)
        self._scan_thread.progress.connect(self.summary.setText)
        self._scan_thread.completed.connect(self._on_scan_completed)
        self._scan_thread.finished.connect(self._on_thread_finished)
        self._scan_thread.start()

    def cancel_scan(self) -> None:
        if self._scan_thread is not None and self._scan_thread.isRunning():
            self.cancel_button.setEnabled(False)
            self.summary.setText("Cancelando análise com segurança...")
            self._scan_thread.cancel()

    def _on_scan_completed(
        self, records: list[DuplicateRecord], errors: int, canceled: bool
    ) -> None:
        self._records = records
        self.table.setRowCount(len(records))
        wasted_bytes = 0
        counted_groups: set[int] = set()
        for row_index, record in enumerate(records):
            size = int(record["size"])
            values = [
                f'Grupo {record["group"]}',
                str(record["name"]),
                str(record["path"]),
                _format_size(size),
                str(record["copies"]),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 3, 4):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row_index, column, item)
            group_id = int(record["group"])
            if group_id not in counted_groups:
                wasted_bytes += size * (int(record["copies"]) - 1)
                counted_groups.add(group_id)

        groups = len({int(record["group"]) for record in records})
        self.export_button.setEnabled(bool(records))
        prefix = "Análise cancelada" if canceled else "Análise concluída"
        self.summary.setText(
            f"{prefix}: {groups} grupos, {len(records)} arquivos identificados; "
            f"potencialmente recuperável: {_format_size(wasted_bytes)}. "
            f"Itens inacessíveis: {errors}."
        )
        sound_enabled = QSettings(
            "Nexus Toolkit", "Nexus Toolkit"
        ).value("sound_effects", False, type=bool)
        if not canceled and sound_enabled:
            QApplication.beep()

    def _on_thread_finished(self) -> None:
        self.scan_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        thread = self._scan_thread
        self._scan_thread = None
        if thread is not None:
            thread.deleteLater()

    def export_results(self) -> None:
        """Export discovered duplicate paths to a CSV chosen by the user."""
        if not self._records:
            return
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar resultados",
            "nexus-arquivos-duplicados.csv",
            "Arquivo CSV (*.csv)",
        )
        if not path:
            return
        if not path.lower().endswith(".csv"):
            path += ".csv"
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as csv_file:
                writer = csv.writer(csv_file, delimiter=";")
                writer.writerow(
                    [
                        "Grupo", "Arquivo", "Caminho", "Tamanho em bytes",
                        "Cópias", "SHA-256",
                    ]
                )
                for record in self._records:
                    writer.writerow(
                        [
                            record["group"],
                            record["name"],
                            record["path"],
                            record["size"],
                            record["copies"],
                            record["hash"],
                        ]
                    )
        except OSError as error:
            QMessageBox.warning(
                self,
                "Falha ao exportar",
                f"Não foi possível salvar o CSV.\\n\\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Resultados exportados",
            f"A lista foi salva em:\\n{path}",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Stop a background scan before this page is destroyed."""
        thread = self._scan_thread
        if thread is not None and thread.isRunning():
            thread.cancel()
            thread.wait()
        super().closeEvent(event)
