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
                "Post-combat delay between mob kills",
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

            # Create compact label with tooltip (remove extra description labels)
            full_label = f"{label}:"
            combat_layout.addRow(full_label, widget)

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

            stuck_layout.addRow(f"{label}:", widget)

        scroll_layout.addWidget(stuck_group)

        # Monitoring Timing Group
        monitor_group = QGroupBox("📊 Monitoring & Logging")
        monitor_layout = QFormLayout(monitor_group)

        monitor_params = [
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

            monitor_layout.addRow(f"{label}:", widget)

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

        # Boolean options (including basic options moved from main window)
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

            combat_layout.addRow(f"{label}:", widget)

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
                "loot_attempts",
                "Loot Attempts",
                "Number of loot key presses",
                1,
                10,
                1,
                "",
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
        """✅ Enhanced Debug Tab - Bot Behavior Diagnostics"""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Debug Configuration
        debug_config_group = QGroupBox("🐛 Debug Configuration")
        debug_config_layout = QFormLayout(debug_config_group)

        # Log level
        self.debug_widgets["log_level"] = QComboBox()
        self.debug_widgets["log_level"].addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.debug_widgets["log_level"].setToolTip("Set logging verbosity level")
        debug_config_layout.addRow("Log Level:", self.debug_widgets["log_level"])

        # Performance monitoring toggle
        self.debug_widgets["performance_monitoring"] = QCheckBox()
        self.debug_widgets["performance_monitoring"].setToolTip("Enable real-time performance tracking")
        debug_config_layout.addRow("Performance Monitoring:", self.debug_widgets["performance_monitoring"])

        layout.addWidget(debug_config_group)

        # Bot Behavior Diagnostics
        behavior_group = QGroupBox("🤖 Bot Behavior Diagnostics")
        behavior_layout = QVBoxLayout(behavior_group)

        # Real-time bot state display
        state_frame = QFrame()
        state_frame.setFrameStyle(QFrame.StyledPanel)
        state_layout = QHBoxLayout(state_frame)

        state_layout.addWidget(QLabel("<b>Current State:</b>"))
        self.current_state_label = QLabel("Not Connected")
        self.current_state_label.setStyleSheet("padding: 4px; background-color: #f0f0f0; border-radius: 3px;")
        state_layout.addWidget(self.current_state_label)

        state_layout.addWidget(QLabel("<b>Combat State:</b>"))
        self.combat_state_label = QLabel("Unknown")
        self.combat_state_label.setStyleSheet("padding: 4px; background-color: #f0f0f0; border-radius: 3px;")
        state_layout.addWidget(self.combat_state_label)

        state_layout.addStretch()
        behavior_layout.addWidget(state_frame)

        # Bot behavior metrics
        metrics_layout = QHBoxLayout()

        # Left metrics
        left_metrics = QGroupBox("📊 Performance Metrics")
        left_metrics_layout = QFormLayout(left_metrics)

        self.ocr_accuracy_label = QLabel("N/A")
        self.targeting_success_label = QLabel("N/A") 
        self.skill_execution_label = QLabel("N/A")

        left_metrics_layout.addRow("OCR Accuracy:", self.ocr_accuracy_label)
        left_metrics_layout.addRow("Targeting Success:", self.targeting_success_label)
        left_metrics_layout.addRow("Skill Execution:", self.skill_execution_label)

        # Right metrics  
        right_metrics = QGroupBox("⚠️ Error Tracking")
        right_metrics_layout = QFormLayout(right_metrics)

        self.error_count_label = QLabel("0")
        self.stuck_count_label = QLabel("0")
        self.failed_targets_label = QLabel("0")

        right_metrics_layout.addRow("Total Errors:", self.error_count_label)
        right_metrics_layout.addRow("Stuck Events:", self.stuck_count_label)
        right_metrics_layout.addRow("Failed Targets:", self.failed_targets_label)

        metrics_layout.addWidget(left_metrics)
        metrics_layout.addWidget(right_metrics)
        behavior_layout.addLayout(metrics_layout)

        layout.addWidget(behavior_group)

        # Real-time Diagnostic Log
        log_group = QGroupBox("📝 Diagnostic Log")
        log_layout = QVBoxLayout(log_group)

        # Log controls
        log_controls = QHBoxLayout()
        
        self.diagnostic_filter = QComboBox()
        self.diagnostic_filter.addItems(["All Events", "Errors Only", "State Changes", "Combat Events", "Performance Issues"])
        self.diagnostic_filter.setToolTip("Filter diagnostic messages")
        log_controls.addWidget(QLabel("Filter:"))
        log_controls.addWidget(self.diagnostic_filter)

        self.clear_log_btn = QPushButton("🗑️ Clear Log")
        self.export_log_btn = QPushButton("💾 Export Log")
        log_controls.addStretch()
        log_controls.addWidget(self.clear_log_btn)
        log_controls.addWidget(self.export_log_btn)

        log_layout.addLayout(log_controls)

        # Diagnostic log display
        self.diagnostic_log = QTextEdit()
        self.diagnostic_log.setReadOnly(True)
        self.diagnostic_log.setMaximumHeight(250)
        self.diagnostic_log.setStyleSheet("QTextEdit { font-family: 'Courier New', monospace; font-size: 10px; }")
        log_layout.addWidget(self.diagnostic_log)

        layout.addWidget(log_group)

        # Initialize diagnostic data
        self._init_diagnostic_system()

        self.tab_widget.addTab(tab, "🐛 Debug")

    def _init_diagnostic_system(self):
        """Initialize the diagnostic monitoring system"""
        try:
            # Connect diagnostic log controls
            if hasattr(self, 'clear_log_btn'):
                self.clear_log_btn.clicked.connect(self._clear_diagnostic_log)
            if hasattr(self, 'export_log_btn'):
                self.export_log_btn.clicked.connect(self._export_diagnostic_log)
            if hasattr(self, 'diagnostic_filter'):
                self.diagnostic_filter.currentTextChanged.connect(self._filter_diagnostic_log)
            
            # Initialize diagnostic data
            self.diagnostic_data = {
                'total_errors': 0,
                'stuck_events': 0,
                'failed_targets': 0,
                'ocr_accuracy': 0.0,
                'targeting_success': 0.0,
                'skill_execution': 0.0,
                'log_entries': []
            }
            
            # Add initial diagnostic message
            self._add_diagnostic_message("Debug", "Diagnostic system initialized")
            
        except Exception as e:
            print(f"Error initializing diagnostic system: {e}")

    def _add_diagnostic_message(self, category, message):
        """Add a message to the diagnostic log"""
        try:
            if hasattr(self, 'diagnostic_log'):
                timestamp = __import__('datetime').datetime.now().strftime("%H:%M:%S")
                formatted_message = f"[{timestamp}] [{category}] {message}"
                
                # Store in data
                self.diagnostic_data['log_entries'].append({
                    'timestamp': timestamp,
                    'category': category,
                    'message': message,
                    'formatted': formatted_message
                })
                
                # Keep only last 500 entries
                if len(self.diagnostic_data['log_entries']) > 500:
                    self.diagnostic_data['log_entries'] = self.diagnostic_data['log_entries'][-500:]
                
                # Update display based on current filter
                self._update_diagnostic_display()
                
        except Exception as e:
            print(f"Error adding diagnostic message: {e}")

    def _update_diagnostic_display(self):
        """Update the diagnostic log display based on current filter"""
        try:
            if not hasattr(self, 'diagnostic_log') or not hasattr(self, 'diagnostic_filter'):
                return
                
            current_filter = self.diagnostic_filter.currentText()
            filtered_entries = []
            
            for entry in self.diagnostic_data['log_entries']:
                if current_filter == "All Events":
                    filtered_entries.append(entry['formatted'])
                elif current_filter == "Errors Only" and entry['category'] in ['Error', 'Critical']:
                    filtered_entries.append(entry['formatted'])
                elif current_filter == "State Changes" and entry['category'] in ['State', 'Combat']:
                    filtered_entries.append(entry['formatted'])
                elif current_filter == "Combat Events" and entry['category'] in ['Combat', 'Skill', 'Target']:
                    filtered_entries.append(entry['formatted'])
                elif current_filter == "Performance Issues" and entry['category'] in ['Performance', 'OCR', 'Timing']:
                    filtered_entries.append(entry['formatted'])
            
            # Update display
            self.diagnostic_log.setText('\n'.join(filtered_entries[-100:]))  # Show last 100 entries
            
            # Auto-scroll to bottom
            cursor = self.diagnostic_log.textCursor()
            cursor.movePosition(cursor.End)
            self.diagnostic_log.setTextCursor(cursor)
            
        except Exception as e:
            print(f"Error updating diagnostic display: {e}")

    def _clear_diagnostic_log(self):
        """Clear the diagnostic log"""
        try:
            self.diagnostic_data['log_entries'] = []
            if hasattr(self, 'diagnostic_log'):
                self.diagnostic_log.clear()
            self._add_diagnostic_message("Debug", "Diagnostic log cleared")
        except Exception as e:
            print(f"Error clearing diagnostic log: {e}")

    def _export_diagnostic_log(self):
        """Export diagnostic log to file"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import os
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                "Export Diagnostic Log", 
                "diagnostic_log.txt", 
                "Text Files (*.txt);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("KBot Diagnostic Log\n")
                    f.write("=" * 50 + "\n\n")
                    for entry in self.diagnostic_data['log_entries']:
                        f.write(entry['formatted'] + '\n')
                
                self._add_diagnostic_message("Debug", f"Log exported to {os.path.basename(filename)}")
                
        except Exception as e:
            self._add_diagnostic_message("Error", f"Failed to export log: {e}")

    def _filter_diagnostic_log(self):
        """Handle filter change"""
        self._update_diagnostic_display()

    def update_diagnostic_metrics(self, metrics_data):
        """Update diagnostic metrics from external source"""
        try:
            if not hasattr(self, 'diagnostic_data'):
                return
                
            # Update error tracking
            if 'total_errors' in metrics_data:
                self.diagnostic_data['total_errors'] = metrics_data['total_errors']
                if hasattr(self, 'error_count_label'):
                    self.error_count_label.setText(str(metrics_data['total_errors']))
            
            if 'stuck_events' in metrics_data:
                self.diagnostic_data['stuck_events'] = metrics_data['stuck_events']
                if hasattr(self, 'stuck_count_label'):
                    self.stuck_count_label.setText(str(metrics_data['stuck_events']))
            
            if 'failed_targets' in metrics_data:
                self.diagnostic_data['failed_targets'] = metrics_data['failed_targets']
                if hasattr(self, 'failed_targets_label'):
                    self.failed_targets_label.setText(str(metrics_data['failed_targets']))
            
            # Update performance metrics
            if 'ocr_accuracy' in metrics_data:
                accuracy = metrics_data['ocr_accuracy']
                self.diagnostic_data['ocr_accuracy'] = accuracy
                if hasattr(self, 'ocr_accuracy_label'):
                    color = "#00aa00" if accuracy > 90 else "#ff8800" if accuracy > 70 else "#dd0000"
                    self.ocr_accuracy_label.setText(f"{accuracy:.1f}%")
                    self.ocr_accuracy_label.setStyleSheet(f"color: {color}; font-weight: bold;")
            
            # Update bot states
            if 'bot_state' in metrics_data:
                state = metrics_data['bot_state']
                if hasattr(self, 'current_state_label'):
                    self.current_state_label.setText(state.title())
                    color = "#00aa00" if state == "running" else "#ff8800" if state == "paused" else "#666666"
                    self.current_state_label.setStyleSheet(f"padding: 4px; background-color: {color}; color: white; border-radius: 3px; font-weight: bold;")
            
            if 'combat_state' in metrics_data:
                combat_state = metrics_data['combat_state']
                if hasattr(self, 'combat_state_label'):
                    self.combat_state_label.setText(combat_state.title())
                    color = "#dd0000" if combat_state == "fighting" else "#00aa00" if combat_state == "searching" else "#666666"
                    self.combat_state_label.setStyleSheet(f"padding: 4px; background-color: {color}; color: white; border-radius: 3px; font-weight: bold;")
                    
        except Exception as e:
            print(f"Error updating diagnostic metrics: {e}")

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
        """✅ Enhanced configuration summary with ALL settings"""
        try:
            if hasattr(self, "config_summary"):
                summary_html = self._generate_comprehensive_summary()
                self.config_summary.setHtml(summary_html)
        except Exception as e:
            if hasattr(self, "config_summary"):
                self.config_summary.setPlainText(f"Error loading summary: {e}")

    def _generate_comprehensive_summary(self) -> str:
        """Generate comprehensive HTML summary of all configuration settings"""
        try:
            html_parts = []
            html_parts.append("<h3 style='color: #2e86de; margin: 0;'>📋 Configuration Overview</h3>")
            
            # Basic Info
            version = self.config_manager.config_data.get("version", "Unknown")
            html_parts.append(f"<p><b>Version:</b> {version}</p>")
            
            # Combat Behavior
            behavior = self.config_manager.get_combat_behavior()
            html_parts.append("<h4 style='color: #00a8ff; margin: 5px 0;'>⚔️ Combat Behavior</h4>")
            html_parts.append(f"<ul style='margin: 5px 0; padding-left: 20px;'>")
            html_parts.append(f"<li>Potion Threshold: <b>{behavior.get('potion_threshold', 'N/A')}%</b></li>")
            html_parts.append(f"<li>Enable Looting: <b>{'✅' if behavior.get('enable_looting') else '❌'}</b></li>")
            html_parts.append(f"<li>Assist Mode: <b>{'✅' if behavior.get('assist_mode') else '❌'}</b></li>")
            html_parts.append(f"<li>Use Skills: <b>{'✅' if behavior.get('use_skills') else '❌'}</b></li>")
            html_parts.append(f"<li>OCR Tolerance: <b>{behavior.get('ocr_tolerance', 'N/A')}%</b></li>")
            html_parts.append("</ul>")
            
            # Timing Settings
            timing = self.config_manager.get_combat_timing()
            html_parts.append("<h4 style='color: #00a8ff; margin: 5px 0;'>⏱️ Key Timings</h4>")
            html_parts.append(f"<ul style='margin: 5px 0; padding-left: 20px;'>")
            html_parts.append(f"<li>Skill Interval: <b>{timing.get('skill_interval', 'N/A')}s</b></li>")
            html_parts.append(f"<li>Attack Interval: <b>{timing.get('attack_interval', 'N/A')}s</b></li>")
            html_parts.append(f"<li>Stuck Detection: <b>{timing.get('stuck_detection_searching', 'N/A')}s</b></li>")
            html_parts.append("</ul>")
            
            # Skills Info
            skills_config = self.config_manager.get_skills_config()
            skills_count = len(skills_config.get("definitions", {}))
            rotations_count = len(skills_config.get("rotations", {}))
            active_rotation = skills_config.get("active_rotation", "None")
            html_parts.append("<h4 style='color: #00a8ff; margin: 5px 0;'>🎯 Skills & Rotations</h4>")
            html_parts.append(f"<ul style='margin: 5px 0; padding-left: 20px;'>")
            html_parts.append(f"<li>Total Skills: <b>{skills_count}</b></li>")
            html_parts.append(f"<li>Rotations: <b>{rotations_count}</b></li>")
            html_parts.append(f"<li>Active Rotation: <b>{active_rotation}</b></li>")
            html_parts.append(f"<li>Global Cooldown: <b>{skills_config.get('global_cooldown', 'N/A')}s</b></li>")
            html_parts.append("</ul>")
            
            # Whitelist
            whitelist = self.config_manager.get_whitelist()
            html_parts.append("<h4 style='color: #00a8ff; margin: 5px 0;'>📋 Targets</h4>")
            html_parts.append(f"<ul style='margin: 5px 0; padding-left: 20px;'>")
            html_parts.append(f"<li>Whitelisted Mobs: <b>{len(whitelist)}</b> ({', '.join(whitelist[:3])}{'...' if len(whitelist) > 3 else ''})</li>")
            html_parts.append("</ul>")
            
            return "".join(html_parts)
            
        except Exception as e:
            return f"<p style='color: red;'>Error generating summary: {e}</p>"

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
            "skill_interval": 0.4,
            "attack_interval": 0.5,
            "target_attempt_interval": 0.2,
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
            "skill_interval": 1.2,
            "attack_interval": 3.0,
            "target_attempt_interval": 0.5,
            "stuck_detection_searching": 12.0,
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
            "skill_interval": 0.6,
            "attack_interval": 0,
            "target_attempt_interval": 0.3,
            "stuck_detection_searching": 8.0,
            "stuck_in_combat_timeout": 10.0,
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
