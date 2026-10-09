from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow
from nexus.presentation.processes_page import ProcessesPage


def test_processes_page_loads_process_information() -> None:
    app = QApplication.instance() or QApplication([])
    page = ProcessesPage()

    assert page.table.columnCount() == 5
    assert page.table.rowCount() > 0
    assert "processos exibidos" in page.summary.text()
    assert "Memória dos processos exibidos" in page.summary.text()

    page.close()
    app.processEvents()


def test_process_search_filters_visible_rows() -> None:
    app = QApplication.instance() or QApplication([])
    page = ProcessesPage()

    first_process_name = str(page._rows[0]["name"])
    page.search_input.setText(first_process_name)

    assert page.table.rowCount() >= 1
    for row in range(page.table.rowCount()):
        displayed_name = page.table.item(row, 1).text().casefold()
        assert first_process_name.casefold() in displayed_name

    page.close()
    app.processEvents()


def test_main_window_uses_real_processes_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert isinstance(window.pages.widget(2), ProcessesPage)

    window.close()
    app.processEvents()
