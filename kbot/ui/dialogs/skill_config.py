# ============================================================================
# FILE: ui/dialogs/skill_config.py
# ============================================================================
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                            QTreeWidgetItem, QPushButton, QGroupBox, QLineEdit,
                            QSpinBox, QComboBox, QCheckBox, QTextEdit, QLabel,
                            QDialogButtonBox, QMessageBox, QSplitter, QTabWidget,
                            QFormLayout, QListWidget, QWidget, QListWidgetItem)
from PyQt5.QtCore import Qt
from typing import Dict, Any

class SkillConfigDialog(QDialog):
    """Advanced skill configuration dialog"""
    
    def __init__(self, skill_manager=None, parent=None):
        super().__init__(parent)
        self.skill_manager = skill_manager
        self.setWindowTitle("Advanced Skill Configuration")
        self.resize(800, 600)
        
        # Store current skill data
        self.skills_data = {}
        self.rotations_data = {}
        
        self._setup_ui()
        self._load_sample_skills()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_skills_tab()
        self._create_rotations_tab()
        self._create_conditions_tab()
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_skills_tab(self):
        """Create the skills management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - skill list
        left_widget = QGroupBox("Skills")
        left_layout = QVBoxLayout(left_widget)
        
        self.skill_tree = QTreeWidget()
        self.skill_tree.setHeaderLabels(["Skill", "Key", "Cooldown", "Type", "Enabled"])
        self.skill_tree.itemClicked.connect(self._on_skill_selected)
        left_layout.addWidget(self.skill_tree)
        
        # Skill management buttons
        skill_buttons = QHBoxLayout()
        self.add_skill_btn = QPushButton("Add Skill")
        self.add_skill_btn.clicked.connect(self._add_skill)
        self.remove_skill_btn = QPushButton("Remove Skill")
        self.remove_skill_btn.clicked.connect(self._remove_skill)
        self.remove_skill_btn.setEnabled(False)
        
        skill_buttons.addWidget(self.add_skill_btn)
        skill_buttons.addWidget(self.remove_skill_btn)
        left_layout.addLayout(skill_buttons)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - skill details
        right_widget = QGroupBox("Skill Details")
        right_layout = QFormLayout(right_widget)
        
        # Skill properties
        self.skill_name_edit = QLineEdit()
        right_layout.addRow("Name:", self.skill_name_edit)
        
        self.skill_key_edit = QLineEdit()
        right_layout.addRow("Key:", self.skill_key_edit)
        
        self.skill_cooldown_spin = QSpinBox()
        self.skill_cooldown_spin.setRange(1, 3600)
        self.skill_cooldown_spin.setSuffix(" sec")
        right_layout.addRow("Cooldown:", self.skill_cooldown_spin)
        
        self.skill_type_combo = QComboBox()
        self.skill_type_combo.addItems(["offensive", "defensive", "buff", "debuff", "utility", "potion"])
        right_layout.addRow("Type:", self.skill_type_combo)
        
        self.skill_priority_spin = QSpinBox()
        self.skill_priority_spin.setRange(1, 10)
        right_layout.addRow("Priority:", self.skill_priority_spin)
        
        self.skill_mana_spin = QSpinBox()
        self.skill_mana_spin.setRange(0, 1000)
        right_layout.addRow("Mana Cost:", self.skill_mana_spin)
        
        self.skill_enabled_cb = QCheckBox()
        right_layout.addRow("Enabled:", self.skill_enabled_cb)
        
        self.skill_desc_edit = QTextEdit()
        self.skill_desc_edit.setMaximumHeight(100)
        right_layout.addRow("Description:", self.skill_desc_edit)
        
        # Update button
        self.update_skill_btn = QPushButton("Update Skill")
        self.update_skill_btn.clicked.connect(self._update_skill)
        self.update_skill_btn.setEnabled(False)
        right_layout.addRow("", self.update_skill_btn)
        
        layout.addWidget(right_widget, 1)
        
        self.tab_widget.addTab(tab, "Skills")
    
    def _create_rotations_tab(self):
        """Create the rotations management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - rotations list
        left_widget = QGroupBox("Skill Rotations")
        left_layout = QVBoxLayout(left_widget)
        
        self.rotations_list = QListWidget()
        self.rotations_list.itemClicked.connect(self._on_rotation_selected)
        left_layout.addWidget(self.rotations_list)
        
        # Rotation buttons
        rotation_buttons = QHBoxLayout()
        self.add_rotation_btn = QPushButton("Add Rotation")
        self.add_rotation_btn.clicked.connect(self._add_rotation)
        self.remove_rotation_btn = QPushButton("Remove Rotation")
        self.remove_rotation_btn.clicked.connect(self._remove_rotation)
        
        rotation_buttons.addWidget(self.add_rotation_btn)
        rotation_buttons.addWidget(self.remove_rotation_btn)
        left_layout.addLayout(rotation_buttons)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - rotation details
        right_widget = QGroupBox("Rotation Details")
        right_layout = QFormLayout(right_widget)
        
        self.rotation_name_edit = QLineEdit()
        right_layout.addRow("Name:", self.rotation_name_edit)
        
        self.rotation_repeat_cb = QCheckBox()
        self.rotation_repeat_cb.setChecked(True)
        right_layout.addRow("Repeat:", self.rotation_repeat_cb)
        
        # Skills in rotation
        right_layout.addRow("Skills in Rotation:", QLabel())
        self.rotation_skills_list = QListWidget()
        self.rotation_skills_list.setMaximumHeight(150)
        right_layout.addRow("", self.rotation_skills_list)
        
        # Available skills
        right_layout.addRow("Available Skills:", QLabel())
        self.available_skills_list = QListWidget()
        self.available_skills_list.setMaximumHeight(150)
        right_layout.addRow("", self.available_skills_list)
        
        # Skill movement buttons
        skill_move_layout = QHBoxLayout()
        self.add_to_rotation_btn = QPushButton("Add to Rotation")
        self.add_to_rotation_btn.clicked.connect(self._add_skill_to_rotation)
        self.remove_from_rotation_btn = QPushButton("Remove from Rotation")
        self.remove_from_rotation_btn.clicked.connect(self._remove_skill_from_rotation)
        
        skill_move_layout.addWidget(self.add_to_rotation_btn)
        skill_move_layout.addWidget(self.remove_from_rotation_btn)
        right_layout.addRow("", skill_move_layout)
        
        # Update rotation button
        self.update_rotation_btn = QPushButton("Update Rotation")
        self.update_rotation_btn.clicked.connect(self._update_rotation)
        right_layout.addRow("", self.update_rotation_btn)
        
        layout.addWidget(right_widget, 1)
        
        self.tab_widget.addTab(tab, "Rotations")
    
    def _create_conditions_tab(self):
        """Create the conditions tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        info_label = QLabel("""
        <b>Skill Conditions:</b><br>
        Configure when skills should be used based on game state.<br>
        This is an advanced feature for fine-tuning skill behavior.
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        # Placeholder for conditions UI
        conditions_group = QGroupBox("Condition Templates")
        conditions_layout = QVBoxLayout(conditions_group)
        
        # Common condition presets
        preset_buttons = QHBoxLayout()
        
        hp_low_btn = QPushButton("HP Below 50%")
        hp_low_btn.clicked.connect(lambda: self._add_condition_preset("hp_below", 50))
        preset_buttons.addWidget(hp_low_btn)
        
        mp_low_btn = QPushButton("MP Below 30%")
        mp_low_btn.clicked.connect(lambda: self._add_condition_preset("mp_below", 30))
        preset_buttons.addWidget(mp_low_btn)
        
        target_low_btn = QPushButton("Target HP Below 25%")
        target_low_btn.clicked.connect(lambda: self._add_condition_preset("target_hp_below", 25))
        preset_buttons.addWidget(target_low_btn)
        
        conditions_layout.addLayout(preset_buttons)
        
        # Conditions list
        self.conditions_list = QListWidget()
        conditions_layout.addWidget(self.conditions_list)
        
        layout.addWidget(conditions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Conditions")
    
    def _load_sample_skills(self):
        """Load sample skills for demonstration"""
        sample_skills = [
            {"name": "Basic Attack", "key": "r", "cooldown": 2, "type": "offensive", "priority": 1, "mana": 0, "enabled": True, "desc": "Basic attack skill"},
            {"name": "HP Potion", "key": "0", "cooldown": 1, "type": "potion", "priority": 10, "mana": 0, "enabled": True, "desc": "Health potion"},
            {"name": "MP Potion", "key": "9", "cooldown": 1, "type": "potion", "priority": 10, "mana": 0, "enabled": True, "desc": "Mana potion"},
            {"name": "Skill 1", "key": "1", "cooldown": 1, "type": "offensive", "priority": 3, "mana": 10, "enabled": True, "desc": "Slot 1 skill"},
            {"name": "Skill 2", "key": "2", "cooldown": 1, "type": "offensive", "priority": 3, "mana": 15, "enabled": True, "desc": "Slot 2 skill"},
            {"name": "Skill F1", "key": "f1", "cooldown": 120, "type": "offensive", "priority": 7, "mana": 50, "enabled": True, "desc": "F1 skill"},
        ]
        
        for skill in sample_skills:
            self.skills_data[skill["name"]] = skill
            self._add_skill_to_tree(skill)
        
        self._update_available_skills()
    
    def _add_skill_to_tree(self, skill):
        """Add skill to the tree widget"""
        item = QTreeWidgetItem([
            skill["name"],
            skill["key"],
            f"{skill['cooldown']} sec",
            skill["type"],
            "Yes" if skill["enabled"] else "No"
        ])
        item.setData(0, Qt.UserRole, skill["name"])
        self.skill_tree.addTopLevelItem(item)
    
    def _on_skill_selected(self, item, column):
        """Handle skill selection"""
        skill_name = item.data(0, Qt.UserRole)
        if skill_name and skill_name in self.skills_data:
            skill = self.skills_data[skill_name]
            
            # Load skill data into form
            self.skill_name_edit.setText(skill["name"])
            self.skill_key_edit.setText(skill["key"])
            self.skill_cooldown_spin.setValue(skill["cooldown"])
            self.skill_type_combo.setCurrentText(skill["type"])
            self.skill_priority_spin.setValue(skill["priority"])
            self.skill_mana_spin.setValue(skill["mana"])
            self.skill_enabled_cb.setChecked(skill["enabled"])
            self.skill_desc_edit.setPlainText(skill["desc"])
            
            self.update_skill_btn.setEnabled(True)
            self.remove_skill_btn.setEnabled(True)
    
    def _add_skill(self):
        """Add a new skill"""
        # Clear form for new skill
        self.skill_name_edit.setText("New Skill")
        self.skill_key_edit.setText("")
        self.skill_cooldown_spin.setValue(1)
        self.skill_type_combo.setCurrentIndex(0)
        self.skill_priority_spin.setValue(1)
        self.skill_mana_spin.setValue(0)
        self.skill_enabled_cb.setChecked(True)
        self.skill_desc_edit.setPlainText("")
        
        self.update_skill_btn.setEnabled(True)
    
    def _update_skill(self):
        """Update the selected skill"""
        name = self.skill_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Skill name cannot be empty")
            return
        
        skill = {
            "name": name,
            "key": self.skill_key_edit.text().strip(),
            "cooldown": self.skill_cooldown_spin.value(),
            "type": self.skill_type_combo.currentText(),
            "priority": self.skill_priority_spin.value(),
            "mana": self.skill_mana_spin.value(),
            "enabled": self.skill_enabled_cb.isChecked(),
            "desc": self.skill_desc_edit.toPlainText()
        }
        
        # Update skills data
        self.skills_data[name] = skill
        
        # Refresh tree
        self._refresh_skill_tree()
        self._update_available_skills()
        
        QMessageBox.information(self, "Success", f"Skill '{name}' updated successfully!")
    
    def _remove_skill(self):
        """Remove the selected skill"""
        current_item = self.skill_tree.currentItem()
        if current_item:
            skill_name = current_item.data(0, Qt.UserRole)
            if skill_name in self.skills_data:
                del self.skills_data[skill_name]
                self._refresh_skill_tree()
                self._update_available_skills()
                self.update_skill_btn.setEnabled(False)
                self.remove_skill_btn.setEnabled(False)
    
    def _refresh_skill_tree(self):
        """Refresh the skill tree widget"""
        self.skill_tree.clear()
        for skill in self.skills_data.values():
            self._add_skill_to_tree(skill)
    
    def _update_available_skills(self):
        """Update the available skills list for rotations"""
        self.available_skills_list.clear()
        for skill_name in self.skills_data.keys():
            self.available_skills_list.addItem(skill_name)
    
    def _add_rotation(self):
        """Add a new rotation"""
        name = f"Rotation {len(self.rotations_data) + 1}"
        self.rotations_data[name] = {
            "name": name,
            "skills": [],
            "repeat": True
        }
        self.rotations_list.addItem(name)
    
    def _remove_rotation(self):
        """Remove selected rotation"""
        current_item = self.rotations_list.currentItem()
        if current_item:
            name = current_item.text()
            if name in self.rotations_data:
                del self.rotations_data[name]
                self.rotations_list.takeItem(self.rotations_list.row(current_item))
    
    def _on_rotation_selected(self, item):
        """Handle rotation selection"""
        name = item.text()
        if name in self.rotations_data:
            rotation = self.rotations_data[name]
            self.rotation_name_edit.setText(rotation["name"])
            self.rotation_repeat_cb.setChecked(rotation["repeat"])
            
            # Update skills in rotation list
            self.rotation_skills_list.clear()
            for skill in rotation["skills"]:
                self.rotation_skills_list.addItem(skill)
    
    def _add_skill_to_rotation(self):
        """Add selected skill to rotation"""
        current_skill = self.available_skills_list.currentItem()
        if current_skill:
            self.rotation_skills_list.addItem(current_skill.text())
    
    def _remove_skill_from_rotation(self):
        """Remove selected skill from rotation"""
        current_item = self.rotation_skills_list.currentItem()
        if current_item:
            self.rotation_skills_list.takeItem(self.rotation_skills_list.row(current_item))
    
    def _update_rotation(self):
        """Update the selected rotation"""
        current_item = self.rotations_list.currentItem()
        if current_item:
            old_name = current_item.text()
            new_name = self.rotation_name_edit.text().strip()
            
            if not new_name:
                QMessageBox.warning(self, "Error", "Rotation name cannot be empty")
                return
            
            # Get skills from list
            skills = []
            for i in range(self.rotation_skills_list.count()):
                skills.append(self.rotation_skills_list.item(i).text())
            
            # Update rotation data
            if old_name in self.rotations_data:
                del self.rotations_data[old_name]
            
            self.rotations_data[new_name] = {
                "name": new_name,
                "skills": skills,
                "repeat": self.rotation_repeat_cb.isChecked()
            }
            
            # Update list item
            current_item.setText(new_name)
            
            QMessageBox.information(self, "Success", f"Rotation '{new_name}' updated successfully!")
    
    def _add_condition_preset(self, condition_type: str, value: int):
        """Add a condition preset"""
        condition_text = f"{condition_type.replace('_', ' ').title()}: {value}%"
        self.conditions_list.addItem(condition_text)
    
    def accept(self):
        """Accept dialog and return configuration"""
        try:
            # In a complete implementation, this would apply the configuration
            # to the skill manager
            QMessageBox.information(self, "Success", "Skill configuration saved!")
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def get_skills_config(self):
        """Get the configured skills"""
        return {
            "skills": self.skills_data,
            "rotations": self.rotations_data
        }