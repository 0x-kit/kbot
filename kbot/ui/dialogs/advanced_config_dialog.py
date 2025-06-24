# ui/dialogs/advanced_config_dialog.py - IMPLEMENTACIÓN COMPLETA

from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QWidget,
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
    QSlider,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QPalette


class AdvancedConfigDialog(QDialog):
    """✅ COMPLETA - Configuración avanzada de todos los parámetros del bot"""

    config_changed = pyqtSignal(dict)  # Signal for real-time updates

    def __init__(self, unified_config_manager, parent=None):
        super().__init__(parent)
        self.config_manager = unified_config_manager
        self.setWindowTitle("🔧 Advanced Bot Configuration")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)

        # Store widgets for easy access
        self.timing_widgets = {}
        self.behavior_widgets = {}
        self.debug_widgets = {}

        self._setup_ui()
        self._load_current_values()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the complete UI with all configuration options"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self._create_timing_tab()
        self._create_behavior_tab()
        self._create_advanced_tab()
        self._create_debug_tab()

        # Bottom buttons
        button_layout = QHBoxLayout()

        # Preset buttons
        self.preset_aggressive_btn = QPushButton("⚡ Aggressive Preset")
        self.preset_conservative_btn = QPushButton("🛡️ Conservative Preset")
        self.preset_balanced_btn = QPushButton("⚖️ Balanced Preset")

        button_layout.addWidget(self.preset_aggressive_btn)
        button_layout.addWidget(self.preset_conservative_btn)
        button_layout.addWidget(self.preset_balanced_btn)
        button_layout.addStretch()

        # Standard dialog buttons
        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_layout.addWidget(self.button_box)

        layout.addLayout(button_layout)

    def _create_timing_tab(self):
        """✅ Tab para todos los parámetros de timing"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Scroll area for many parameters
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Combat Timing Group
        combat_group = QGroupBox("⚔️ Combat Timing")
        combat_layout = QFormLayout(combat_group)

        # Create timing controls with descriptions
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
                "Time between basic attacks",
                0.5,
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
                "post_combat_delay",
                "Post-Combat Delay",
                "Wait time after killing target",
                0.0,
                10.0,
                0.1,
                "s",
            ),
            (
                "assist_interval",
                "Assist Interval",
                "How often to use assist skill",
                0.1,
                3.0,
                0.1,
                "s",
            ),
        ]

        for param, label, tooltip, min_val, max_val, step, suffix in timing_params:
            widget = QDoubleSpinBox()
            widget.setRange(min_val, max_val)
            widget.setSingleStep(step)
            widget.setSuffix(f" {suffix}")
            widget.setToolTip(tooltip)
            widget.setMinimumWidth(100)

            # Add colored indicator for optimal ranges
            if param == "skill_interval":
                widget.setStyleSheet(
                    "QDoubleSpinBox { background-color: #e8f5e8; }"
                )  # Green tint
            elif param == "attack_interval":
                widget.setStyleSheet(
                    "QDoubleSpinBox { background-color: #ffe8e8; }"
                )  # Red tint

            self.timing_widgets[param] = widget

            # Create label with description
            full_label = f"{label}:"
            desc_label = QLabel(f"<small>{tooltip}</small>")
            desc_label.setStyleSheet("color: gray;")

            combat_layout.addRow(full_label, widget)
            combat_layout.addRow("", desc_label)

        scroll_layout.addWidget(combat_group)

        # Anti-Stuck Timing Group
        stuck_group = QGroupBox("🔄 Anti-Stuck Detection")
        stuck_layout = QFormLayout(stuck_group)

        stuck_params = [
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
                "unstuck_cooldown",
                "Unstuck Cooldown",
                "Cooldown between unstuck attempts",
                1.0,
                10.0,
                0.5,
                "s",
            ),
        ]

        for param, label, tooltip, min_val, max_val, step, suffix in stuck_params:
            widget = QDoubleSpinBox()
            widget.setRange(min_val, max_val)
            widget.setSingleStep(step)
            widget.setSuffix(f" {suffix}")
            widget.setToolTip(tooltip)
            widget.setStyleSheet(
                "QDoubleSpinBox { background-color: #fff8e8; }"
            )  # Orange tint

            self.timing_widgets[param] = widget

            desc_label = QLabel(f"<small>{tooltip}</small>")
            desc_label.setStyleSheet("color: gray;")

            stuck_layout.addRow(f"{label}:", widget)
            stuck_layout.addRow("", desc_label)

        scroll_layout.addWidget(stuck_group)

        # Monitoring Timing Group
        monitor_group = QGroupBox("📊 Monitoring & Logging")
        monitor_layout = QFormLayout(monitor_group)

        monitor_params = [
            (
                "combat_log_interval",
                "Combat Log Rate",
                "How often to log combat progress",
                1.0,
                30.0,
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

        for param, label, tooltip, min_val, max_val, step, suffix in monitor_params:
            widget = QDoubleSpinBox()
            widget.setRange(min_val, max_val)
            widget.setSingleStep(step)
            widget.setSuffix(f" {suffix}")
            widget.setToolTip(tooltip)
            widget.setStyleSheet(
                "QDoubleSpinBox { background-color: #e8e8ff; }"
            )  # Blue tint

            self.timing_widgets[param] = widget

            desc_label = QLabel(f"<small>{tooltip}</small>")
            desc_label.setStyleSheet("color: gray;")

            monitor_layout.addRow(f"{label}:", widget)
            monitor_layout.addRow("", desc_label)

        scroll_layout.addWidget(monitor_group)

        # Performance indicator
        performance_frame = QFrame()
        performance_frame.setFrameStyle(QFrame.Box)
        performance_layout = QVBoxLayout(performance_frame)

        self.performance_label = QLabel("⚡ Performance Impact: Calculating...")
        self.performance_label.setAlignment(Qt.AlignCenter)
        self.performance_label.setStyleSheet("font-weight: bold; padding: 10px;")
        performance_layout.addWidget(self.performance_label)

        scroll_layout.addWidget(performance_frame)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "⏱️ Timing")

    def _create_behavior_tab(self):
        """✅ Tab para parámetros de comportamiento"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Combat Behavior Group
        combat_group = QGroupBox("⚔️ Combat Behavior")
        combat_layout = QFormLayout(combat_group)

        # Boolean options
        bool_params = [
            ("auto_potions", "Auto Potions", "Automatically use HP/MP potions"),
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

            desc_label = QLabel(f"<small>{tooltip}</small>")
            desc_label.setStyleSheet("color: gray;")

            combat_layout.addRow(f"{label}:", widget)
            combat_layout.addRow("", desc_label)

        scroll_layout.addWidget(combat_group)

        # Thresholds Group
        threshold_group = QGroupBox("🎯 Thresholds & Tolerances")
        threshold_layout = QFormLayout(threshold_group)

        # Potion threshold
        self.behavior_widgets["potion_threshold"] = QSpinBox()
        self.behavior_widgets["potion_threshold"].setRange(1, 99)
        self.behavior_widgets["potion_threshold"].setSuffix("%")
        self.behavior_widgets["potion_threshold"].setToolTip(
            "HP/MP percentage to trigger potion use"
        )
        threshold_layout.addRow(
            "Potion Threshold:", self.behavior_widgets["potion_threshold"]
        )

        # OCR tolerance
        self.behavior_widgets["ocr_tolerance"] = QSpinBox()
        self.behavior_widgets["ocr_tolerance"].setRange(50, 100)
        self.behavior_widgets["ocr_tolerance"].setSuffix("%")
        self.behavior_widgets["ocr_tolerance"].setToolTip(
            "OCR text matching accuracy required"
        )
        threshold_layout.addRow(
            "OCR Tolerance:", self.behavior_widgets["ocr_tolerance"]
        )

        # Fuzzy match threshold
        # self.behavior_widgets["fuzzy_match_threshold"] = QSpinBox()
        # self.behavior_widgets["fuzzy_match_threshold"].setRange(50, 100)
        # self.behavior_widgets["fuzzy_match_threshold"].setSuffix("%")
        # self.behavior_widgets["fuzzy_match_threshold"].setToolTip(
        #     "Fuzzy string matching threshold for target names"
        # )
        # threshold_layout.addRow(
        #     "Fuzzy Match Threshold:", self.behavior_widgets["fuzzy_match_threshold"]
        # )

        scroll_layout.addWidget(threshold_group)

        # Looting Configuration Group
        loot_group = QGroupBox("📦 Looting Configuration")
        loot_layout = QFormLayout(loot_group)

        loot_params = [
            (
                "loot_duration",
                "Loot Duration",
                "Total time spent looting",
                0.1,
                5.0,
                0.1,
                "s",
            ),
            (
                "loot_initial_delay",
                "Initial Delay",
                "Delay before first loot attempt",
                0.0,
                2.0,
                0.1,
                "s",
            ),
            (
                "loot_attempts",
                "Loot Attempts",
                "Number of loot key presses",
                1,
                10,
                1,
                "",
            ),
            (
                "loot_attempt_interval",
                "Attempt Interval",
                "Time between loot attempts",
                0.1,
                2.0,
                0.1,
                "s",
            ),
        ]

        for param, label, tooltip, min_val, max_val, step, suffix in loot_params:
            if param == "loot_attempts":
                widget = QSpinBox()
                widget.setRange(int(min_val), int(max_val))
                widget.setSingleStep(int(step))
            else:
                widget = QDoubleSpinBox()
                widget.setRange(min_val, max_val)
                widget.setSingleStep(step)

            if suffix:
                widget.setSuffix(f" {suffix}")
            widget.setToolTip(tooltip)

            self.behavior_widgets[param] = widget

            desc_label = QLabel(f"<small>{tooltip}</small>")
            desc_label.setStyleSheet("color: gray;")

            loot_layout.addRow(f"{label}:", widget)
            loot_layout.addRow("", desc_label)

        # Loot key
        self.behavior_widgets["loot_key"] = QLineEdit()
        self.behavior_widgets["loot_key"].setMaxLength(1)
        self.behavior_widgets["loot_key"].setToolTip("Key to press for looting")
        loot_layout.addRow("Loot Key:", self.behavior_widgets["loot_key"])

        scroll_layout.addWidget(loot_group)
        scroll_layout.addStretch()

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        self.tab_widget.addTab(tab, "🎮 Behavior")

    def _create_advanced_tab(self):
        """✅ Tab para configuración avanzada"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Skills Global Settings
        skills_group = QGroupBox("🎯 Skills Global Settings")
        skills_layout = QFormLayout(skills_group)

        # Global cooldown
        self.global_cooldown_spin = QDoubleSpinBox()
        self.global_cooldown_spin.setRange(0.05, 1.0)
        self.global_cooldown_spin.setSingleStep(0.05)
        self.global_cooldown_spin.setSuffix(" s")
        self.global_cooldown_spin.setToolTip("Minimum time between any skill uses")
        skills_layout.addRow("Global Cooldown:", self.global_cooldown_spin)

        layout.addWidget(skills_group)

        # Whitelist Management
        whitelist_group = QGroupBox("📋 Mob Whitelist")
        whitelist_layout = QVBoxLayout(whitelist_group)

        whitelist_layout.addWidget(QLabel("Allowed mobs (one per line):"))
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setMaximumHeight(200)
        self.whitelist_edit.setToolTip(
            "Enter mob names that the bot is allowed to attack"
        )
        whitelist_layout.addWidget(self.whitelist_edit)

        layout.addWidget(whitelist_group)

        # Configuration Management
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

        # Configuration summary
        self.config_summary = QTextEdit()
        self.config_summary.setMaximumHeight(150)
        self.config_summary.setReadOnly(True)
        config_layout.addRow("Summary:", self.config_summary)

        layout.addWidget(config_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "🔧 Advanced")

    def _create_debug_tab(self):
        """✅ Tab para configuración de debug"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Debug Options
        debug_group = QGroupBox("🐛 Debug & Monitoring")
        debug_layout = QFormLayout(debug_group)

        # Log level
        self.debug_widgets["log_level"] = QComboBox()
        self.debug_widgets["log_level"].addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.debug_widgets["log_level"].setToolTip("Set logging verbosity level")
        debug_layout.addRow("Log Level:", self.debug_widgets["log_level"])

        # Debug options
        debug_bool_params = [
            ("save_screenshots", "Save Screenshots", "Save screenshots for debugging"),
            (
                "performance_monitoring",
                "Performance Monitoring",
                "Monitor and log performance metrics",
            ),
            (
                "verbose_combat_logs",
                "Verbose Combat Logs",
                "Enable detailed combat logging",
            ),
        ]

        for param, label, tooltip in debug_bool_params:
            widget = QCheckBox()
            widget.setToolTip(tooltip)
            self.debug_widgets[param] = widget
            debug_layout.addRow(f"{label}:", widget)

        layout.addWidget(debug_group)

        # Performance Monitor
        perf_group = QGroupBox("📈 Performance Monitor")
        perf_layout = QVBoxLayout(perf_group)

        self.performance_monitor = QTextEdit()
        self.performance_monitor.setReadOnly(True)
        self.performance_monitor.setMaximumHeight(200)
        perf_layout.addWidget(self.performance_monitor)

        layout.addWidget(perf_group)
        layout.addStretch()

        self.tab_widget.addTab(tab, "🐛 Debug")

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

            # Load debug settings
            debug_config = self.config_manager.config_data.get("debug", {})
            for param, widget in self.debug_widgets.items():
                if param in debug_config:
                    value = debug_config[param]
                    if isinstance(widget, QCheckBox):
                        widget.setChecked(bool(value))
                    elif isinstance(widget, QComboBox):
                        widget.setCurrentText(str(value))

            # Update displays
            self._update_performance_indicator()
            self._update_config_summary()

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

        # Connect preset buttons
        self.preset_aggressive_btn.clicked.connect(self._apply_aggressive_preset)
        self.preset_conservative_btn.clicked.connect(self._apply_conservative_preset)
        self.preset_balanced_btn.clicked.connect(self._apply_balanced_preset)

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
        self._update_performance_indicator()
        self._emit_config_change()

    def _on_behavior_changed(self):
        """Handle behavior parameter changes"""
        self._emit_config_change()

    def _on_whitelist_changed(self):
        """Handle whitelist changes for real-time updates"""
        self._emit_config_change()

    def _update_performance_indicator(self):
        """✅ Actualizar indicador de rendimiento"""
        try:
            # Calculate performance impact based on timing values
            total_calls_per_second = 0

            for param, widget in self.timing_widgets.items():
                value = widget.value()
                if value > 0:
                    calls_per_second = 1.0 / value
                    total_calls_per_second += calls_per_second

            # Determine performance level
            if total_calls_per_second > 15:
                level = "🔥 VERY HIGH"
                color = "#ff4444"
            elif total_calls_per_second > 10:
                level = "⚡ HIGH"
                color = "#ff8844"
            elif total_calls_per_second > 5:
                level = "⚖️ MODERATE"
                color = "#44aa44"
            else:
                level = "🐌 LOW"
                color = "#4444ff"

            self.performance_label.setText(
                f"⚡ Performance Impact: {level} ({total_calls_per_second:.1f} ops/sec)"
            )
            self.performance_label.setStyleSheet(
                f"font-weight: bold; padding: 10px; color: {color};"
            )

        except Exception as e:
            self.performance_label.setText("⚡ Performance Impact: Error calculating")

    def _update_config_summary(self):
        """✅ Actualizar resumen de configuración"""
        try:
            if hasattr(self, "config_summary"):
                summary = self.config_manager.get_summary()
                summary_text = []
                for key, value in summary.items():
                    summary_text.append(f"{key}: {value}")

                self.config_summary.setPlainText("\n".join(summary_text))
        except Exception as e:
            if hasattr(self, "config_summary"):
                self.config_summary.setPlainText(f"Error loading summary: {e}")

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

    def _apply_aggressive_preset(self):
        """Apply aggressive combat preset"""
        aggressive_timing = {
            "skill_interval": 0.8,
            "attack_interval": 1.0,
            "target_attempt_interval": 0.2,
            "post_combat_delay": 1.0,
            "assist_interval": 0.6,
            "stuck_detection_searching": 4.0,
            "stuck_in_combat_timeout": 6.0,
        }

        for param, value in aggressive_timing.items():
            if param in self.timing_widgets:
                self.timing_widgets[param].setValue(value)

        self._update_performance_indicator()
        QMessageBox.information(
            self,
            "Preset Applied",
            "⚡ Aggressive preset applied!\nHigh performance, fast combat.",
        )

    def _apply_conservative_preset(self):
        """Apply conservative combat preset"""
        conservative_timing = {
            "skill_interval": 1.5,
            "attack_interval": 2.0,
            "target_attempt_interval": 0.5,
            "post_combat_delay": 2.5,
            "assist_interval": 1.2,
            "stuck_detection_searching": 10.0,
            "stuck_in_combat_timeout": 15.0,
        }

        for param, value in conservative_timing.items():
            if param in self.timing_widgets:
                self.timing_widgets[param].setValue(value)

        self._update_performance_indicator()
        QMessageBox.information(
            self,
            "Preset Applied",
            "🛡️ Conservative preset applied!\nSafe, stable operation.",
        )

    def _apply_balanced_preset(self):
        """Apply balanced combat preset"""
        balanced_timing = {
            "skill_interval": 1.0,
            "attack_interval": 1.2,
            "target_attempt_interval": 0.3,
            "post_combat_delay": 1.5,
            "assist_interval": 0.8,
            "stuck_detection_searching": 6.0,
            "stuck_in_combat_timeout": 8.0,
        }

        for param, value in balanced_timing.items():
            if param in self.timing_widgets:
                self.timing_widgets[param].setValue(value)

        self._update_performance_indicator()
        QMessageBox.information(
            self,
            "Preset Applied",
            "⚖️ Balanced preset applied!\nOptimal balance of speed and stability.",
        )

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
