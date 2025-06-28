# ui/dialogs/advanced_config_dialog.py - IMPLEMENTACIÓN COMPLETA

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QFormLayout,
    QLabel,
    QSpinBox,
    QDoubleSpinBox,
    QCheckBox,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QDialogButtonBox,
    QMessageBox,
    QTextEdit,
    QComboBox,
    QWidget,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette


class AdvancedConfigDialog(QDialog):
    """Configuración avanzada simplificada del bot"""

    config_changed = pyqtSignal(dict)

    def __init__(self, unified_config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = unified_config_manager
        self.setWindowTitle("🔧 Advanced Bot Configuration")
        self.setMinimumSize(600, 500)
        self.resize(700, 600)

        # Store widgets for easy access
        self.timing_widgets = {}
        self.behavior_widgets = {}

        self._setup_ui()
        self._load_current_values()
        self._connect_signals()

    def _setup_ui(self):
        """Setup simplified single-screen UI"""
        layout = QVBoxLayout(self)

        # Create scroll area for all content
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Create horizontal layout for timing and behavior sections
        combat_layout = QHBoxLayout()
        
        # Create left column for timing
        timing_widget = QWidget()
        timing_widget.setMinimumWidth(350)  # Fixed width for consistency
        timing_column = QVBoxLayout(timing_widget)
        self._create_timing_section(timing_column)
        combat_layout.addWidget(timing_widget)
        
        # Create right column for behavior
        behavior_widget = QWidget()
        behavior_widget.setMinimumWidth(350)  # Same width as timing
        behavior_column = QVBoxLayout(behavior_widget)
        self._create_behavior_section(behavior_column)
        combat_layout.addWidget(behavior_widget)
        
        scroll_layout.addLayout(combat_layout)
        
        # Add other sections normally
        self._create_whitelist_section(scroll_layout)
        self._create_config_management_section(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # Bottom buttons - only standard dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        layout.addWidget(self.button_box)

    def _create_timing_section(self, parent_layout):
        """Create Combat Timing section including global cooldown"""
        timing_group = QGroupBox("⏱️ Combat Timing")
        timing_layout = QFormLayout(timing_group)

        # Global cooldown (moved from advanced tab)
        self.global_cooldown_spin = QDoubleSpinBox()
        self.global_cooldown_spin.setRange(0.05, 1.0)
        self.global_cooldown_spin.setSingleStep(0.05)
        self.global_cooldown_spin.setSuffix(" s")
        self.global_cooldown_spin.setToolTip("Minimum time between any skill uses")
        self.global_cooldown_spin.setFixedWidth(120)  # Fixed width for consistency
        timing_layout.addRow("Global Cooldown:", self.global_cooldown_spin)

        # Timing parameters
        timing_params = [
            (
                "skill_interval",
                "Skill Interval",
                "Time between skills",
                0.1,
                5.0,
                0.1,
                "s",
            ),
            (
                "attack_interval",
                "Attack Interval",
                "Post-combat delay",
                0.0,
                10.0,
                0.1,
                "s",
            ),
            (
                "target_attempt_interval",
                "Target Search",
                "How often to search for targets",
                0.1,
                2.0,
                0.1,
                "s",
            ),
            (
                "stuck_detection_searching",
                "Search Timeout",
                "Time before anti-stuck when searching",
                3.0,
                30.0,
                0.5,
                "s",
            ),
            (
                "stuck_in_combat_timeout",
                "Combat Timeout",
                "Time before anti-stuck in combat",
                5.0,
                60.0,
                0.5,
                "s",
            ),
            (
                "vitals_check_interval",
                "Vitals Check Rate",
                "How often to check HP/MP",
                0.1,
                2.0,
                0.1,
                "s",
            ),
            (
                "stats_update_interval",
                "Stats Update Rate",
                "How often to update statistics",
                1.0,
                30.0,
                0.5,
                "s",
            ),
        ]

        for param, label, tooltip, min_val, max_val, step, suffix in timing_params:
            widget = QDoubleSpinBox()
            widget.setRange(min_val, max_val)
            widget.setSingleStep(step)
            widget.setSuffix(f" {suffix}")
            widget.setToolTip(tooltip)
            widget.setFixedWidth(120)  # Fixed width for consistency
            self.timing_widgets[param] = widget
            timing_layout.addRow(f"{label}:", widget)

        parent_layout.addWidget(timing_group)

    def _create_behavior_section(self, parent_layout):
        """Create Combat Behavior section"""
        behavior_group = QGroupBox("⚔️ Combat Behavior")
        behavior_layout = QFormLayout(behavior_group)

        # Boolean options
        bool_params = [
            ("enable_looting", "Enable Looting", "Loot items after killing targets"),
            (
                "assist_mode",
                "Assist Mode",
                "Use assist skill instead of searching for targets",
            ),
            ("use_skills", "Use Skills", "Enable skill usage in combat"),
        ]

        for param, label, tooltip in bool_params:
            widget = QCheckBox()
            widget.setToolTip(tooltip)
            self.behavior_widgets[param] = widget
            behavior_layout.addRow(f"{label}:", widget)

        # Thresholds
        self.behavior_widgets["potion_threshold"] = QSpinBox()
        self.behavior_widgets["potion_threshold"].setRange(1, 99)
        self.behavior_widgets["potion_threshold"].setSuffix("%")
        self.behavior_widgets["potion_threshold"].setToolTip(
            "HP/MP percentage to trigger potion use"
        )
        self.behavior_widgets["potion_threshold"].setFixedWidth(120)  # Fixed width for consistency
        behavior_layout.addRow(
            "Potion Threshold:", self.behavior_widgets["potion_threshold"]
        )

        self.behavior_widgets["ocr_tolerance"] = QSpinBox()
        self.behavior_widgets["ocr_tolerance"].setRange(50, 100)
        self.behavior_widgets["ocr_tolerance"].setSuffix("%")
        self.behavior_widgets["ocr_tolerance"].setToolTip(
            "OCR accuracy for text matching and target name validation (fuzzy matching threshold)"
        )
        self.behavior_widgets["ocr_tolerance"].setFixedWidth(120)  # Fixed width for consistency
        behavior_layout.addRow("OCR/Target Tolerance:", self.behavior_widgets["ocr_tolerance"])

        # Looting parameters
        self.behavior_widgets["loot_duration"] = QDoubleSpinBox()
        self.behavior_widgets["loot_duration"].setRange(0.1, 5.0)
        self.behavior_widgets["loot_duration"].setSingleStep(0.1)
        self.behavior_widgets["loot_duration"].setSuffix(" s")
        self.behavior_widgets["loot_duration"].setToolTip("Total time spent looting")
        self.behavior_widgets["loot_duration"].setFixedWidth(120)  # Fixed width for consistency
        behavior_layout.addRow("Loot Duration:", self.behavior_widgets["loot_duration"])

        self.behavior_widgets["loot_attempts"] = QSpinBox()
        self.behavior_widgets["loot_attempts"].setRange(1, 10)
        self.behavior_widgets["loot_attempts"].setToolTip("Number of loot key presses")
        self.behavior_widgets["loot_attempts"].setFixedWidth(120)  # Fixed width for consistency
        behavior_layout.addRow("Loot Attempts:", self.behavior_widgets["loot_attempts"])

        self.behavior_widgets["loot_key"] = QLineEdit()
        self.behavior_widgets["loot_key"].setMaxLength(1)
        self.behavior_widgets["loot_key"].setToolTip("Key to press for looting")
        self.behavior_widgets["loot_key"].setFixedWidth(120)  # Fixed width for consistency
        behavior_layout.addRow("Loot Key:", self.behavior_widgets["loot_key"])

        parent_layout.addWidget(behavior_group)

    def _create_whitelist_section(self, parent_layout):
        """Create Mob Whitelist section"""
        whitelist_group = QGroupBox("📋 Mob Whitelist")
        whitelist_layout = QVBoxLayout(whitelist_group)

        whitelist_layout.addWidget(QLabel("Allowed mobs (one per line):"))
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setMaximumHeight(150)
        self.whitelist_edit.setToolTip(
            "Enter mob names that the bot is allowed to attack"
        )
        whitelist_layout.addWidget(self.whitelist_edit)

        parent_layout.addWidget(whitelist_group)

    def _create_config_management_section(self, parent_layout):
        """Create Configuration Management section"""
        config_group = QGroupBox("⚙️ Configuration Management")
        config_layout = QFormLayout(config_group)

        config_buttons_layout = QHBoxLayout()

        self.export_btn = QPushButton("💾 Export Config")
        self.import_btn = QPushButton("📁 Import Config")
        self.reset_btn = QPushButton("🔄 Reset to Defaults")
        self.validate_btn = QPushButton("✅ Validate Config")

        config_buttons_layout.addWidget(self.export_btn)
        config_buttons_layout.addWidget(self.import_btn)
        config_buttons_layout.addWidget(self.reset_btn)
        config_buttons_layout.addWidget(self.validate_btn)

        config_layout.addRow("Actions:", config_buttons_layout)


        parent_layout.addWidget(config_group)

    def _load_current_values(self):
        """✅ Cargar valores actuales desde la configuración"""
        try:
            # Load timing values
            timing = self.config_manager.get_combat_timing()
            for param, widget in self.timing_widgets.items():
                if param in timing:
                    widget.setValue(timing[param])

            # Load behavior values
            behavior = self.config_manager.get_combat_behavior()
            for param, widget in self.behavior_widgets.items():
                if param in behavior:
                    value = behavior[param]
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                    elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                        widget.setValue(value)
                    elif isinstance(widget, QLineEdit):
                        widget.setText(str(value))

            # Load skills config
            skills_config = self.config_manager.get_skills_config()
            if hasattr(self, "global_cooldown_spin"):
                self.global_cooldown_spin.setValue(
                    skills_config.get("global_cooldown", 0.15)
                )

            # Load whitelist
            whitelist = self.config_manager.get_whitelist()
            if hasattr(self, "whitelist_edit"):
                self.whitelist_edit.setPlainText("\n".join(whitelist))

            # Debug widgets removed in simplification

            # Config summary removed in simplification

        except Exception as e:
            QMessageBox.warning(
                self, "Load Error", f"Failed to load some configuration values: {e}"
            )

    def _connect_signals(self):
        """✅ Conectar señales de widgets"""
        # Connect timing widgets
        for widget in self.timing_widgets.values():
            widget.valueChanged.connect(self._on_timing_changed)

        # Connect behavior widgets
        for widget in self.behavior_widgets.values():
            if isinstance(widget, QCheckBox):
                widget.stateChanged.connect(self._on_behavior_changed)
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                widget.valueChanged.connect(self._on_behavior_changed)
            elif isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._on_behavior_changed)

        # Connect whitelist widget for real-time updates
        if hasattr(self, "whitelist_edit"):
            self.whitelist_edit.textChanged.connect(self._on_whitelist_changed)

        # Connect config management buttons
        if hasattr(self, "export_btn"):
            self.export_btn.clicked.connect(self._export_config)
            self.import_btn.clicked.connect(self._import_config)
            self.reset_btn.clicked.connect(self._reset_to_defaults)
            self.validate_btn.clicked.connect(self._validate_config)

        # Connect dialog buttons
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.button_box.button(QDialogButtonBox.Apply).clicked.connect(
            self._apply_changes
        )

    def _on_timing_changed(self):
        """Handle timing parameter changes"""
        self._emit_config_change()

    def _on_behavior_changed(self):
        """Handle behavior parameter changes"""
        self._emit_config_change()

    def _on_whitelist_changed(self):
        """Handle whitelist changes for real-time updates"""
        self._emit_config_change()


    def _emit_config_change(self):
        """Emit configuration change signal"""
        try:
            config = self._get_current_config()
            self.config_changed.emit(config)
        except Exception as e:
            pass  # Ignore errors in real-time updates

    def _get_current_config(self) -> dict:
        """✅ Obtener configuración actual desde la UI"""
        config = {}

        # Timing
        timing = {}
        for param, widget in self.timing_widgets.items():
            timing[param] = widget.value()
        config["timing"] = timing

        # Behavior
        behavior = {}
        for param, widget in self.behavior_widgets.items():
            if isinstance(widget, QCheckBox):
                behavior[param] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                behavior[param] = widget.value()
            elif isinstance(widget, QLineEdit):
                behavior[param] = widget.text()
        config["behavior"] = behavior

        # Whitelist
        if hasattr(self, "whitelist_edit"):
            whitelist_text = self.whitelist_edit.toPlainText()
            whitelist = [
                line.strip() for line in whitelist_text.splitlines() if line.strip()
            ]
            config["whitelist"] = whitelist

        return config

    def _apply_changes(self):
        """Apply changes without closing dialog"""
        try:
            self._save_current_config()
            QMessageBox.information(
                self, "Changes Applied", "✅ Configuration changes have been applied!"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {e}")

    def _save_current_config(self):
        """✅ Guardar configuración actual"""
        # Save timing
        timing = {}
        for param, widget in self.timing_widgets.items():
            timing[param] = widget.value()
        self.config_manager.set_combat_timing(timing)

        # Save behavior
        behavior = {}
        for param, widget in self.behavior_widgets.items():
            if isinstance(widget, QCheckBox):
                behavior[param] = widget.isChecked()
            elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
                behavior[param] = widget.value()
            elif isinstance(widget, QLineEdit):
                behavior[param] = widget.text()
        self.config_manager.set_combat_behavior(behavior)

        # Save whitelist
        if hasattr(self, "whitelist_edit"):
            whitelist_text = self.whitelist_edit.toPlainText()
            whitelist = [
                line.strip() for line in whitelist_text.splitlines() if line.strip()
            ]
            self.config_manager.set_whitelist(whitelist)

        # Save skills config
        if hasattr(self, "global_cooldown_spin"):
            skills_config = self.config_manager.get_skills_config()
            skills_config["global_cooldown"] = self.global_cooldown_spin.value()
            self.config_manager.set_skills_config(skills_config)

        # Save configuration to file
        self.config_manager.save_config()

    def _export_config(self):
        """Export configuration to file"""
        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                self.config_manager.export_config(filename)
                QMessageBox.information(
                    self, "Export Success", f"Configuration exported to {filename}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export: {e}")

    def _import_config(self):
        """Import configuration from file"""
        from PyQt5.QtWidgets import QFileDialog

        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "", "JSON Files (*.json)"
        )
        if filename:
            try:
                self.config_manager.import_config(filename)
                self._load_current_values()
                QMessageBox.information(
                    self, "Import Success", f"Configuration imported from {filename}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to import: {e}")

    def _reset_to_defaults(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self,
            "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            try:
                self.config_manager.reset_to_defaults()
                self._load_current_values()
                QMessageBox.information(
                    self, "Reset Complete", "Configuration reset to defaults"
                )
            except Exception as e:
                QMessageBox.critical(self, "Reset Error", f"Failed to reset: {e}")

    def _validate_config(self):
        """Validate current configuration"""
        try:
            issues = self.config_manager.validate_config()
            if issues:
                issues_text = "\n".join(f"• {issue}" for issue in issues)
                QMessageBox.warning(
                    self, "Configuration Issues", f"Issues found:\n{issues_text}"
                )
            else:
                QMessageBox.information(
                    self, "Validation Success", "✅ Configuration is valid!"
                )
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Failed to validate: {e}")

    def accept(self):
        """Accept dialog and save configuration"""
        try:
            self._save_current_config()
            super().accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Save Error", f"Failed to save configuration: {e}"
            )

    def reject(self):
        """Reject dialog without saving"""
        super().reject()
