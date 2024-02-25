import os
import subprocess
import sys

from PySide6.QtCore import QMimeData, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


def convert_to_tx(input_file, output_file, add_runstats=False):
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
    command = ["oiiotool.exe", tx_file, "-o", output_tif]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    )
    stdout, stderr = process.communicate()
    return stdout, stderr


class DragDropWidget(QWidget):
    def __init__(self):
        super().__init__()

        # Creating QTextEdit for status bar
        self.status_text_edit = QTextEdit()
        self.status_text_edit.setReadOnly(True)  # Setting read-only

        # Creating QTextEdit for console information
        self.console_text_edit = QTextEdit()
        self.console_text_edit.setReadOnly(True)  # Setting read-only
        self.console_text_edit.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )

        # Creating label
        self.label = QLabel("Convert to TX file:")
        self.label.setAlignment(Qt.AlignCenter)

        # Setting style for label
        self.label.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 10px;
                font-family: 'Dank Mono', Arial, sans-serif; /* Font family */
            }
        """
        )

        # Setting style for status bar
        self.status_text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                font-family: 'Dank Mono', Arial, sans-serif; /* Font family */
            }
        """
        )

        # Setting style for console information
        self.console_text_edit.setStyleSheet(
            """
            QTextEdit {
                background-color: #000000;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 5px;
                color: #FFFFFF;
                font-family: 'Dank Mono', Arial, sans-serif; /* Font family */
            }
        """
        )

        # Creating layout for widget
        layout = QVBoxLayout()
        layout.addWidget(self.label)

        # Creating and setting layout for checkboxes
        checkboxes_layout = QHBoxLayout()
        layout.addLayout(checkboxes_layout)

        # Adding checkboxes
        self.checkbox1 = QCheckBox("--runstats")
        self.checkbox2 = QCheckBox("convert tx to tif")

        layout.addWidget(self.status_text_edit)
        layout.addWidget(self.console_text_edit)

        # Setting additional styles for checkboxes
        checkboxes = [
            self.checkbox1,
            self.checkbox2,
        ]
        for checkbox in checkboxes:
            checkbox.setStyleSheet(
                """
                QCheckBox {
                    spacing: 10px; /* Spacing between text and button */
                    font-size: 12px; /* Text size */
                    font-family: 'Dank Mono', Arial, sans-serif; /* Font family */
                }
            """
            )

        # Setting two columns for checkboxes
        column1 = QVBoxLayout()
        column2 = QVBoxLayout()
        for i, checkbox in enumerate(checkboxes):
            if i < len(checkboxes) / 2:
                column1.addWidget(checkbox)
            else:
                column2.addWidget(checkbox)

        checkboxes_layout.addLayout(column1)
        checkboxes_layout.addLayout(column2)

        # Setting drag and drop event handling
        self.setLayout(layout)
        self.setAcceptDrops(True)

        # Checking --runstats checkbox at startup
        self.checkbox1.setChecked(True)
        self.checkbox2.setChecked(False)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            urls = mime_data.urls()
            processed_files = []
            error_messages = []  # Storing error messages
            console_output = []  # Storing console output

            for url in urls:
                file_path = url.toLocalFile()

                if not os.path.exists(file_path):
                    error_messages.append(f"File not found: {file_path}")
                    continue

                if file_path.endswith(".tx") and not self.checkbox2.isChecked():
                    stdout, stderr = check_tx_file(file_path)
                    processed_files.append(file_path)
                    if stderr:
                        error_messages.append(stderr)  # Add error message to the list
                    if stdout:
                        console_output.append(stdout)
                elif file_path.endswith(".tx") and self.checkbox2.isChecked():
                    output_file_path = os.path.splitext(file_path)[0] + ".tif"
                    if os.path.exists(output_file_path):
                        overwrite = self.confirm_overwrite(output_file_path)
                        if not overwrite:
                            continue
                    stdout, stderr = convert_tx_to_tif(file_path, output_file_path)
                    processed_files.append(output_file_path)
                    if stderr:
                        error_messages.append(stderr)  # Add error message to the list
                    if stdout:
                        console_output.append(stdout)
                else:
                    output_file_path = os.path.splitext(file_path)[0] + ".tx"
                    if os.path.exists(output_file_path):
                        overwrite = self.confirm_overwrite(output_file_path)
                        if not overwrite:
                            continue
                    stdout, stderr = convert_to_tx(
                        file_path, output_file_path, self.checkbox1.isChecked()
                    )
                    processed_files.append(output_file_path)
                    if stderr:
                        error_messages.append(stderr)  # Add error message to the list
                    if stdout:
                        console_output.append(stdout)

                # Add confirmation in console
                console_output.append(f"File {file_path} has been processed.")

            self.update_status_bar(processed_files, error_messages)

            # Update console information window
            if console_output:
                self.update_console_text("\n".join(console_output))

            event.accept()
        else:
            event.ignore()

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

    def update_console_text(self, text):
        self.console_text_edit.setPlainText(text)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = DragDropWidget()
    widget.setWindowTitle("Simple GUI for oiiotool 0.2")
    widget.resize(900, 600)
    widget.show()
    sys.exit(app.exec())
