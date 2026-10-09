from __future__ import annotations

import platform
import shutil
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import psutil
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from nexus.presentation.charts import DonutChart, UsageBarChart


class DashboardPage(QWidget):
    """Live local-system dashboard with native Qt charts."""

    def __init__(self, open_page: Callable[[int], None]) -> None:
        super().__init__()
        self.open_page = open_page
        self.setObjectName("dashboardPage")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("dashboardContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(30, 26, 30, 30)
        layout.setSpacing(18)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        header = QHBoxLayout()
        titles = QVBoxLayout()
        title = QLabel("Centro de comando")
        title.setObjectName("pageTitle")
        subtitle = QLabel("Tudo sobre seu computador, em um só lugar.")
        subtitle.setObjectName("muted")
        titles.addWidget(title)
        titles.addWidget(subtitle)
        header.addLayout(titles)
        header.addStretch()
        refresh_button = QPushButton("Atualizar agora  ↻")
        refresh_button.setObjectName("secondaryButton")
        refresh_button.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_button.clicked.connect(self.refresh)
        header.addWidget(refresh_button, alignment=Qt.AlignmentFlag.AlignTop)
        self.status = QLabel("● MONITORAMENTO ATIVO")
        self.status.setObjectName("statusPill")
        self.status.setStyleSheet(
            "QLabel { background: #126b3a; color: #ffffff; "
            "padding: 9px 12px; border-radius: 8px; font-weight: 700; }"
        )
        self._status_blink_on = True
        self.status_timer = QTimer(self)
        self.status_timer.setInterval(650)
        self.status_timer.timeout.connect(self._blink_status)
        self.status_timer.start()
        header.addWidget(self.status, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        # Compact welcome strip leaves more room for live system indicators.
        welcome_strip = QFrame()
        welcome_strip.setObjectName("hero")
        welcome_layout = QHBoxLayout(welcome_strip)
        welcome_layout.setContentsMargins(18, 12, 18, 12)
        welcome_text = QLabel(
            "Visão geral do sistema  ·  Métricas atualizadas automaticamente"
        )
        welcome_text.setObjectName("sectionTitle")
        welcome_layout.addWidget(welcome_text)
        welcome_layout.addStretch()
        open_monitoring = QPushButton("Abrir monitoramento  →")
        open_monitoring.setObjectName("primaryButton")
        open_monitoring.clicked.connect(lambda: self.open_page(1))
        welcome_layout.addWidget(open_monitoring)
        layout.addWidget(welcome_strip)

        self.metrics: dict[str, QLabel] = {}
        self.metric_details: dict[str, QLabel] = {}
        metric_row = QHBoxLayout()
        for key, name in [
            ("cpu", "PROCESSADOR"), ("memory", "MEMÓRIA RAM"),
            ("disk", "ARMAZENAMENTO"), ("processes", "PROCESSOS"),
        ]:
            card = QFrame()
            card.setObjectName("metricCard")
            card_layout = QVBoxLayout(card)
            card_layout.setContentsMargins(15, 14, 15, 14)
            eyebrow = QLabel(name)
            eyebrow.setObjectName("metricEyebrow")
            value = QLabel("—")
            value.setObjectName("metricValue")
            detail = QLabel("Atualização automática")
            detail.setObjectName("muted")
            self.metrics[key] = value
            self.metric_details[key] = detail
            card_layout.addWidget(eyebrow)
            card_layout.addWidget(value)
            card_layout.addWidget(detail)
            metric_row.addWidget(card, 1)
        layout.addLayout(metric_row)

        chart_title = QLabel("Saúde dos recursos")
        chart_title.setObjectName("sectionTitle")
        self.updated = QLabel("Consultando recursos…")
        self.updated.setObjectName("muted")
        chart_header = QHBoxLayout()
        chart_header.addWidget(chart_title)
        chart_header.addStretch()
        chart_header.addWidget(self.updated)
        layout.addLayout(chart_header)

        donuts = QHBoxLayout()
        self.donuts: dict[str, DonutChart] = {}
        for key, title_text, color in [
            ("cpu", "CPU", "#8874ed"),
            ("memory", "Memória", "#38a6a5"),
            ("disk", "Disco", "#e3a34b"),
        ]:
            panel = QFrame()
            panel.setObjectName("panel")
            panel_layout = QVBoxLayout(panel)
            chart = DonutChart(title_text, color)
            self.donuts[key] = chart
            panel_layout.addWidget(chart)
            donuts.addWidget(panel, 1)
        layout.addLayout(donuts)

        bar_panel = QFrame()
        bar_panel.setObjectName("panel")
        bar_layout = QVBoxLayout(bar_panel)
        bar_layout.setContentsMargins(16, 14, 16, 12)
        bar_title = QLabel("Comparativo de utilização")
        bar_title.setObjectName("sectionTitle")
        bar_description = QLabel("Percentual de uso · escala de 0 a 100%")
        bar_description.setObjectName("muted")
        self.bars = UsageBarChart()
        bar_layout.addWidget(bar_title)
        bar_layout.addWidget(bar_description)
        bar_layout.addWidget(self.bars)
        layout.addWidget(bar_panel)

        bottom = QHBoxLayout()
        system_panel = QFrame()
        system_panel.setObjectName("panel")
        system_layout = QVBoxLayout(system_panel)
        system_title = QLabel("Informações do sistema")
        system_title.setObjectName("sectionTitle")
        self.system_info = QLabel("Carregando dados locais…")
        self.system_info.setObjectName("muted")
        self.system_info.setWordWrap(True)
        self.system_info.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        system_layout.addWidget(system_title)
        system_layout.addWidget(self.system_info)
        bottom.addWidget(system_panel, 3)

        actions_panel = QFrame()
        actions_panel.setObjectName("panel")
        actions_layout = QVBoxLayout(actions_panel)
        actions_title = QLabel("Acesso rápido")
        actions_title.setObjectName("sectionTitle")
        actions_layout.addWidget(actions_title)
        for label, index in [
            ("Monitoramento", 1), ("Processos", 2), ("Armazenamento", 3),
            ("Arquivos duplicados", 4), ("Relatórios", 5),
        ]:
            action = QPushButton(label + "  ↗")
            action.setObjectName("quickActionButton")
            action.setCursor(Qt.CursorShape.PointingHandCursor)
            action.clicked.connect(
                lambda checked=False, page=index: self.open_page(page)
            )
            actions_layout.addWidget(action)
        bottom.addWidget(actions_panel, 2)
        layout.addLayout(bottom)

        self.timer = QTimer(self)
        self.timer.setInterval(4000)
        self.timer.timeout.connect(self.refresh)
        self.timer.start()
        self.refresh()

    def _blink_status(self) -> None:
        if "MONITORAMENTO ATIVO" not in self.status.text():
            return
        self._status_blink_on = not self._status_blink_on
        background = "#16803f" if self._status_blink_on else "#0b4d2b"
        self.status.setStyleSheet(
            "QLabel { "
            f"background: {background}; color: #ffffff; "
            "padding: 9px 12px; border-radius: 8px; font-weight: 700; }"
        )

    def refresh(self) -> None:
        try:
            cpu = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            root = Path.home().anchor or "C:\\"
            disk = shutil.disk_usage(root)
            disk_percent = disk.used / disk.total * 100 if disk.total else 0.0
            count = len(psutil.pids())
            ram_used, ram_total = memory.used / (1024 ** 3), memory.total / (1024 ** 3)
            disk_used, disk_total = disk.used / (1024 ** 3), disk.total / (1024 ** 3)
            for key, value in [
                ("cpu", f"{cpu:.0f}%"), ("memory", f"{memory.percent:.0f}%"),
                ("disk", f"{disk_percent:.0f}%"), ("processes", str(count)),
            ]:
                self.metrics[key].setText(value)
            self.metric_details["cpu"].setText("Uso atual do processador")
            self.metric_details["memory"].setText(
                f"{ram_used:.1f} de {ram_total:.1f} GB em uso"
            )
            self.metric_details["disk"].setText(
                f"{disk.free / (1024 ** 3):.1f} GB livres"
            )
            self.metric_details["processes"].setText("Processos detectados no sistema")
            self.donuts["cpu"].set_value(cpu, f"{cpu:.0f}%", "Uso do processador")
            self.donuts["memory"].set_value(
                memory.percent,
                f"{memory.percent:.0f}%",
                f"{ram_used:.1f} / {ram_total:.1f} GB",
            )
            self.donuts["disk"].set_value(
                disk_percent,
                f"{disk_percent:.0f}%",
                f"{disk_used:.0f} / {disk_total:.0f} GB",
            )
            self.bars.set_values(
                [("CPU", cpu), ("RAM", memory.percent), ("Disco", disk_percent)]
            )
            uptime = max(0, int(datetime.now().timestamp() - psutil.boot_time()))
            hours, minutes = divmod(uptime // 60, 60)
            days, hours = divmod(hours, 24)
            uptime_text = f"{days}d {hours}h" if days else f"{hours}h {minutes}min"
            processor = platform.processor().strip() or (
                f"{psutil.cpu_count() or 0} CPUs lógicas"
            )
            self.system_info.setText(
                f"Sistema: {platform.system()} {platform.release()}\n"
                f"Arquitetura: {platform.machine()}\n"
                f"Processador: {processor}\n"
                f"Memória: {ram_total:.1f} GB instalada\n"
                f"Unidade principal: {root} · {disk_total:.1f} GB\n"
                f"Tempo ligado: {uptime_text}"
            )
            self.updated.setText("Atualizado às " + datetime.now().strftime("%H:%M:%S"))
            self.status.setText("● MONITORAMENTO ATIVO")
        except (OSError, RuntimeError, ValueError) as error:
            self.status.setText("● DADOS PARCIAIS")
            self.status_timer.stop()
            self.status.setStyleSheet(
                "QLabel { background: #8a5b12; color: #ffffff; "
                "padding: 9px 12px; border-radius: 8px; font-weight: 700; }"
            )
            self.system_info.setText(
                f"Não foi possível ler todos os dados locais.\n{error}"
            )
