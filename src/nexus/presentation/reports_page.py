from __future__ import annotations

import platform
from datetime import datetime

import psutil
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ReportsPage(QWidget):
    """Generate a local system diagnostic report and optionally export it."""

    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("reportsPage")
        self._report_text = ""
        self.setStyleSheet(
            """
            QLabel#pageTitle { font-size: 27px; font-weight: 700; }
            QLabel#muted { color: #9ba4b8; }
            QFrame#panel {
                background: #191e2b; border: 1px solid #2c3345; border-radius: 13px;
            }
            QTextEdit {
                background: #10131b; color: #edf0f7; border: 1px solid #343b50;
                border-radius: 8px; padding: 12px;
                selection-background-color: #39345f;
            }
            QPushButton#primaryButton {
                background: #8874ed; color: #ffffff; border: none;
                border-radius: 8px; padding: 10px 15px; font-weight: 600;
            }
            QPushButton#primaryButton:hover { background: #9a88f5; }
            QPushButton#secondaryButton {
                background: #252b3b; color: #edf0f7; border: 1px solid #343b50;
                border-radius: 8px; padding: 10px 15px;
            }
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        title = QLabel("Relatórios")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Gere um resumo local de diagnóstico para consultar ou guardar como arquivo."
        )
        description.setObjectName("muted")
        description.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(description)

        actions = QHBoxLayout()
        generate = QPushButton("Gerar relatório")
        generate.setObjectName("primaryButton")
        generate.setCursor(Qt.CursorShape.PointingHandCursor)
        generate.clicked.connect(self.generate_report)
        actions.addWidget(generate)

        export = QPushButton("Exportar TXT")
        export.setObjectName("secondaryButton")
        export.setCursor(Qt.CursorShape.PointingHandCursor)
        export.clicked.connect(self.export_report)
        actions.addWidget(export)
        actions.addStretch()
        layout.addLayout(actions)

        panel = QFrame()
        panel.setObjectName("panel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(12, 12, 12, 12)
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setPlaceholderText(
            "Clique em “Gerar relatório” para criar uma nova prévia."
        )
        panel_layout.addWidget(self.preview)
        layout.addWidget(panel, 1)

        note = QLabel(
            "O relatório é criado localmente. Nada é enviado pela internet. "
            "A exportação só ocorre após você escolher o local do arquivo."
        )
        note.setObjectName("muted")
        note.setWordWrap(True)
        layout.addWidget(note)

        self.generate_report()

    def generate_report(self) -> None:
        """Collect basic machine metrics into a readable report."""
        try:
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage(psutil.disk_partitions(all=False)[0].mountpoint)
            processes = list(psutil.process_iter(attrs=["pid", "name"]))
            cpu_percent = psutil.cpu_percent(interval=0.1)
            report = [
                "NEXUS TOOLKIT — RELATÓRIO DE DIAGNÓSTICO",
                "=" * 46,
                f"Gerado em: {datetime.now().astimezone().strftime('%d/%m/%Y %H:%M:%S %Z')}",
                "",
                "SISTEMA",
                f"Sistema operacional: {platform.system()} {platform.release()}",
                f"Arquitetura: {platform.machine()}",
                f"Versão do Python: {platform.python_version()}",
                "",
                "PROCESSADOR",
                f"Processadores lógicos: {psutil.cpu_count(logical=True) or 0}",
                f"Uso aproximado da CPU: {cpu_percent:.1f}%",
                "",
                "MEMÓRIA RAM",
                f"Uso: {memory.percent:.1f}%",
                f"Em uso: {memory.used / (1024 ** 3):.2f} GB",
                f"Total: {memory.total / (1024 ** 3):.2f} GB",
                "",
                "ARMAZENAMENTO (UNIDADE ACESSÍVEL PRINCIPAL)",
                f"Unidade: {psutil.disk_partitions(all=False)[0].mountpoint}",
                f"Total: {disk.total / (1024 ** 3):.2f} GB",
                f"Usado: {disk.used / (1024 ** 3):.2f} GB",
                f"Livre: {disk.free / (1024 ** 3):.2f} GB",
                "",
                "PROCESSOS",
                f"Quantidade observada: {len(processes)}",
                "",
                "Observação: relatório informativo, coletado em modo somente leitura.",
            ]
            self._report_text = "\n".join(report)
            self.preview.setPlainText(self._report_text)
        except (OSError, RuntimeError, IndexError) as error:
            QMessageBox.warning(
                self,
                "Não foi possível gerar o relatório",
                f"Algumas informações do sistema não puderam ser consultadas.\n\n{error}",
            )

    def export_report(self) -> None:
        """Save the current report only after the user chooses a destination."""
        if not self._report_text:
            self.generate_report()
        if not self._report_text:
            return
        path, _selected_filter = QFileDialog.getSaveFileName(
            self,
            "Exportar relatório",
            "nexus-relatorio.txt",
            "Arquivo de texto (*.txt)",
        )
        if not path:
            return
        if not path.lower().endswith(".txt"):
            path += ".txt"
        try:
            with open(path, "w", encoding="utf-8") as report_file:
                report_file.write(self._report_text)
        except OSError as error:
            QMessageBox.warning(
                self,
                "Falha ao exportar",
                f"Não foi possível salvar o relatório.\n\n{error}",
            )
            return
        QMessageBox.information(
            self,
            "Relatório exportado",
            f"O relatório foi salvo em:\n{path}",
        )
