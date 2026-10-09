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
        self.setStyleSheet(
            """
            QLabel#pageTitle { font-size: 27px; font-weight: 700; }
            QLabel#muted { color: #9ba4b8; }
            QFrame#panel {
                background: #191e2b; border: 1px solid #2c3345; border-radius: 13px;
            }
            QLineEdit {
                background: #10131b; color: #edf0f7; border: 1px solid #343b50;
                border-radius: 8px; padding: 10px;
            }
            QTableWidget {
                background: #151925; alternate-background-color: #191e2b;
                color: #edf0f7; gridline-color: #2c3345;
                border: 1px solid #2c3345; border-radius: 8px;
                selection-background-color: #39345f;
            }
            QHeaderView::section {
                background: #202538; color: #c6baff; border: none;
                border-bottom: 1px solid #343b50; padding: 9px;
                font-weight: 600;
            }
            QPushButton#primaryButton {
                background: #8874ed; color: #ffffff; border: none;
                border-radius: 8px; padding: 10px 15px; font-weight: 600;
            }
            QPushButton#primaryButton:hover { background: #9a88f5; }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        title = QLabel("Armazenamento")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Confira as unidades montadas, o sistema de arquivos e a capacidade disponível."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por unidade, caminho ou sistema...")
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
        self.summary = QLabel("Consultando unidades...")
        self.summary.setObjectName("muted")
        panel_layout.addWidget(self.summary)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["Unidade / caminho", "Dispositivo", "Sistema de arquivos", "Total", "Usado", "Livre"]
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
        for column in (2, 3, 4, 5):
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
        for partition in psutil.disk_partitions(all=False):
            mountpoint = partition.mountpoint
            try:
                usage = shutil.disk_usage(mountpoint)
            except (OSError, PermissionError):
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
        if not rows:
            self.summary.setText(
                "Nenhuma unidade acessível foi encontrada. Tente verificar novamente."
            )

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
                f'{volume["filesystem"]} · {float(volume["percent"]):.1f}% usado',
                self._format_size(int(volume["total"])),
                self._format_size(int(volume["used"])),
                self._format_size(int(volume["free"])),
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column >= 3:
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row_index, column, item)
        self.summary.setText(
            f"{len(visible)} de {len(self._rows)} unidades acessíveis exibidas"
        )
