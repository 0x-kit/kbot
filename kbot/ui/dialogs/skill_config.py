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
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, pyqtSlot
import os
from .icon_selector_dialog import IconSelectorDialog


class SkillConfigDialog(QDialog):
    """✅ MODIFICADO: Diálogo de configuración de skills con asignación de iconos."""

    def __init__(self, skill_manager, config_manager, parent=None):
        super().__init__(parent)
        self.skill_manager = skill_manager
        self.config_manager = config_manager
        self.setWindowTitle("Skill Configuration")
        self.resize(600, 400)

        self._setup_ui()
        self.load_config()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Panel izquierdo: Lista de Skills
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        self.skill_tree = QTreeWidget()
        self.skill_tree.setHeaderLabels(["Skill", "Key", "Enabled"])
        self.skill_tree.itemSelectionChanged.connect(self.on_skill_selected)
        left_layout.addWidget(self.skill_tree)

        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Add Skill")
        add_btn.clicked.connect(self.add_skill)
        remove_btn = QPushButton("Remove Skill")
        remove_btn.clicked.connect(self.remove_skill)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        left_layout.addLayout(btn_layout)
        left_panel.setLayout(left_layout)
        splitter.addWidget(left_panel)

        # Panel derecho: Detalles del Skill
        right_panel = QWidget()
        self.details_layout = QFormLayout(right_panel)
        self.details_layout.setContentsMargins(10, 10, 10, 10)

        self.skill_name_edit = QLineEdit()
        self.skill_key_edit = QLineEdit()
        self.skill_cooldown_spin = (
            QDoubleSpinBox()
        )  # Reinterpretado como check interval
        self.skill_cooldown_spin.setSuffix(" s")
        self.skill_type_combo = QComboBox()
        self.skill_type_combo.addItems(
            ["offensive", "buff", "hp_potion", "mp_potion", "auto_attack", "assist"]
        )
        self.skill_priority_spin = QSpinBox()
        self.skill_priority_spin.setRange(1, 10)
        self.skill_mana_spin = QSpinBox()
        self.skill_mana_spin.setRange(0, 5000)
        self.skill_enabled_cb = QCheckBox()
        self.skill_desc_edit = QLineEdit()

        # ✅ NUEVO: Campo de duración para buffs
        self.skill_duration_spin = QDoubleSpinBox()
        self.skill_duration_spin.setRange(0, 14400)  # 0 a 1 hora
        self.skill_duration_spin.setSuffix(" sec")
        self.skill_duration_spin.setValue(0.0)

        # ✅ NUEVO: Selector visual de iconos
        self.icon_layout = QHBoxLayout()
        self.skill_icon_edit = QLineEdit()
        self.skill_icon_edit.setReadOnly(True)
        self.skill_icon_edit.setPlaceholderText("No visual skill selected")
        icon_btn = QPushButton("Select Skill...")
        icon_btn.clicked.connect(self.select_skill_icon)
        clear_btn = QPushButton("Clear")
        clear_btn.setFixedWidth(50)
        clear_btn.clicked.connect(self.clear_skill_icon)
        self.icon_layout.addWidget(self.skill_icon_edit)
        self.icon_layout.addWidget(icon_btn)
        self.icon_layout.addWidget(clear_btn)

        self.details_layout.addRow("Enabled:", self.skill_enabled_cb)
        self.details_layout.addRow("Name:", self.skill_name_edit)
        self.details_layout.addRow("Key:", self.skill_key_edit)
        self.details_layout.addRow("Priority:", self.skill_priority_spin)
        self.details_layout.addRow("Type:", self.skill_type_combo)
        # self.details_layout.addRow("Mana Cost:", self.skill_mana_spin)
        self.details_layout.addRow("Duration (buffs):", self.skill_duration_spin)
        self.details_layout.addRow("Visual skill (optional):", self.icon_layout)
        self.details_layout.addRow(
            "Check Interval (optional):", self.skill_cooldown_spin
        )
        # self.details_layout.addRow("Description:", self.skill_desc_edit)

        right_panel.setLayout(self.details_layout)
        splitter.addWidget(right_panel)
        splitter.setSizes([300, 500])

        # Botones del diálogo
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def load_config(self):
        self.skill_tree.clear()
        skills = self.config_manager.get_skills_config().get("definitions", {})

        # Ordenar por clave 'key': números primero, luego letras
        sorted_skills = sorted(
            skills.items(),
            key=lambda item: (
                item[1]
                .get("key", "")[0]
                .isalpha(),  # False (0) si empieza por número, True (1) si letra
                item[1].get("key", ""),  # luego ordena por valor alfabético
            ),
        )

        for name, data in sorted_skills:
            self.add_skill_to_tree(name, data)

    def add_skill_to_tree(self, name, data):
        item = QTreeWidgetItem(
            [name, data.get("key", ""), "Yes" if data.get("enabled") else "No"]
        )
        item.setData(0, Qt.UserRole, name)
        self.skill_tree.addTopLevelItem(item)

    @pyqtSlot()
    def on_skill_selected(self):
        selected_items = self.skill_tree.selectedItems()
        if not selected_items:
            return

        # Guardar datos del skill anterior antes de cambiar
        if hasattr(self, "current_skill_name") and self.current_skill_name:
            self.save_current_skill_details()

        # Cargar datos del nuevo skill
        self.current_skill_name = selected_items[0].data(0, Qt.UserRole)
        skills = self.config_manager.get_skills_config().get("definitions", {})
        data = skills.get(self.current_skill_name, {})

        self.skill_name_edit.setText(self.current_skill_name)
        self.skill_key_edit.setText(data.get("key", ""))
        # ✅ CORREGIDO: Usar check_interval con compatibilidad hacia atrás
        self.skill_cooldown_spin.setValue(
            float(data.get("check_interval", data.get("cooldown", 1.0)))
        )
        self.skill_type_combo.setCurrentText(data.get("skill_type", "offensive"))
        self.skill_priority_spin.setValue(int(data.get("priority", 1)))
        self.skill_mana_spin.setValue(int(1))
        # ✅ NUEVO: Cargar duración
        self.skill_duration_spin.setValue(float(data.get("duration", 0.0)))
        self.skill_icon_edit.setText(data.get("icon", ""))
        self.skill_enabled_cb.setChecked(data.get("enabled", True))
        # self.skill_desc_edit.setText(data.get("description", ""))

    def save_current_skill_details(self):
        if not hasattr(self, "current_skill_name") or not self.current_skill_name:
            return

        all_skills = self.config_manager.get_skills_config()
        definitions = all_skills.get("definitions", {})

        old_name = self.current_skill_name
        new_name = self.skill_name_edit.text()

        data = {
            "key": self.skill_key_edit.text(),
            "check_interval": self.skill_cooldown_spin.value(),
            "skill_type": self.skill_type_combo.currentText(),
            "priority": self.skill_priority_spin.value(),
            "mana_cost": 0,
            "icon": self.skill_icon_edit.text(),
            "duration": self.skill_duration_spin.value(),
            "conditions": [],
            "description": None,
            "enabled": self.skill_enabled_cb.isChecked(),
        }

        if old_name != new_name:
            if new_name in definitions:
                # Evitar duplicados, revertir el nombre
                self.skill_name_edit.setText(old_name)
                return
            definitions.pop(old_name, None)
            definitions[new_name] = data
            self.current_skill_name = new_name
        else:
            definitions[old_name] = data

        self.config_manager.set_skills_config(all_skills)

    def add_skill(self):
        i = 1
        definitions = self.config_manager.get_skills_config().get("definitions", {})
        while f"New Skill {i}" in definitions:
            i += 1
        name = f"New Skill {i}"

        data = {
            "key": "",
            "check_interval": 1.0,
            "skill_type": "offensive",
            "priority": "1",
            "enabled": True,
        }
        definitions[name] = data
        self.add_skill_to_tree(name, data)

    def remove_skill(self):
        selected = self.skill_tree.selectedItems()
        if not selected:
            return

        name = selected[0].data(0, Qt.UserRole)
        all_skills = self.config_manager.get_skills_config()
        if name in all_skills["definitions"]:
            del all_skills["definitions"][name]
            self.config_manager.set_skills_config(all_skills)
            self.load_config()

    @pyqtSlot()
    def select_skill_icon(self):
        """Abrir el selector visual de iconos."""
        dialog = IconSelectorDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            selected_path = dialog.get_selected_icon_path()
            if selected_path:
                # Hacer la ruta relativa si es posible
                try:
                    relative_path = os.path.relpath(selected_path, os.getcwd())
                    self.skill_icon_edit.setText(relative_path.replace("\\", "/"))
                except ValueError:
                    self.skill_icon_edit.setText(selected_path)

    @pyqtSlot()
    def clear_skill_icon(self):
        """Limpiar la selección de icono."""
        self.skill_icon_edit.clear()

    def accept(self):
        self.save_current_skill_details()
        self.config_manager.save_config()
        # Actualizar el skill manager en el bot engine
        if self.skill_manager:
            skills_config = self.config_manager.get_skills_config()
            self.skill_manager.import_config(skills_config)
        super().accept()
