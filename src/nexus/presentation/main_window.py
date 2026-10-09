from __future__ import annotations

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from nexus.presentation.cleanup_page import CleanupPage
from nexus.presentation.dashboard_page import DashboardPage
from nexus.presentation.duplicate_files_page import DuplicateFilesPage
from nexus.presentation.monitoring_page import MonitoringPage
from nexus.presentation.processes_page import ProcessesPage
from nexus.presentation.reports_page import ReportsPage
from nexus.presentation.settings_page import SettingsPage
from nexus.presentation.storage_page import StoragePage


class MainWindow(QMainWindow):
    """Main application window with a compact, GLPI-inspired navigation shell."""

    NAVIGATION = [
        ("Visão geral", "⌂"),
        ("Monitoramento", "◉"),
        ("Processos", "▤"),
        ("Armazenamento", "▣"),
        ("Arquivos duplicados", "⧉"),
        ("Relatórios", "▥"),
        ("Configurações", "⚙"),
        ("Limpeza e otimização", "✦"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nexus Toolkit")
        self.resize(1440, 900)
        self.setMinimumSize(980, 650)
        self.preferences = QSettings("Nexus Toolkit", "Nexus Toolkit")
        self.apply_preferences(self._read_preferences())

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Primary navigation bar, inspired by the compact GLPI top navigation.
        topbar = QFrame()
        topbar.setObjectName("topbar")
        top_layout = QHBoxLayout(topbar)
        top_layout.setContentsMargins(22, 0, 18, 0)
        top_layout.setSpacing(12)

        brand = QLabel("NEXUS")
        brand.setObjectName("topBrand")
        top_layout.addWidget(brand)
        brand_subtitle = QLabel("TOOLKIT")
        brand_subtitle.setObjectName("topBrandSubtitle")
        top_layout.addWidget(brand_subtitle)
        top_layout.addSpacing(22)

        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard())
        page_factories = [
            MonitoringPage,
            ProcessesPage,
            StoragePage,
            DuplicateFilesPage,
            ReportsPage,
        ]
        for factory in page_factories:
            self.pages.addWidget(factory())
        settings_page = SettingsPage()
        settings_page.settings_changed.connect(self.apply_preferences)
        self.pages.addWidget(settings_page)
        self.pages.addWidget(CleanupPage())

        self._menu_buttons: list[QToolButton] = []
        menu_specs = [
            ("Visão geral", [("Painel principal", 0)]),
            ("Monitoramento", [("Recursos do sistema", 1)]),
            ("Ferramentas", [
                ("Processos", 2), ("Armazenamento", 3),
                ("Arquivos duplicados", 4), ("Limpeza e otimização", 7),
            ]),
            ("Relatórios", [("Relatórios do sistema", 5)]),
            ("Administração", [("Configurações", 6)]),
        ]
        for label, entries in menu_specs:
            button = QToolButton()
            button.setObjectName("topNavButton")
            button.setText(label + "  ▾")
            button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
            menu = QMenu(button)
            for item_label, page_index in entries:
                action = QAction(item_label, menu)
                action.triggered.connect(
                    lambda checked=False, index=page_index: self.navigate_to(index)
                )
                menu.addAction(action)
            button.setMenu(menu)
            top_layout.addWidget(button)
            self._menu_buttons.append(button)

        top_layout.addStretch()
        self.user_label = QLabel("●  LOCAL")
        self.user_label.setObjectName("userPill")
        top_layout.addWidget(self.user_label)
        root.addWidget(topbar)

        # Secondary utility row with breadcrumb, quick search and menu shortcut.
        utility = QFrame()
        utility.setObjectName("utilityBar")
        utility_layout = QHBoxLayout(utility)
        utility_layout.setContentsMargins(22, 9, 22, 9)
        utility_layout.setSpacing(12)
        self.breadcrumb = QLabel("⌂  Início  /  Visão geral")
        self.breadcrumb.setObjectName("breadcrumb")
        utility_layout.addWidget(self.breadcrumb)
        utility_layout.addStretch()
        self.search = QLineEdit()
        self.search.setObjectName("globalSearch")
        self.search.setPlaceholderText("Encontrar uma ferramenta…")
        self.search.setClearButtonEnabled(True)
        self.search.setMaximumWidth(340)
        self.search.returnPressed.connect(self._search_navigation)
        utility_layout.addWidget(self.search)
        self.search_button = QPushButton("⌕")
        self.search_button.setObjectName("searchButton")
        self.search_button.setToolTip("Encontrar uma ferramenta")
        self.search_button.clicked.connect(self._search_navigation)
        utility_layout.addWidget(self.search_button)
        root.addWidget(utility)

        self.pages.currentChanged.connect(self._update_breadcrumb)
        root.addWidget(self.pages, 1)
        startup_index = int(self.preferences.value("startup_page", 0))
        if 0 <= startup_index < self.pages.count():
            self.pages.setCurrentIndex(startup_index)
        self._update_breadcrumb(self.pages.currentIndex())

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
            bg, panel, panel_alt = "#f3f5f9", "#ffffff", "#f7f8fb"
            text, muted, border = "#202b40", "#68758c", "#dfe4ec"
            field, header = "#ffffff", "#eef2f7"
            hero, hero_border = "#eaf2ff", "#d8e5f8"
            topbar, top_text = "#2d4168", "#f3f6fc"
        else:
            bg, panel, panel_alt = "#101722", "#172131", "#1d2a3d"
            text, muted, border = "#edf2fb", "#9daac0", "#2d3a50"
            field, header = "#111a28", "#202d42"
            hero, hero_border = "#1a2c45", "#2c4568"
            topbar, top_text = "#172844", "#f3f6fc"
        font_size = {"compact": "12px", "standard": "13px", "large": "14px"}.get(
            density, "13px"
        )
        padding = "7px 11px" if density == "compact" else "10px 14px"
        return f"""
        QMainWindow, QWidget#central, QWidget#monitoringPage,
        QWidget#processesPage, QWidget#storagePage, QWidget#reportsPage,
        QWidget#duplicateFilesPage, QWidget#settingsPage, QWidget#dashboardPage,
        QWidget#cleanupPage, QWidget#settingsContent, QWidget#dashboardContent,
        QScrollArea {{
            background: {bg}; color: {text}; font-family: "Segoe UI";
            font-size: {font_size}; border: none;
        }}
        QWidget {{ color: {text}; }}
        QFrame#topbar {{ background: {topbar}; border: none; min-height: 58px; }}
        QLabel#topBrand {{ color: #ffffff; font-size: 24px; font-weight: 900; }}
        QLabel#topBrandSubtitle {{ color: #c1cce0; font-size: 10px; font-weight: 700; }}
        QPushButton, QToolButton {{ font-family: "Segoe UI"; }}
        QToolButton#topNavButton {{
            color: {top_text}; background: transparent; border: none;
            border-radius: 5px; padding: 10px 9px; font-weight: 600;
        }}
        QToolButton#topNavButton:hover, QToolButton#topNavButton::menu-button:hover {{
            background: #ffffff20;
        }}
        QMenu {{ background: {panel}; color: {text}; border: 1px solid {border};
            padding: 5px; }}
        QMenu::item {{ padding: 9px 28px 9px 12px; border-radius: 4px; }}
        QMenu::item:selected {{ background: {selected}; color: {accent_text}; }}
        QFrame#utilityBar {{ background: {panel}; border-bottom: 1px solid {border}; }}
        QLabel#breadcrumb {{ color: {muted}; font-size: 13px; }}
        QLabel#userPill {{ color: #dce8fb; background: #ffffff20;
            border-radius: 14px; padding: 8px 12px; font-weight: 700; }}
        QLineEdit#globalSearch {{
            background: {field}; color: {text}; border: 1px solid {border};
            border-radius: 8px; padding: 9px 12px;
        }}
        QPushButton#searchButton {{
            background: {panel}; color: {muted}; border: 1px solid {border};
            border-radius: 8px; min-width: 38px; padding: 7px;
        }}
        QLabel#muted {{ color: {muted}; }}
        QLabel#pageTitle {{ font-size: 27px; font-weight: 700; }}
        QLabel#heroTitle {{ font-size: 25px; font-weight: 700; color: {text}; }}
        QLabel#cardTitle, QLabel#sectionTitle {{ font-size: 15px; font-weight: 600; }}
        QLabel#metricEyebrow {{ color: {muted}; font-size: 10px;
            font-weight: 700; letter-spacing: 1px; }}
        QLabel#heroMonogram {{ color: {accent_text}; font-size: 25px;
            font-weight: 800; background: {selected}; border-radius: 16px; }}
        QLabel#statusPill {{ color: {accent_text}; background: {selected};
            padding: 9px 12px; border-radius: 8px; font-weight: 600; }}
        QLabel#cardValue, QLabel#metricValue {{ font-size: 22px;
            font-weight: 700; color: {accent_text}; }}
        QFrame#hero {{ background: {hero}; border: 1px solid {hero_border};
            border-radius: 13px; }}
        QFrame#card, QFrame#panel, QFrame#metricCard, QFrame#settingsCard {{
            background: {panel}; border: 1px solid {border}; border-radius: 11px;
        }}
        QPushButton#navButton {{
            text-align: left; padding: 12px 14px; border: 1px solid transparent;
            border-radius: 9px; background: transparent; color: {muted};
        }}
        QPushButton#navButton:hover {{ background: {panel_alt}; color: {text}; }}
        QPushButton#navButton:checked {{ background: {selected};
            color: {accent_text}; border-left: 3px solid {primary}; font-weight: 600; }}
        QPushButton#primaryButton {{
            background: {primary}; color: #ffffff; border: none;
            border-radius: 8px; padding: {padding}; font-weight: 600;
        }}
        QPushButton#primaryButton:hover {{ background: {hover}; }}
        QPushButton#quickActionButton {{ text-align: left; background: {panel_alt};
            color: {text}; border: 1px solid {border}; border-radius: 8px;
            padding: 9px 11px; }}
        QPushButton#quickActionButton:hover {{ background: {selected};
            border-color: {primary}; }}
        QPushButton#secondaryButton {{ background: {panel_alt}; color: {text};
            border: 1px solid {border}; border-radius: 8px; padding: {padding}; }}
        QPushButton#secondaryButton:hover {{ border-color: {primary};
            background: {selected}; }}
        QPushButton:disabled {{ color: {muted}; background: {panel_alt}; }}
        QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {{
            background: {field}; color: {text}; border: 1px solid {border};
            border-radius: 8px; padding: 9px; selection-background-color: {selected};
        }}
        QComboBox QAbstractItemView {{ background: {panel}; color: {text};
            selection-background-color: {selected}; }}
        QTableWidget, QListWidget {{ background: {panel_alt};
            alternate-background-color: {panel}; color: {text};
            gridline-color: {border}; border: 1px solid {border};
            border-radius: 8px; selection-background-color: {selected}; }}
        QHeaderView::section {{ background: {header}; color: {accent_text};
            border: none; border-bottom: 1px solid {border}; padding: 9px;
            font-weight: 600; }}
        QCheckBox {{ spacing: 9px; }}
        QCheckBox::indicator {{ width: 17px; height: 17px; }}
        QCheckBox::indicator:checked {{ background: {primary};
            border: 1px solid {primary}; border-radius: 4px; }}
        QCheckBox::indicator:unchecked {{ background: {field};
            border: 1px solid {border}; border-radius: 4px; }}
        QScrollBar:vertical {{ background: {bg}; width: 10px; margin: 0; }}
        QScrollBar::handle:vertical {{ background: {border};
            border-radius: 5px; min-height: 24px; }}
        QToolTip {{ background: {panel}; color: {text};
            border: 1px solid {border}; padding: 5px; }}
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

    def navigate_to(self, index: int) -> None:
        if 0 <= index < self.pages.count():
            self.pages.setCurrentIndex(index)

    def _update_breadcrumb(self, index: int) -> None:
        if 0 <= index < len(self.NAVIGATION):
            name, icon = self.NAVIGATION[index]
            self.breadcrumb.setText(f"⌂  Início  /  {name}")
            self.user_label.setText("●  LOCAL")
            self.setWindowTitle(f"Nexus Toolkit — {name}")

    def _search_navigation(self) -> None:
        query = self.search.text().strip().casefold()
        if not query:
            self.search.setFocus()
            return
        matches = [
            (index, name)
            for index, (name, _icon) in enumerate(self.NAVIGATION)
            if query in name.casefold()
        ]
        if matches:
            self.navigate_to(matches[0][0])
            self.search.clear()
        else:
            self.search.setToolTip("Nenhuma ferramenta encontrada com esse nome.")
            self.search.setFocus()

    def _build_dashboard(self) -> QWidget:
        return DashboardPage(self.navigate_to)
