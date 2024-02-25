import os
import subprocess
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def convert_to_tx(input_file, output_file, add_runstats=False):
    try:
        command = ["oiiotool.exe", input_file, "-otex", output_file]
        if add_runstats:
            command.append("--runstats")
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr
    except Exception as e:
        return "", str(e)


def check_tx_file(tx_file):
    try:
        command = ["iinfo.exe", "-v", tx_file]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr
    except Exception as e:
        return "", str(e)


def convert_tx_to_tif(tx_file, output_tif):
    try:
        command = ["oiiotool.exe", tx_file, "-o", output_tif]
        process = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        return stdout, stderr
    except Exception as e:
        return "", str(e)


class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Setting Fusion style for the whole application
        QApplication.setStyle("fusion")

        self.label = QLabel("Convert to TX file:")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet(
            "font-family: 'Dank Mono', Arial; font-size: 16px; color: #2196f3;"
        )
        self.label.setMinimumHeight(50)  # Ustawienie minimalnej wysokości

        # Creating QTextEdit for status bar
        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)
        self.status_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: none;
                background-color: #242424;
                color: #FFFFFF;
                font-family: 'Dank Mono', Arial;
                font-size: 12px;
            }
            """
        )
        # Creating separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Creating QTextEdit for console information
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)
        self.console_text_edit.setStyleSheet(
            """
            QTextEdit {
                border: none;
                background-color: #232323;
                color: #FFFFFF;
                font-family: 'Dank Mono', Arial;
                font-size: 12px;
            }
            """
        )

        # Creating progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                border: none;
                border-radius: 5px;
                background-color: #232323; /* Background */
                color: #FFFFFF; /* Text color */
                height: 10px; /* Height */
            }
            QProgressBar::chunk {
                background-color: #2196f3;
            }
            """
        )

        # Creating checkboxes
        self.checkbox1 = QCheckBox("show stats")
        self.checkbox2 = QCheckBox("convert tx to tif")

        # Applying styles to checkboxes
        for checkbox in (self.checkbox1, self.checkbox2):
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    color: #FFFFFF;
                    font-family: 'Dank Mono', Arial;
                    font-size: 12px;
                    spacing: 10px;
                }
                QCheckBox::indicator:unchecked {
                    background-color: #4d4d4d;
                }
                """
            )

        # Creating layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # Creating layout for checkboxes
        checkboxes_layout = QHBoxLayout()
        layout.addLayout(checkboxes_layout)

        # Adding checkboxes to layout
        checkboxes_layout.addWidget(self.checkbox1)
        checkboxes_layout.addWidget(self.checkbox2)

        # Adding QTextEdit to layout
        layout.addWidget(self.status_text_edit)
        layout.addWidget(separator)
        layout.addWidget(self.console_text_edit)

        # Adding progress bar to layout
        layout.addWidget(self.progress_bar)

        # Setting layout
        self.setLayout(layout)

        # Setting drag and drop event handling
        self.setAcceptDrops(True)

        # Setting default values for checkboxes
        self.checkbox1.setChecked(True)
        self.checkbox2.setChecked(False)

        # Adding custom style for scroll bars
        self.setStyleSheet(
            """
            QScrollBar:vertical {
                border: none;
                background: #2c2c2c;
                width: 10px;
                margin: 0px; /* Usunięcie marginesu */
            }
            QScrollBar::handle:vertical {
                background-color: #2196f3;
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical {
                height: 0;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
            QScrollBar::up-arrow:vertical, QScrollBar::down-arrow:vertical {
                border: none;
                background: none;
                color: none;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            """
        )

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            self.process_dropped_files(urls)
            event.accept()
        else:
            event.ignore()

    def process_tx_file(self, file_path):
        """
        Process .tx file based on user choice.
        """
        stdout, stderr = "", ""
        if not os.path.exists(file_path):
            stderr = f"File not found: {file_path}"
        elif file_path.endswith(".tx") and not self.checkbox2.isChecked():
            stdout, stderr = check_tx_file(file_path)
        elif file_path.endswith(".tx") and self.checkbox2.isChecked():
            output_file_path = os.path.splitext(file_path)[0] + ".tif"
            if os.path.exists(output_file_path):
                overwrite = self.confirm_overwrite(output_file_path)
                if not overwrite:
                    return stdout, stderr
            stdout, stderr = convert_tx_to_tif(file_path, output_file_path)
        else:
            output_file_path = os.path.splitext(file_path)[0] + ".tx"
            if os.path.exists(output_file_path):
                overwrite = self.confirm_overwrite(output_file_path)
                if not overwrite:
                    return stdout, stderr
            stdout, stderr = convert_to_tx(file_path, output_file_path, self.checkbox1.isChecked())

        return stdout, stderr

    def process_dropped_files(self, file_urls):
        """
        Process files dropped onto the widget.
        """
        processed_files = []
        error_messages = []
        console_output = []
        
        total_files = len(file_urls)
        files_processed = 0

        for url in file_urls:
            file_path = url.toLocalFile()

            try:
                stdout, stderr = self.process_tx_file(file_path)
                if stderr:
                    error_messages.append(stderr)
                if stdout:
                    console_output.append(stdout)
                processed_files.append(file_path)
            except Exception as e:
                error_messages.append(str(e))

            files_processed += 1
            progress = int((files_processed / total_files) * 100)
            self.progress_bar.setValue(progress)

            console_output.append(f"File {file_path} has been processed.")

        self.update_status_bar(processed_files, error_messages)
        if console_output:
            self.update_console_text("\n".join(console_output))

    def confirm_overwrite(self, file_path):
        msg_box = QMessageBox()
        msg_box.setWindowTitle("Confirm Overwrite")
        msg_box.setText(
            f"File {file_path} already exists. Do you want to overwrite it?"
        )
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setStandardButtons(
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        msg_box.setDefaultButton(QMessageBox.No)
        response = msg_box.exec()
        return response == QMessageBox.Yes

    def update_status_bar(self, processed_files, error_messages):
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

        self.status_text_edit.setPlainText(status_text)

        # Reset progress bar
        self.progress_bar.setValue(0)

    def update_console_text(self, text):
        self.console_text_edit.setPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DragDropWidget()
    widget.setWindowTitle("Simple GUI for oiiotool 0.30")
    widget.resize(800, 600)
    widget.show()
    sys.exit(app.exec())
