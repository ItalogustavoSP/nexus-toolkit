from __future__ import annotations

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


class ProcessesPage(QWidget):
    """Read-only searchable view of running processes."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("processesPage")
        self._rows: list[dict[str, str | int | float]] = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        title = QLabel("Processos")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Consulte os aplicativos e serviços em execução, sem encerrar processos."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        toolbar = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por nome, PID ou usuário...")
        self.search_input.setClearButtonEnabled(True)
        self.search_input.textChanged.connect(self._apply_filter)
        toolbar.addWidget(self.search_input, 1)

        refresh = QPushButton("Atualizar lista")
        refresh.setObjectName("primaryButton")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_processes)
        toolbar.addWidget(refresh)
        layout.addLayout(toolbar)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        panel_layout.setSpacing(8)

        self.summary = QLabel("Carregando processos...")
        self.summary.setObjectName("muted")
        panel_layout.addWidget(self.summary)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["PID", "Processo", "Usuário", "CPU", "Memória"]
        )
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        for column in (0, 2, 3, 4):
            self.table.horizontalHeader().setSectionResizeMode(
                column, QHeaderView.ResizeMode.ResizeToContents
            )
        panel_layout.addWidget(self.table, 1)
        layout.addWidget(panel, 1)

        note = QLabel(
            "Modo somente leitura. O Nexus Toolkit não encerra processos nem "
            "modifica o funcionamento dos aplicativos."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.refresh_processes()

    def refresh_processes(self) -> None:
        """Read current process information and refresh the table."""
        rows: list[dict[str, str | int | float]] = []
        try:
            for process in psutil.process_iter(
                attrs=["pid", "name", "username", "memory_info"]
            ):
                try:
                    info = process.info
                    memory_info = info.get("memory_info")
                    rows.append(
                        {
                            "pid": int(info.get("pid") or 0),
                            "name": str(info.get("name") or "Desconhecido"),
                            "username": str(info.get("username") or "—"),
                            "cpu": float(process.cpu_percent(interval=None)),
                            "memory": (
                                float(memory_info.rss) if memory_info else 0.0
                            ),
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except (OSError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Falha ao consultar processos",
                f"Não foi possível atualizar a lista.\n\n{error}",
            )
            return

        self._rows = sorted(rows, key=lambda row: str(row["name"]).casefold())
        self._apply_filter()

    def _apply_filter(self, _text: str = "") -> None:
        """Display only process rows matching the search query."""
        query = self.search_input.text().strip().casefold()
        visible_rows = [
            row
            for row in self._rows
            if query
            in f'{row["pid"]} {row["name"]} {row["username"]}'.casefold()
        ]
        self.table.setRowCount(len(visible_rows))
        for row_index, process in enumerate(visible_rows):
            values = [
                str(process["pid"]),
                str(process["name"]),
                str(process["username"]),
                f'{float(process["cpu"]):.1f}%',
                f'{float(process["memory"]) / (1024 ** 2):.1f} MB',
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column in (0, 3, 4):
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                    )
                self.table.setItem(row_index, column, item)

        visible_memory = sum(float(row["memory"]) for row in visible_rows)
        self.summary.setText(
            f"{len(visible_rows)} de {len(self._rows)} processos exibidos · "
            f"Memória dos processos exibidos: "
            f"{visible_memory / (1024 ** 2):.1f} MB"
        )
