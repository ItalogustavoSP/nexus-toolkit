from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nexus.services.cleanup_service import (
    CleanupItem,
    delete_temporary_files,
    scan_temporary_files,
)


def _format_size(size_bytes: int) -> str:
    value = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if value < 1024 or unit == "PB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} PB"


class _CleanupScanThread(QThread):
    completed = Signal(object, int)

    def run(self) -> None:
        items, errors = scan_temporary_files()
        self.completed.emit(items, errors)


class CleanupPage(QWidget):
    """Review and safely remove old files from temporary folders."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("cleanupPage")
        self._items: list[CleanupItem] = []
        self._scan_thread: _CleanupScanThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(15)

        title = QLabel("Limpeza e otimização")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Analise arquivos temporários antigos e escolha exatamente o que "
            "deseja remover. A análise não apaga nem modifica arquivos."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        overview = QFrame()
        overview.setObjectName("hero")
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(18, 16, 18, 16)
        overview_title = QLabel("Limpeza segura de arquivos temporários")
        overview_title.setObjectName("sectionTitle")
        overview_text = QLabel(
            "Por segurança, apenas arquivos com mais de 24 horas em pastas "
            "temporárias reconhecidas são listados. Pastas e links simbólicos "
            "não são removidos."
        )
        overview_text.setObjectName("muted")
        overview_text.setWordWrap(True)
        overview_layout.addWidget(overview_title)
        overview_layout.addWidget(overview_text)
        layout.addWidget(overview)

        actions = QHBoxLayout()
        self.scan_button = QPushButton("Analisar arquivos")
        self.scan_button.setObjectName("primaryButton")
        self.scan_button.clicked.connect(self.start_scan)
        actions.addWidget(self.scan_button)
        self.select_all_button = QPushButton("Selecionar todos")
        self.select_all_button.setObjectName("secondaryButton")
        self.select_all_button.clicked.connect(self.select_all)
        self.select_all_button.setEnabled(False)
        actions.addWidget(self.select_all_button)
        self.clear_selection_button = QPushButton("Limpar seleção")
        self.clear_selection_button.setObjectName("secondaryButton")
        self.clear_selection_button.clicked.connect(self.clear_selection)
        self.clear_selection_button.setEnabled(False)
        actions.addWidget(self.clear_selection_button)
        self.clean_button = QPushButton("Remover selecionados")
        self.clean_button.setObjectName("primaryButton")
        self.clean_button.clicked.connect(self.clean_selected)
        self.clean_button.setEnabled(False)
        actions.addWidget(self.clean_button)
        actions.addStretch()
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)
        self.summary = QLabel("Clique em “Analisar arquivos” para começar.")
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        panel_layout.addWidget(self.summary)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(
            ["Selecionar", "Arquivo", "Última modificação", "Tamanho"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for column in (0, 2, 3):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        self.table.itemChanged.connect(self._update_selection_summary)
        panel_layout.addWidget(self.table, 1)
        layout.addWidget(panel, 1)

        note = QLabel(
            "A limpeza exige seleção e confirmação explícitas. Arquivos em uso, "
            "recentes ou fora das pastas temporárias aprovadas serão ignorados. "
            "O módulo não limpa o Registro, caches de navegador nem arquivos do "
            "Windows Update."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

    @staticmethod
    def _selected_size(items: list[CleanupItem]) -> int:
        return sum(item.size_bytes for item in items)

    def start_scan(self) -> None:
        if self._scan_thread is not None and self._scan_thread.isRunning():
            return
        self.scan_button.setEnabled(False)
        self.clean_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)
        self.summary.setText("Analisando pastas temporárias...")
        self._scan_thread = _CleanupScanThread()
        self._scan_thread.completed.connect(self._on_scan_completed)
        self._scan_thread.finished.connect(self._on_scan_finished)
        self._scan_thread.start()

    def _on_scan_completed(self, items: list[CleanupItem], errors: int) -> None:
        self._items = items
        self.table.blockSignals(True)
        self.table.setRowCount(len(items))
        for row, item in enumerate(items):
            checkbox = QCheckBox()
            checkbox.setToolTip("Marque para incluir este arquivo na limpeza")
            checkbox.setAccessibleName(f"Selecionar {Path(item.path).name}")
            self.table.setCellWidget(row, 0, checkbox)
            name_item = QTableWidgetItem(Path(item.path).name)
            name_item.setToolTip(item.path)
            name_item.setData(Qt.ItemDataRole.UserRole, item.path)
            self.table.setItem(row, 1, name_item)
            modified = datetime.fromtimestamp(item.modified_at).strftime(
                "%d/%m/%Y %H:%M"
            )
            self.table.setItem(row, 2, QTableWidgetItem(modified))
            self.table.setItem(
                row, 3, QTableWidgetItem(_format_size(item.size_bytes))
            )
        self.table.blockSignals(False)
        self.select_all_button.setEnabled(bool(items))
        self.clear_selection_button.setEnabled(bool(items))
        self.clean_button.setEnabled(bool(items))
        self.summary.setText(
            f"Análise concluída: {len(items)} arquivos antigos encontrados · "
            f"{_format_size(self._selected_size(items))} disponíveis para revisão. "
            f"Erros de acesso: {errors}. Nenhum arquivo foi apagado."
        )

    def _on_scan_finished(self) -> None:
        self.scan_button.setEnabled(True)
        thread = self._scan_thread
        self._scan_thread = None
        if thread is not None:
            thread.deleteLater()

    def _checkboxes(self) -> list[QCheckBox]:
        return [
            checkbox
            for row in range(self.table.rowCount())
            if isinstance(
                (checkbox := self.table.cellWidget(row, 0)), QCheckBox
            )
        ]

    def select_all(self) -> None:
        for checkbox in self._checkboxes():
            checkbox.setChecked(True)
        self._update_selection_summary()

    def clear_selection(self) -> None:
        for checkbox in self._checkboxes():
            checkbox.setChecked(False)
        self._update_selection_summary()

    def _update_selection_summary(self, _item: QTableWidgetItem | None = None) -> None:
        selected_rows = [
            row
            for row in range(self.table.rowCount())
            if isinstance(self.table.cellWidget(row, 0), QCheckBox)
            and self.table.cellWidget(row, 0).isChecked()
        ]
        selected_size = sum(self._items[row].size_bytes for row in selected_rows)
        self.summary.setText(
            f"{len(self._items)} arquivos encontrados · "
            f"{len(selected_rows)} selecionados · "
            f"{_format_size(selected_size)} selecionados para remoção. "
            "A exclusão só ocorre após confirmação."
        )

    def clean_selected(self) -> None:
        selected = [
            self._items[row]
            for row in range(self.table.rowCount())
            if isinstance(self.table.cellWidget(row, 0), QCheckBox)
            and self.table.cellWidget(row, 0).isChecked()
        ]
        if not selected:
            QMessageBox.information(
                self, "Nenhum arquivo selecionado",
                "Marque pelo menos um arquivo para continuar.",
            )
            return
        total = self._selected_size(selected)
        answer = QMessageBox.question(
            self,
            "Confirmar limpeza",
            f"Remover {len(selected)} arquivos temporários selecionados "
            f"({_format_size(total)})?\n\n"
            "Essa ação não pode ser desfeita. Arquivos em uso serão ignorados.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted, freed, skipped = delete_temporary_files(
            [item.path for item in selected]
        )
        self.summary.setText(
            f"Limpeza finalizada: {deleted} arquivos removidos · "
            f"{_format_size(freed)} liberados · {skipped} ignorados ou "
            "indisponíveis. Faça uma nova análise para atualizar a lista."
        )
        self.clean_button.setEnabled(False)
        self.select_all_button.setEnabled(False)
        self.clear_selection_button.setEnabled(False)

    def closeEvent(self, event) -> None:
        thread = self._scan_thread
        if thread is not None and thread.isRunning():
            thread.wait()
        super().closeEvent(event)
