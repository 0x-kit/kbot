# ui/dialogs/simple_visual_config.py
"""
Simplified Visual Skill Configuration Dialog

A much simpler and more intuitive interface for configuring the visual skill system.
Focuses on the essential functionality with better UX.
"""

import os
import time
from typing import Dict, List, Optional, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QPushButton,
    QComboBox, QListWidget, QListWidgetItem, QTextEdit, QCheckBox,
    QProgressBar, QMessageBox, QSplitter, QFrame, QGridLayout,
    QSpinBox, QSlider, QTabWidget, QWidget, QScrollArea
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap, QIcon

from skill_system.visual_system import VisualSkillSystem
from skill_system.config import VisualSkillConfig
from skill_system.skill_types import SkillState
from .visual_region_selector import VisualRegionSelector


class SimpleVisualConfigDialog(QDialog):
    """Simplified visual skill configuration dialog with better UX"""
    
    def __init__(self, bot_engine=None, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        
        self.setWindowTitle("Visual Skill System - Easy Setup")
        self.setMinimumSize(800, 600)
        
        # Core components
        self.config = VisualSkillConfig()
        self.visual_system = VisualSkillSystem()
        self.region_selector = None
        
        # State
        self.current_class = self.config.get_current_class()
        self.skill_bar_configured = False
        
        self.setup_ui()
        self.load_initial_data()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.update_status)
        self.status_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        """Setup the simplified user interface"""
        layout = QVBoxLayout(self)
        
        # Header
        self.setup_header(layout)
        
        # Main content
        self.setup_main_content(layout)
        
        # Footer
        self.setup_footer(layout)
    
    def setup_header(self, layout):
        """Setup header with title and quick status"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 5px; padding: 10px;")
        header_layout = QVBoxLayout(header_frame)
        
        # Title
        title_label = QLabel("🎮 Visual Skill System - Easy Setup")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #2c3e50;")
        header_layout.addWidget(title_label)
        
        # Quick status
        status_layout = QHBoxLayout()
        
        # Class status
        self.class_status_label = QLabel("❓ Class: Not selected")
        status_layout.addWidget(self.class_status_label)
        
        # Region status  
        self.region_status_label = QLabel("❓ Skill Bar: Not configured")
        status_layout.addWidget(self.region_status_label)
        
        # Detection status
        self.detection_status_label = QLabel("❓ Detection: Not ready")
        status_layout.addWidget(self.detection_status_label)
        
        status_layout.addStretch()
        header_layout.addLayout(status_layout)
        
        layout.addWidget(header_frame)
    
    def setup_main_content(self, layout):
        """Setup main content area with steps"""
        # Create step-by-step interface
        steps_group = QGroupBox("Setup Steps")
        steps_layout = QVBoxLayout(steps_group)
        
        # Step 1: Class Selection
        self.setup_step1(steps_layout)
        
        # Step 2: Skill Bar Configuration
        self.setup_step2(steps_layout)
        
        # Step 3: Quick Test
        self.setup_step3(steps_layout)
        
        # Step 4: Monitor (real-time view)
        self.setup_step4(steps_layout)
        
        layout.addWidget(steps_group)
    
    def setup_step1(self, layout):
        """Step 1: Character Class Selection"""
        step1_frame = QFrame()
        step1_frame.setFrameStyle(QFrame.StyledPanel)
        step1_frame.setStyleSheet("border: 2px solid #007bff; border-radius: 5px; padding: 10px;")
        step1_layout = QVBoxLayout(step1_frame)
        
        # Header
        step1_header = QLabel("📋 Step 1: Select Your Character Class")
        step1_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #007bff;")
        step1_layout.addWidget(step1_header)
        
        # Class selection
        class_layout = QHBoxLayout()
        class_layout.addWidget(QLabel("Character Class:"))
        
        self.class_combo = QComboBox()
        self.class_combo.setMinimumWidth(200)
        self.class_combo.currentTextChanged.connect(self.on_class_changed)
        class_layout.addWidget(self.class_combo)
        
        # Class info
        self.class_info_label = QLabel("Select a class to see available skills")
        self.class_info_label.setStyleSheet("color: #6c757d; font-style: italic;")
        class_layout.addWidget(self.class_info_label)
        
        class_layout.addStretch()
        step1_layout.addLayout(class_layout)
        
        layout.addWidget(step1_frame)
    
    def setup_step2(self, layout):
        """Step 2: Skill Bar Configuration"""
        step2_frame = QFrame()
        step2_frame.setFrameStyle(QFrame.StyledPanel)
        step2_frame.setStyleSheet("border: 2px solid #28a745; border-radius: 5px; padding: 10px;")
        step2_layout = QVBoxLayout(step2_frame)
        
        # Header
        step2_header = QLabel("🎯 Step 2: Configure Skill Bar Region")
        step2_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #28a745;")
        step2_layout.addWidget(step2_header)
        
        # Description
        description = QLabel(
            "Click 'Configure Skill Bar' to visually select where your skill bar is located on screen. "
            "This uses the same visual selection system as the pixel test."
        )
        description.setWordWrap(True)
        description.setStyleSheet("color: #495057; margin-bottom: 10px;")
        step2_layout.addWidget(description)
        
        # Configuration controls
        config_layout = QHBoxLayout()
        
        self.configure_region_btn = QPushButton("🎯 Configure Skill Bar")
        self.configure_region_btn.clicked.connect(self.open_region_selector)
        self.configure_region_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        config_layout.addWidget(self.configure_region_btn)
        
        # Quick presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Quick presets:"))
        
        preset_1080p = QPushButton("1080p")
        preset_1080p.clicked.connect(lambda: self.apply_quick_preset(1080))
        preset_layout.addWidget(preset_1080p)
        
        preset_1440p = QPushButton("1440p")
        preset_1440p.clicked.connect(lambda: self.apply_quick_preset(1440))
        preset_layout.addWidget(preset_1440p)
        
        config_layout.addLayout(preset_layout)
        config_layout.addStretch()
        
        # Region status
        self.region_details_label = QLabel("No region configured")
        self.region_details_label.setStyleSheet("color: #6c757d; font-style: italic;")
        config_layout.addWidget(self.region_details_label)
        
        step2_layout.addLayout(config_layout)
        layout.addWidget(step2_frame)
    
    def setup_step3(self, layout):
        """Step 3: Quick Test"""
        step3_frame = QFrame()
        step3_frame.setFrameStyle(QFrame.StyledPanel)
        step3_frame.setStyleSheet("border: 2px solid #ffc107; border-radius: 5px; padding: 10px;")
        step3_layout = QVBoxLayout(step3_frame)
        
        # Header
        step3_header = QLabel("🧪 Step 3: Test Detection")
        step3_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #856404;")
        step3_layout.addWidget(step3_header)
        
        # Test controls
        test_layout = QHBoxLayout()
        
        self.auto_detect_btn = QPushButton("🔍 Auto-Detect Skills")
        self.auto_detect_btn.clicked.connect(self.auto_detect_skills)
        self.auto_detect_btn.setEnabled(False)
        self.auto_detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #e0a800; }
            QPushButton:disabled { background-color: #cccccc; color: #666666; }
        """)
        test_layout.addWidget(self.auto_detect_btn)
        
        # Test results
        self.test_results_label = QLabel("Configure class and skill bar first")
        self.test_results_label.setStyleSheet("color: #6c757d; font-style: italic;")
        test_layout.addWidget(self.test_results_label)
        
        test_layout.addStretch()
        step3_layout.addLayout(test_layout)
        
        layout.addWidget(step3_frame)
    
    def setup_step4(self, layout):
        """Step 4: Real-time Monitor"""
        step4_frame = QFrame()
        step4_frame.setFrameStyle(QFrame.StyledPanel)
        step4_frame.setStyleSheet("border: 2px solid #17a2b8; border-radius: 5px; padding: 10px;")
        step4_layout = QVBoxLayout(step4_frame)
        
        # Header
        step4_header = QLabel("📊 Step 4: Real-time Monitor")
        step4_header.setStyleSheet("font-weight: bold; font-size: 14px; color: #17a2b8;")
        step4_layout.addWidget(step4_header)
        
        # Monitor controls
        monitor_controls = QHBoxLayout()
        
        self.start_monitor_btn = QPushButton("▶️ Start Monitoring")
        self.start_monitor_btn.clicked.connect(self.toggle_monitoring)
        self.start_monitor_btn.setEnabled(False)
        monitor_controls.addWidget(self.start_monitor_btn)
        
        # Monitor status
        self.monitor_status_label = QLabel("Ready to monitor")
        self.monitor_status_label.setStyleSheet("color: #6c757d;")
        monitor_controls.addWidget(self.monitor_status_label)
        
        monitor_controls.addStretch()
        step4_layout.addLayout(monitor_controls)
        
        # Skills list (simplified)
        self.skills_list = QListWidget()
        self.skills_list.setMaximumHeight(150)
        step4_layout.addWidget(self.skills_list)
        
        layout.addWidget(step4_frame)
    
    def setup_footer(self, layout):
        """Setup footer with action buttons"""
        footer_layout = QHBoxLayout()
        
        # Status
        self.overall_status_label = QLabel("🔴 Not ready - complete setup steps")
        self.overall_status_label.setStyleSheet("font-weight: bold;")
        footer_layout.addWidget(self.overall_status_label)
        
        footer_layout.addStretch()
        
        # Advanced settings
        self.advanced_btn = QPushButton("⚙️ Advanced Settings")
        self.advanced_btn.clicked.connect(self.open_advanced_settings)
        footer_layout.addWidget(self.advanced_btn)
        
        # Help button
        self.help_btn = QPushButton("❓ Help")
        self.help_btn.clicked.connect(self.show_help)
        footer_layout.addWidget(self.help_btn)
        
        # Close button
        self.close_btn = QPushButton("✅ Done")
        self.close_btn.clicked.connect(self.accept)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 20px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        footer_layout.addWidget(self.close_btn)
        
        layout.addLayout(footer_layout)
    
    def load_initial_data(self):
        """Load initial data and populate UI"""
        try:
            # Load available classes
            self.class_combo.clear()
            self.class_combo.addItem("Select a class...", None)
            
            classes = self.visual_system.class_manager.get_available_classes()
            for class_name, display_name in classes:
                self.class_combo.addItem(f"{display_name} ({class_name})", class_name)
            
            # Set current class if any
            if self.current_class:
                for i in range(self.class_combo.count()):
                    if self.class_combo.itemData(i) == self.current_class:
                        self.class_combo.setCurrentIndex(i)
                        break
            
            self.update_status()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load initial data: {e}")
    
    def on_class_changed(self):
        """Handle class selection change"""
        class_name = self.class_combo.currentData()
        
        if class_name:
            try:
                # Update current class
                self.current_class = class_name
                self.config.set_current_class(class_name)
                
                # Initialize visual system
                self.visual_system.class_manager.set_current_class(class_name)
                
                # Update class info
                profile = self.visual_system.class_manager.get_current_profile()
                if profile:
                    skill_count = len(profile.skills)
                    rotation_count = len(profile.rotations)
                    self.class_info_label.setText(
                        f"{skill_count} skills, {rotation_count} rotations available"
                    )
                
                self.update_status()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to change class: {e}")
        else:
            self.class_info_label.setText("Select a class to see available skills")
    
    def open_region_selector(self):
        """Open the visual region selector"""
        if not self.bot_engine:
            QMessageBox.warning(
                self, "Warning", 
                "Bot engine not available. Cannot configure regions visually."
            )
            return
        
        if not self.bot_engine.window_manager.target_window:
            QMessageBox.warning(
                self, "Warning",
                "Please select a game window first in the main interface."
            )
            return
        
        try:
            self.region_selector = VisualRegionSelector(
                self.bot_engine, self.visual_system, self
            )
            self.region_selector.region_selected.connect(self.on_region_selected)
            self.region_selector.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open region selector: {e}")
    
    @pyqtSlot(tuple)
    def on_region_selected(self, region):
        """Handle region selection from visual selector"""
        try:
            x, y, w, h = region
            
            # Save region to config
            regions = self.config.get_skill_bar_regions()
            regions['main_bar'] = [x, y, w, h]
            self.config.set_skill_bar_regions(regions)
            self.config.save_config()
            
            # Update status
            self.skill_bar_configured = True
            self.region_details_label.setText(f"Region: ({x}, {y}, {w}×{h})")
            
            # Enable next steps
            self.auto_detect_btn.setEnabled(True)
            
            self.update_status()
            
            QMessageBox.information(
                self, "Success",
                f"Skill bar region configured successfully!\n"
                f"Region: ({x}, {y}, {w}×{h})"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save region: {e}")
    
    def apply_quick_preset(self, resolution):
        """Apply quick preset for common resolutions"""
        try:
            if resolution == 1080:
                region = (300, 1020, 720, 60)
                preset_name = "1080p"
            elif resolution == 1440:
                region = (400, 1360, 960, 80)
                preset_name = "1440p"
            else:
                return
            
            # Save region
            regions = self.config.get_skill_bar_regions()
            regions['main_bar'] = list(region)
            self.config.set_skill_bar_regions(regions)
            self.config.save_config()
            
            # Update status
            self.skill_bar_configured = True
            x, y, w, h = region
            self.region_details_label.setText(f"Preset {preset_name}: ({x}, {y}, {w}×{h})")
            
            # Enable next steps
            self.auto_detect_btn.setEnabled(True)
            
            self.update_status()
            
            QMessageBox.information(
                self, "Preset Applied",
                f"{preset_name} preset applied successfully!\n"
                f"Region: ({x}, {y}, {w}×{h})\n\n"
                f"You can test this or use the visual selector to fine-tune."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply preset: {e}")
    
    def auto_detect_skills(self):
        """Perform automatic skill detection"""
        if not self.current_class:
            QMessageBox.warning(self, "Warning", "Please select a character class first")
            return
        
        if not self.skill_bar_configured:
            QMessageBox.warning(self, "Warning", "Please configure skill bar region first")
            return
        
        try:
            # Get skill bar region
            regions = self.config.get_skill_bar_regions()
            main_bar = regions.get('main_bar')
            if not main_bar:
                QMessageBox.warning(self, "Warning", "No skill bar region configured")
                return
            
            # Initialize visual system
            skill_bar_regions = [tuple(main_bar)]
            success = self.visual_system.initialize_class(self.current_class, skill_bar_regions)
            
            if not success:
                QMessageBox.critical(self, "Error", "Failed to initialize visual system")
                return
            
            # Perform detection
            self.auto_detect_btn.setEnabled(False)
            self.auto_detect_btn.setText("🔍 Detecting...")
            
            results = self.visual_system.auto_detect_skills()
            
            # Update UI
            self.auto_detect_btn.setEnabled(True)
            self.auto_detect_btn.setText("🔍 Auto-Detect Skills")
            
            # Show results
            skills_found = len(results)
            if skills_found > 0:
                self.test_results_label.setText(f"✅ Found {skills_found} skills!")
                self.start_monitor_btn.setEnabled(True)
                
                # Update skills list
                self.update_skills_list()
                
                QMessageBox.information(
                    self, "Detection Complete",
                    f"Successfully detected {skills_found} skills!\n\n"
                    f"You can now start monitoring to see real-time skill states."
                )
            else:
                self.test_results_label.setText("❌ No skills detected")
                QMessageBox.warning(
                    self, "No Skills Found",
                    "No skills were detected in the configured region.\n\n"
                    "Try:\n"
                    "• Adjusting the skill bar region\n"
                    "• Making sure the game is visible\n"
                    "• Checking that skills are visible in the skill bar"
                )
            
            self.update_status()
            
        except Exception as e:
            self.auto_detect_btn.setEnabled(True)
            self.auto_detect_btn.setText("🔍 Auto-Detect Skills")
            QMessageBox.critical(self, "Error", f"Auto-detection failed: {e}")
    
    def toggle_monitoring(self):
        """Toggle real-time monitoring"""
        try:
            if self.visual_system.state.value == "running":
                # Stop monitoring
                self.visual_system.stop_monitoring()
                self.start_monitor_btn.setText("▶️ Start Monitoring")
                self.monitor_status_label.setText("Monitoring stopped")
            else:
                # Start monitoring
                if self.visual_system.start_monitoring():
                    self.start_monitor_btn.setText("⏹️ Stop Monitoring")
                    self.monitor_status_label.setText("Monitoring active...")
                    
                    # Start update timer for skills list
                    if not hasattr(self, 'monitor_timer'):
                        self.monitor_timer = QTimer()
                        self.monitor_timer.timeout.connect(self.update_skills_list)
                    self.monitor_timer.start(1000)  # Update every second
                else:
                    QMessageBox.critical(self, "Error", "Failed to start monitoring")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Monitoring toggle failed: {e}")
    
    def update_skills_list(self):
        """Update the skills list with current states"""
        try:
            profile = self.visual_system.class_manager.get_current_profile()
            if not profile:
                return
            
            self.skills_list.clear()
            
            for skill_name, skill in profile.skills.items():
                if skill.position:  # Only show positioned skills
                    state_icon = {
                        SkillState.READY: "🟢",
                        SkillState.COOLDOWN: "🟡", 
                        SkillState.UNAVAILABLE: "🔴",
                        SkillState.UNKNOWN: "⚪"
                    }.get(skill.current_state, "❓")
                    
                    cooldown_remaining = skill.get_cooldown_remaining()
                    cooldown_text = f" ({cooldown_remaining:.1f}s)" if cooldown_remaining > 0 else ""
                    
                    item_text = f"{state_icon} {skill_name} [{skill.key}]{cooldown_text}"
                    item = QListWidgetItem(item_text)
                    self.skills_list.addItem(item)
            
        except Exception as e:
            print(f"Error updating skills list: {e}")
    
    def update_status(self):
        """Update status indicators"""
        try:
            # Class status
            if self.current_class:
                profile = self.visual_system.class_manager.get_current_profile()
                if profile:
                    self.class_status_label.setText(f"✅ Class: {profile.display_name}")
                else:
                    self.class_status_label.setText(f"⚠️ Class: {self.current_class} (no profile)")
            else:
                self.class_status_label.setText("❓ Class: Not selected")
            
            # Region status
            if self.skill_bar_configured:
                self.region_status_label.setText("✅ Skill Bar: Configured")
            else:
                self.region_status_label.setText("❓ Skill Bar: Not configured")
            
            # Detection status
            profile = self.visual_system.class_manager.get_current_profile()
            if profile and self.skill_bar_configured:
                detected_skills = sum(1 for skill in profile.skills.values() if skill.position)
                if detected_skills > 0:
                    self.detection_status_label.setText(f"✅ Detection: {detected_skills} skills found")
                else:
                    self.detection_status_label.setText("⚠️ Detection: Ready to scan")
            else:
                self.detection_status_label.setText("❓ Detection: Not ready")
            
            # Overall status
            if self.current_class and self.skill_bar_configured:
                if profile and any(skill.position for skill in profile.skills.values()):
                    self.overall_status_label.setText("🟢 Ready - system configured and working!")
                else:
                    self.overall_status_label.setText("🟡 Almost ready - run detection test")
            else:
                steps_needed = []
                if not self.current_class:
                    steps_needed.append("select class")
                if not self.skill_bar_configured:
                    steps_needed.append("configure skill bar")
                
                self.overall_status_label.setText(f"🔴 Not ready - {', '.join(steps_needed)}")
            
        except Exception as e:
            print(f"Error updating status: {e}")
    
    def open_advanced_settings(self):
        """Open advanced settings dialog"""
        try:
            from .visual_skill_config import VisualSkillConfigDialog
            advanced_dialog = VisualSkillConfigDialog(self)
            advanced_dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open advanced settings: {e}")
    
    def show_help(self):
        """Show help dialog"""
        help_text = """
        <h3>Visual Skill System Help</h3>
        
        <h4>Getting Started:</h4>
        <ol>
        <li><b>Select Class:</b> Choose your character class from the dropdown</li>
        <li><b>Configure Skill Bar:</b> Use the visual selector to mark where your skill bar is</li>
        <li><b>Test Detection:</b> Run auto-detection to find your skills</li>
        <li><b>Monitor:</b> Start real-time monitoring to see skill states</li>
        </ol>
        
        <h4>Tips:</h4>
        <ul>
        <li>Make sure your game window is visible when configuring</li>
        <li>Use presets for common resolutions (1080p, 1440p)</li>
        <li>The visual selector shows a live preview of your selection</li>
        <li>Green circles = skills ready, yellow = on cooldown, red = unavailable</li>
        </ul>
        
        <h4>Troubleshooting:</h4>
        <ul>
        <li>If no skills are detected, try adjusting the skill bar region</li>
        <li>Make sure your skill bar is visible and not obscured</li>
        <li>Different resolutions may need different regions</li>
        <li>Use Advanced Settings for fine-tuning detection parameters</li>
        </ul>
        """
        
        QMessageBox.information(self, "Help", help_text)
    
    def closeEvent(self, event):
        """Handle close event"""
        try:
            # Stop monitoring if active
            if hasattr(self, 'monitor_timer'):
                self.monitor_timer.stop()
            
            if self.visual_system.state.value == "running":
                self.visual_system.stop_monitoring()
            
            # Save current configuration
            self.config.save_config()
            
        except Exception as e:
            print(f"Error during close: {e}")
        
        event.accept()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = SimpleVisualConfigDialog()
    dialog.show()
    sys.exit(app.exec_())