from PySide6.QtWidgets import QApplication

from nexus.presentation.dashboard_page import DashboardPage
from nexus.presentation.main_window import MainWindow


def test_dashboard_builds_live_metrics_and_charts() -> None:
    app = QApplication.instance() or QApplication([])
    dashboard = DashboardPage(lambda _index: None)
    assert set(dashboard.metrics) == {"cpu", "memory", "disk", "processes"}
    assert set(dashboard.donuts) == {"cpu", "memory", "disk"}
    assert dashboard.system_info.text()
    dashboard.close()
    app.processEvents()


def test_main_window_uses_dashboard_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    assert isinstance(window.pages.widget(0), DashboardPage)
    window.close()
    app.processEvents()
