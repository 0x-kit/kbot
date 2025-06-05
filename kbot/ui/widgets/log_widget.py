# ui/widgets/log_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QTextCursor, QFont

class LogWidget(QWidget):
    """Widget for displaying bot logs"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_lines = 1000
        self.auto_scroll = True
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control bar
        control_layout = QHBoxLayout()
        
        self.auto_scroll_cb = QCheckBox("Auto-scroll")
        self.auto_scroll_cb.setChecked(True)
        self.auto_scroll_cb.stateChanged.connect(self._on_auto_scroll_changed)
        control_layout.addWidget(self.auto_scroll_cb)
        
        control_layout.addStretch()
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_btn)
        
        layout.addLayout(control_layout)
        
        # Log display
        self.log_display = QTextBrowser()
        self.log_display.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_display)
    
    @pyqtSlot(str)
    def add_message(self, message: str):
        """Add a message to the log"""
        self.log_display.append(message)
        
        # Limit number of lines
        if self.log_display.document().lineCount() > self.max_lines:
            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 
                              self.log_display.document().lineCount() - self.max_lines)
            cursor.removeSelectedText()
        
        # Auto-scroll to bottom
        if self.auto_scroll:
            self.log_display.moveCursor(QTextCursor.End)
    
    def clear_log(self):
        """Clear the log display"""
        self.log_display.clear()
    
    def _on_auto_scroll_changed(self, state):
        """Handle auto-scroll checkbox change"""
        self.auto_scroll = state == Qt.Checked