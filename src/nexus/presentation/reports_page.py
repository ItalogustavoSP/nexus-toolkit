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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(34, 30, 34, 30)
        layout.setSpacing(18)

        title = QLabel("Relatórios")
        title.setObjectName("pageTitle")
        description = QLabel(
            "Gere um resumo local de diagnóstico para consultar ou guardar " 
            "como arquivo."
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
        """Collect a local system diagnostic report, including accessible drives."""
        try:
            memory = psutil.virtual_memory()
            processes = list(psutil.process_iter(attrs=["pid", "name"]))
            cpu_percent = psutil.cpu_percent(interval=0.1)
            disk_lines: list[str] = []
            seen_mountpoints: set[str] = set()
            for partition in psutil.disk_partitions(all=False):
                mountpoint = partition.mountpoint
                if mountpoint in seen_mountpoints:
                    continue
                seen_mountpoints.add(mountpoint)
                try:
                    disk = psutil.disk_usage(mountpoint)
                except OSError:
                    continue
                disk_lines.extend(
                    [
                        f"Unidade: {mountpoint}",
                        f"Dispositivo: {partition.device or 'Não identificado'}",
                        f"Sistema de arquivos: {partition.fstype or 'Desconhecido'}",
                        f"Total: {disk.total / (1024 ** 3):.2f} GB",
                        f"Usado: {disk.used / (1024 ** 3):.2f} GB " 
                        f"({disk.percent:.1f}%)",
                        f"Livre: {disk.free / (1024 ** 3):.2f} GB",
                        "",
                    ]
                )

            uptime_seconds = max(
                0, int(datetime.now().timestamp() - psutil.boot_time())
            )
            days, remainder = divmod(uptime_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes = remainder // 60
            processor = platform.processor().strip() or "Não identificado"
            generated_at = datetime.now().astimezone().strftime(
                "%d/%m/%Y %H:%M:%S %Z"
            )
            report = [
                "NEXUS TOOLKIT — RELATÓRIO DE DIAGNÓSTICO",
                "=" * 46,
                "Desenvolvido por: Italo Gustavo",
                "Versão do aplicativo: 0.1.0",
                f"Gerado em: {generated_at}",
                "",
                "SISTEMA",
                f"Sistema operacional: {platform.system()} {platform.release()}",
                f"Versão do sistema: {platform.version()}",
                f"Arquitetura: {platform.machine()}",
                f"Versão do Python: {platform.python_version()}",
                "",
                "PROCESSADOR",
                f"Modelo: {processor}",
                f"Processadores lógicos: {psutil.cpu_count(logical=True) or 0}",
                f"Uso aproximado da CPU: {cpu_percent:.1f}%",
                f"Tempo desde a inicialização: {days} dias, {hours} horas " 
                f"e {minutes} minutos",
                "",
                "MEMÓRIA RAM",
                f"Uso: {memory.percent:.1f}%",
                f"Em uso: {memory.used / (1024 ** 3):.2f} GB",
                f"Disponível: {memory.available / (1024 ** 3):.2f} GB",
                f"Total: {memory.total / (1024 ** 3):.2f} GB",
                "",
                "UNIDADES DE ARMAZENAMENTO",
                *(disk_lines or ["Nenhuma unidade acessível foi identificada."]),
                "PROCESSOS",
                f"Quantidade observada: {len(processes)}",
                "",
                "Observação: relatório informativo, coletado em modo somente leitura.",
            ]
            self._report_text = "\n".join(report)
            self.preview.setPlainText(self._report_text)
        except (OSError, RuntimeError, IndexError, ValueError) as error:
            QMessageBox.warning(
                self,
                "Não foi possível gerar o relatório",
                "Algumas informações do sistema não puderam ser consultadas.\n\n"
                f"{error}",
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
