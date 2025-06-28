# ui/widgets/status_widget.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, 
    QProgressBar, QGroupBox, QFrame
)
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
        
        target_layout.addLayout(target_hp_layout)
        main_layout.addWidget(target_frame)
        
        layout.addWidget(main_group)
        
        # Skillbar section
        self._setup_skillbar_widget()
        layout.addWidget(self.skillbar_group)
        
        layout.addStretch()
    
    def _setup_skillbar_widget(self):
        """Setup skillbar status widget"""
        self.skillbar_group = QGroupBox("🎯 Skillbar Status")
        skillbar_layout = QVBoxLayout(self.skillbar_group)
        
        # Skills container
        self.skills_frame = QFrame()
        self.skills_layout = QVBoxLayout(self.skills_frame)
        
        # Default message when no skills configured
        self.no_skills_label = QLabel("No skills configured")
        self.no_skills_label.setAlignment(Qt.AlignCenter)
        self.no_skills_label.setStyleSheet("color: #666; font-style: italic;")
        self.skills_layout.addWidget(self.no_skills_label)
        
        skillbar_layout.addWidget(self.skills_frame)
        
        # Skills data storage
        self.skill_widgets = {}  # {skill_name: {label, status_label, progress_bar}}
    
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
        
        if not skills_data:
            self.no_skills_label.show()
            return
            
        self.no_skills_label.hide()
        
        # Add skills
        for skill_data in skills_data:
            skill_name = skill_data.get('name', 'Unknown')
            skill_key = skill_data.get('key', '?')
            skill_enabled = skill_data.get('enabled', False)
            skill_cooldown = skill_data.get('cooldown_remaining', 0)
            skill_type = skill_data.get('type', 'Unknown')
            
            self._add_skill_widget(skill_name, skill_key, skill_enabled, skill_cooldown, skill_type)
    
    def _add_skill_widget(self, name: str, key: str, enabled: bool, cooldown: float, skill_type: str):
        """Add a skill widget to the skillbar display"""
        skill_frame = QFrame()
        skill_frame.setFrameStyle(QFrame.Box)
        skill_layout = QHBoxLayout(skill_frame)
        skill_layout.setContentsMargins(5, 3, 5, 3)
        
        # Skill info
        info_label = QLabel(f"[{key}] {name}")
        info_label.setMinimumWidth(120)
        skill_layout.addWidget(info_label)
        
        # Status indicator
        if cooldown > 0:
            status_text = f"CD: {cooldown:.1f}s"
            status_color = "#ff8800"
        elif enabled:
            status_text = "Ready"
            status_color = "#00aa00"
        else:
            status_text = "Disabled"
            status_color = "#666666"
        
        status_label = QLabel(status_text)
        status_label.setStyleSheet(f"color: {status_color}; font-weight: bold;")
        status_label.setMinimumWidth(70)
        skill_layout.addWidget(status_label)
        
        # Type indicator
        type_label = QLabel(f"({skill_type})")
        type_label.setStyleSheet("color: #888; font-size: 10px;")
        skill_layout.addWidget(type_label)
        
        # Store widget references
        self.skill_widgets[name] = {
            'frame': skill_frame,
            'info_label': info_label,
            'status_label': status_label,
            'type_label': type_label
        }
        
        self.skills_layout.addWidget(skill_frame)
    
    def _remove_skill_widget(self, skill_name: str):
        """Remove a skill widget from display"""
        if skill_name in self.skill_widgets:
            widget_data = self.skill_widgets[skill_name]
            widget_data['frame'].setParent(None)
            del self.skill_widgets[skill_name]
    
    def update_target(self, target_name: str):
        """Update target name display"""
        if target_name:
            self.target_name_label.setText(target_name)
        else:
            self.target_name_label.setText("No target")