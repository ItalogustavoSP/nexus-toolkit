import sys

from PySide6.QtWidgets import QApplication

from nexus.presentation.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus Toolkit")
    app.setOrganizationName("Nexus Toolkit")

    window = MainWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())