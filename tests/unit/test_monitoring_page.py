from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow
from nexus.presentation.monitoring_page import MonitoringPage


def test_monitoring_page_builds_resource_cards() -> None:
    app = QApplication.instance() or QApplication([])
    page = MonitoringPage()

    assert set(page.metric_values) == {"cpu", "memory", "disk", "system"}
    assert all(label.text() for label in page.metric_values.values())

    page.close()
    app.processEvents()


def test_monitoring_refresh_populates_values() -> None:
    app = QApplication.instance() or QApplication([])
    page = MonitoringPage()

    page.refresh_metrics()

    assert page.metric_values["cpu"].text()
    assert page.metric_values["memory"].text()
    assert page.metric_values["disk"].text()
    assert page.metric_values["system"].text()

    page.close()
    app.processEvents()


def test_main_window_uses_real_monitoring_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert isinstance(window.pages.widget(1), MonitoringPage)

    window.close()
    app.processEvents()
