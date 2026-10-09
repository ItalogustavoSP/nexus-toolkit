from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow
from nexus.presentation.storage_page import StoragePage


def test_storage_page_loads_accessible_volumes() -> None:
    app = QApplication.instance() or QApplication([])
    page = StoragePage()

    assert page.table.columnCount() == 6
    assert page.summary.text()
    assert page.table.rowCount() == len(page._rows)

    page.close()
    app.processEvents()


def test_storage_search_filters_rows() -> None:
    app = QApplication.instance() or QApplication([])
    page = StoragePage()

    if page._rows:
        mountpoint = str(page._rows[0]["mountpoint"])
        page.search_input.setText(mountpoint)
        assert page.table.rowCount() >= 1
        for row in range(page.table.rowCount()):
            assert mountpoint.casefold() in page.table.item(row, 0).text().casefold()

    page.close()
    app.processEvents()


def test_main_window_uses_storage_page() -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert isinstance(window.pages.widget(3), StoragePage)

    window.close()
    app.processEvents()
