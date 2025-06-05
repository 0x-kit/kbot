# ui/widgets/status_widget.py
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QProgressBar, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any

class StatusWidget(QWidget):
    """Widget for displaying bot status and vitals"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Vitals group
        vitals_group = QGroupBox("Vitals")
        vitals_layout = QGridLayout(vitals_group)
        
        # HP
        vitals_layout.addWidget(QLabel("HP:"), 0, 0)
        self.hp_bar = QProgressBar()
        self.hp_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #ff4444;
            }
        """)
        vitals_layout.addWidget(self.hp_bar, 0, 1)
        self.hp_label = QLabel("0%")
        vitals_layout.addWidget(self.hp_label, 0, 2)
        
        # MP
        vitals_layout.addWidget(QLabel("MP:"), 1, 0)
        self.mp_bar = QProgressBar()
        self.mp_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #4444ff;
            }
        """)
        vitals_layout.addWidget(self.mp_bar, 1, 1)
        self.mp_label = QLabel("0%")
        vitals_layout.addWidget(self.mp_label, 1, 2)
        
        layout.addWidget(vitals_group)
        
        # Target group
        target_group = QGroupBox("Target")
        target_layout = QVBoxLayout(target_group)
        
        self.target_name_label = QLabel("No target")
        self.target_name_label.setFont(QFont("Arial", 10, QFont.Bold))
        target_layout.addWidget(self.target_name_label)
        
        # Target HP
        target_hp_layout = QGridLayout()
        target_hp_layout.addWidget(QLabel("Target HP:"), 0, 0)
        self.target_hp_bar = QProgressBar()
        self.target_hp_bar.setStyleSheet("""
            QProgressBar::chunk {
                background-color: #ff8844;
            }
        """)
        target_hp_layout.addWidget(self.target_hp_bar, 0, 1)
        self.target_hp_label = QLabel("0%")
        target_hp_layout.addWidget(self.target_hp_label, 0, 2)
        
        target_layout.addLayout(target_hp_layout)
        layout.addWidget(target_group)
        
        layout.addStretch()
    
    def update_vitals(self, vitals: Dict[str, Any]):
        """Update vitals display"""
        hp = vitals.get('hp', 0)
        mp = vitals.get('mp', 0)
        target_hp = vitals.get('target_health', 0)
        target_exists = vitals.get('target_exists', False)
        
        # Update HP
        self.hp_bar.setValue(hp)
        self.hp_label.setText(f"{hp}%")
        
        # Update MP
        self.mp_bar.setValue(mp)
        self.mp_label.setText(f"{mp}%")
        
        # Update target HP
        if target_exists:
            self.target_hp_bar.setValue(target_hp)
            self.target_hp_label.setText(f"{target_hp}%")
        else:
            self.target_hp_bar.setValue(0)
            self.target_hp_label.setText("0%")
    
    def update_target(self, target_name: str):
        """Update target name display"""
        if target_name:
            self.target_name_label.setText(target_name)
        else:
            self.target_name_label.setText("No target")