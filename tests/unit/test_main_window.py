from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow


def test_main_window_builds_all_navigation_pages() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.windowTitle() == "Nexus Toolkit — Visão geral"
    assert window.pages.count() == 8
    assert len(window._menu_buttons) == 5

    window.close()
    app.processEvents()


def test_navigation_changes_current_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    tools_menu = next(
        button for button in window._menu_buttons
        if button.text().startswith("Ferramentas")
    )
    tools_menu.menu().actions()[0].trigger()
    assert window.pages.currentIndex() == 2

    window.close()
    app.processEvents()
