import os
import subprocess
import sys

from PySide6.QtCore import Qt, QThread, Signal, QObject
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class WorkerSignals(QObject):
    result = Signal(tuple)


class Worker(QThread):
    def __init__(self, file_path, checkbox1_checked, checkbox2_checked):
        super().__init__()
        self.file_path = file_path
        self.checkbox1_checked = checkbox1_checked
        self.checkbox2_checked = checkbox2_checked
        self.signals = WorkerSignals()

    def run(self):
        processed_files = []
        error_messages = []
        console_output = []

        if not os.path.exists(self.file_path):
            error_messages.append(f"File not found: {self.file_path}")
        elif self.file_path.endswith(".tx") and not self.checkbox2_checked:
            stdout, stderr = check_tx_file(self.file_path)
            processed_files.append(self.file_path)
            if stderr:
                error_messages.append(stderr)
            if stdout:
                console_output.append(stdout)
        elif self.file_path.endswith(".tx") and self.checkbox2_checked:
            output_file_path = os.path.splitext(self.file_path)[0] + ".tif"
            if os.path.exists(output_file_path):
                overwrite = confirm_overwrite(output_file_path)
                if not overwrite:
                    self.signals.result.emit(([], ["User canceled overwrite"], []))
                    return
            stdout, stderr = convert_tx_to_tif(self.file_path, output_file_path)
            processed_files.append(output_file_path)
            if stderr:
                error_messages.append(stderr)
            if stdout:
                console_output.append(stdout)
        else:
            output_file_path = os.path.splitext(self.file_path)[0] + ".tx"
            if os.path.exists(output_file_path):
                overwrite = confirm_overwrite(output_file_path)
                if not overwrite:
                    self.signals.result.emit(([], ["User canceled overwrite"], []))
                    return
            stdout, stderr = convert_to_tx(
                self.file_path, output_file_path, self.checkbox1_checked
            )
            processed_files.append(output_file_path)
            if stderr:
                error_messages.append(stderr)
            if stdout:
                console_output.append(stdout)

        console_output.append(f"File {self.file_path} has been processed.")
        self.signals.result.emit((processed_files, error_messages, console_output))


def convert_to_tx(input_file, output_file, add_runstats=False):
    if os.path.exists(output_file):
        overwrite = confirm_overwrite(output_file)
        if not overwrite:
            return "", "User canceled overwrite"

    command = ["oiiotool.exe", input_file, "-otex", output_file]
    if add_runstats:
        command.append("--runstats")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def check_tx_file(tx_file):
    command = ["iinfo.exe", "-v", tx_file]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def convert_tx_to_tif(tx_file, output_tif):
    if os.path.exists(output_tif):
        overwrite = confirm_overwrite(output_tif)
        if not overwrite:
            return "", "User canceled overwrite"

    command = ["oiiotool.exe", tx_file, "-o", output_tif]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


def confirm_overwrite(file_path):
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Confirm Overwrite")
    msg_box.setText(f"File {file_path} already exists. Do you want to overwrite it?")
    msg_box.setIcon(QMessageBox.Warning)
    msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
    msg_box.setDefaultButton(QMessageBox.No)
    response = msg_box.exec()
    return response == QMessageBox.Yes


class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet(
            """
            QWidget {
                background-color: #333333; 
                color: #FFFFFF; 
                font-family: 'dank Mono', Arial, sans-serif; 
            }

            QScrollBar:vertical {
                border: none;
                background: #555555;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }

            QScrollBar::handle:vertical {
                background: #888888;
                min-height: 20px;
            }

            QScrollBar::add-line:vertical {
                background: #555555;
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }

            QScrollBar::sub-line:vertical {
                background: #555555;
                height: 0 px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }

            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                background: none;
            }

            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

        label_style = """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'dank Mono', Arial, sans-serif; 
            }
        """

        self.label = QLabel("Convert to TX file:")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(label_style)

        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)
        self.status_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #272727;
                border-radius: 5px;
                background-color: #222222; 
                color: #FFFFFF; 
            }
            """
        )
        self.status_text_edit.setMinimumHeight(50)

        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: 1px solid #272727;
                border-radius: 5px;
                background-color: #000000; 
                color: #FFFFFF; 
                font-family: 'dank Mono', Arial, sans-serif; 
            }
            """
        )
        self.console_text_edit.setMinimumHeight(50)

        layout = QVBoxLayout()
        layout.addWidget(self.label)

        checkboxes_layout = QHBoxLayout()
        layout.addLayout(checkboxes_layout)

        self.checkbox1 = QCheckBox("--runstats")
        self.checkbox2 = QCheckBox("convert tx to tif")

        checkbox_style = """
            QCheckBox {
                spacing: 10px; 
                font-size: 12px; 
            }
        """
        self.checkbox1.setStyleSheet(checkbox_style)
        self.checkbox2.setStyleSheet(checkbox_style)

        checkboxes_layout.addWidget(self.checkbox1)
        checkboxes_layout.addWidget(self.checkbox2)

        layout.addWidget(self.status_text_edit)
        layout.addWidget(self.console_text_edit)

        self.setLayout(layout)

        self.setAcceptDrops(True)

        self.checkbox1.setChecked(True)
        self.checkbox2.setChecked(False)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        if self.worker_thread and self.worker_thread.isRunning():
            return

        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            for url in urls:
                file_path = url.toLocalFile()
                self.worker_thread = Worker(
                    file_path,
                    self.checkbox1.isChecked(),
                    self.checkbox2.isChecked(),
                )
                self.worker_thread.signals.result.connect(self.handle_worker_result)
                self.worker_thread.start()
            event.accept()
        else:
            event.ignore()

    def handle_worker_result(self, result):
        processed_files, error_messages, console_output = result
        status_text = ""
        if processed_files:
            num_files = len(processed_files)
            status_text += f"Number of processed files: {num_files}\n\n"
            status_text += "Processed files:\n"
            status_text += "\n".join(processed_files)
        else:
            status_text += "No processed files\n\n"

        if error_messages:
            status_text += "\n\nErrors:\n"
            status_text += "\n".join(error_messages)

        self.status_text_edit.clear()
        self.status_text_edit.repaint()
        self.status_text_edit.setPlainText(status_text)

        if console_output:
            self.console_text_edit.clear()
            self.console_text_edit.repaint()
            self.console_text_edit.setPlainText("\n".join(console_output))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DragDropWidget()
    widget.setWindowTitle("Simple GUI for oiiotool 0.22")
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec_())
