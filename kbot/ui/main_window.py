# ui/main_window.py
import sys
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QCheckBox, QSpinBox, QTextEdit,
    QTabWidget, QSplitter, QStatusBar, QMenuBar, QAction, QMessageBox,
    QProgressBar, QFrame, QDialogButtonBox, QDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon
from PIL import Image
from core.bot_engine import BotEngine, BotState
from ui.dialogs.window_selector import WindowSelectorDialog
from ui.dialogs.region_config import RegionConfigDialog
from ui.dialogs.skill_config import SkillConfigDialog
from ui.widgets.log_widget import LogWidget
from ui.widgets.status_widget import StatusWidget
from utils.exceptions import BotError
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import QScrollArea
import traceback

class TantraBotMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        """Initialize main window with detailed debugging"""
        super().__init__()
        print("DEBUG: MainWindow __init__ started")
        
        try:
            print("DEBUG: Setting window properties...")
            # UI setup
            self.setWindowTitle("Tantra Bot v2.0.0 - by cursebox")
            self.setMinimumSize(900, 700)
            self.resize(1200, 800)
            print("DEBUG: Window properties set")
            
            print("DEBUG: Importing bot engine...")
            from core.bot_engine import BotEngine
            print("DEBUG: BotEngine imported successfully")
            
            print("DEBUG: Creating bot engine instance...")
            # Initialize bot engine
            self.bot_engine = BotEngine()
            print("DEBUG: Bot engine created successfully")
            
            print("DEBUG: Setting up UI...")
            # Create UI
            self._setup_ui()
            print("DEBUG: UI setup completed")
            
            print("DEBUG: Setting up menu bar...")
            self._setup_menu_bar()
            print("DEBUG: Menu bar setup completed")
            
            print("DEBUG: Setting up status bar...")
            self._setup_status_bar()
            print("DEBUG: Status bar setup completed")
            
            print("DEBUG: Connecting signals...")
            self._connect_signals()
            print("DEBUG: Signals connected")
            
            print("DEBUG: Loading configuration...")
            # Load initial configuration
            self._load_configuration()
            print("DEBUG: Configuration loaded")
            
            print("DEBUG: Setting up refresh timer...")
            # Setup refresh timer for UI updates
            from PyQt5.QtCore import QTimer
            self.refresh_timer = QTimer()
            self.refresh_timer.timeout.connect(self._update_ui)
            self.refresh_timer.start(1000)  # Update every second
            print("DEBUG: Refresh timer setup completed")
            
            print("DEBUG: MainWindow initialization completed successfully")
            
        except Exception as e:
            print(f"DEBUG ERROR in MainWindow.__init__: {e}")
            print(f"DEBUG ERROR TYPE: {type(e).__name__}")
            import traceback
            print(f"DEBUG TRACEBACK:")
            print(traceback.format_exc())
            raise  # Re-raise the exception
    
    def _setup_ui(self):
        """Setup the user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout - vertical splitter
        splitter = QSplitter(Qt.Vertical)
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(splitter)
        
        # Top section - tabbed interface
        self.tab_widget = QTabWidget()
        splitter.addWidget(self.tab_widget)
        
        # Create tabs
        self._create_control_tab()
        self._create_skills_tab()
        self._create_config_tab()
        self._create_stats_tab()
        
        # Bottom section - log and status
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)
        
        # Log widget
        self.log_widget = LogWidget()
        bottom_layout.addWidget(self.log_widget, 2)
        
        # Status widget
        self.status_widget = StatusWidget()
        bottom_layout.addWidget(self.status_widget, 1)
        
        splitter.addWidget(bottom_widget)
        
        # Set splitter proportions
        splitter.setSizes([400, 200])
    
    def _create_control_tab(self):
        """Create the main control tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Control buttons section
        control_group = QGroupBox("Bot Control")
        control_layout = QVBoxLayout(control_group)
        
        # Main control buttons
        button_layout = QHBoxLayout()
        
        self.start_stop_btn = QPushButton("Start Bot")
        self.start_stop_btn.setMinimumHeight(40)
        self.start_stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        button_layout.addWidget(self.start_stop_btn)
        
        self.pause_resume_btn = QPushButton("Pause")
        self.pause_resume_btn.setMinimumHeight(40)
        self.pause_resume_btn.setEnabled(False)
        button_layout.addWidget(self.pause_resume_btn)
        
        control_layout.addLayout(button_layout)
        
        # Bot status
        self.bot_status_label = QLabel("Status: Stopped")
        self.bot_status_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        control_layout.addWidget(self.bot_status_label)
        
        layout.addWidget(control_group)
        
        # Window management section
        window_group = QGroupBox("Window Management")
        window_layout = QVBoxLayout(window_group)
        
        self.select_window_btn = QPushButton("Select Game Window")
        window_layout.addWidget(self.select_window_btn)
        
        self.current_window_label = QLabel("No window selected")
        window_layout.addWidget(self.current_window_label)
        
        layout.addWidget(window_group)
        
        # Options section
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_pots_cb = QCheckBox("Auto Potions (HP & MP)")
        self.auto_pots_cb.setChecked(True)
        options_layout.addWidget(self.auto_pots_cb)
        
        # Potion threshold
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Potion Threshold:"))
        self.potion_threshold_spin = QSpinBox()
        self.potion_threshold_spin.setRange(1, 99)
        self.potion_threshold_spin.setValue(70)
        self.potion_threshold_spin.setSuffix("%")
        threshold_layout.addWidget(self.potion_threshold_spin)
        threshold_layout.addStretch()
        options_layout.addLayout(threshold_layout)
        
        layout.addWidget(options_group)
        
        # Mob whitelist section
        whitelist_group = QGroupBox("Mob Whitelist")
        whitelist_layout = QVBoxLayout(whitelist_group)
        
        whitelist_layout.addWidget(QLabel("Allowed mobs (one per line):"))
        self.whitelist_edit = QTextEdit()
        self.whitelist_edit.setMaximumHeight(100)
        self.whitelist_edit.setPlainText("Byokbo")
        whitelist_layout.addWidget(self.whitelist_edit)
        
        layout.addWidget(whitelist_group)
        
        # Test buttons section
        test_group = QGroupBox("Testing & Configuration")
        test_layout = QGridLayout(test_group)
        
        self.test_pixels_btn = QPushButton("Test Pixel Accuracy")
        test_layout.addWidget(self.test_pixels_btn, 0, 0)
        
        self.test_ocr_btn = QPushButton("Test OCR")
        test_layout.addWidget(self.test_ocr_btn, 0, 1)
        
        self.config_regions_btn = QPushButton("Configure Regions")
        test_layout.addWidget(self.config_regions_btn, 1, 0)
        
        self.config_skills_btn = QPushButton("Configure Skills")
        test_layout.addWidget(self.config_skills_btn, 1, 1)
        
        layout.addWidget(test_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Control")
    
    def _create_skills_tab(self):
        """Create the skills configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <b>Skill Configuration:</b><br>
        • Slots 1-8: Number keys with configurable cooldowns<br>
        • Slots F1-F10: Function keys with configurable cooldowns<br>
        • HP Potions: Slot 0 (default)<br>
        • MP Potions: Slot 9 (default)
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Slots 1-8
        slots_group = QGroupBox("Slots 1-8 (Number Keys)")
        slots_layout = QGridLayout(slots_group)
        # Define default values for each slot (index 0-7 for slots 1-8)
        default_values = [1, 1, 1, 150, 1, 1, 150, 600]  # slots 1,2,3,4,5,6,7,8
        self.slot_spins = []
        for i in range(8):
            label = QLabel(f"Slot {i+1}:")
            spin = QSpinBox()
            spin.setRange(1, 3600)  # 1 second to 1 hour
            spin.setValue(default_values[i])
            spin.setSuffix(" sec")
            
            slots_layout.addWidget(label, i // 4, (i % 4) * 2)
            slots_layout.addWidget(spin, i // 4, (i % 4) * 2 + 1)
            self.slot_spins.append(spin)
        
        layout.addWidget(slots_group)
        
        # F-Key slots
        f_slots_group = QGroupBox("F-Key Slots (F1-F10)")
        f_slots_layout = QGridLayout(f_slots_group)
        
        self.f_slot_spins = []
        for i in range(10):
            label = QLabel(f"F{i+1}:")
            spin = QSpinBox()
            spin.setRange(1, 3600)
            spin.setValue(120)
            spin.setSuffix(" sec")
            
            f_slots_layout.addWidget(label, i // 5, (i % 5) * 2)
            f_slots_layout.addWidget(spin, i // 5, (i % 5) * 2 + 1)
            self.f_slot_spins.append(spin)
        
        layout.addWidget(f_slots_group)
        
        # Advanced skill configuration button
        advanced_btn = QPushButton("Advanced Skill Configuration")
        advanced_btn.clicked.connect(self._open_skill_config)
        layout.addWidget(advanced_btn)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Skills")
    
    def _create_config_tab(self):
        """Create the configuration tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Region configuration
        region_group = QGroupBox("Region Configuration")
        region_layout = QVBoxLayout(region_group)
        
        region_info = QLabel("""
        Configure screen regions for HP/MP bars and target detection.
        Use 'Configure Regions' button to set coordinates.
        """)
        region_layout.addWidget(region_info)
        
        self.config_regions_btn2 = QPushButton("Configure Regions")
        region_layout.addWidget(self.config_regions_btn2)
        
        layout.addWidget(region_group)
        
        # Timing configuration
        timing_group = QGroupBox("Timing Configuration")
        timing_layout = QGridLayout(timing_group)
        
        # Combat timing
        timing_layout.addWidget(QLabel("Combat Check Interval:"), 0, 0)
        self.combat_timing_spin = QSpinBox()
        self.combat_timing_spin.setRange(100, 5000)
        self.combat_timing_spin.setValue(1000)
        self.combat_timing_spin.setSuffix(" ms")
        timing_layout.addWidget(self.combat_timing_spin, 0, 1)
        
        timing_layout.addWidget(QLabel("Attack Interval:"), 1, 0)
        self.attack_timing_spin = QSpinBox()
        self.attack_timing_spin.setRange(500, 5000)
        self.attack_timing_spin.setValue(1500)
        self.attack_timing_spin.setSuffix(" ms")
        timing_layout.addWidget(self.attack_timing_spin, 1, 1)
        
        timing_layout.addWidget(QLabel("Potion Interval:"), 2, 0)
        self.potion_timing_spin = QSpinBox()
        self.potion_timing_spin.setRange(100, 2000)
        self.potion_timing_spin.setValue(500)
        self.potion_timing_spin.setSuffix(" ms")
        timing_layout.addWidget(self.potion_timing_spin, 2, 1)
        
        layout.addWidget(timing_group)
        
        # Configuration file management
        file_group = QGroupBox("Configuration Management")
        file_layout = QVBoxLayout(file_group)
        
        file_buttons = QHBoxLayout()
        
        self.save_config_btn = QPushButton("Save Configuration")
        file_buttons.addWidget(self.save_config_btn)
        
        self.load_config_btn = QPushButton("Reload Configuration")
        file_buttons.addWidget(self.load_config_btn)
        
        self.reset_config_btn = QPushButton("Reset to Defaults")
        file_buttons.addWidget(self.reset_config_btn)
        
        file_layout.addLayout(file_buttons)
        
        layout.addWidget(file_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Configuration")
    
    def _create_stats_tab(self):
        """Create the statistics tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Runtime stats
        runtime_group = QGroupBox("Runtime Statistics")
        runtime_layout = QGridLayout(runtime_group)
        
        self.runtime_label = QLabel("Runtime: 0:00:00")
        runtime_layout.addWidget(QLabel("Current Runtime:"), 0, 0)
        runtime_layout.addWidget(self.runtime_label, 0, 1)
        
        self.targets_label = QLabel("0")
        runtime_layout.addWidget(QLabel("Targets Killed:"), 1, 0)
        runtime_layout.addWidget(self.targets_label, 1, 1)
        
        self.potions_label = QLabel("0")
        runtime_layout.addWidget(QLabel("Potions Used:"), 2, 0)
        runtime_layout.addWidget(self.potions_label, 2, 1)
        
        self.skills_label = QLabel("0")
        runtime_layout.addWidget(QLabel("Skills Used:"), 3, 0)
        runtime_layout.addWidget(self.skills_label, 3, 1)
        
        layout.addWidget(runtime_group)
        
        # Input stats
        input_group = QGroupBox("Input Statistics")
        input_layout = QGridLayout(input_group)
        
        self.total_inputs_label = QLabel("0")
        input_layout.addWidget(QLabel("Total Inputs:"), 0, 0)
        input_layout.addWidget(self.total_inputs_label, 0, 1)
        
        self.success_rate_label = QLabel("0%")
        input_layout.addWidget(QLabel("Success Rate:"), 1, 0)
        input_layout.addWidget(self.success_rate_label, 1, 1)
        
        layout.addWidget(input_group)
        
        # Performance stats
        perf_group = QGroupBox("Performance")
        perf_layout = QGridLayout(perf_group)
        
        self.errors_label = QLabel("0")
        perf_layout.addWidget(QLabel("Errors:"), 0, 0)
        perf_layout.addWidget(self.errors_label, 0, 1)
        
        # Reset stats button
        reset_stats_btn = QPushButton("Reset Statistics")
        reset_stats_btn.clicked.connect(self._reset_stats)
        perf_layout.addWidget(reset_stats_btn, 1, 0, 1, 2)
        
        layout.addWidget(perf_group)
        
        layout.addStretch()
        self.tab_widget.addTab(tab, "Statistics")
    
    def _setup_menu_bar(self):
        """Setup the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        save_action = QAction('Save Configuration', self)
        save_action.triggered.connect(self._save_configuration)
        file_menu.addAction(save_action)
        
        load_action = QAction('Load Configuration', self)
        load_action.triggered.connect(self._load_configuration)
        file_menu.addAction(load_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        window_action = QAction('Select Window', self)
        window_action.triggered.connect(self._select_window)
        tools_menu.addAction(window_action)
        
        regions_action = QAction('Configure Regions', self)
        regions_action.triggered.connect(self._configure_regions)
        tools_menu.addAction(regions_action)
        
        skills_action = QAction('Configure Skills', self)
        skills_action.triggered.connect(self._open_skill_config)
        tools_menu.addAction(skills_action)
        
        tools_menu.addSeparator()
        
        test_pixels_action = QAction('Test Pixels', self)
        test_pixels_action.triggered.connect(self._test_pixels)
        tools_menu.addAction(test_pixels_action)
        
        test_ocr_action = QAction('Test OCR', self)
        test_ocr_action.triggered.connect(self._test_ocr)
        tools_menu.addAction(test_ocr_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _setup_status_bar(self):
        """Setup the status bar"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Status indicators
        self.bot_state_label = QLabel("Stopped")
        self.status_bar.addWidget(self.bot_state_label)
        
        self.status_bar.addPermanentWidget(QLabel("Tantra Bot v2.0.0"))
    
    def _connect_signals(self):
        """Connect all signals"""
        # Bot engine signals
        self.bot_engine.state_changed.connect(self._on_bot_state_changed)
        self.bot_engine.vitals_updated.connect(self._on_vitals_updated)
        self.bot_engine.target_changed.connect(self._on_target_changed)
        self.bot_engine.error_occurred.connect(self._on_error_occurred)
        
        # Connect logger to log widget
        self.bot_engine.logger.log_message.connect(self.log_widget.add_message)
        
        # UI element signals
        self.start_stop_btn.clicked.connect(self._toggle_bot)
        self.pause_resume_btn.clicked.connect(self._pause_resume_bot)
        self.select_window_btn.clicked.connect(self._select_window)
        self.test_pixels_btn.clicked.connect(self._test_pixels)
        self.test_ocr_btn.clicked.connect(self._test_ocr)
        self.config_regions_btn.clicked.connect(self._configure_regions)
        self.config_regions_btn2.clicked.connect(self._configure_regions)
        self.config_skills_btn.clicked.connect(self._open_skill_config)
        self.save_config_btn.clicked.connect(self._save_configuration)
        self.load_config_btn.clicked.connect(self._load_configuration)
        self.reset_config_btn.clicked.connect(self._reset_configuration)
        
        # Configuration change signals
        self.auto_pots_cb.stateChanged.connect(self._on_config_changed)
        self.potion_threshold_spin.valueChanged.connect(self._on_config_changed)
        self.whitelist_edit.textChanged.connect(self._on_config_changed)
    
    def _load_configuration(self):
        """Load configuration into UI"""
        try:
            config = self.bot_engine.config_manager
            
            # Load options
            self.auto_pots_cb.setChecked(config.get_option('auto_pots', True))
            self.potion_threshold_spin.setValue(config.get_option('potion_threshold', 70))
            
            # Load whitelist
            whitelist = config.get_whitelist()
            self.whitelist_edit.setPlainText('\n'.join(whitelist))
            
            # Load slots
            slots = config.get_slots()
            for i, spin in enumerate(self.slot_spins):
                slot_key = f'slot{i+1}'
                if slot_key in slots:
                    try:
                        spin.setValue(int(float(slots[slot_key])))
                    except ValueError:
                        pass
            
            for i, spin in enumerate(self.f_slot_spins):
                slot_key = f'slotF{i+1}'
                if slot_key in slots:
                    try:
                        spin.setValue(int(float(slots[slot_key])))
                    except ValueError:
                        pass
            
            # Load timing
            timing = config.get_timing()
            self.combat_timing_spin.setValue(int(timing.get('combat_check', 1.0) * 1000))
            self.attack_timing_spin.setValue(int(timing.get('attack', 1.5) * 1000))
            self.potion_timing_spin.setValue(int(timing.get('potion', 0.5) * 1000))
            
            self.status_bar.showMessage("Configuration loaded", 2000)
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load configuration: {e}")
    
    def _save_configuration(self):
        """Save configuration from UI"""
        try:
            config = self.bot_engine.config_manager
            
            # Save options
            config.set_option('auto_pots', self.auto_pots_cb.isChecked())
            config.set_option('potion_threshold', self.potion_threshold_spin.value())
            
            # Save whitelist
            whitelist_text = self.whitelist_edit.toPlainText()
            whitelist = [line.strip() for line in whitelist_text.splitlines() if line.strip()]
            config.set_whitelist(whitelist)
            
            # Save slots
            slots = {}
            for i, spin in enumerate(self.slot_spins):
                slots[f'slot{i+1}'] = str(spin.value())
            
            for i, spin in enumerate(self.f_slot_spins):
                slots[f'slotF{i+1}'] = str(spin.value())
            
            config.set_slots(slots)
            
            # Save timing
            timing = {
                'combat_check': self.combat_timing_spin.value() / 1000.0,
                'attack': self.attack_timing_spin.value() / 1000.0,
                'potion': self.potion_timing_spin.value() / 1000.0,
                'target_switch': 0.7
            }
            config.set_timing(timing)
            
            # Save to file
            self.bot_engine.save_config()
            
            self.status_bar.showMessage("Configuration saved", 2000)
            QMessageBox.information(self, "Success", "Configuration saved successfully!")
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration: {e}")
    
    def _reset_configuration(self):
        """Reset configuration to defaults"""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.bot_engine.config_manager.reset_to_defaults()
                self._load_configuration()
                self.status_bar.showMessage("Configuration reset to defaults", 2000)
            except Exception as e:
                QMessageBox.critical(self, "Reset Error", f"Failed to reset configuration: {e}")
    
    @pyqtSlot()
    def _toggle_bot(self):
        """Toggle bot start/stop"""
        try:
            if self.bot_engine.get_state() == "stopped":
                # Validate configuration before starting
                if not self._validate_before_start():
                    return
                
                # Apply current UI settings
                self._apply_ui_settings()
                
                if self.bot_engine.start():
                    self.start_stop_btn.setText("Stop Bot")
                    self.start_stop_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #f44336;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #d32f2f;
                        }
                        QPushButton:pressed {
                            background-color: #b71c1c;
                        }
                    """)
                    self.pause_resume_btn.setEnabled(True)
            else:
                if self.bot_engine.stop():
                    self.start_stop_btn.setText("Start Bot")
                    self.start_stop_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #4CAF50;
                            color: white;
                            border: none;
                            border-radius: 5px;
                            font-weight: bold;
                            font-size: 14px;
                        }
                        QPushButton:hover {
                            background-color: #45a049;
                        }
                        QPushButton:pressed {
                            background-color: #3d8b40;
                        }
                    """)
                    self.pause_resume_btn.setEnabled(False)
                    self.pause_resume_btn.setText("Pause")
        
        except Exception as e:
            QMessageBox.critical(self, "Bot Error", f"Bot operation failed: {e}")
    
    @pyqtSlot()
    def _pause_resume_bot(self):
        """Pause/resume bot"""
        try:
            state = self.bot_engine.get_state()
            if state == "running":
                if self.bot_engine.pause():
                    self.pause_resume_btn.setText("Resume")
            elif state == "paused":
                if self.bot_engine.resume():
                    self.pause_resume_btn.setText("Pause")
        except Exception as e:
            QMessageBox.critical(self, "Bot Error", f"Pause/resume failed: {e}")
    
    def _validate_before_start(self) -> bool:
        """Validate settings before starting bot"""
        # Check if window is selected
        if not self.bot_engine.window_manager.target_window:
            QMessageBox.warning(
                self, "No Window Selected",
                "Please select a game window before starting the bot."
            )
            return False
        
        # Check if whitelist is configured
        whitelist_text = self.whitelist_edit.toPlainText().strip()
        if not whitelist_text:
            reply = QMessageBox.question(
                self, "Empty Whitelist",
                "No mobs are configured in the whitelist. The bot will attack any target. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return False
        
        return True
    
    def _apply_ui_settings(self):
        """Apply current UI settings to bot engine"""
        # Update configuration from UI
        config = self.bot_engine.config_manager
        
        # Options
        config.set_option('auto_pots', self.auto_pots_cb.isChecked())
        config.set_option('potion_threshold', self.potion_threshold_spin.value())
        
        # Whitelist
        whitelist_text = self.whitelist_edit.toPlainText()
        whitelist = [line.strip() for line in whitelist_text.splitlines() if line.strip()]
        config.set_whitelist(whitelist)
        
        # Update bot engine
        self.bot_engine.update_config()
    
    @pyqtSlot()
    def _select_window(self):
        """Open window selection dialog"""
        try:
            dialog = WindowSelectorDialog(self.bot_engine.window_manager, self)
            if dialog.exec_() == dialog.Accepted:
                window_info = self.bot_engine.window_manager.get_target_window_info()
                if window_info:
                    self.current_window_label.setText(f"Selected: {window_info['title']}")
                    self.status_bar.showMessage("Window selected successfully", 2000)
        except Exception as e:
            QMessageBox.critical(self, "Window Selection Error", f"Failed to select window: {e}")
    
    @pyqtSlot()
    def _configure_regions(self):
        """Open region configuration dialog"""
        try:
            dialog = RegionConfigDialog(self.bot_engine.pixel_analyzer, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Region Config Error", f"Failed to configure regions: {e}")
    
    @pyqtSlot()
    def _open_skill_config(self):
        """Open skill configuration dialog"""
        try:
            dialog = SkillConfigDialog(self.bot_engine.skill_manager, self)
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Skill Config Error", f"Failed to configure skills: {e}")

    def _show_pixel_test_results_optimized(self, vitals, debug_image, regions, window_rect):
        """Show optimized pixel test results"""
        try:
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Pixel Test Results (UI Only)")
            dialog.setFixedSize(600, 500)
            
            layout = QVBoxLayout(dialog)
            
            # Results text
            results_text = f"""
            <h3>Pixel Analysis Results</h3>
            <table border="1" cellpadding="5">
            <tr><td><b>HP:</b></td><td>{vitals['hp']}%</td></tr>
            <tr><td><b>MP:</b></td><td>{vitals['mp']}%</td></tr>
            <tr><td><b>Target Exists:</b></td><td>{'Yes' if vitals['target_exists'] else 'No'}</td></tr>
            <tr><td><b>Target Health:</b></td><td>{vitals['target_health']}%</td></tr>
            <tr><td><b>Target Name:</b></td><td>{vitals.get('target_name', 'None')}</td></tr>
            </table>
            
            <h4>Capture Info:</h4>
            <p><b>Window Rect:</b> {window_rect}</p>
            <p><b>UI Capture Area:</b> Top-left 200x100 pixels</p>
            
            <h4>Region Coordinates:</h4>
            <table border="1" cellpadding="5">
            <tr><th>Region</th><th>Coordinates (x1,y1,x2,y2)</th></tr>
            <tr><td>HP Bar</td><td>{regions['hp']}</td></tr>
            <tr><td>MP Bar</td><td>{regions['mp']}</td></tr>
            <tr><td>Target Health</td><td>{regions['target']}</td></tr>
            <tr><td>Target Name</td><td>{regions['target_name']}</td></tr>
            </table>
            """
            
            results_label = QLabel(results_text)
            results_label.setWordWrap(True)
            layout.addWidget(results_label)
            
            # Image display (only UI area - much smaller and clearer)
            if debug_image:
                image_label = QLabel("UI Region (200x100 pixels with regions marked):")
                layout.addWidget(image_label)
                
                # Convert PIL image to QPixmap
                if debug_image.mode != "RGB":
                    debug_image = debug_image.convert("RGB")
                
                # Scale up the small UI image for better visibility
                scale_factor = 2  # Make it 3x bigger for visibility
                new_size = (debug_image.width * scale_factor, debug_image.height * scale_factor)
                debug_image = debug_image.resize(new_size, Image.NEAREST)
                
                # Convert to QImage
                data = debug_image.tobytes("raw", "RGB")
                qimg = QImage(data, debug_image.width, debug_image.height, QImage.Format_RGB888)
                
                # Create pixmap and display
                pixmap = QPixmap.fromImage(qimg)
                img_display = QLabel()
                img_display.setPixmap(pixmap)
                img_display.setAlignment(Qt.AlignCenter)
                img_display.setStyleSheet("border: 1px solid #ccc; background-color: white;")
                
                layout.addWidget(img_display)
            
            # Tips
            tips_text = self._get_pixel_test_tips(vitals)
            tips_label = QLabel(tips_text)
            tips_label.setWordWrap(True)
            tips_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            layout.addWidget(tips_label)
            
            # Close button
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dialog.accept)
            layout.addWidget(btn_box)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Display Error", f"Failed to show test results: {e}")
        
    @pyqtSlot()
    def _test_pixels(self):
        """Test pixel accuracy with optimized UI-only capture"""
        try:
            # Check if window is selected
            if not self.bot_engine.window_manager.target_window:
                QMessageBox.warning(
                    self, "No Window Selected",
                    "Please select a game window first using 'Select Game Window'."
                )
                return
            
            # Update window rectangle
            self.bot_engine.window_manager.update_target_window_rect()
            
            # Get window rectangle
            window_rect = self.bot_engine.window_manager.target_window.rect
            
            # Set UI capture region (only top-left corner where UI is)
            self.bot_engine.pixel_analyzer.set_ui_capture_region(window_rect)
            
            # Get current regions
            regions = self.bot_engine.config_manager.get_regions()
            
            # Analyze vitals using optimized capture
            vitals = self.bot_engine.pixel_analyzer.analyze_vitals(regions)
            
            # Create debug image with only UI area
            debug_image = self.bot_engine.pixel_analyzer.create_debug_image_ui(regions)
            
            # Show results
            self._show_pixel_test_results_optimized(vitals, debug_image, regions, window_rect)
            
        except Exception as e:
            error_msg = f"Pixel test failed: {str(e)}\n\nFull error:\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Test Error", error_msg)


    def _get_pixel_test_tips(self, vitals):
        """Get tips and interpretation for pixel test results"""
        tips = ["<b>Pixel Test Interpretation:</b>"]
        
        # HP/MP analysis
        if vitals['hp'] == 0 and vitals['mp'] == 0:
            tips.append("⚠️ <b>No HP/MP detected:</b> Check if game window is selected and visible. Make sure HP/MP bars are on screen.")
        elif vitals['hp'] < 10 or vitals['mp'] < 10:
            tips.append("⚠️ <b>Very low readings:</b> Region coordinates might be incorrect or bars are nearly empty.")
        elif vitals['hp'] > 95 and vitals['mp'] > 95:
            tips.append("✅ <b>Good readings:</b> HP/MP detection appears to be working correctly.")
        
        # Target analysis
        if not vitals['target_exists']:
            tips.append("ℹ️ <b>No target detected:</b> This is normal if no target is selected in game.")
        elif vitals['target_health'] > 0:
            tips.append(f"✅ <b>Target detected:</b> {vitals['target_health']}% health remaining.")
        
        # Target name analysis
        if vitals.get('target_name'):
            tips.append(f"✅ <b>OCR working:</b> Detected target name '{vitals['target_name']}'")
        else:
            tips.append("⚠️ <b>No target name:</b> OCR might need adjustment or no target selected.")
        
        # General tips
        tips.extend([
            "",
            "<b>Troubleshooting Tips:</b>",
            "• Make sure your game window is visible and not minimized",
            "• Check that HP/MP bars are not empty when testing",
            "• If readings are wrong, use 'Configure Regions' to adjust coordinates",
            "• Target a mob in-game before testing target detection"
        ])
        
        return "<br>".join(tips)

    def _get_ocr_test_tips(self, ocr_result):
        """Get tips and interpretation for OCR test results"""
        tips = ["<b>OCR Test Interpretation:</b>"]
        
        extracted_name = ocr_result.get('extracted_name', '')
        success = ocr_result.get('success', False)
        
        if not extracted_name:
            tips.extend([
                "⚠️ <b>No text detected:</b>",
                "• Make sure you have a target selected in game",
                "• Check that target name region coordinates are correct",
                "• Verify Tesseract OCR is properly installed"
            ])
        elif len(extracted_name) < 3:
            tips.extend([
                "⚠️ <b>Very short text detected:</b>",
                "• Text might be partially cut off",
                "• Try adjusting the target name region size",
                "• Check if target name is fully visible"
            ])
        elif success:
            tips.extend([
                f"✅ <b>Text successfully detected:</b> '{extracted_name}'",
                "• OCR appears to be working correctly",
                "• You can add this name to your mob whitelist"
            ])
        else:
            tips.extend([
                f"⚠️ <b>Text detected but may need verification:</b> '{extracted_name}'",
                "• Check if the detected text matches what you see in game",
                "• Consider adjusting OCR settings if consistently wrong"
            ])
        
        # General OCR tips
        tips.extend([
            "",
            "<b>OCR Troubleshooting:</b>",
            "• Target a mob with a clear, visible name",
            "• Make sure game text is not too small or blurry",
            "• Check that target name region doesn't include health bar",
            "• If OCR is consistently wrong, try different region coordinates"
        ])
        
        return "<br>".join(tips)

    def _convert_pil_to_qlabel(self, pil_image, max_size=(300, 100)):
        """Convert PIL image to QLabel for display"""
        try:
            # Convert to RGB if needed
            if pil_image.mode != "RGB":
                pil_image = pil_image.convert("RGB")
            
            # Scale image if too large
            if pil_image.width > max_size[0] or pil_image.height > max_size[1]:
                pil_image.thumbnail(max_size, Image.LANCZOS)
            
            # Scale up small images for better visibility
            if pil_image.width < 100:
                scale_factor = 100 / pil_image.width
                new_size = (int(pil_image.width * scale_factor), int(pil_image.height * scale_factor))
                pil_image = pil_image.resize(new_size, Image.NEAREST)
            
            # Convert to QImage
            data = pil_image.tobytes("raw", "RGB")
            qimg = QImage(data, pil_image.width, pil_image.height, QImage.Format_RGB888)
            
            # Create QLabel with pixmap
            pixmap = QPixmap.fromImage(qimg)
            label = QLabel()
            label.setPixmap(pixmap)
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("border: 1px solid #ccc; background-color: white;")
            
            return label
            
        except Exception as e:
            error_label = QLabel(f"Error displaying image: {e}")
            error_label.setStyleSheet("color: red; border: 1px solid red; padding: 5px;")
            return error_label


    def _show_ocr_test_results(self, ocr_result, region_coords):
        """Show OCR test results in a dialog"""
        try:
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("OCR Test Results")
            dialog.setFixedSize(700, 600)
            
            layout = QVBoxLayout(dialog)
            
            # Results text
            results_text = f"""
            <h3>OCR Test Results</h3>
            <table border="1" cellpadding="5">
            <tr><td><b>Extracted Text:</b></td><td>"{ocr_result.get('extracted_name', 'None')}"</td></tr>
            <tr><td><b>Region Coordinates:</b></td><td>{region_coords}</td></tr>
            <tr><td><b>Test Success:</b></td><td>{'Yes' if ocr_result.get('success', False) else 'No'}</td></tr>
            </table>
            """
            
            results_label = QLabel(results_text)
            results_label.setWordWrap(True)
            layout.addWidget(results_label)
            
            # Original image
            if 'original_image' in ocr_result:
                layout.addWidget(QLabel("<b>Original Image:</b>"))
                orig_img = self._convert_pil_to_qlabel(ocr_result['original_image'])
                if orig_img:
                    layout.addWidget(orig_img)
            
            # Processed image
            if 'processed_image' in ocr_result:
                layout.addWidget(QLabel("<b>Processed Image:</b>"))
                proc_img = self._convert_pil_to_qlabel(ocr_result['processed_image'])
                if proc_img:
                    layout.addWidget(proc_img)
            
            # OCR tips
            tips_text = self._get_ocr_test_tips(ocr_result)
            tips_label = QLabel(tips_text)
            tips_label.setWordWrap(True)
            tips_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            layout.addWidget(tips_label)
            
            # Close button
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dialog.accept)
            layout.addWidget(btn_box)
            
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Display Error", f"Failed to show OCR results: {e}")


    
    @pyqtSlot()
    def _test_ocr(self):
        """Test OCR accuracy with visual feedback"""
        try:
            # Check if window is selected
            if not self.bot_engine.window_manager.target_window:
                QMessageBox.warning(
                    self, "No Window Selected",
                    "Please select a game window first using 'Select Game Window'."
                )
                return
            
            # Update window rectangle
            self.bot_engine.window_manager.update_target_window_rect()
            
            # Set monitor rect for pixel analyzer
            if self.bot_engine.window_manager.target_window:
                self.bot_engine.pixel_analyzer.set_monitor_rect(
                    self.bot_engine.window_manager.target_window.rect
                )
            
            # Get target name region
            regions = self.bot_engine.config_manager.get_regions()
            target_name_region = regions['target_name']
            
            # Test OCR accuracy
            ocr_result = self.bot_engine.pixel_analyzer.test_ocr_accuracy(target_name_region)
            
            # Show OCR test results
            self._show_ocr_test_results(ocr_result, target_name_region)
            
        except Exception as e:
            error_msg = f"OCR test failed: {str(e)}\n\nFull error:\n{traceback.format_exc()}"
            QMessageBox.critical(self, "Test Error", error_msg)

    def _show_pixel_test_results(self, vitals, debug_image, regions):
        """Show pixel test results in a dialog"""
        try:
            # Create dialog
            dialog = QDialog(self)
            dialog.setWindowTitle("Pixel Test Results")
            dialog.setFixedSize(800, 700)
            
            layout = QVBoxLayout(dialog)
            
            # Results text
            results_text = f"""
            <h3>Pixel Analysis Results</h3>
            <table border="1" cellpadding="5">
            <tr><td><b>HP:</b></td><td>{vitals['hp']}%</td></tr>
            <tr><td><b>MP:</b></td><td>{vitals['mp']}%</td></tr>
            <tr><td><b>Target Exists:</b></td><td>{'Yes' if vitals['target_exists'] else 'No'}</td></tr>
            <tr><td><b>Target Health:</b></td><td>{vitals['target_health']}%</td></tr>
            <tr><td><b>Target Name:</b></td><td>{vitals.get('target_name', 'None')}</td></tr>
            </table>
            
            <h4>Region Coordinates:</h4>
            <table border="1" cellpadding="5">
            <tr><th>Region</th><th>Coordinates (x1,y1,x2,y2)</th></tr>
            <tr><td>HP Bar</td><td>{regions['hp']}</td></tr>
            <tr><td>MP Bar</td><td>{regions['mp']}</td></tr>
            <tr><td>Target Health</td><td>{regions['target']}</td></tr>
            <tr><td>Target Name</td><td>{regions['target_name']}</td></tr>
            </table>
            """
            
            results_label = QLabel(results_text)
            results_label.setWordWrap(True)
            layout.addWidget(results_label)
            
            # Image display
            if debug_image:
                image_label = QLabel("Debug Image (Regions Highlighted):")
                layout.addWidget(image_label)
                
                # Convert PIL image to QPixmap
                if debug_image.mode != "RGB":
                    debug_image = debug_image.convert("RGB")
                
                # Scale image if too large
                max_width, max_height = 750, 400
                if debug_image.width > max_width or debug_image.height > max_height:
                    debug_image.thumbnail((max_width, max_height), Image.LANCZOS)
                
                # Convert to QImage
                data = debug_image.tobytes("raw", "RGB")
                qimg = QImage(data, debug_image.width, debug_image.height, QImage.Format_RGB888)
                
                # Create pixmap and display
                pixmap = QPixmap.fromImage(qimg)
                img_display = QLabel()
                img_display.setPixmap(pixmap)
                img_display.setAlignment(Qt.AlignCenter)
                
                # Add scroll area for large images
                scroll_area = QScrollArea()
                scroll_area.setWidget(img_display)
                scroll_area.setFixedHeight(300)
                layout.addWidget(scroll_area)
            
            # Interpretation and tips
            tips_text = self._get_pixel_test_tips(vitals)
            tips_label = QLabel(tips_text)
            tips_label.setWordWrap(True)
            tips_label.setStyleSheet("background-color: #f0f0f0; padding: 10px; border: 1px solid #ccc;")
            layout.addWidget(tips_label)
            
            # Close button
            btn_box = QDialogButtonBox(QDialogButtonBox.Ok)
            btn_box.accepted.connect(dialog.accept)
            layout.addWidget(btn_box)
            
            dialog.exec_()
        
        except Exception as e:
            QMessageBox.critical(self, "Display Error", f"Failed to show test results: {e}")
    
    @pyqtSlot()
    def _reset_stats(self):
        """Reset bot statistics"""
        # Reset would be implemented
        QMessageBox.information(self, "Reset Stats", "Statistics reset (to be implemented)")
    
    @pyqtSlot()
    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self, "About Tantra Bot",
            """
            <h3>Tantra Bot v2.0.0</h3>
            <p>Advanced automation bot for Tantra Online</p>
            <p><b>Features:</b></p>
            <ul>
            <li>Intelligent combat automation</li>
            <li>Advanced skill management</li>
            <li>OCR-based target recognition</li>
            <li>Configurable mob whitelist</li>
            <li>Auto-potion system</li>
            </ul>
            <p><b>Created by:</b> cursebox</p>
            <p><b>Built with:</b> Python, PyQt5, OpenCV, Tesseract</p>
            """
        )
    
    def _update_ui(self):
        """Update UI with current bot status and stats"""
        try:
            # Update bot state
            state = self.bot_engine.get_state()
            self.bot_status_label.setText(f"Status: {state.title()}")
            self.bot_state_label.setText(state.title())
            
            # Update vitals in status widget
            vitals = self.bot_engine.get_vitals()
            if vitals:
                self.status_widget.update_vitals(vitals)
            
            # Update statistics
            stats = self.bot_engine.get_stats()
            
            # Format runtime
            if stats.get('current_runtime', 0) > 0:
                runtime = int(stats['current_runtime'])
                hours = runtime // 3600
                minutes = (runtime % 3600) // 60
                seconds = runtime % 60
                self.runtime_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            self.targets_label.setText(str(stats.get('targets_killed', 0)))
            self.potions_label.setText(str(stats.get('potions_used', 0)))
            self.skills_label.setText(str(stats.get('skills_used', 0)))
            self.total_inputs_label.setText(str(stats.get('total_inputs', 0)))
            self.success_rate_label.setText(f"{stats.get('success_rate', 0):.1f}%")
            self.errors_label.setText(str(stats.get('errors_occurred', 0)))
            
        except Exception as e:
            print(f"Error updating UI: {e}")
    
    @pyqtSlot(str)
    def _on_bot_state_changed(self, state: str):
        """Handle bot state changes"""
        # UI updates are handled in _update_ui
        pass
    
    @pyqtSlot(dict)
    def _on_vitals_updated(self, vitals: Dict[str, Any]):
        """Handle vitals updates"""
        # UI updates are handled in _update_ui
        pass
    
    @pyqtSlot(str)
    def _on_target_changed(self, target: str):
        """Handle target changes"""
        self.status_widget.update_target(target)
    
    @pyqtSlot(str)
    def _on_error_occurred(self, error: str):
        """Handle bot errors"""
        QMessageBox.critical(self, "Bot Error", f"An error occurred: {error}")
    
    @pyqtSlot()
    def _on_config_changed(self):
        """Handle configuration changes"""
        # Auto-save could be implemented here
        pass
    
    def closeEvent(self, event):
        """Handle application close"""
        if self.bot_engine.get_state() != "stopped":
            reply = QMessageBox.question(
                self, "Bot Running",
                "The bot is still running. Stop it before closing?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.bot_engine.stop()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()