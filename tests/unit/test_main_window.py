from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow


def test_main_window_builds_all_navigation_pages() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.windowTitle() == "Nexus Toolkit"
    assert window.pages.count() == 8
    assert len(window.nav_group.buttons()) == 8

    window.close()
    app.processEvents()


def test_navigation_changes_current_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window.nav_group.button(2).click()
    assert window.pages.currentIndex() == 2

    window.close()
    app.processEvents()
