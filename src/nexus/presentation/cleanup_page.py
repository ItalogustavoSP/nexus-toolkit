from __future__ import annotations

from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
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

PAGE_SIZE = 250


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
    """Conservative, paginated review of old files in temporary folders."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("cleanupPage")
        self._items: list[CleanupItem] = []
        self._selected_paths: set[str] = set()
        self._page_index = 0
        self._scan_errors = 0
        self._scan_thread: _CleanupScanThread | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(15)

        title = QLabel("Limpeza inteligente")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Encontre candidatos à limpeza sem apagar nada durante a análise. "
            "O Nexus usa regras conservadoras; nenhum método consegue garantir "
            "que todo arquivo temporário esteja sem uso."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        overview = QFrame()
        overview.setObjectName("hero")
        overview_layout = QVBoxLayout(overview)
        overview_layout.setContentsMargins(18, 16, 18, 16)
        overview_title = QLabel("Análise conservadora")
        overview_title.setObjectName("sectionTitle")
        overview_text = QLabel(
            "Somente arquivos dentro de pastas temporárias reconhecidas, com "
            "pelo menos 7 dias sem modificação, entram na lista. Pastas, links "
            "simbólicos, documentos pessoais e unidades inteiras não são alvo. "
            "Revise a seleção antes de qualquer exclusão."
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
        self.select_page_button = QPushButton("Selecionar página")
        self.select_page_button.setObjectName("secondaryButton")
        self.select_page_button.clicked.connect(self.select_current_page)
        self.select_page_button.setEnabled(False)
        actions.addWidget(self.select_page_button)
        self.clear_page_button = QPushButton("Limpar seleção da página")
        self.clear_page_button.setObjectName("secondaryButton")
        self.clear_page_button.clicked.connect(self.clear_current_page)
        self.clear_page_button.setEnabled(False)
        actions.addWidget(self.clear_page_button)
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
        self.table.itemChanged.connect(self._on_item_changed)
        panel_layout.addWidget(self.table, 1)

        pager = QHBoxLayout()
        self.previous_button = QPushButton("Página anterior")
        self.previous_button.clicked.connect(self.previous_page)
        self.previous_button.setEnabled(False)
        pager.addWidget(self.previous_button)
        self.page_label = QLabel("Página 0 de 0")
        self.page_label.setObjectName("muted")
        pager.addWidget(self.page_label)
        self.next_button = QPushButton("Próxima página")
        self.next_button.clicked.connect(self.next_page)
        self.next_button.setEnabled(False)
        pager.addWidget(self.next_button)
        pager.addStretch()
        panel_layout.addLayout(pager)
        layout.addWidget(panel, 1)

        note = QLabel(
            "A análise não modifica arquivos. A exclusão exige seleção manual e "
            "confirmação. Arquivos em uso ou inacessíveis podem ser ignorados. "
            "O Nexus não limpa Registro, caches de navegador nem Windows Update."
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
        self.select_page_button.setEnabled(False)
        self.clear_page_button.setEnabled(False)
        self.summary.setText("Analisando pastas temporárias em segundo plano...")
        self._scan_thread = _CleanupScanThread()
        self._scan_thread.completed.connect(self._on_scan_completed)
        self._scan_thread.finished.connect(self._on_scan_finished)
        self._scan_thread.start()

    def _on_scan_completed(self, items: list[CleanupItem], errors: int) -> None:
        self._items = items
        self._selected_paths.clear()
        self._page_index = 0
        self._scan_errors = errors
        self._render_page()
        self._update_summary(
            f"Análise concluída: {len(items)} candidatos · "
            f"{_format_size(self._selected_size(items))} encontrados · "
            f"erros de acesso: {errors}. Nenhum arquivo foi apagado."
        )

    def _on_scan_finished(self) -> None:
        self.scan_button.setEnabled(True)
        thread = self._scan_thread
        self._scan_thread = None
        if thread is not None:
            thread.deleteLater()

    def _render_page(self) -> None:
        start = self._page_index * PAGE_SIZE
        visible = self._items[start : start + PAGE_SIZE]
        self.table.blockSignals(True)
        self.table.setRowCount(len(visible))
        for row, item in enumerate(visible):
            checkbox_item = QTableWidgetItem()
            checkbox_item.setFlags(
                Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
            )
            checkbox_item.setCheckState(
                Qt.CheckState.Checked
                if item.path in self._selected_paths
                else Qt.CheckState.Unchecked
            )
            checkbox_item.setData(Qt.ItemDataRole.UserRole, item.path)
            self.table.setItem(row, 0, checkbox_item)
            name_item = QTableWidgetItem(Path(item.path).name)
            name_item.setToolTip(item.path)
            name_item.setData(Qt.ItemDataRole.UserRole, item.path)
            self.table.setItem(row, 1, name_item)
            modified = datetime.fromtimestamp(item.modified_at).strftime(
                "%d/%m/%Y %H:%M"
            )
            self.table.setItem(row, 2, QTableWidgetItem(modified))
            self.table.setItem(row, 3, QTableWidgetItem(_format_size(item.size_bytes)))
        self.table.blockSignals(False)
        pages = (len(self._items) + PAGE_SIZE - 1) // PAGE_SIZE
        self.page_label.setText(
            f"Página {self._page_index + 1 if pages else 0} de {pages} "
            f"· {len(visible)} arquivos nesta página"
        )
        self.previous_button.setEnabled(self._page_index > 0)
        self.next_button.setEnabled(start + PAGE_SIZE < len(self._items))
        has_items = bool(self._items)
        self.select_page_button.setEnabled(has_items)
        self.clear_page_button.setEnabled(has_items)
        self.clean_button.setEnabled(bool(self._selected_paths))

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 0:
            return
        path = item.data(Qt.ItemDataRole.UserRole)
        if not path:
            return
        if item.checkState() == Qt.CheckState.Checked:
            self._selected_paths.add(path)
        else:
            self._selected_paths.discard(path)
        self._update_summary()

    def _update_summary(self, prefix: str = "") -> None:
        selected = [item for item in self._items if item.path in self._selected_paths]
        base = (
            f"{len(self._items)} candidatos · {len(selected)} selecionados · "
            f"{_format_size(self._selected_size(selected))} selecionados para "
            "revisão. Nenhum arquivo será removido sem confirmação."
        )
        self.summary.setText(f"{prefix}\n{base}" if prefix else base)
        self.clean_button.setEnabled(bool(selected))

    def select_current_page(self) -> None:
        start = self._page_index * PAGE_SIZE
        for item in self._items[start : start + PAGE_SIZE]:
            self._selected_paths.add(item.path)
        self._render_page()
        self._update_summary()

    def clear_current_page(self) -> None:
        start = self._page_index * PAGE_SIZE
        for item in self._items[start : start + PAGE_SIZE]:
            self._selected_paths.discard(item.path)
        self._render_page()
        self._update_summary()

    def previous_page(self) -> None:
        if self._page_index > 0:
            self._page_index -= 1
            self._render_page()

    def next_page(self) -> None:
        if (self._page_index + 1) * PAGE_SIZE < len(self._items):
            self._page_index += 1
            self._render_page()

    def clean_selected(self) -> None:
        selected = [
            item for item in self._items if item.path in self._selected_paths
        ]
        if not selected:
            QMessageBox.information(
                self, "Nenhum arquivo selecionado",
                "Marque os arquivos que deseja revisar antes de continuar.",
            )
            return
        total = self._selected_size(selected)
        answer = QMessageBox.question(
            self,
            "Confirmar limpeza",
            f"Remover {len(selected)} arquivos selecionados "
            f"({_format_size(total)})?\n\n"
            "Esta ação não pode ser desfeita. Continue apenas se revisou "
            "os caminhos e entende que esses arquivos podem ser removidos.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        deleted, freed, skipped = delete_temporary_files(
            [item.path for item in selected]
        )
        self._selected_paths.clear()
        self.clean_button.setEnabled(False)
        self._update_summary(
            f"Limpeza concluída: {deleted} removidos · "
            f"{_format_size(freed)} liberados · {skipped} ignorados. "
            "Execute uma nova análise para atualizar a lista."
        )

    def closeEvent(self, event) -> None:
        thread = self._scan_thread
        if thread is not None and thread.isRunning():
            thread.wait()
        super().closeEvent(event)
