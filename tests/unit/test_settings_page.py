from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow
from nexus.presentation.settings_page import SettingsPage


def _app() -> QApplication:
    return QApplication.instance() or QApplication([])


def test_settings_page_persists_theme_and_accent() -> None:
    app = _app()
    stored = QSettings("Nexus Toolkit", "Nexus Toolkit")
    stored.clear()
    page = SettingsPage()

    assert page.theme_combo.currentData() == "dark"
    assert page.accent_combo.count() == 5

    page.theme_combo.setCurrentIndex(page.theme_combo.findData("light"))
    page.accent_combo.setCurrentIndex(page.accent_combo.findData("blue"))

    assert stored.value("theme") == "light"
    assert stored.value("accent") == "blue"

    page.close()
    stored.clear()
    app.processEvents()


def test_settings_are_connected_to_main_window_theme() -> None:
    app = _app()
    stored = QSettings("Nexus Toolkit", "Nexus Toolkit")
    stored.clear()
    window = MainWindow()
    page = window.pages.widget(6)

    assert isinstance(page, SettingsPage)
    assert "#10131b" in window.styleSheet()

    page.theme_combo.setCurrentIndex(page.theme_combo.findData("light"))
    assert "#f4f6fb" in window.styleSheet()

    window.close()
    stored.clear()
    app.processEvents()


def test_settings_page_has_export_import_and_reset_actions() -> None:
    app = _app()
    page = SettingsPage()

    assert page.export_button.text() == "Exportar configurações"
    assert page.import_button.text() == "Importar configurações"
    assert page.reset_button.text() == "Restaurar padrão"
    assert page.sound_checkbox.text()
    assert page.confirm_exit_checkbox.text()

    page.close()
    app.processEvents()
