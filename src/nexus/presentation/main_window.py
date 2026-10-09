from __future__ import annotations

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nexus.presentation.dashboard_page import DashboardPage
from nexus.presentation.duplicate_files_page import DuplicateFilesPage
from nexus.presentation.monitoring_page import MonitoringPage
from nexus.presentation.processes_page import ProcessesPage
from nexus.presentation.reports_page import ReportsPage
from nexus.presentation.settings_page import SettingsPage
from nexus.presentation.storage_page import StoragePage


class MainWindow(QMainWindow):
    """Main application window for Nexus Toolkit."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nexus Toolkit")
        self.resize(1240, 800)
        self.setMinimumSize(900, 600)
        self.preferences = QSettings("Nexus Toolkit", "Nexus Toolkit")
        self.apply_preferences(self._read_preferences())

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(14, 10, 14, 8)
        self.menu_toggle = QPushButton("☰")
        self.menu_toggle.setObjectName("menuToggle")
        self.menu_toggle.setToolTip("Abrir ou fechar o menu principal")
        self.menu_toggle.setAccessibleName("Menu principal")
        self.menu_toggle.setFixedSize(42, 38)
        self.menu_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        toolbar.addWidget(self.menu_toggle)
        toolbar.addStretch()
        root.addLayout(toolbar)

        content_row = QHBoxLayout()
        content_row.setContentsMargins(0, 0, 0, 0)
        content_row.setSpacing(0)
        root.addLayout(content_row, 1)

        # Build the page stack before the sidebar connects navigation signals.
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard())

        sections = [
            ("Monitoramento", "Acompanhe o uso de recursos do computador."),
            ("Processos", "Consulte os processos em execução."),
            ("Armazenamento", "Analise discos, volumes e espaço disponível."),
            (
                "Arquivos duplicados",
                "Localize cópias idênticas e exporte os resultados.",
            ),
            ("Relatórios", "Consulte relatórios de diagnóstico do sistema."),
            ("Configurações", "Gerencie as preferências locais do aplicativo."),
        ]
        for title, description in sections:
            if title == "Monitoramento":
                self.pages.addWidget(MonitoringPage())
            elif title == "Processos":
                self.pages.addWidget(ProcessesPage())
            elif title == "Armazenamento":
                self.pages.addWidget(StoragePage())
            elif title == "Arquivos duplicados":
                self.pages.addWidget(DuplicateFilesPage())
            elif title == "Relatórios":
                self.pages.addWidget(ReportsPage())
            elif title == "Configurações":
                settings_page = SettingsPage()
                settings_page.settings_changed.connect(self.apply_preferences)
                self.pages.addWidget(settings_page)
            else:
                self.pages.addWidget(self._build_placeholder(title, description))

        startup_index = int(self.preferences.value("startup_page", 0))
        if 0 <= startup_index < self.pages.count():
            self.pages.setCurrentIndex(startup_index)

        self.sidebar = self._build_sidebar()
        self.sidebar.hide()
        content_row.addWidget(self.sidebar)
        content_row.addWidget(self.pages, 1)
        self.menu_toggle.clicked.connect(self._toggle_sidebar)

    def _read_preferences(self) -> dict[str, object]:
        return {
            "theme": str(self.preferences.value("theme", "dark")),
            "accent": str(self.preferences.value("accent", "violet")),
            "density": str(self.preferences.value("density", "standard")),
            "sound_effects": self.preferences.value("sound_effects", False, type=bool),
            "confirm_exit": self.preferences.value("confirm_exit", False, type=bool),
            "startup_page": self.preferences.value("startup_page", 0, type=int),
        }

    def apply_preferences(self, preferences: dict[str, object]) -> None:
        """Apply saved appearance and behavior preferences."""
        theme = str(preferences.get("theme", "dark"))
        accent_name = str(preferences.get("accent", "violet"))
        density = str(preferences.get("density", "standard"))
        self.preferences.setValue("theme", theme)
        self.preferences.setValue("accent", accent_name)
        self.preferences.setValue("density", density)
        self.preferences.setValue(
            "sound_effects", bool(preferences.get("sound_effects", False))
        )
        self.preferences.setValue(
            "confirm_exit", bool(preferences.get("confirm_exit", False))
        )
        self.preferences.setValue(
            "startup_page", int(preferences.get("startup_page", 0))
        )
        self.setStyleSheet(self._stylesheet(theme, accent_name, density))
        self.preferences.sync()

    @staticmethod
    def _stylesheet(
        theme: str = "dark",
        accent_name: str = "violet",
        density: str = "standard",
    ) -> str:
        accents = {
            "violet": ("#8874ed", "#9a88f5", "#302a50", "#c6baff"),
            "blue": ("#2878d4", "#398be8", "#203a5b", "#a9d2ff"),
            "green": ("#218c68", "#2da77d", "#1e443a", "#a9efd3"),
            "orange": ("#c66b2d", "#df8040", "#503522", "#ffd0aa"),
            "pink": ("#ca548c", "#df6ba2", "#50253b", "#ffc0dc"),
        }
        primary, hover, selected, accent_text = accents.get(
            accent_name, accents["violet"]
        )
        if theme == "light":
            bg, sidebar, panel, panel_alt = "#f4f6fb", "#ffffff", "#ffffff", "#edf0f7"
            text, muted, border = "#202637", "#667085", "#dce1eb"
            field, header = "#ffffff", "#e9edf6"
            hero, hero_border = "#f0edff", "#d8d0ff"
        else:
            bg, sidebar, panel, panel_alt = "#10131b", "#151925", "#191e2b", "#151925"
            text, muted, border = "#edf0f7", "#9ba4b8", "#2c3345"
            field, header = "#10131b", "#202538"
            hero, hero_border = "#20203a", "#39345f"
        font_size = {"compact": "12px", "standard": "13px", "large": "14px"}.get(
            density, "13px"
        )
        padding = "7px 11px" if density == "compact" else "10px 14px"
        return f"""
        QMainWindow, QWidget#central, QWidget#monitoringPage,
        QWidget#processesPage, QWidget#storagePage, QWidget#reportsPage,
        QWidget#duplicateFilesPage, QWidget#settingsPage, QWidget#dashboardPage,
        QWidget#settingsContent, QWidget#dashboardContent, QScrollArea {{
            background: {bg}; color: {text}; font-family: "Segoe UI";
            font-size: {font_size}; border: none;
        }}
        QWidget {{ color: {text}; }}
        QFrame#sidebar {{ background: {sidebar}; border-right: 1px solid {border}; }}
        QLabel#brand {{ color: {accent_text}; font-size: 20px; font-weight: 700; }}
        QPushButton#menuToggle {{
            background: {panel}; color: {text}; border: 1px solid {border};
            border-radius: 9px; font-size: 20px; font-weight: 700;
        }}
        QPushButton#menuToggle:hover {{ background: {selected}; border-color: {primary}; }}
        QLabel#muted {{ color: {muted}; }}
        QLabel#pageTitle {{ font-size: 27px; font-weight: 700; }}
        QLabel#heroTitle {{ font-size: 25px; font-weight: 700; color: {text}; }}
        QLabel#cardTitle, QLabel#sectionTitle {{ font-size: 15px; font-weight: 600; }}
                    QLabel#metricEyebrow {{ color: {muted};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            }}
                    QLabel#heroMonogram {{ color: {accent_text};
            font-size: 25px;
            font-weight: 800;
            background: {selected};
            border-radius: 16px;
            }}
                    QLabel#statusPill {{ color: {accent_text};
            background: {selected};
            padding: 9px 12px;
            border-radius: 8px;
            font-weight: 600;
            }}
                    QLabel#cardValue, QLabel#metricValue {{ font-size: 22px;
            font-weight: 700;
            color: {accent_text};
            }}
                    QFrame#hero {{ background: {hero};
            border: 1px solid {hero_border};
            border-radius: 16px;
            }}
        QFrame#card, QFrame#panel, QFrame#metricCard, QFrame#settingsCard {{
            background: {panel}; border: 1px solid {border}; border-radius: 13px;
        }}
        QPushButton#navButton {{
            text-align: left; padding: 12px 14px; border: 1px solid transparent;
            border-radius: 9px; background: transparent; color: {muted};
        }}
        QPushButton#navButton:hover {{ background: {panel_alt}; color: {text}; }}
        QPushButton#navButton:checked {{
                        background: {selected};
            color: {accent_text};
            border-left: 3px solid {primary};
            font-weight: 600;
        }}
        QPushButton#primaryButton {{
            background: {primary}; color: #ffffff; border: none;
            border-radius: 8px; padding: {padding}; font-weight: 600;
        }}
        QPushButton#primaryButton:hover {{ background: {hover}; }}
        QPushButton#primaryButton:pressed {{ background: {primary}; }}
                    QPushButton#quickActionButton {{ text-align: left;
            background: {panel_alt};
            color: {text};
            border: 1px solid {border};
            border-radius: 8px;
            padding: 9px 11px;
            }}
                    QPushButton#quickActionButton:hover {{ background: {selected};
            border-color: {primary};
            }}
                    QPushButton#quickActionButton:pressed {{ background: {selected};
            padding-left: 14px;
            }}
        QPushButton#secondaryButton {{
            background: {panel_alt}; color: {text}; border: 1px solid {border};
            border-radius: 8px; padding: {padding};
        }}
                    QPushButton#secondaryButton:hover {{ border-color: {primary};
            background: {selected};
            }}
        QPushButton:disabled {{ color: {muted}; background: {panel_alt}; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
            background: {field}; color: {text}; border: 1px solid {border};
            border-radius: 8px; padding: 9px; selection-background-color: {selected};
        }}
        QComboBox QAbstractItemView {{
            background: {panel}; color: {text}; selection-background-color: {selected};
        }}
        QTableWidget, QListWidget {{
            background: {panel_alt}; alternate-background-color: {panel};
            color: {text}; gridline-color: {border}; border: 1px solid {border};
            border-radius: 8px; selection-background-color: {selected};
        }}
        QHeaderView::section {{
            background: {header}; color: {accent_text}; border: none;
            border-bottom: 1px solid {border}; padding: 9px; font-weight: 600;
        }}
        QCheckBox {{ spacing: 9px; }}
        QCheckBox::indicator {{ width: 17px; height: 17px; }}
                    QCheckBox::indicator:checked {{ background: {primary};
            border: 1px solid {primary};
            border-radius: 4px;
            }}
                    QCheckBox::indicator:unchecked {{ background: {field};
            border: 1px solid {border};
            border-radius: 4px;
            }}
        QScrollBar:vertical {{ background: {bg}; width: 10px; margin: 0; }}
                    QScrollBar::handle:vertical {{ background: {border};
            border-radius: 5px;
            min-height: 24px;
            }}
                    QToolTip {{ background: {panel};
            color: {text};
            border: 1px solid {border};
            padding: 5px;
            }}
        """

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.isVisible() and self.preferences.value(
            "confirm_exit", False, type=bool
        ):
            answer = QMessageBox.question(
                self,
                "Sair do Nexus Toolkit",
                "Deseja realmente fechar o Nexus Toolkit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )
            if answer != QMessageBox.StandardButton.Yes:
                event.ignore()
                return
        event.accept()

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 25, 16, 18)
        layout.setSpacing(8)

        brand = QLabel("Nexus Toolkit")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        layout.addSpacing(20)

        menu_label = QLabel("MENU PRINCIPAL")
        menu_label.setObjectName("muted")
        layout.addWidget(menu_label)
        layout.addSpacing(5)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        navigation = [
            "Visão geral",
            "Monitoramento",
            "Processos",
            "Armazenamento",
            "Arquivos duplicados",
            "Relatórios",
            "Configurações",
        ]
        for index, name in enumerate(navigation):
            button = QPushButton(f"  {name}")
            button.setObjectName("navButton")
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            button.setMinimumHeight(42)
            self.nav_group.addButton(button, index)
            layout.addWidget(button)

        self.nav_group.idClicked.connect(self.pages.setCurrentIndex)
        self.nav_group.button(self.pages.currentIndex()).setChecked(True)
        layout.addStretch()

        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("color: #292f40;")
        layout.addWidget(separator)

        footer = QLabel("Versão 0.1.0 · Em desenvolvimento")
        footer.setObjectName("muted")
        footer.setWordWrap(True)
        layout.addWidget(footer)
        return sidebar

    def _toggle_sidebar(self) -> None:
        visible = self.sidebar.isVisible()
        self.sidebar.setVisible(not visible)
        self.menu_toggle.setText("☰" if visible else "✕")
        self.menu_toggle.setToolTip(
            "Abrir o menu principal" if visible else "Fechar o menu principal"
        )

    def _build_dashboard(self) -> QWidget:
        return DashboardPage(self._navigate_to_page)

    def _navigate_to_page(self, index: int) -> None:
        self.nav_group.button(index).click()

    @staticmethod
    def _build_placeholder(title_text: str, description_text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(16)

        title = QLabel(title_text)
        title.setObjectName("pageTitle")
        description = QLabel(description_text)
        description.setObjectName("muted")
        description.setWordWrap(True)

        panel = QFrame()
        panel.setObjectName("card")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(24, 24, 24, 24)
        panel_layout.setSpacing(12)

        status = QLabel("MÓDULO EM DESENVOLVIMENTO")
        status.setStyleSheet("color: #b7a8ff; font-weight: 600;")
        message = QLabel(
            "Esta área será implementada nas próximas etapas, com "
            "funcionalidades reais e testes automatizados."
        )
        message.setObjectName("muted")
        message.setWordWrap(True)

        panel_layout.addWidget(status)
        panel_layout.addWidget(message)
        layout.addWidget(title)
        layout.addWidget(description)
        layout.addWidget(panel)
        layout.addStretch()
        return page
