from __future__ import annotations

import shutil

import psutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


class StoragePage(QWidget):
    """Read-only overview of mounted storage volumes."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("storagePage")
        self._rows: list[dict[str, str | int | float]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        title = QLabel("Armazenamento")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Confira as unidades montadas, a capacidade total e o espaço disponível."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Pesquisar por unidade, caminho ou sistema..."
        )
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.search_input, 1)

        refresh = QPushButton("Verificar unidades")
        refresh.setObjectName("primaryButton")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_volumes)
        toolbar.addWidget(refresh)
        layout.addLayout(toolbar)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)
        self.summary = QLabel("Consultando unidades...")
        self.summary.setObjectName("muted")
        self.summary.setWordWrap(True)
        panel_layout.addWidget(self.summary)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            [
                "Unidade / caminho",
                "Dispositivo",
                "Sistema de arquivos",
                "Total",
                "Usado",
                "Livre",
                "Uso (%)",
            ]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for column in (2, 3, 4, 5, 6):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        panel_layout.addWidget(self.table, 1)
        layout.addWidget(panel, 1)

        note = QLabel(
            "Modo somente leitura: o módulo apenas consulta informações das unidades. "
            "Nenhum arquivo é apagado, movido ou modificado."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.refresh_volumes()

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format a byte count using binary units."""
        value = float(size_bytes)
        for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
            if value < 1024 or unit == "PB":
                return f"{value:.1f} {unit}"
            value /= 1024
        return f"{value:.1f} PB"

    def refresh_volumes(self) -> None:
        """Read mounted volumes and skip drives that are unavailable."""
        rows: list[dict[str, str | int | float]] = []
        try:
            partitions = psutil.disk_partitions(all=False)
        except (OSError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Falha ao consultar armazenamento",
                f"Não foi possível listar as unidades.\n\n{error}",
            )
            return

        for partition in partitions:
            mountpoint = partition.mountpoint
            try:
                usage = shutil.disk_usage(mountpoint)
            except OSError:
                continue
            rows.append(
                {
                    "mountpoint": mountpoint,
                    "device": partition.device or "—",
                    "filesystem": partition.fstype or "Desconhecido",
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percent": usage.used / usage.total * 100 if usage.total else 0.0,
                }
            )

        self._rows = sorted(rows, key=lambda row: str(row["mountpoint"]).casefold())
        self._apply_filter()

    def _apply_filter(self, _text: str = "") -> None:
        """Filter volume rows by mount point, device, or filesystem."""
        query = self.search_input.text().strip().casefold()
        visible = [
            row
            for row in self._rows
            if query
            in f'{row["mountpoint"]} {row["device"]} {row["filesystem"]}'.casefold()
        ]
        self.table.setRowCount(len(visible))
        for row_index, volume in enumerate(visible):
            values = [
                str(volume["mountpoint"]),
                str(volume["device"]),
                str(volume["filesystem"]),
                self._format_size(int(volume["total"])),
                self._format_size(int(volume["used"])),
                self._format_size(int(volume["free"])),
                f'{float(volume["percent"]):.1f}%',
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column >= 3:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row_index, column, item)

        total_bytes = sum(int(row["total"]) for row in visible)
        free_bytes = sum(int(row["free"]) for row in visible)
        self.summary.setText(
            f"{len(visible)} de {len(self._rows)} unidades exibidas · "
            f"Capacidade exibida: {self._format_size(total_bytes)} · "
            f"Espaço livre: {self._format_size(free_bytes)}"
        )
        if not self._rows:
            self.summary.setText(
                "Nenhuma unidade acessível foi encontrada. Tente verificar novamente."
            )
