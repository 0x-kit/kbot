# ui/dialogs/visual_skill_config.py
"""
Visual Skill Configuration Dialog

Complete UI for configuring the visual skill detection system.
Features class selection, skill management, rotation editing, and real-time monitoring.
"""

import os
import time
import json
from typing import Dict, List, Optional, Any
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QComboBox, QTreeWidget, QTreeWidgetItem, QPushButton, QGroupBox,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QTextEdit, QLabel,
    QListWidget, QListWidgetItem, QFormLayout, QGridLayout,
    QProgressBar, QSlider, QFrame, QSplitter, QMessageBox,
    QFileDialog, QDialogButtonBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QToolButton
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QIcon, QPainter, QFont

from skill_system.visual_system import VisualSkillSystem
from skill_system.class_manager import ClassManager
from skill_system.config import VisualSkillConfig
from skill_system.skill_types import SkillType, SkillState


class SkillMonitorWidget(QWidget):
    """Widget for real-time skill monitoring"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.visual_system: Optional[VisualSkillSystem] = None
        self.monitoring_enabled = False
        
        self.setup_ui()
        
        # Update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_display)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.clicked.connect(self.toggle_monitoring)
        controls_layout.addWidget(self.start_btn)
        
        self.auto_detect_btn = QPushButton("Auto-Detect Skills")
        self.auto_detect_btn.clicked.connect(self.auto_detect_skills)
        controls_layout.addWidget(self.auto_detect_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # Skill display
        self.skill_tree = QTreeWidget()
        self.skill_tree.setHeaderLabels(["Skill", "State", "Cooldown", "Position", "Confidence"])
        self.skill_tree.setColumnWidth(0, 150)
        self.skill_tree.setColumnWidth(1, 100)
        self.skill_tree.setColumnWidth(2, 80)
        self.skill_tree.setColumnWidth(3, 120)
        layout.addWidget(self.skill_tree)
        
        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.detection_rate_label = QLabel("Detection Rate: 0.0 Hz")
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.detection_rate_label)
        layout.addLayout(status_layout)
    
    def set_visual_system(self, visual_system: VisualSkillSystem):
        """Set the visual system to monitor"""
        self.visual_system = visual_system
        if visual_system:
            # Add callbacks
            visual_system.add_callback('skill_state_changed', self.on_skill_state_changed)
            visual_system.add_callback('skill_detected', self.on_skill_detected)
    
    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        if not self.visual_system:
            QMessageBox.warning(self, "Warning", "No visual system available")
            return
        
        if self.monitoring_enabled:
            self.stop_monitoring()
        else:
            self.start_monitoring()
    
    def start_monitoring(self):
        """Start real-time monitoring"""
        if not self.visual_system:
            return
        
        if self.visual_system.start_monitoring():
            self.monitoring_enabled = True
            self.start_btn.setText("Stop Monitoring")
            self.status_label.setText("Monitoring...")
            self.update_timer.start(100)  # Update every 100ms
        else:
            QMessageBox.critical(self, "Error", "Failed to start monitoring")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        if self.visual_system:
            self.visual_system.stop_monitoring()
        
        self.monitoring_enabled = False
        self.start_btn.setText("Start Monitoring")
        self.status_label.setText("Stopped")
        self.update_timer.stop()
    
    def auto_detect_skills(self):
        """Trigger auto-detection of skills"""
        if not self.visual_system:
            QMessageBox.warning(self, "Warning", "No visual system available")
            return
        
        self.status_label.setText("Auto-detecting skills...")
        results = self.visual_system.auto_detect_skills()
        
        if results:
            QMessageBox.information(self, "Success", f"Detected {len(results)} skills")
        else:
            QMessageBox.warning(self, "Warning", "No skills detected")
        
        self.status_label.setText("Ready")
    
    def update_display(self):
        """Update the skill display"""
        if not self.visual_system or not self.monitoring_enabled:
            return
        
        profile = self.visual_system.class_manager.get_current_profile()
        if not profile:
            return
        
        # Clear existing items
        self.skill_tree.clear()
        
        # Add skills
        for skill_name, skill in profile.skills.items():
            item = QTreeWidgetItem([
                skill_name,
                skill.current_state.value,
                f"{skill.get_cooldown_remaining():.1f}s",
                f"({skill.position.region[0]}, {skill.position.region[1]})" if skill.position else "Not found",
                f"{skill.detection_confidence:.2f}"
            ])
            
            # Color code by state
            if skill.current_state == SkillState.READY:
                item.setBackground(1, Qt.green)
            elif skill.current_state == SkillState.COOLDOWN:
                item.setBackground(1, Qt.yellow)
            elif skill.current_state == SkillState.UNAVAILABLE:
                item.setBackground(1, Qt.red)
            
            self.skill_tree.addTopLevelItem(item)
        
        # Update detection rate
        stats = self.visual_system.get_system_stats()
        detection_rate = stats.get('scan_count', 0) / max(1, time.time() - stats.get('last_scan_time', time.time()))
        self.detection_rate_label.setText(f"Detection Rate: {detection_rate:.1f} Hz")
    
    @pyqtSlot(object, object, object)
    def on_skill_state_changed(self, skill, old_state, new_state):
        """Handle skill state change"""
        # This will be handled by update_display
        pass
    
    @pyqtSlot(int, object)
    def on_skill_detected(self, slot_index, result):
        """Handle skill detection"""
        if result.detected_skill:
            print(f"Detected {result.detected_skill.name} in slot {slot_index}")


class VisualSkillConfigDialog(QDialog):
    """Main dialog for visual skill system configuration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Visual Skill System Configuration")
        self.setMinimumSize(1000, 700)
        
        # Core components
        self.config = VisualSkillConfig()
        self.visual_system = VisualSkillSystem()
        
        # Data
        self.current_class = self.config.get_current_class()
        self.unsaved_changes = False
        
        self.setup_ui()
        self.load_configuration()
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.auto_save)
        self.auto_save_timer.start(30000)  # Auto-save every 30 seconds
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Header with class selection
        self.setup_header(layout)
        
        # Main tab widget
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_class_tab()
        self.setup_skills_tab()
        self.setup_rotations_tab()
        self.setup_detection_tab()
        self.setup_monitor_tab()
        
        # Footer with buttons
        self.setup_footer(layout)
    
    def setup_header(self, layout):
        """Setup header with class selection"""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_layout = QHBoxLayout(header_frame)
        
        # Class selection
        header_layout.addWidget(QLabel("Character Class:"))
        self.class_combo = QComboBox()
        self.class_combo.currentTextChanged.connect(self.on_class_changed)
        header_layout.addWidget(self.class_combo)
        
        # Class preview (icon if available)
        self.class_preview_label = QLabel()
        self.class_preview_label.setFixedSize(64, 64)
        self.class_preview_label.setStyleSheet("border: 1px solid gray;")
        header_layout.addWidget(self.class_preview_label)
        
        header_layout.addStretch()
        
        # Quick actions
        self.quick_scan_btn = QPushButton("Quick Scan")
        self.quick_scan_btn.clicked.connect(self.quick_skill_scan)
        header_layout.addWidget(self.quick_scan_btn)
        
        layout.addWidget(header_frame)
    
    def setup_class_tab(self):
        """Setup class management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - class list and info
        left_widget = QGroupBox("Class Information")
        left_layout = QVBoxLayout(left_widget)
        
        # Class display name
        form_layout = QFormLayout()
        self.class_display_name_edit = QLineEdit()
        self.class_display_name_edit.textChanged.connect(self.mark_unsaved)
        form_layout.addRow("Display Name:", self.class_display_name_edit)
        
        # Resource path
        self.resource_path_edit = QLineEdit()
        self.resource_path_edit.setReadOnly(True)
        form_layout.addRow("Resource Path:", self.resource_path_edit)
        
        # Auto-discovery settings
        self.auto_discovery_cb = QCheckBox("Enable Auto-Discovery")
        self.auto_discovery_cb.setChecked(True)
        form_layout.addRow("", self.auto_discovery_cb)
        
        left_layout.addLayout(form_layout)
        
        # Class statistics
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout(stats_group)
        
        self.skills_count_label = QLabel("0")
        self.rotations_count_label = QLabel("0")
        self.detected_skills_label = QLabel("0")
        
        stats_layout.addRow("Total Skills:", self.skills_count_label)
        stats_layout.addRow("Rotations:", self.rotations_count_label)
        stats_layout.addRow("Detected Skills:", self.detected_skills_label)
        
        left_layout.addWidget(stats_group)
        left_layout.addStretch()
        
        layout.addWidget(left_widget, 1)
        
        # Right side - class actions
        right_widget = QGroupBox("Actions")
        right_layout = QVBoxLayout(right_widget)
        
        # Auto-discovery
        self.discover_skills_btn = QPushButton("Discover Skills from Resources")
        self.discover_skills_btn.clicked.connect(self.discover_class_skills)
        right_layout.addWidget(self.discover_skills_btn)
        
        # Import/Export
        self.export_class_btn = QPushButton("Export Class Configuration")
        self.export_class_btn.clicked.connect(self.export_class_config)
        right_layout.addWidget(self.export_class_btn)
        
        self.import_class_btn = QPushButton("Import Class Configuration")
        self.import_class_btn.clicked.connect(self.import_class_config)
        right_layout.addWidget(self.import_class_btn)
        
        right_layout.addStretch()
        
        # Reset options
        reset_group = QGroupBox("Reset Options")
        reset_layout = QVBoxLayout(reset_group)
        
        self.reset_skills_btn = QPushButton("Reset All Skills")
        self.reset_skills_btn.clicked.connect(self.reset_class_skills)
        reset_layout.addWidget(self.reset_skills_btn)
        
        self.reset_rotations_btn = QPushButton("Reset All Rotations")
        self.reset_rotations_btn.clicked.connect(self.reset_class_rotations)
        reset_layout.addWidget(self.reset_rotations_btn)
        
        right_layout.addWidget(reset_group)
        layout.addWidget(right_widget, 1)
        
        self.tab_widget.addTab(tab, "Class")
    
    def setup_skills_tab(self):
        """Setup skills management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - skill list
        left_widget = QGroupBox("Skills")
        left_layout = QVBoxLayout(left_widget)
        
        # Skill filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter:"))
        self.skill_filter_edit = QLineEdit()
        self.skill_filter_edit.textChanged.connect(self.filter_skills)
        filter_layout.addWidget(self.skill_filter_edit)
        left_layout.addLayout(filter_layout)
        
        # Skill tree
        self.skills_tree = QTreeWidget()
        self.skills_tree.setHeaderLabels(["Skill", "Key", "Type", "Priority", "Enabled"])
        self.skills_tree.itemClicked.connect(self.on_skill_selected)
        left_layout.addWidget(self.skills_tree)
        
        # Skill management buttons
        skill_btn_layout = QHBoxLayout()
        self.add_skill_btn = QPushButton("Add")
        self.add_skill_btn.clicked.connect(self.add_skill)
        self.remove_skill_btn = QPushButton("Remove")
        self.remove_skill_btn.clicked.connect(self.remove_skill)
        self.duplicate_skill_btn = QPushButton("Duplicate")
        self.duplicate_skill_btn.clicked.connect(self.duplicate_skill)
        
        skill_btn_layout.addWidget(self.add_skill_btn)
        skill_btn_layout.addWidget(self.remove_skill_btn)
        skill_btn_layout.addWidget(self.duplicate_skill_btn)
        left_layout.addLayout(skill_btn_layout)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - skill details
        right_widget = QGroupBox("Skill Details")
        right_layout = QFormLayout(right_widget)
        
        # Basic properties
        self.skill_name_edit = QLineEdit()
        self.skill_name_edit.textChanged.connect(self.mark_unsaved)
        right_layout.addRow("Name:", self.skill_name_edit)
        
        self.skill_key_edit = QLineEdit()
        self.skill_key_edit.textChanged.connect(self.mark_unsaved)
        right_layout.addRow("Hotkey:", self.skill_key_edit)
        
        self.skill_type_combo = QComboBox()
        for skill_type in SkillType:
            self.skill_type_combo.addItem(skill_type.value.title(), skill_type)
        self.skill_type_combo.currentTextChanged.connect(self.mark_unsaved)
        right_layout.addRow("Type:", self.skill_type_combo)
        
        # Icon selection
        icon_layout = QHBoxLayout()
        self.skill_icon_edit = QLineEdit()
        self.skill_icon_edit.textChanged.connect(self.mark_unsaved)
        self.browse_icon_btn = QPushButton("Browse")
        self.browse_icon_btn.clicked.connect(self.browse_skill_icon)
        icon_layout.addWidget(self.skill_icon_edit)
        icon_layout.addWidget(self.browse_icon_btn)
        right_layout.addRow("Icon:", icon_layout)
        
        # Timing properties
        self.cooldown_spin = QDoubleSpinBox()
        self.cooldown_spin.setRange(0.0, 3600.0)
        self.cooldown_spin.setSingleStep(0.1)
        self.cooldown_spin.setSuffix(" sec")
        self.cooldown_spin.valueChanged.connect(self.mark_unsaved)
        right_layout.addRow("Cooldown:", self.cooldown_spin)
        
        self.cast_time_spin = QDoubleSpinBox()
        self.cast_time_spin.setRange(0.0, 10.0)
        self.cast_time_spin.setSingleStep(0.1)
        self.cast_time_spin.setSuffix(" sec")
        self.cast_time_spin.valueChanged.connect(self.mark_unsaved)
        right_layout.addRow("Cast Time:", self.cast_time_spin)
        
        # Game mechanics
        self.priority_spin = QSpinBox()
        self.priority_spin.setRange(1, 10)
        self.priority_spin.valueChanged.connect(self.mark_unsaved)
        right_layout.addRow("Priority:", self.priority_spin)
        
        self.mana_cost_spin = QSpinBox()
        self.mana_cost_spin.setRange(0, 1000)
        self.mana_cost_spin.valueChanged.connect(self.mark_unsaved)
        right_layout.addRow("Mana Cost:", self.mana_cost_spin)
        
        # Checkboxes
        self.enabled_cb = QCheckBox()
        self.enabled_cb.stateChanged.connect(self.mark_unsaved)
        right_layout.addRow("Enabled:", self.enabled_cb)
        
        self.visual_cooldown_cb = QCheckBox()
        self.visual_cooldown_cb.stateChanged.connect(self.mark_unsaved)
        right_layout.addRow("Visual Cooldown:", self.visual_cooldown_cb)
        
        self.range_check_cb = QCheckBox()
        self.range_check_cb.stateChanged.connect(self.mark_unsaved)
        right_layout.addRow("Range Check:", self.range_check_cb)
        
        # Description
        self.skill_description_edit = QTextEdit()
        self.skill_description_edit.setMaximumHeight(80)
        self.skill_description_edit.textChanged.connect(self.mark_unsaved)
        right_layout.addRow("Description:", self.skill_description_edit)
        
        layout.addWidget(right_widget, 1)
        
        self.tab_widget.addTab(tab, "Skills")
    
    def setup_rotations_tab(self):
        """Setup rotations management tab"""
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # Left side - rotation list
        left_widget = QGroupBox("Rotations")
        left_layout = QVBoxLayout(left_widget)
        
        self.rotations_list = QListWidget()
        self.rotations_list.itemClicked.connect(self.on_rotation_selected)
        left_layout.addWidget(self.rotations_list)
        
        # Rotation management buttons
        rotation_btn_layout = QHBoxLayout()
        self.add_rotation_btn = QPushButton("Add")
        self.add_rotation_btn.clicked.connect(self.add_rotation)
        self.remove_rotation_btn = QPushButton("Remove")
        self.remove_rotation_btn.clicked.connect(self.remove_rotation)
        self.test_rotation_btn = QPushButton("Test")
        self.test_rotation_btn.clicked.connect(self.test_rotation)
        
        rotation_btn_layout.addWidget(self.add_rotation_btn)
        rotation_btn_layout.addWidget(self.remove_rotation_btn)
        rotation_btn_layout.addWidget(self.test_rotation_btn)
        left_layout.addLayout(rotation_btn_layout)
        
        layout.addWidget(left_widget, 1)
        
        # Right side - rotation editor
        right_widget = QGroupBox("Rotation Editor")
        right_layout = QVBoxLayout(right_widget)
        
        # Rotation properties
        props_layout = QFormLayout()
        self.rotation_name_edit = QLineEdit()
        self.rotation_name_edit.textChanged.connect(self.mark_unsaved)
        props_layout.addRow("Name:", self.rotation_name_edit)
        
        self.rotation_repeat_cb = QCheckBox()
        self.rotation_repeat_cb.stateChanged.connect(self.mark_unsaved)
        props_layout.addRow("Repeat:", self.rotation_repeat_cb)
        
        self.rotation_adaptive_cb = QCheckBox()
        self.rotation_adaptive_cb.setChecked(True)
        self.rotation_adaptive_cb.stateChanged.connect(self.mark_unsaved)
        props_layout.addRow("Adaptive:", self.rotation_adaptive_cb)
        
        right_layout.addLayout(props_layout)
        
        # Skill lists
        lists_layout = QHBoxLayout()
        
        # Available skills
        available_group = QGroupBox("Available Skills")
        available_layout = QVBoxLayout(available_group)
        self.available_skills_list = QListWidget()
        self.available_skills_list.itemDoubleClicked.connect(self.add_skill_to_rotation)
        available_layout.addWidget(self.available_skills_list)
        lists_layout.addWidget(available_group)
        
        # Control buttons
        controls_layout = QVBoxLayout()
        controls_layout.addStretch()
        
        self.add_to_rotation_btn = QPushButton(">>")
        self.add_to_rotation_btn.clicked.connect(self.add_skill_to_rotation)
        controls_layout.addWidget(self.add_to_rotation_btn)
        
        self.remove_from_rotation_btn = QPushButton("<<")
        self.remove_from_rotation_btn.clicked.connect(self.remove_skill_from_rotation)
        controls_layout.addWidget(self.remove_from_rotation_btn)
        
        self.move_up_btn = QPushButton("Up")
        self.move_up_btn.clicked.connect(self.move_skill_up)
        controls_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("Down")
        self.move_down_btn.clicked.connect(self.move_skill_down)
        controls_layout.addWidget(self.move_down_btn)
        
        controls_layout.addStretch()
        lists_layout.addLayout(controls_layout)
        
        # Rotation skills
        rotation_group = QGroupBox("Rotation Skills")
        rotation_layout = QVBoxLayout(rotation_group)
        self.rotation_skills_list = QListWidget()
        self.rotation_skills_list.itemDoubleClicked.connect(self.remove_skill_from_rotation)
        rotation_layout.addWidget(self.rotation_skills_list)
        lists_layout.addWidget(rotation_group)
        
        right_layout.addLayout(lists_layout)
        layout.addWidget(right_widget, 2)
        
        self.tab_widget.addTab(tab, "Rotations")
    
    def setup_detection_tab(self):
        """Setup detection settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Detection settings
        detection_group = QGroupBox("Detection Settings")
        detection_layout = QFormLayout(detection_group)
        
        self.template_threshold_slider = QSlider(Qt.Horizontal)
        self.template_threshold_slider.setRange(50, 100)
        self.template_threshold_slider.setValue(85)
        self.template_threshold_slider.valueChanged.connect(self.update_threshold_labels)
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(self.template_threshold_slider)
        self.template_threshold_label = QLabel("0.85")
        threshold_layout.addWidget(self.template_threshold_label)
        detection_layout.addRow("Template Threshold:", threshold_layout)
        
        self.cooldown_threshold_slider = QSlider(Qt.Horizontal)
        self.cooldown_threshold_slider.setRange(50, 100)
        self.cooldown_threshold_slider.setValue(70)
        self.cooldown_threshold_slider.valueChanged.connect(self.update_threshold_labels)
        cooldown_layout = QHBoxLayout()
        cooldown_layout.addWidget(self.cooldown_threshold_slider)
        self.cooldown_threshold_label = QLabel("0.70")
        cooldown_layout.addWidget(self.cooldown_threshold_label)
        detection_layout.addRow("Cooldown Threshold:", cooldown_layout)
        
        self.scan_interval_spin = QDoubleSpinBox()
        self.scan_interval_spin.setRange(0.01, 1.0)
        self.scan_interval_spin.setSingleStep(0.01)
        self.scan_interval_spin.setValue(0.1)
        self.scan_interval_spin.setSuffix(" sec")
        detection_layout.addRow("Scan Interval:", self.scan_interval_spin)
        
        self.multi_scale_cb = QCheckBox()
        self.multi_scale_cb.setChecked(True)
        detection_layout.addRow("Multi-Scale Detection:", self.multi_scale_cb)
        
        layout.addWidget(detection_group)
        
        # Execution settings
        execution_group = QGroupBox("Execution Settings")
        execution_layout = QFormLayout(execution_group)
        
        self.global_cooldown_spin = QDoubleSpinBox()
        self.global_cooldown_spin.setRange(0.0, 1.0)
        self.global_cooldown_spin.setSingleStep(0.01)
        self.global_cooldown_spin.setValue(0.15)
        self.global_cooldown_spin.setSuffix(" sec")
        execution_layout.addRow("Global Cooldown:", self.global_cooldown_spin)
        
        self.visual_verification_cb = QCheckBox()
        self.visual_verification_cb.setChecked(True)
        execution_layout.addRow("Visual Verification:", self.visual_verification_cb)
        
        self.auto_retry_cb = QCheckBox()
        self.auto_retry_cb.setChecked(True)
        execution_layout.addRow("Auto Retry:", self.auto_retry_cb)
        
        self.max_retries_spin = QSpinBox()
        self.max_retries_spin.setRange(1, 10)
        self.max_retries_spin.setValue(3)
        execution_layout.addRow("Max Retries:", self.max_retries_spin)
        
        layout.addWidget(execution_group)
        
        # Skill bar regions
        regions_group = QGroupBox("Skill Bar Regions")
        regions_layout = QFormLayout(regions_group)
        
        # Main bar region
        main_bar_layout = QHBoxLayout()
        self.main_bar_x_spin = QSpinBox()
        self.main_bar_x_spin.setRange(0, 2000)
        self.main_bar_x_spin.setValue(100)
        main_bar_layout.addWidget(self.main_bar_x_spin)
        
        self.main_bar_y_spin = QSpinBox()
        self.main_bar_y_spin.setRange(0, 2000)
        self.main_bar_y_spin.setValue(500)
        main_bar_layout.addWidget(self.main_bar_y_spin)
        
        self.main_bar_w_spin = QSpinBox()
        self.main_bar_w_spin.setRange(100, 2000)
        self.main_bar_w_spin.setValue(600)
        main_bar_layout.addWidget(self.main_bar_w_spin)
        
        self.main_bar_h_spin = QSpinBox()
        self.main_bar_h_spin.setRange(10, 200)
        self.main_bar_h_spin.setValue(50)
        main_bar_layout.addWidget(self.main_bar_h_spin)
        
        regions_layout.addRow("Main Bar (X,Y,W,H):", main_bar_layout)
        
        layout.addWidget(regions_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Detection")
    
    def setup_monitor_tab(self):
        """Setup monitoring tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Create monitor widget
        self.monitor_widget = SkillMonitorWidget()
        layout.addWidget(self.monitor_widget)
        
        self.tab_widget.addTab(tab, "Monitor")
    
    def setup_footer(self, layout):
        """Setup footer with action buttons"""
        footer_layout = QHBoxLayout()
        
        # Status indicator
        self.unsaved_indicator = QLabel("●")
        self.unsaved_indicator.setStyleSheet("color: red; font-size: 16px;")
        self.unsaved_indicator.setVisible(False)
        footer_layout.addWidget(self.unsaved_indicator)
        
        self.status_label = QLabel("Ready")
        footer_layout.addWidget(self.status_label)
        
        footer_layout.addStretch()
        
        # Action buttons
        self.save_btn = QPushButton("Save Configuration")
        self.save_btn.clicked.connect(self.save_configuration)
        footer_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load Configuration")
        self.load_btn.clicked.connect(self.load_configuration)
        footer_layout.addWidget(self.load_btn)
        
        self.reset_btn = QPushButton("Reset to Defaults")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        footer_layout.addWidget(self.reset_btn)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        footer_layout.addWidget(button_box)
        
        layout.addLayout(footer_layout)
    
    def load_configuration(self):
        """Load configuration from file"""
        try:
            self.config.load_config()
            
            # Populate class combo
            self.class_combo.clear()
            for class_name, display_name in self.config.get_available_classes():
                self.class_combo.addItem(display_name, class_name)
            
            # Set current class
            current_class = self.config.get_current_class()
            for i in range(self.class_combo.count()):
                if self.class_combo.itemData(i) == current_class:
                    self.class_combo.setCurrentIndex(i)
                    break
            
            # Load detection settings
            detection_settings = self.config.get_detection_settings()
            self.template_threshold_slider.setValue(int(detection_settings.get('template_threshold', 0.85) * 100))
            self.cooldown_threshold_slider.setValue(int(detection_settings.get('cooldown_threshold', 0.7) * 100))
            self.scan_interval_spin.setValue(detection_settings.get('scan_interval', 0.1))
            self.multi_scale_cb.setChecked(detection_settings.get('use_multi_scale', True))
            
            # Load execution settings
            execution_settings = self.config.get_execution_settings()
            self.global_cooldown_spin.setValue(execution_settings.get('global_cooldown', 0.15))
            self.visual_verification_cb.setChecked(execution_settings.get('visual_verification', True))
            self.auto_retry_cb.setChecked(execution_settings.get('auto_retry', True))
            self.max_retries_spin.setValue(execution_settings.get('max_retries', 3))
            
            # Load skill bar regions
            regions = self.config.get_skill_bar_regions()
            main_bar = regions.get('main_bar', [100, 500, 600, 50])
            self.main_bar_x_spin.setValue(main_bar[0])
            self.main_bar_y_spin.setValue(main_bar[1])
            self.main_bar_w_spin.setValue(main_bar[2])
            self.main_bar_h_spin.setValue(main_bar[3])
            
            self.refresh_all_displays()
            self.unsaved_changes = False
            self.update_unsaved_indicator()
            
            self.status_label.setText("Configuration loaded")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save current configuration"""
        try:
            # Save detection settings
            detection_settings = {
                'template_threshold': self.template_threshold_slider.value() / 100.0,
                'cooldown_threshold': self.cooldown_threshold_slider.value() / 100.0,
                'scan_interval': self.scan_interval_spin.value(),
                'use_multi_scale': self.multi_scale_cb.isChecked()
            }
            self.config.set_detection_settings(detection_settings)
            
            # Save execution settings
            execution_settings = {
                'global_cooldown': self.global_cooldown_spin.value(),
                'visual_verification': self.visual_verification_cb.isChecked(),
                'auto_retry': self.auto_retry_cb.isChecked(),
                'max_retries': self.max_retries_spin.value()
            }
            self.config.set_execution_settings(execution_settings)
            
            # Save skill bar regions
            regions = {
                'main_bar': [
                    self.main_bar_x_spin.value(),
                    self.main_bar_y_spin.value(),
                    self.main_bar_w_spin.value(),
                    self.main_bar_h_spin.value()
                ]
            }
            self.config.set_skill_bar_regions(regions)
            
            # Save configuration file
            if self.config.save_config():
                self.unsaved_changes = False
                self.update_unsaved_indicator()
                self.status_label.setText("Configuration saved")
                QMessageBox.information(self, "Success", "Configuration saved successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to save configuration")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save configuration: {e}")
    
    def mark_unsaved(self):
        """Mark configuration as having unsaved changes"""
        self.unsaved_changes = True
        self.update_unsaved_indicator()
    
    def update_unsaved_indicator(self):
        """Update the unsaved changes indicator"""
        self.unsaved_indicator.setVisible(self.unsaved_changes)
    
    def auto_save(self):
        """Auto-save configuration if there are unsaved changes"""
        if self.unsaved_changes:
            self.save_configuration()
    
    def on_class_changed(self, display_name):
        """Handle class selection change"""
        class_name = self.class_combo.currentData()
        if class_name and class_name != self.current_class:
            self.current_class = class_name
            self.config.set_current_class(class_name)
            self.refresh_all_displays()
            self.mark_unsaved()
    
    def refresh_all_displays(self):
        """Refresh all UI displays with current data"""
        self.refresh_skills_display()
        self.refresh_rotations_display()
        self.update_class_info()
        self.update_threshold_labels()
    
    def refresh_skills_display(self):
        """Refresh the skills display"""
        self.skills_tree.clear()
        
        class_config = self.config.get_class_config(self.current_class)
        if not class_config:
            return
        
        skills = class_config.get('skills', {})
        for skill_name, skill_data in skills.items():
            item = QTreeWidgetItem([
                skill_name,
                skill_data.get('key', ''),
                skill_data.get('type', 'visual'),
                str(skill_data.get('priority', 3)),
                "Yes" if skill_data.get('enabled', True) else "No"
            ])
            item.setData(0, Qt.UserRole, skill_name)
            self.skills_tree.addTopLevelItem(item)
    
    def refresh_rotations_display(self):
        """Refresh the rotations display"""
        self.rotations_list.clear()
        self.available_skills_list.clear()
        
        class_config = self.config.get_class_config(self.current_class)
        if not class_config:
            return
        
        # Add rotations
        rotations = class_config.get('rotations', {})
        for rotation_name in rotations.keys():
            item = QListWidgetItem(rotation_name)
            item.setData(Qt.UserRole, rotation_name)
            self.rotations_list.addItem(item)
        
        # Add available skills
        skills = class_config.get('skills', {})
        for skill_name in skills.keys():
            item = QListWidgetItem(skill_name)
            item.setData(Qt.UserRole, skill_name)
            self.available_skills_list.addItem(item)
    
    def update_class_info(self):
        """Update class information display"""
        class_config = self.config.get_class_config(self.current_class)
        if not class_config:
            return
        
        self.class_display_name_edit.setText(class_config.get('display_name', ''))
        
        # Update statistics
        skills_count = len(class_config.get('skills', {}))
        rotations_count = len(class_config.get('rotations', {}))
        
        self.skills_count_label.setText(str(skills_count))
        self.rotations_count_label.setText(str(rotations_count))
    
    def update_threshold_labels(self):
        """Update threshold labels"""
        self.template_threshold_label.setText(f"{self.template_threshold_slider.value() / 100.0:.2f}")
        self.cooldown_threshold_label.setText(f"{self.cooldown_threshold_slider.value() / 100.0:.2f}")
    
    def quick_skill_scan(self):
        """Perform quick skill scan"""
        if not self.current_class:
            return
        
        # Initialize visual system for current class
        skill_bar_region = (
            self.main_bar_x_spin.value(),
            self.main_bar_y_spin.value(),
            self.main_bar_w_spin.value(),
            self.main_bar_h_spin.value()
        )
        
        self.visual_system.initialize_class(self.current_class, [skill_bar_region])
        self.monitor_widget.set_visual_system(self.visual_system)
        
        self.status_label.setText("Quick scan completed")
    
    # Placeholder methods for other functionality
    def on_skill_selected(self, item, column):
        """Handle skill selection"""
        pass
    
    def add_skill(self):
        """Add new skill"""
        pass
    
    def remove_skill(self):
        """Remove selected skill"""
        pass
    
    def duplicate_skill(self):
        """Duplicate selected skill"""
        pass
    
    def browse_skill_icon(self):
        """Browse for skill icon"""
        pass
    
    def filter_skills(self, text):
        """Filter skills list"""
        pass
    
    def on_rotation_selected(self, item):
        """Handle rotation selection"""
        pass
    
    def add_rotation(self):
        """Add new rotation"""
        pass
    
    def remove_rotation(self):
        """Remove selected rotation"""
        pass
    
    def test_rotation(self):
        """Test selected rotation"""
        pass
    
    def add_skill_to_rotation(self):
        """Add skill to rotation"""
        pass
    
    def remove_skill_from_rotation(self):
        """Remove skill from rotation"""
        pass
    
    def move_skill_up(self):
        """Move skill up in rotation"""
        pass
    
    def move_skill_down(self):
        """Move skill down in rotation"""
        pass
    
    def discover_class_skills(self):
        """Auto-discover skills for current class"""
        pass
    
    def export_class_config(self):
        """Export class configuration"""
        pass
    
    def import_class_config(self):
        """Import class configuration"""
        pass
    
    def reset_class_skills(self):
        """Reset class skills"""
        pass
    
    def reset_class_rotations(self):
        """Reset class rotations"""
        pass
    
    def reset_to_defaults(self):
        """Reset entire configuration to defaults"""
        reply = QMessageBox.question(
            self, "Reset Configuration",
            "Are you sure you want to reset all settings to defaults? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.reset_to_defaults()
            self.load_configuration()
    
    def closeEvent(self, event):
        """Handle close event"""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Save:
                self.save_configuration()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    dialog = VisualSkillConfigDialog()
    dialog.show()
    sys.exit(app.exec_())