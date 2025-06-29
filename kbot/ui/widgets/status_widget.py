# ui/widgets/status_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QProgressBar, QGroupBox, QFrame
)
from PyQt5.QtGui import QPixmap
import os
from PyQt5.QtCore import Qt
from typing import Dict, Any, List

class StatusWidget(QWidget):
    """Widget for displaying bot status and vitals"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Main status group - reorganized to single column
        main_group = QGroupBox("Game Status")
        main_layout = QVBoxLayout(main_group)
        
        # Vitals section
        vitals_frame = QFrame()
        vitals_frame.setFrameStyle(QFrame.StyledPanel)
        vitals_layout = QGridLayout(vitals_frame)
        
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
        
        # Set column proportions for consistent bar width
        vitals_layout.setColumnStretch(0, 0)  # Labels fixed width
        vitals_layout.setColumnStretch(1, 1)  # Bars stretch
        vitals_layout.setColumnStretch(2, 0)  # Percentage labels fixed width
        
        main_layout.addWidget(vitals_frame)
        
        # Target section - same width as vitals
        target_frame = QFrame()
        target_frame.setFrameStyle(QFrame.StyledPanel)
        target_layout = QVBoxLayout(target_frame)
        
        self.target_name_label = QLabel("No target")
        self.target_name_label.setStyleSheet("font-weight: bold; text-align: center;")
        self.target_name_label.setAlignment(Qt.AlignCenter)
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
        
        # Set same column proportions as vitals for consistent width
        target_hp_layout.setColumnStretch(0, 0)  # Labels fixed width
        target_hp_layout.setColumnStretch(1, 1)  # Bars stretch
        target_hp_layout.setColumnStretch(2, 0)  # Percentage labels fixed width
        
        target_layout.addLayout(target_hp_layout)
        main_layout.addWidget(target_frame)
        
        layout.addWidget(main_group)
        
        # Skillbar section
        self._setup_skillbar_widget()
        layout.addWidget(self.skillbar_group)
        
        layout.addStretch()
    
    def _setup_skillbar_widget(self):
        """Setup skillbar status widget with grid layout"""
        self.skillbar_group = QGroupBox("🎯 Skillbar Status")
        skillbar_layout = QVBoxLayout(self.skillbar_group)
        
        # Skills container with grid layout
        self.skills_frame = QFrame()
        self.skills_layout = QGridLayout(self.skills_frame)
        self.skills_layout.setSpacing(5)
        self.skills_layout.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Align to top-left
        
        # Default message when no skills configured
        self.no_skills_label = QLabel("No skills configured")
        self.no_skills_label.setAlignment(Qt.AlignCenter)
        self.no_skills_label.setStyleSheet("color: #666; font-style: italic;")
        self.skills_layout.addWidget(self.no_skills_label, 0, 0, 1, 2)  # Span 2 columns
        
        skillbar_layout.addWidget(self.skills_frame)
        
        # Skills data storage
        self.skill_widgets = {}  # {skill_name: widget}
        self.skills_count = 0
    
    def update_vitals(self, vitals: Dict[str, Any]):
        """Actualiza TODOS los elementos del widget con la información de vitals."""
        hp = vitals.get('hp', 0)
        mp = vitals.get('mp', 0)
        target_name = vitals.get('target_name', 'No target')
        target_hp = vitals.get('target_health', 0)
        
        # Actualizar HP
        self.hp_bar.setValue(hp)
        self.hp_label.setText(f"{hp}%")
        
        # Actualizar MP
        self.mp_bar.setValue(mp)
        self.mp_label.setText(f"{mp}%")

        # Actualizar Target Name
        self.target_name_label.setText(target_name if target_name else "No target")

        # Actualizar Target HP
        self.target_hp_bar.setValue(target_hp)
        self.target_hp_label.setText(f"{target_hp}%")
    
    def update_skills(self, skills_data: List[Dict[str, Any]]):
        """Update skillbar display with current skills status"""
        # Clear existing skills
        for skill_name in list(self.skill_widgets.keys()):
            self._remove_skill_widget(skill_name)
        self.skills_count = 0  # Reset counter
        
        if not skills_data:
            self.no_skills_label.show()
            return
            
        self.no_skills_label.hide()
        
        # Add skills - pasamos todo el diccionario de datos
        for skill_data in skills_data:
            self._add_skill_widget(skill_data)
    
    def _add_skill_widget(self, skill_data: Dict[str, Any]):
        """Add a skill widget to the skillbar grid display"""
        name = skill_data['name']
        key = skill_data['key']
        enabled = skill_data['enabled']
        skill_type = skill_data['type']
        icon_path = skill_data.get('icon', '')
        
        # Create skill widget
        skill_widget = QFrame()
        skill_widget.setFrameStyle(QFrame.Box)
        skill_widget.setFixedSize(120, 60)  # Compact size
        skill_layout = QVBoxLayout(skill_widget)
        skill_layout.setContentsMargins(3, 3, 3, 3)
        skill_layout.setSpacing(2)
        
        # Top row: Icon + Key + Name
        top_layout = QHBoxLayout()
        top_layout.setSpacing(3)
        
        # Icon (small)
        icon_label = QLabel()
        icon_label.setFixedSize(16, 16)
        if icon_path and os.path.exists(icon_path):
            try:
                pixmap = QPixmap(icon_path)
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(16, 16, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    icon_label.setPixmap(scaled_pixmap)
                else:
                    icon_label.setText("🎯")  # Fallback emoji
            except Exception:
                icon_label.setText("🎯")  # Fallback emoji
        else:
            icon_label.setText("🎯")  # Default emoji
        icon_label.setStyleSheet("color: #888;")
        top_layout.addWidget(icon_label)
        
        # Key + Name
        name_label = QLabel(f"[{key}] {name[:6]}.." if len(name) > 6 else f"[{key}] {name}")
        name_label.setStyleSheet("color: #333; font-size: 10px; font-weight: bold;")
        top_layout.addWidget(name_label)
        
        skill_layout.addLayout(top_layout)
        
        # Status line with color coding
        if not enabled:
            status_text = "Disabled"
            status_color = "#999"  # Gris para disabled
        elif skill_type == 'offensive':
            if skill_data.get('visual_cooldown', False):
                status_text = "Cooldown"
                status_color = "#f39c12"  # Naranja para cooldown
            else:
                status_text = "Ready"
                status_color = "#27ae60"  # Verde para ready
        elif skill_type == 'buff':
            buff_remaining = skill_data.get('buff_remaining', 0)
            if buff_remaining > 0:
                status_text = f"{buff_remaining:.0f}s left"
                status_color = "#3498db"  # Azul para buff activo
            else:
                status_text = "Expired"
                status_color = "#e67e22"  # Naranja para expired
        else:
            status_text = "Unknown"
            status_color = "#999"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-size: 9px; font-weight: bold;")
        status_label.setAlignment(Qt.AlignCenter)
        skill_layout.addWidget(status_label)
        
        # Type indicator
        type_label = QLabel(skill_type.capitalize())
        type_label.setStyleSheet("color: #999; font-size: 8px;")
        type_label.setAlignment(Qt.AlignCenter)
        skill_layout.addWidget(type_label)
        
        # Calculate grid position (2 columns)
        row = self.skills_count // 2
        col = self.skills_count % 2
        
        # Store widget references
        self.skill_widgets[name] = {
            'widget': skill_widget,
            'icon_label': icon_label,
            'name_label': name_label,
            'status_label': status_label,
            'type_label': type_label,
            'row': row,
            'col': col
        }
        
        self.skills_layout.addWidget(skill_widget, row, col)
        self.skills_count += 1
    
    def _remove_skill_widget(self, skill_name: str):
        """Remove a skill widget from display"""
        if skill_name in self.skill_widgets:
            widget_data = self.skill_widgets[skill_name]
            widget_data['widget'].setParent(None)
            del self.skill_widgets[skill_name]
            self.skills_count = max(0, self.skills_count - 1)
    
    def update_target(self, target_name: str):
        """Update target name display"""
        if target_name:
            self.target_name_label.setText(target_name)
        else:
            self.target_name_label.setText("No target")