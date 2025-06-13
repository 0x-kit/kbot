from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QPushButton, QGroupBox, QLineEdit, QLabel, 
                            QDialogButtonBox, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt
from core.window_manager import WindowManager
from utils.exceptions import WindowError

class WindowSelectorDialog(QDialog):
    """Dialog for selecting and managing game windows"""
    
    def __init__(self, window_manager: WindowManager, parent=None):
        super().__init__(parent)
        self.window_manager = window_manager
        self.setWindowTitle("Select Game Window")
        self.setFixedSize(500, 600)
        self._setup_ui()
        self._refresh_windows()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Window renamer section
        renamer_group = QGroupBox("Window Renamer")
        renamer_layout = QVBoxLayout(renamer_group)
        
        renamer_layout.addWidget(QLabel("Current window title:"))
        self.current_title_edit = QLineEdit()
        self.current_title_edit.setPlaceholderText("Enter exact window title to rename")
        renamer_layout.addWidget(self.current_title_edit)
        
        renamer_layout.addWidget(QLabel("New window title:"))
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("Enter new window title")
        renamer_layout.addWidget(self.new_title_edit)
        
        self.rename_btn = QPushButton("Rename Window")
        self.rename_btn.clicked.connect(self._rename_window)
        renamer_layout.addWidget(self.rename_btn)
        
        layout.addWidget(renamer_group)
        
        # Window selector section
        selector_group = QGroupBox("Available Windows")
        selector_layout = QVBoxLayout(selector_group)
        
        self.window_list = QListWidget()
        self.window_list.itemDoubleClicked.connect(self.accept)
        selector_layout.addWidget(self.window_list)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Window List")
        self.refresh_btn.clicked.connect(self._refresh_windows)
        selector_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(selector_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _refresh_windows(self):
        """Refresh the list of available windows"""
        self.window_list.clear()
        
        try:
            windows = self.window_manager.get_all_windows(refresh_cache=True)
            
            for window in windows:
                item = QListWidgetItem(f"{window.title} (0x{window.hwnd:X})")
                item.setData(Qt.UserRole, window.hwnd)
                self.window_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh windows: {e}")
    
    def _rename_window(self):
        """Rename a window"""
        current_title = self.current_title_edit.text()
        new_title = self.new_title_edit.text().strip()
        
        if not current_title or not new_title:
            QMessageBox.warning(self, "Error", "Both current and new titles must be specified")
            return
        
        try:
            # Find window by title
            windows = self.window_manager.get_all_windows()
            target_window = None
            
            for window in windows:
                if window.title == current_title:
                    target_window = window
                    break
            
            if not target_window:
                QMessageBox.warning(self, "Error", f"Window with title '{current_title}' not found")
                return
            
            # Rename the window
            if self.window_manager.rename_window(new_title, target_window.hwnd):
                QMessageBox.information(self, "Success", "Window renamed successfully!")
                self._refresh_windows()
                self.current_title_edit.clear()
                self.new_title_edit.clear()
            
        except WindowError as e:
            QMessageBox.critical(self, "Error", f"Failed to rename window: {e}")
    
    def get_selected_window_hwnd(self):
        """Get the selected window handle"""
        current_item = self.window_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
    
    def accept(self):
        """Accept dialog and set target window"""
        hwnd = self.get_selected_window_hwnd()
        if hwnd:
            try:
                if self.window_manager.set_target_window(hwnd):
                    super().accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to set target window")
            except WindowError as e:
                QMessageBox.critical(self, "Error", f"Failed to set target window: {e}")
        else:
            QMessageBox.warning(self, "Error", "Please select a window")