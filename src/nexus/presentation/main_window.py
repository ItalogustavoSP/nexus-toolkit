from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nexus.presentation.monitoring_page import MonitoringPage
from nexus.presentation.processes_page import ProcessesPage


class MainWindow(QMainWindow):
    """Main application window for Nexus Toolkit."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Nexus Toolkit")
        self.resize(1240, 800)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(self._stylesheet())

        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Build the page stack before the sidebar connects navigation signals.
        self.pages = QStackedWidget()
        self.pages.addWidget(self._build_dashboard())

        sections = [
            ("Monitoramento", "Acompanhe o uso de recursos do computador."),
            ("Processos", "Consulte os processos em execução."),
            ("Armazenamento", "Analise discos, volumes e espaço disponível."),
            ("Arquivos duplicados", "Prepare verificações de arquivos duplicados."),
            ("Relatórios", "Consulte relatórios de diagnóstico do sistema."),
            ("Configurações", "Gerencie as preferências locais do aplicativo."),
        ]
        for title, description in sections:
            if title == "Monitoramento":
                self.pages.addWidget(MonitoringPage())
            elif title == "Processos":
                self.pages.addWidget(ProcessesPage())
            else:
                self.pages.addWidget(self._build_placeholder(title, description))

        root.addWidget(self._build_sidebar())
        root.addWidget(self.pages, 1)

    @staticmethod
    def _stylesheet() -> str:
        return """
        QMainWindow, QWidget#central {
            background: #10131b;
            color: #edf0f7;
            font-family: "Segoe UI";
            font-size: 13px;
        }
        QFrame#sidebar {
            background: #151925;
            border-right: 1px solid #292f40;
        }
        QLabel#brand { color: #b7a8ff; font-size: 23px; font-weight: 700; }
        QLabel#muted { color: #9ba4b8; }
        QLabel#pageTitle { font-size: 27px; font-weight: 700; }
        QLabel#heroTitle { font-size: 25px; font-weight: 700; color: #ffffff; }
        QLabel#cardTitle { font-size: 15px; font-weight: 600; }
        QLabel#cardValue { font-size: 22px; font-weight: 700; color: #b7a8ff; }
        QFrame#hero {
            background: #20203a; border: 1px solid #39345f; border-radius: 16px;
        }
        QFrame#card {
            background: #191e2b; border: 1px solid #2c3345; border-radius: 13px;
        }
        QPushButton#navButton {
            text-align: left; padding: 12px 14px; border: none;
            border-radius: 8px; background: transparent; color: #aeb7ca;
        }
        QPushButton#navButton:hover { background: #23293a; color: #ffffff; }
        QPushButton#navButton:checked {
            background: #302a50; color: #c6baff; font-weight: 600;
        }
        QPushButton#primaryButton {
            background: #8874ed; color: #ffffff; border: none;
            border-radius: 8px; padding: 11px 16px; font-weight: 600;
        }
        QPushButton#primaryButton:hover { background: #9a88f5; }
        """

    def _build_sidebar(self) -> QFrame:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(235)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 25, 16, 18)
        layout.setSpacing(8)

        brand = QLabel("NEXUS")
        brand.setObjectName("brand")
        layout.addWidget(brand)

        subtitle = QLabel("TOOLKIT  /  WINDOWS")
        subtitle.setObjectName("muted")
        layout.addWidget(subtitle)
        layout.addSpacing(28)

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
        self.nav_group.button(0).setChecked(True)
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

    def _build_dashboard(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(22)

        header = QHBoxLayout()
        heading = QVBoxLayout()
        title = QLabel("Visão geral")
        title.setObjectName("pageTitle")
        description = QLabel("Seu centro de diagnóstico e manutenção do Windows.")
        description.setObjectName("muted")
        heading.addWidget(title)
        heading.addWidget(description)
        header.addLayout(heading)
        header.addStretch()

        status = QLabel("●  VERSÃO INICIAL")
        status.setStyleSheet(
            "color: #b7a8ff; background: #25213c; padding: 9px 12px;"
            "border-radius: 8px;"
        )
        header.addWidget(status, alignment=Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(25, 24, 25, 24)
        hero_layout.setSpacing(12)

        hero_title = QLabel("Bem-vindo ao Nexus Toolkit")
        hero_title.setObjectName("heroTitle")
        hero_description = QLabel(
            "Uma central de ferramentas para conhecer melhor seu computador, "
            "analisar recursos e realizar manutenções com mais controle e segurança."
        )
        hero_description.setObjectName("muted")
        hero_description.setWordWrap(True)
        explore = QPushButton("Explorar módulos")
        explore.setObjectName("primaryButton")
        explore.setCursor(Qt.CursorShape.PointingHandCursor)
        explore.clicked.connect(lambda: self.nav_group.button(1).click())
        hero_layout.addWidget(hero_title)
        hero_layout.addWidget(hero_description)
        hero_layout.addSpacing(5)
        hero_layout.addWidget(explore, alignment=Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(hero)

        section_title = QLabel("Visão do projeto")
        section_title.setObjectName("cardTitle")
        layout.addWidget(section_title)

        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(14)
        cards = [
            ("Módulos planejados", "06", "Áreas de ferramentas"),
            ("Execução", "Local", "Foco em privacidade"),
            ("Infraestrutura", "Modular", "Preparada para crescer"),
        ]
        for card_title, value, detail in cards:
            cards_layout.addWidget(self._make_card(card_title, value, detail))
        layout.addLayout(cards_layout)

        notice = QLabel(
            "O monitoramento já consulta informações básicas do computador em "
            "modo somente leitura. Os demais módulos continuam em desenvolvimento; "
            "nenhum arquivo ou configuração é alterado por esta tela."
        )
        notice.setObjectName("muted")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addStretch()
        return page

    @staticmethod
    def _make_card(title_text: str, value: str, detail: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        card.setMinimumHeight(145)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(10)

        title = QLabel(title_text)
        title.setObjectName("cardTitle")
        value_label = QLabel(value)
        value_label.setObjectName("cardValue")
        detail_label = QLabel(detail)
        detail_label.setObjectName("muted")
        layout.addWidget(title)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        layout.addStretch()
        return card

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
