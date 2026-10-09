from __future__ import annotations

import platform
import shutil
from pathlib import Path

import psutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class MonitoringPage(QWidget):
    """Read-only overview of current machine resources."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("monitoringPage")
        self.setStyleSheet(
            """
            QLabel#pageTitle { font-size: 27px; font-weight: 700; }
            QLabel#muted { color: #9ba4b8; }
            QLabel#metricValue { font-size: 24px; font-weight: 700; color: #b7a8ff; }
            QLabel#metricTitle { font-size: 14px; font-weight: 600; }
            QFrame#metricCard {
                background: #191e2b; border: 1px solid #2c3345; border-radius: 13px;
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

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Monitoramento")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Veja informações básicas dos recursos do computador em tempo real."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        titles.addWidget(title)
        titles.addWidget(description)
        header.addLayout(titles)
        header.addStretch()

        refresh = QPushButton("Atualizar dados")
        refresh.setObjectName("primaryButton")
        refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh.clicked.connect(self.refresh_metrics)
        header.addWidget(refresh, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.metric_values: dict[str, QLabel] = {}
        grid = QGridLayout()
        grid.setSpacing(14)
        metrics = [
            ("cpu", "Processadores lógicos"),
            ("memory", "Memória RAM"),
            ("disk", "Espaço livre no disco"),
            ("system", "Sistema operacional"),
        ]
        for index, (key, label_text) in enumerate(metrics):
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(18, 18, 18, 18)
            card_layout.setSpacing(10)

            label = QLabel(label_text)
            label.setObjectName("metricTitle")
            value = QLabel("—")
            value.setObjectName("metricValue")
            value.setWordWrap(True)
            detail = QLabel("")
            detail.setObjectName("muted")
            detail.setWordWrap(True)
            self.metric_values[key] = value
            setattr(self, f"{key}_detail", detail)

            card_layout.addWidget(label)
            card_layout.addWidget(value)
            card_layout.addWidget(detail)
            card_layout.addStretch()
            grid.addWidget(card, index // 2, index % 2)
        layout.addLayout(grid)
        layout.addStretch()

        note = QLabel(
            "Somente leitura: esta tela consulta informações do sistema e não "
            "altera configurações, processos ou arquivos."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.refresh_metrics()

    def refresh_metrics(self) -> None:
        """Refresh resource information without changing system state."""
        try:
            cpu_count = psutil.cpu_count(logical=True) or 0
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk_root = Path.home().anchor or "C:\\"
            disk = shutil.disk_usage(disk_root)

            self.metric_values["cpu"].setText(f"{cpu_count} disponíveis")
            self.cpu_detail.setText(f"Uso atual aproximado: {cpu_percent:.0f}%")

            self.metric_values["memory"].setText(f"{memory.percent:.0f}% em uso")
            self.memory_detail.setText(
                f"{memory.used / (1024 ** 3):.1f} GB usados de "
                f"{memory.total / (1024 ** 3):.1f} GB"
            )

            self.metric_values["disk"].setText(
                f"{disk.free / (1024 ** 3):.1f} GB livres"
            )
            self.disk_detail.setText(
                f"Unidade {disk_root} · {disk.used / (1024 ** 3):.1f} GB usados"
            )

            self.metric_values["system"].setText(platform.system())
            self.system_detail.setText(f"{platform.release()} · {platform.machine()}")
        except (OSError, RuntimeError) as error:
            QMessageBox.warning(
                self,
                "Não foi possível consultar os recursos",
                f"Confira as permissões do sistema e tente novamente.\n\n{error}",
            )
