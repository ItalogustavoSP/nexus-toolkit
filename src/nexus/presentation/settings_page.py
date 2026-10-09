from __future__ import annotations

import json
import platform
import sys
from pathlib import Path
from typing import Any

import psutil
import PySide6

from PySide6.QtCore import QSettings, Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)


DEFAULTS: dict[str, Any] = {
    "theme": "dark",
    "accent": "violet",
    "density": "standard",
    "sound_effects": False,
    "confirm_exit": False,
    "startup_page": 0,
}


class SettingsPage(QWidget):
    """Local, persistent application preferences with import/export support."""

    settings_changed = Signal(dict)

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("settingsPage")
        self.settings = QSettings("Nexus Toolkit", "Nexus Toolkit")
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        content = QWidget()
        content.setObjectName("settingsContent")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)
        scroll.setWidget(content)
        root.addWidget(scroll)

        title = QLabel("Configurações")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Personalize a aparência e o comportamento do Nexus Toolkit. "
            "As preferências ficam salvas somente neste computador."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        appearance = self._card("Aparência")
        appearance_layout = QFormLayout()
        appearance.layout().addLayout(appearance_layout)
        appearance_layout.setContentsMargins(18, 18, 18, 18)
        appearance_layout.setHorizontalSpacing(24)
        appearance_layout.setVerticalSpacing(14)

        self.theme_combo = QComboBox()
        self.theme_combo.addItem("Escuro", "dark")
        self.theme_combo.addItem("Claro", "light")
        appearance_layout.addRow("Tema do programa", self.theme_combo)

        self.accent_combo = QComboBox()
        for label, value in [
            ("Violeta", "violet"),
            ("Azul", "blue"),
            ("Verde", "green"),
            ("Laranja", "orange"),
            ("Rosa", "pink"),
        ]:
            self.accent_combo.addItem(label, value)
        appearance_layout.addRow("Cor de destaque", self.accent_combo)

        self.density_combo = QComboBox()
        for label, value in [
            ("Compacta", "compact"),
            ("Padrão", "standard"),
            ("Ampliada", "large"),
        ]:
            self.density_combo.addItem(label, value)
        appearance_layout.addRow("Tamanho da interface", self.density_combo)
        layout.addWidget(appearance)

        behavior = self._card("Comportamento")
        behavior_layout = QVBoxLayout()
        behavior.layout().addLayout(behavior_layout)
        behavior_layout.setContentsMargins(18, 18, 18, 18)
        behavior_layout.setSpacing(13)

        self.sound_checkbox = QCheckBox("Reproduzir som ao concluir uma análise")
        self.sound_checkbox.setToolTip(
            "Usa o som de aviso do sistema ao terminar tarefas compatíveis."
        )
        behavior_layout.addWidget(self.sound_checkbox)

        self.confirm_exit_checkbox = QCheckBox(
            "Pedir confirmação antes de fechar o programa"
        )
        behavior_layout.addWidget(self.confirm_exit_checkbox)

        self.startup_combo = QComboBox()
        for label, index in [
            ("Visão geral", 0),
            ("Monitoramento", 1),
            ("Processos", 2),
            ("Armazenamento", 3),
            ("Arquivos duplicados", 4),
            ("Relatórios", 5),
            ("Configurações", 6),
        ]:
            self.startup_combo.addItem(label, index)
        behavior_layout.addWidget(QLabel("Abrir esta página ao iniciar:"))
        behavior_layout.addWidget(self.startup_combo)
        layout.addWidget(behavior)

        privacy = self._card("Privacidade e dados")
        privacy_layout = QVBoxLayout()
        privacy.layout().addLayout(privacy_layout)
        privacy_layout.setContentsMargins(18, 18, 18, 18)
        privacy_layout.setSpacing(8)
        privacy_text = QLabel(
            "O Nexus Toolkit não exige login nem conta. As preferências são "
            "armazenadas localmente pelo Windows; as ferramentas atuais consultam "
            "dados do computador localmente. Não há envio de telemetria configurado."
        )
        privacy_text.setObjectName("muted")
        privacy_text.setWordWrap(True)
        privacy_layout.addWidget(privacy_text)
        layout.addWidget(privacy)

        about = self._card("Sobre o Nexus Toolkit")
        about_layout = QVBoxLayout()
        about.layout().addLayout(about_layout)
        about_layout.setContentsMargins(18, 18, 18, 18)
        about_layout.setSpacing(10)

        about_title = QLabel("Nexus Toolkit")
        about_title.setStyleSheet("font-size: 19px; font-weight: 700;")
        about_layout.addWidget(about_title)
        about_description = QLabel(
            "Ferramentas locais para monitoramento, diagnóstico e organização "
            "do computador, com foco em transparência e segurança."
        )
        about_description.setObjectName("muted")
        about_description.setWordWrap(True)
        about_layout.addWidget(about_description)

        self.developer_label = QLabel("Desenvolvido por Italo Gustavo")
        self.developer_label.setStyleSheet("font-weight: 600;")
        about_layout.addWidget(self.developer_label)
        self.version_label = QLabel("Versão do aplicativo: 0.1.0")
        about_layout.addWidget(self.version_label)

        self.system_details = QLabel()
        self.system_details.setObjectName("muted")
        self.system_details.setWordWrap(True)
        self.system_details.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        logical_cpus = psutil.cpu_count(logical=True) or "Não identificado"
        self.system_details.setText(
            f"Sistema operacional: {platform.system()} {platform.release()}\n"
            f"Versão do sistema: {platform.version()}\n"
            f"Arquitetura: {platform.machine()}\n"
            f"Processador lógico: {logical_cpus}\n"
            f"Memória RAM: {psutil.virtual_memory().total / (1024 ** 3):.1f} GB\n"
            f"Python: {platform.python_version()}\n"
            f"Qt / PySide6: {PySide6.__version__}\n"
            f"Executável: {Path(sys.executable).name}"
        )
        about_layout.addWidget(self.system_details)
        layout.addWidget(about)

        actions_card = self._card("Backup e manutenção")
        actions = QHBoxLayout()
        actions_card.layout().addLayout(actions)
        actions.setContentsMargins(18, 18, 18, 18)
        self.export_button = QPushButton("Exportar configurações")
        self.export_button.setObjectName("secondaryButton")
        self.export_button.clicked.connect(self.export_settings)
        actions.addWidget(self.export_button)
        self.import_button = QPushButton("Importar configurações")
        self.import_button.setObjectName("secondaryButton")
        self.import_button.clicked.connect(self.import_settings)
        actions.addWidget(self.import_button)
        self.reset_button = QPushButton("Restaurar padrão")
        self.reset_button.setObjectName("primaryButton")
        self.reset_button.clicked.connect(self.reset_settings)
        actions.addWidget(self.reset_button)
        layout.addWidget(actions_card)

        self.status_label = QLabel("Configurações aplicadas automaticamente.")
        self.status_label.setObjectName("muted")
        layout.addWidget(self.status_label)
        layout.addStretch()

        self._load_preferences()
        for control in (
            self.theme_combo,
            self.accent_combo,
            self.density_combo,
        ):
            control.currentIndexChanged.connect(self._save_and_emit)
        self.sound_checkbox.toggled.connect(self._save_and_emit)
        self.confirm_exit_checkbox.toggled.connect(self._save_and_emit)
        self.startup_combo.currentIndexChanged.connect(self._save_and_emit)

    @staticmethod
    def _card(title_text: str) -> QFrame:
        card = QFrame()
        card.setObjectName("settingsCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(0, 0, 0, 0)
        heading = QLabel(title_text)
        heading.setObjectName("sectionTitle")
        layout.addWidget(heading)
        return card

    def _load_preferences(self) -> None:
        self.theme_combo.setCurrentIndex(
            max(0, self.theme_combo.findData(self.settings.value("theme", "dark")))
        )
        self.accent_combo.setCurrentIndex(
            max(0, self.accent_combo.findData(self.settings.value("accent", "violet")))
        )
        self.density_combo.setCurrentIndex(
            max(0, self.density_combo.findData(self.settings.value("density", "standard")))
        )
        self.sound_checkbox.setChecked(
            self.settings.value("sound_effects", False, type=bool)
        )
        self.confirm_exit_checkbox.setChecked(
            self.settings.value("confirm_exit", False, type=bool)
        )
        self.startup_combo.setCurrentIndex(
            max(0, self.startup_combo.findData(
                self.settings.value("startup_page", 0, type=int)
            ))
        )

    def current_preferences(self) -> dict[str, Any]:
        return {
            "theme": self.theme_combo.currentData(),
            "accent": self.accent_combo.currentData(),
            "density": self.density_combo.currentData(),
            "sound_effects": self.sound_checkbox.isChecked(),
            "confirm_exit": self.confirm_exit_checkbox.isChecked(),
            "startup_page": self.startup_combo.currentData(),
        }

    def _save_and_emit(self, _value: object = None) -> None:
        preferences = self.current_preferences()
        for key, value in preferences.items():
            self.settings.setValue(key, value)
        self.settings.sync()
        self.status_label.setText("Preferências salvas e aplicadas.")
        self.settings_changed.emit(preferences)

    def _set_controls(self, preferences: dict[str, Any]) -> None:
        controls = [
            self.theme_combo,
            self.accent_combo,
            self.density_combo,
            self.sound_checkbox,
            self.confirm_exit_checkbox,
            self.startup_combo,
        ]
        for control in controls:
            control.blockSignals(True)
        self.theme_combo.setCurrentIndex(
            self.theme_combo.findData(preferences["theme"])
        )
        self.accent_combo.setCurrentIndex(
            self.accent_combo.findData(preferences["accent"])
        )
        self.density_combo.setCurrentIndex(
            self.density_combo.findData(preferences["density"])
        )
        self.sound_checkbox.setChecked(preferences["sound_effects"])
        self.confirm_exit_checkbox.setChecked(preferences["confirm_exit"])
        self.startup_combo.setCurrentIndex(
            self.startup_combo.findData(preferences["startup_page"])
        )
        for control in controls:
            control.blockSignals(False)

    def reset_settings(self) -> None:
        answer = QMessageBox.question(
            self,
            "Restaurar configurações",
            "Deseja restaurar todas as preferências para os valores padrão?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return
        self._set_controls(DEFAULTS)
        self._save_and_emit()
        self.status_label.setText("Preferências padrão restauradas.")

    def export_settings(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Exportar configurações", "nexus-configuracoes.json",
            "Arquivo JSON (*.json)",
        )
        if not path:
            return
        if not path.lower().endswith(".json"):
            path += ".json"
        try:
            Path(path).write_text(
                json.dumps(self.current_preferences(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as error:
            QMessageBox.warning(self, "Falha na exportação", str(error))
            return
        self.status_label.setText(f"Configurações exportadas: {Path(path).name}")

    def import_settings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar configurações", "", "Arquivo JSON (*.json)"
        )
        if not path:
            return
        try:
            imported = json.loads(Path(path).read_text(encoding="utf-8"))
            if not isinstance(imported, dict):
                raise ValueError("O arquivo precisa conter um objeto JSON.")
            validated = dict(DEFAULTS)
            if isinstance(imported.get("theme"), str) and imported["theme"] in {"dark", "light"}:
                validated["theme"] = imported["theme"]
            if isinstance(imported.get("accent"), str) and imported["accent"] in {
                "violet", "blue", "green", "orange", "pink"
            }:
                validated["accent"] = imported["accent"]
            if isinstance(imported.get("density"), str) and imported["density"] in {
                "compact", "standard", "large"
            }:
                validated["density"] = imported["density"]
            for key in ("sound_effects", "confirm_exit"):
                if isinstance(imported.get(key), bool):
                    validated[key] = imported[key]
            if isinstance(imported.get("startup_page"), int) and 0 <= imported["startup_page"] <= 6:
                validated["startup_page"] = imported["startup_page"]
        except (OSError, json.JSONDecodeError, ValueError) as error:
            QMessageBox.warning(
                self, "Arquivo inválido",
                f"Não foi possível importar as configurações.\n\n{error}",
            )
            return

        self._set_controls(validated)
        self._save_and_emit()
        self.status_label.setText("Configurações importadas e aplicadas.")
