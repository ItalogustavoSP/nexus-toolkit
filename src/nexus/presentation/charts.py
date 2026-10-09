from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget


class DonutChart(QWidget):
    """Lightweight native Qt donut chart, without external plotting libraries."""

    def __init__(self, title: str, accent: str = "#8874ed") -> None:
        super().__init__()
        self.title = title
        self.accent = QColor(accent)
        self.percent = 0.0
        self.center_text = "0%"
        self.detail = "Aguardando dados"
        self.setMinimumSize(150, 160)

    def set_value(self, percent: float, center_text: str, detail: str) -> None:
        self.percent = max(0.0, min(100.0, percent))
        self.center_text = center_text
        self.detail = detail
        self.update()

    def set_accent(self, accent: str) -> None:
        self.accent = QColor(accent)
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        width = self.width()
        diameter = min(width - 34, 108)
        x = (width - diameter) / 2
        y = 12
        rect = QRectF(x, y, diameter, diameter)
        muted = self.palette().color(self.foregroundRole())
        muted.setAlpha(45)
        painter.setPen(QPen(muted, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.drawArc(rect, 0, 360 * 16)
        painter.setPen(
            QPen(
                self.accent, 12, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap
            )
        )
        painter.drawArc(rect, 90 * 16, -int(self.percent * 3.6 * 16))
        painter.setPen(self.palette().color(self.foregroundRole()))
        font = QFont(self.font())
        font.setBold(True)
        font.setPointSize(15)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, self.center_text)
        title_rect = QRectF(0, y + diameter + 8, width, 22)
        painter.setFont(QFont(self.font().family(), 10, QFont.Weight.DemiBold))
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignHCenter, self.title)
        detail_rect = QRectF(0, y + diameter + 29, width, 28)
        painter.setPen(self.palette().color(self.foregroundRole()))
        painter.setFont(QFont(self.font().family(), 8))
        painter.drawText(
            detail_rect,
            Qt.AlignmentFlag.AlignHCenter,
            self.detail,
        )


class UsageBarChart(QWidget):
    """Native column chart for CPU, memory and storage usage percentages."""

    def __init__(self) -> None:
        super().__init__()
        self.values: list[tuple[str, float]] = [
            ("CPU", 0.0),
            ("RAM", 0.0),
            ("Disco", 0.0),
        ]
        self.setMinimumHeight(205)
        self.setMinimumWidth(280)

    def set_values(self, values: list[tuple[str, float]]) -> None:
        self.values = [(name, max(0.0, min(100.0, value))) for name, value in values]
        self.update()

    def paintEvent(self, event: object) -> None:
        del event
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        foreground = self.palette().color(self.foregroundRole())
        muted = QColor(foreground)
        muted.setAlpha(155)
        accent = QColor("#8874ed")
        colors = [accent, QColor("#38a6a5"), QColor("#e3a34b")]
        margin = 24
        top = 24
        bottom = self.height() - 34
        chart_height = max(30, bottom - top)
        chart_width = max(100, self.width() - margin * 2)
        painter.setPen(QPen(muted, 1, Qt.PenStyle.DashLine))
        for tick in (0, 25, 50, 75, 100):
            y = bottom - chart_height * tick / 100
            painter.drawLine(int(margin), int(y), int(self.width() - margin), int(y))
            painter.setFont(QFont(self.font().family(), 8))
            painter.drawText(
                QRectF(0, y - 8, margin - 4, 16),
                Qt.AlignmentFlag.AlignRight,
                str(tick),
            )
        count = max(1, len(self.values))
        slot = chart_width / count
        bar_width = min(48.0, slot * 0.48)
        for index, (name, value) in enumerate(self.values):
            center = margin + slot * (index + 0.5)
            bar_height = chart_height * value / 100
            bar_rect = QRectF(
                center - bar_width / 2,
                bottom - bar_height,
                bar_width,
                bar_height,
            )
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(colors[index % len(colors)]))
            painter.drawRoundedRect(bar_rect, 6, 6)
            painter.setPen(foreground)
            painter.setFont(QFont(self.font().family(), 9, QFont.Weight.DemiBold))
            painter.drawText(
                QRectF(center - slot / 2, bottom - bar_height - 23, slot, 18),
                Qt.AlignmentFlag.AlignHCenter,
                f"{value:.0f}%",
            )
            painter.setPen(muted)
            painter.setFont(QFont(self.font().family(), 9))
            painter.drawText(
                QRectF(center - slot / 2, bottom + 8, slot, 20),
                Qt.AlignmentFlag.AlignHCenter,
                name,
            )
