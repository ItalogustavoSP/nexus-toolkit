from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow
from nexus.presentation.reports_page import ReportsPage


def test_reports_page_generates_local_preview() -> None:
    app = QApplication.instance() or QApplication([])
    page = ReportsPage()

    assert "RELATÓRIO DE DIAGNÓSTICO" in page.preview.toPlainText()
    report = page.preview.toPlainText()
    assert "SISTEMA" in report
    assert "Desenvolvido por: Italo Gustavo" in report
    assert "MEMÓRIA RAM" in report
    assert "UNIDADES DE ARMAZENAMENTO" in report
    assert "Tempo desde a inicialização:" in report
    assert page._report_text == report

    page.close()
    app.processEvents()


def test_main_window_uses_reports_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert isinstance(window.pages.widget(5), ReportsPage)

    window.close()
    app.processEvents()
