# ============================================================================
# FILE: ui/dialogs/skill_config.py
# ============================================================================
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QGroupBox,
    QLineEdit,
    QSpinBox,
    QComboBox,
    QCheckBox,
    QTextEdit,
    QLabel,
    QDialogButtonBox,
    QMessageBox,
    QSplitter,
    QTabWidget,
    QFormLayout,
    QListWidget,
    QWidget,
    QListWidgetItem,
)
from PyQt5.QtCore import Qt
from typing import Dict, Any


class SkillConfigDialog(QDialog):
    """Advanced skill configuration dialog - FUNCTIONAL VERSION"""

    def __init__(self, skill_manager=None, config_manager=None, parent=None):
        super().__init__(parent)
        self.skill_manager = skill_manager
        self.config_manager = config_manager
        self.setWindowTitle("Advanced Skill Configuration")
        self.resize(600, 300)

        # Store current skill data
        self.skills_data = {}
        self.rotations_data = {}
        self.current_skill_name = None
        self.current_rotation_name = None

        # Timer for delayed updates
        from PyQt5.QtCore import QTimer

        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self._delayed_rotation_update)

        self._setup_ui()
        self._load_current_configuration()

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
        button_layout = QHBoxLayout()

        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self._save_configuration)
        button_layout.addWidget(self.save_btn)

        self.load_btn = QPushButton("Reload Configuration")
        self.load_btn.clicked.connect(self._load_current_configuration)
        button_layout.addWidget(self.load_btn)

        button_layout.addStretch()

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_layout.addWidget(button_box)

        layout.addLayout(button_layout)

    def _create_skills_tab(self):
        """Create the skills management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)

        # Left side - skill list
        left_widget = QGroupBox("Skills")
        left_layout = QVBoxLayout(left_widget)

        self.skill_tree = QTreeWidget()
        self.skill_tree.setHeaderLabels(
            ["Skill", "Key", "Cooldown", "Type", "Priority", "Enabled"]
        )
        self.skill_tree.itemClicked.connect(self._on_skill_selected)
        left_layout.addWidget(self.skill_tree)

        # Skill management buttons
        skill_buttons = QHBoxLayout()
        self.add_skill_btn = QPushButton("Add Skill")
        self.add_skill_btn.clicked.connect(self._add_skill)
        self.remove_skill_btn = QPushButton("Remove Skill")
        self.remove_skill_btn.clicked.connect(self._remove_skill)
        self.remove_skill_btn.setEnabled(False)
        self.refresh_skills_btn = QPushButton("Refresh List")
        self.refresh_skills_btn.clicked.connect(self._manual_refresh_skills)

        skill_buttons.addWidget(self.add_skill_btn)
        skill_buttons.addWidget(self.remove_skill_btn)
        skill_buttons.addWidget(self.refresh_skills_btn)
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
        self.skill_type_combo.addItems(
            [
                "offensive",
                "buff",
                "utility",
                "hp_potion",
                "mp_potion",
                "auto_attack",
                "assist",
            ]
        )
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

        # Connect signals after all widgets are created
        self._connect_skill_signals()

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
        self.refresh_rotations_btn = QPushButton("Refresh List")
        self.refresh_rotations_btn.clicked.connect(self._manual_refresh_rotations)

        rotation_buttons.addWidget(self.add_rotation_btn)
        rotation_buttons.addWidget(self.remove_rotation_btn)
        rotation_buttons.addWidget(self.refresh_rotations_btn)
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
        self.available_skills_list.itemDoubleClicked.connect(
            self._add_skill_to_rotation
        )
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

        layout.addWidget(right_widget, 1)

        # Connect signals after all widgets are created
        self._connect_rotation_signals()

        self.tab_widget.addTab(tab, "Rotations")

    def _create_conditions_tab(self):
        """Create the conditions tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        info_label = QLabel(
            """
        <b>Skill Conditions:</b><br>
        Configure when skills should be used based on game state.<br>
        This feature will be implemented in future phases.
        """
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addStretch()
        self.tab_widget.addTab(tab, "Conditions")

    def _load_current_configuration(self):
        """Load current configuration from skill manager and config"""
        try:
            # Clear existing data
            self.skills_data.clear()
            self.rotations_data.clear()

            # Load from skill manager if available
            if self.skill_manager:
                skill_config = self.skill_manager.export_config()

                # Load skills
                for skill_name, skill_data in skill_config.get("skills", {}).items():
                    self.skills_data[skill_name] = {
                        "name": skill_name,
                        "key": skill_data.get("key", ""),
                        "cooldown": int(
                            float(skill_data.get("cooldown", 1))
                        ),  # Ensure int
                        "type": skill_data.get("skill_type", "offensive"),
                        "priority": int(
                            float(skill_data.get("priority", 1))
                        ),  # Ensure int
                        "mana": int(
                            float(skill_data.get("mana_cost", 0))
                        ),  # Ensure int
                        "enabled": skill_data.get("enabled", True),
                        "desc": skill_data.get("description", ""),
                    }

                # Load rotations
                for rot_name, rot_data in skill_config.get("rotations", {}).items():
                    self.rotations_data[rot_name] = {
                        "name": rot_name,
                        "skills": rot_data.get("skills", []),
                        "repeat": rot_data.get("repeat", True),
                        "enabled": rot_data.get("enabled", True),
                    }

            # Refresh UI
            self._refresh_skill_tree()
            self._refresh_rotations_list()
            self._update_available_skills()

            self.logger_info("Configuration loaded successfully")

        except Exception as e:
            QMessageBox.critical(
                self, "Load Error", f"Failed to load configuration: {e}"
            )

    def _save_configuration(self):
        """Save current configuration to skill manager and config"""
        try:
            # Save current form data first
            if self.current_skill_name:
                self._save_current_skill_data()
            if self.current_rotation_name:
                self._save_current_rotation_data()

            if not self.skill_manager:
                QMessageBox.warning(self, "Save Error", "No skill manager available")
                return

            print(
                f"Saving {len(self.skills_data)} skills and {len(self.rotations_data)} rotations"
            )  # Debug

            # Prepare configuration for skill manager
            skills_config = {}
            for skill_name, skill_data in self.skills_data.items():
                skills_config[skill_name] = {
                    "key": skill_data["key"],
                    "cooldown": skill_data["cooldown"],
                    "skill_type": skill_data["type"],
                    "priority": skill_data["priority"],
                    "mana_cost": skill_data["mana"],
                    "conditions": [],  # TODO: Implement conditions
                    "description": skill_data["desc"],
                    "enabled": skill_data["enabled"],
                }
                print(f"  Skill: {skill_name} -> {skills_config[skill_name]}")  # Debug

            rotations_config = {}
            for rot_name, rot_data in self.rotations_data.items():
                rotations_config[rot_name] = {
                    "skills": rot_data["skills"],
                    "repeat": rot_data["repeat"],
                    "enabled": rot_data.get("enabled", True),
                }
                print(
                    f"  Rotation: {rot_name} -> {rotations_config[rot_name]}"
                )  # Debug

            # Import to skill manager
            full_config = {
                "skills": skills_config,
                "rotations": rotations_config,
                "active_rotation": None,
                "global_cooldown": 0.2,
            }

            self.skill_manager.import_config(full_config)

            # Save to config file if available
            if self.config_manager:
                self.config_manager.set_skills(full_config)
                self.config_manager.save_config()

            QMessageBox.information(
                self,
                "Success",
                f"Configuration saved successfully!\n"
                f"Skills: {len(skills_config)}\n"
                f"Rotations: {len(rotations_config)}",
            )

        except Exception as e:
            import traceback

            error_msg = f"Failed to save configuration: {e}\n\nFull error:\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Save Error", error_msg)
            print(error_msg)

    def _refresh_skill_tree(self):
        """Refresh the skill tree widget"""
        self.skill_tree.clear()
        for skill in self.skills_data.values():
            self._add_skill_to_tree(skill)

    def _add_skill_to_tree(self, skill):
        """Add skill to the tree widget"""
        item = QTreeWidgetItem(
            [
                skill["name"],
                skill["key"],
                f"{skill['cooldown']} sec",
                skill["type"],
                str(skill["priority"]),
                "Yes" if skill["enabled"] else "No",
            ]
        )
        item.setData(0, Qt.UserRole, skill["name"])
        self.skill_tree.addTopLevelItem(item)

    def _on_skill_selected(self, item, column):
        """
        CORREGIDO: Maneja la selección de un skill, asegurando que la
        selección visual no "salte".
        """
        # Si no es un item válido, no hacemos nada.
        if not item:
            return

        new_skill_name = item.data(0, Qt.UserRole)

        # Si el usuario hace clic en el mismo item, no hacemos nada.
        if new_skill_name == self.current_skill_name:
            return

        # 1. Guardar los datos del skill ANTERIOR (si había uno seleccionado).
        if self.current_skill_name:
            self._save_current_skill_data()

        # 2. Actualizar la variable al NUEVO skill seleccionado.
        self.current_skill_name = new_skill_name

        # Si el nuevo skill no está en nuestros datos (p.ej. se borró), salimos.
        if new_skill_name not in self.skills_data:
            self.remove_skill_btn.setEnabled(False)
            return

        skill = self.skills_data[new_skill_name]

        # 3. Rellenar el formulario con los datos del nuevo skill.
        #    Desconectamos las señales para evitar bucles.
        self._disconnect_skill_signals()
        self.skill_name_edit.setText(skill["name"])
        self.skill_key_edit.setText(skill["key"])
        self.skill_cooldown_spin.setValue(int(skill["cooldown"]))
        self.skill_type_combo.setCurrentText(skill["type"])
        self.skill_priority_spin.setValue(int(skill["priority"]))
        self.skill_mana_spin.setValue(int(skill["mana"]))
        self.skill_enabled_cb.setChecked(skill["enabled"])
        self.skill_desc_edit.setPlainText(skill["desc"])
        self._connect_skill_signals()

        # Habilitar el botón de borrado
        self.remove_skill_btn.setEnabled(True)

    def _save_current_skill_data(self):
        """
        CORREGIDO: Guarda los datos del formulario en el diccionario de datos,
        manejando correctamente el cambio de nombre.
        """
        if (
            not self.current_skill_name
            or self.current_skill_name not in self.skills_data
        ):
            return

        old_name = self.current_skill_name
        new_name = self.skill_name_edit.text().strip()

        # Si el nombre no ha cambiado, simplemente actualizamos los datos.
        if old_name == new_name:
            skill_data = self.skills_data[old_name]
        # Si el nombre ha cambiado...
        else:
            # Comprobamos si el nuevo nombre ya existe (y no es el mismo que el antiguo)
            if new_name in self.skills_data:
                QMessageBox.warning(
                    self,
                    "Duplicate Name",
                    f"A skill named '{new_name}' already exists.",
                )
                self.skill_name_edit.setText(old_name)  # Revertir el cambio en la UI
                return

            # Creamos una nueva entrada y eliminamos la antigua
            skill_data = self.skills_data.pop(old_name)
            self.skills_data[new_name] = skill_data
            self.logger_info(f"Skill '{old_name}' renamed to '{new_name}'.")

        # Actualizamos todos los campos del diccionario
        skill_data["name"] = new_name
        skill_data["key"] = self.skill_key_edit.text().strip()
        skill_data["cooldown"] = self.skill_cooldown_spin.value()
        skill_data["type"] = self.skill_type_combo.currentText()
        skill_data["priority"] = self.skill_priority_spin.value()
        skill_data["mana"] = self.skill_mana_spin.value()
        skill_data["enabled"] = self.skill_enabled_cb.isChecked()
        skill_data["desc"] = self.skill_desc_edit.toPlainText()

        # Actualizamos el nombre del item actual para reflejar el cambio
        self.current_skill_name = new_name

    def _connect_skill_signals(self):
        """Connect skill form signals"""
        self.skill_name_edit.textChanged.connect(self._on_skill_data_changed)
        self.skill_key_edit.textChanged.connect(self._on_skill_data_changed)
        self.skill_cooldown_spin.valueChanged.connect(self._on_skill_data_changed)
        self.skill_type_combo.currentTextChanged.connect(self._on_skill_data_changed)
        self.skill_priority_spin.valueChanged.connect(self._on_skill_data_changed)
        self.skill_mana_spin.valueChanged.connect(self._on_skill_data_changed)
        self.skill_enabled_cb.stateChanged.connect(self._on_skill_data_changed)
        self.skill_desc_edit.textChanged.connect(self._on_skill_data_changed)

    def _disconnect_skill_signals(self):
        """Disconnect skill form signals"""
        self.skill_name_edit.textChanged.disconnect()
        self.skill_key_edit.textChanged.disconnect()
        self.skill_cooldown_spin.valueChanged.disconnect()
        self.skill_type_combo.currentTextChanged.disconnect()
        self.skill_priority_spin.valueChanged.disconnect()
        self.skill_mana_spin.valueChanged.disconnect()
        self.skill_enabled_cb.stateChanged.disconnect()
        self.skill_desc_edit.textChanged.disconnect()

    def _on_skill_data_changed(self):
        """Handle skill data changes"""
        if not self.current_skill_name:
            return

        # Update skill data
        if self.current_skill_name in self.skills_data:
            skill = self.skills_data[self.current_skill_name]
            skill["name"] = self.skill_name_edit.text()
            skill["key"] = self.skill_key_edit.text()
            skill["cooldown"] = self.skill_cooldown_spin.value()
            skill["type"] = self.skill_type_combo.currentText()
            skill["priority"] = self.skill_priority_spin.value()
            skill["mana"] = self.skill_mana_spin.value()
            skill["enabled"] = self.skill_enabled_cb.isChecked()
            skill["desc"] = self.skill_desc_edit.toPlainText()

            # Refresh tree
            self._refresh_skill_tree()
            self._update_available_skills()

    def _add_skill(self):
        """
        Añade un nuevo skill con un nombre único temporal y lo selecciona para su edición.
        """
        # Generar un nombre único para la nueva habilidad
        i = 1
        while f"New Skill {i}" in self.skills_data:
            i += 1
        new_skill_name = f"New Skill {i}"

        # Crear datos por defecto para la nueva habilidad
        new_skill_data = {
            "name": new_skill_name,
            "key": "",
            "cooldown": 1,
            "type": "offensive",
            "priority": 1,
            "mana": 0,
            "enabled": True,
            "desc": "",
        }

        # Añadir al diccionario de datos y al árbol visual
        self.skills_data[new_skill_name] = new_skill_data
        self._add_skill_to_tree(new_skill_data)

        # Seleccionar el nuevo item en el árbol para que el usuario pueda editarlo
        for i in range(self.skill_tree.topLevelItemCount()):
            item = self.skill_tree.topLevelItem(i)
            if item.text(0) == new_skill_name:
                self.skill_tree.setCurrentItem(item)
                self._on_skill_selected(
                    item, 0
                )  # Llama manualmente para rellenar el formulario
                break

        self.skill_name_edit.setFocus()  # Pone el foco en el campo de nombre
        self.skill_name_edit.selectAll()  # Selecciona todo el texto para que el usuario pueda sobrescribir

    def _remove_skill(self):
        """Remove the selected skill"""
        if self.current_skill_name and self.current_skill_name in self.skills_data:
            del self.skills_data[self.current_skill_name]
            self.current_skill_name = None
            self._refresh_skill_tree()
            self._update_available_skills()
            self.remove_skill_btn.setEnabled(False)

    def _refresh_rotations_list(self):
        """Refresh rotations list"""
        # Remember current selection
        current_selection = self.current_rotation_name

        # Clear and repopulate
        self.rotations_list.clear()
        for rotation_name in self.rotations_data.keys():
            item = QListWidgetItem(rotation_name)
            self.rotations_list.addItem(item)

            # Restore selection if it still exists
            if rotation_name == current_selection:
                self.rotations_list.setCurrentItem(item)

    def _update_available_skills(self):
        """Update the available skills list for rotations"""
        self.available_skills_list.clear()
        for skill_name in self.skills_data.keys():
            if self.skills_data[skill_name]["enabled"]:
                self.available_skills_list.addItem(skill_name)

    def _add_rotation(self):
        """Add a new rotation"""
        name = f"Rotation {len(self.rotations_data) + 1}"
        self.rotations_data[name] = {
            "name": name,
            "skills": [],
            "repeat": True,
            "enabled": True,
        }
        self._refresh_rotations_list()

    def _remove_rotation(self):
        """Remove selected rotation"""
        if (
            self.current_rotation_name
            and self.current_rotation_name in self.rotations_data
        ):
            del self.rotations_data[self.current_rotation_name]
            self.current_rotation_name = None
            self._refresh_rotations_list()

    def _on_rotation_selected(self, item):
        """Handle rotation selection"""
        # Check if item is still valid
        if not item or not hasattr(item, "text"):
            return

        try:
            rotation_name = item.text()
        except RuntimeError:
            # Item has been deleted, ignore
            return

        if not rotation_name or rotation_name not in self.rotations_data:
            return

        # Save current rotation first if any and it's different
        if self.current_rotation_name and self.current_rotation_name != rotation_name:
            self._save_current_rotation_data()

        self.current_rotation_name = rotation_name
        rotation = self.rotations_data[rotation_name]

        # Temporarily disconnect signals
        self._disconnect_rotation_signals()

        try:
            self.rotation_name_edit.setText(rotation["name"])
            self.rotation_repeat_cb.setChecked(rotation["repeat"])

            # Update skills in rotation list
            self.rotation_skills_list.clear()
            for skill in rotation["skills"]:
                self.rotation_skills_list.addItem(skill)

            print(
                f"Loaded rotation '{rotation_name}' with {len(rotation['skills'])} skills: {rotation['skills']}"
            )  # Debug
            rotation_name = item.data(0, Qt.UserRole)

        except Exception as e:
            print(f"Error loading rotation data: {e}")

        # Reconnect signals
        self._connect_rotation_signals()

    def _save_current_rotation_data(self):
        """Save current rotation data from form"""
        if (
            not self.current_rotation_name
            or self.current_rotation_name not in self.rotations_data
        ):
            return

        order_before_saving = [
            self.rotation_skills_list.item(i).text()
            for i in range(self.rotation_skills_list.count())
        ]
        print(
            f"DEBUG: _save_current_rotation_data -> Orden A PUNTO DE GUARDAR: {order_before_saving}"
        )

        rotation = self.rotations_data[self.current_rotation_name]
        old_name = rotation["name"]
        new_name = self.rotation_name_edit.text().strip()

        # Update rotation data
        rotation["name"] = new_name
        rotation["repeat"] = self.rotation_repeat_cb.isChecked()

        # Update skills list from UI
        skills = []
        for i in range(self.rotation_skills_list.count()):
            skill_name = self.rotation_skills_list.item(i).text()
            skills.append(skill_name)
        rotation["skills"] = skills

        # If name changed, update the dictionary key AND the list
        if old_name != new_name and new_name:
            # Remove old entry and add new one
            del self.rotations_data[old_name]
            self.rotations_data[new_name] = rotation
            self.current_rotation_name = new_name

            # Update the list item text
            current_item = self.rotations_list.currentItem()
            if current_item:
                current_item.setText(new_name)

            print(f"Renamed rotation from '{old_name}' to '{new_name}'")

        print(f"Saved rotation '{new_name}' with skills: {skills}")  # Debug

    def _connect_rotation_signals(self):
        """Connect rotation form signals"""
        try:
            # Use timer for name changes to avoid too frequent updates
            self.rotation_name_edit.textChanged.connect(
                lambda: self.update_timer.start(500)
            )
            self.rotation_repeat_cb.stateChanged.connect(self._on_rotation_data_changed)
        except Exception as e:
            print(f"Error connecting rotation signals: {e}")

    def _disconnect_rotation_signals(self):
        """Disconnect rotation form signals"""
        try:
            self.rotation_name_edit.textChanged.disconnect()
            self.rotation_repeat_cb.stateChanged.disconnect()
        except Exception as e:
            # Ignore if already disconnected or error
            pass

    def _on_rotation_data_changed(self):
        """Handle rotation data changes - FIXED VERSION"""
        if not self.current_rotation_name:
            return

        if self.current_rotation_name not in self.rotations_data:
            return

        # Get the current rotation data
        rotation = self.rotations_data[self.current_rotation_name]
        old_name = rotation["name"]
        new_name = self.rotation_name_edit.text().strip()

        # Update basic rotation data
        rotation["repeat"] = self.rotation_repeat_cb.isChecked()

        # Update skills list from UI
        skills = []
        for i in range(self.rotation_skills_list.count()):
            skills.append(self.rotation_skills_list.item(i).text())
        rotation["skills"] = skills

        # 🔧 CRITICAL FIX: Update dictionary key if name changed
        if old_name != new_name and new_name:
            # Update the name in the data
            rotation["name"] = new_name

            # Remove old entry and add with new key
            del self.rotations_data[old_name]
            self.rotations_data[new_name] = rotation

            # Update current tracking
            self.current_rotation_name = new_name

            # Update the list item text
            current_item = self.rotations_list.currentItem()
            if current_item:
                current_item.setText(new_name)

            print(f"Auto-updated rotation name: '{old_name}' -> '{new_name}'")
        else:
            # Just update the name in existing data
            rotation["name"] = new_name

    def _add_skill_to_rotation(self):
        """Add selected skill to rotation"""
        current_skill = self.available_skills_list.currentItem()
        if current_skill and self.current_rotation_name:
            skill_name = current_skill.text()

            # Check if skill is already in rotation
            existing_skills = []
            for i in range(self.rotation_skills_list.count()):
                existing_skills.append(self.rotation_skills_list.item(i).text())

            if skill_name not in existing_skills:
                self.rotation_skills_list.addItem(skill_name)
                self._on_rotation_data_changed()  # Update data
                print(
                    f"Added '{skill_name}' to rotation '{self.current_rotation_name}'"
                )
            else:
                print(f"Skill '{skill_name}' already in rotation")
        current_list_order = [
            self.rotation_skills_list.item(i).text()
            for i in range(self.rotation_skills_list.count())
        ]
        print(
            f"DEBUG: _add_skill_to_rotation -> Orden visual de skills AHORA: {current_list_order}"
        )

    def _remove_skill_from_rotation(self):
        """Remove selected skill from rotation"""
        current_item = self.rotation_skills_list.currentItem()
        if current_item and self.current_rotation_name:
            skill_name = current_item.text()
            row = self.rotation_skills_list.row(current_item)
            self.rotation_skills_list.takeItem(row)
            self._on_rotation_data_changed()  # Update data
            print(
                f"Removed '{skill_name}' from rotation '{self.current_rotation_name}'"
            )

    def accept(self):
        """Accept dialog and save configuration"""
        self._save_configuration()
        super().accept()

    def _delayed_rotation_update(self):
        """Delayed update for rotation name changes - FIXED VERSION"""
        # Simply call the fixed _on_rotation_data_changed method
        self._on_rotation_data_changed()

    def _manual_refresh_rotations(self):
        """Manually refresh the rotations list"""
        # Save current selection first
        if self.current_rotation_name:
            self._save_current_rotation_data()

        # Clear selection to avoid conflicts
        self.rotations_list.clearSelection()
        self.current_rotation_name = None

        # Refresh list
        self._refresh_rotations_list()

        print("Rotations list refreshed manually")

    def _manual_refresh_skills(self):
        """Manually refresh the skills list"""
        # Save current selection first
        if self.current_skill_name:
            self._save_current_skill_data()

        # Clear selection to avoid conflicts
        self.skill_tree.clearSelection()
        self.current_skill_name = None

        # Refresh tree
        self._refresh_skill_tree()
        self._update_available_skills()

        print("Skills list refreshed manually")

    def logger_info(self, message):
        """Helper for logging"""
        print(f"SkillConfig: {message}")  # Simple logging for now
