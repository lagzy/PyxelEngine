"""
Editor Console Panel with stdout/stderr redirection.
"""
import sys
from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QTextCursor

class ConsoleStream(QObject):
    text_written = Signal(str)

    def write(self, text):
        if text:
            self.text_written.emit(text)

    def flush(self):
        pass

class ConsolePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)

        self.stdout_stream = ConsoleStream()
        self.stderr_stream = ConsoleStream()
        self.stdout_stream.text_written.connect(self.append_stdout)
        self.stderr_stream.text_written.connect(self.append_stderr)

        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self.stdout_stream
        sys.stderr = self.stderr_stream

    def append_stdout(self, text):
        self.text_edit.setTextColor(Qt.white)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def append_stderr(self, text):
        self.text_edit.setTextColor(Qt.red)
        self.text_edit.insertPlainText(text)
        self.text_edit.moveCursor(QTextCursor.End)

    def closeEvent(self, event):
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        super().closeEvent(event)
