# ui/dialogs/visual_region_selector.py
"""
Visual Region Selector for Skill Bar Configuration

Provides an intuitive interface for selecting skill bar regions using visual feedback,
similar to the existing test_pixels functionality but specifically for skill bars.
"""

import time
from typing import List, Tuple, Optional, Callable
from PIL import Image, ImageDraw, ImageFont

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QSpinBox, QCheckBox, QComboBox,
    QScrollArea, QFrame, QMessageBox, QProgressBar, QTextEdit,
    QSplitter, QTabWidget, QWidget, QSlider
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QPixmap, QImage, QFont as QFont_GUI, QPainter, QPen, QColor

from skill_system.visual_system import VisualSkillSystem
from skill_system.skill_types import SkillBarMapping


class SkillBarDetectionThread(QThread):
    """Thread for performing skill bar detection"""
    
    detection_progress = pyqtSignal(int)  # Progress percentage
    detection_result = pyqtSignal(object)  # Detection results
    detection_error = pyqtSignal(str)     # Error message
    
    def __init__(self, visual_system, skill_bar_region, parent=None):
        super().__init__(parent)
        self.visual_system = visual_system
        self.skill_bar_region = skill_bar_region
        self.should_stop = False
    
    def run(self):
        """Run skill detection in background"""
        try:
            self.detection_progress.emit(10)
            
            # Initialize skill bar mapping
            slot_count = 12  # Configurable
            x, y, w, h = self.skill_bar_region
            slot_width = w // slot_count
            
            slot_regions = []
            for i in range(slot_count):
                slot_x = x + (i * slot_width)
                slot_regions.append((slot_x, y, slot_width, h))
            
            self.detection_progress.emit(30)
            
            if self.should_stop:
                return
            
            # Create skill bar mapping
            skill_bar_mapping = SkillBarMapping(
                bar_region=self.skill_bar_region,
                slot_regions=slot_regions
            )
            
            self.detection_progress.emit(50)
            
            # Get current profile
            profile = self.visual_system.class_manager.get_current_profile()
            if not profile:
                self.detection_error.emit("No class profile available")
                return
            
            self.detection_progress.emit(70)
            
            if self.should_stop:
                return
            
            # Perform detection
            skills_to_detect = list(profile.skills.values())
            results = self.visual_system.detector.scan_skill_bar(
                skill_bar_mapping, skills_to_detect, profile.detection_settings
            )
            
            self.detection_progress.emit(100)
            
            # Emit results
            self.detection_result.emit({
                'mapping': skill_bar_mapping,
                'results': results,
                'skills_found': len(results)
            })
            
        except Exception as e:
            self.detection_error.emit(str(e))
    
    def stop(self):
        """Stop the detection thread"""
        self.should_stop = True


class VisualRegionSelector(QDialog):
    """Enhanced visual region selector for skill bars"""
    
    region_selected = pyqtSignal(tuple)  # Emitted when region is confirmed
    
    def __init__(self, bot_engine, visual_system: VisualSkillSystem, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine
        self.visual_system = visual_system
        
        self.setWindowTitle("Visual Skill Bar Region Selector")
        self.setMinimumSize(900, 700)
        
        # State
        self.current_capture = None
        self.selected_region = None
        self.skill_bar_mapping = None
        self.detection_results = {}
        
        # Detection thread
        self.detection_thread = None
        
        self.setup_ui()
        self.load_current_settings()
        
        # Auto-refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.auto_refresh)
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Setup tabs
        self.setup_capture_tab()
        self.setup_detection_tab()
        self.setup_preview_tab()
        
        # Footer
        self.setup_footer(layout)
    
    def setup_capture_tab(self):
        """Setup the screen capture and region selection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <b>Step 1: Capture Game Screen</b><br>
        • Make sure your game window is visible and the skill bar is showing<br>
        • Click "Capture Screen" to take a screenshot<br>
        • Use the coordinate controls to select the skill bar region<br>
        • The preview will show your selection with slot divisions
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0f8ff; padding: 10px; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Control panel
        controls_group = QGroupBox("Capture Controls")
        controls_layout = QHBoxLayout(controls_group)
        
        self.capture_btn = QPushButton("📷 Capture Screen")
        self.capture_btn.clicked.connect(self.capture_screen)
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #0056b3; }
        """)
        controls_layout.addWidget(self.capture_btn)
        
        self.auto_refresh_cb = QCheckBox("Auto-refresh (1 sec)")
        self.auto_refresh_cb.stateChanged.connect(self.toggle_auto_refresh)
        controls_layout.addWidget(self.auto_refresh_cb)
        
        controls_layout.addStretch()
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        zoom_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(100, 400)
        self.zoom_slider.setValue(200)
        self.zoom_slider.valueChanged.connect(self.update_preview)
        zoom_layout.addWidget(self.zoom_slider)
        self.zoom_label = QLabel("200%")
        zoom_layout.addWidget(self.zoom_label)
        controls_layout.addLayout(zoom_layout)
        
        layout.addWidget(controls_group)
        
        # Region configuration
        region_group = QGroupBox("Skill Bar Region")
        region_layout = QGridLayout(region_group)
        
        # Coordinate controls
        region_layout.addWidget(QLabel("X:"), 0, 0)
        self.region_x_spin = QSpinBox()
        self.region_x_spin.setRange(0, 2000)
        self.region_x_spin.setValue(100)
        self.region_x_spin.valueChanged.connect(self.update_preview)
        region_layout.addWidget(self.region_x_spin, 0, 1)
        
        region_layout.addWidget(QLabel("Y:"), 0, 2)
        self.region_y_spin = QSpinBox()
        self.region_y_spin.setRange(0, 2000)
        self.region_y_spin.setValue(500)
        self.region_y_spin.valueChanged.connect(self.update_preview)
        region_layout.addWidget(self.region_y_spin, 0, 3)
        
        region_layout.addWidget(QLabel("Width:"), 1, 0)
        self.region_w_spin = QSpinBox()
        self.region_w_spin.setRange(100, 2000)
        self.region_w_spin.setValue(720)
        self.region_w_spin.valueChanged.connect(self.update_preview)
        region_layout.addWidget(self.region_w_spin, 1, 1)
        
        region_layout.addWidget(QLabel("Height:"), 1, 2)
        self.region_h_spin = QSpinBox()
        self.region_h_spin.setRange(20, 200)
        self.region_h_spin.setValue(60)
        self.region_h_spin.valueChanged.connect(self.update_preview)
        region_layout.addWidget(self.region_h_spin, 1, 3)
        
        # Slot configuration
        region_layout.addWidget(QLabel("Skill Slots:"), 2, 0)
        self.slots_spin = QSpinBox()
        self.slots_spin.setRange(6, 16)
        self.slots_spin.setValue(12)
        self.slots_spin.valueChanged.connect(self.update_preview)
        region_layout.addWidget(self.slots_spin, 2, 1)
        
        # Quick presets
        presets_layout = QHBoxLayout()
        presets_layout.addWidget(QLabel("Presets:"))
        
        preset_1080p = QPushButton("1080p")
        preset_1080p.clicked.connect(lambda: self.apply_preset(1080))
        presets_layout.addWidget(preset_1080p)
        
        preset_1440p = QPushButton("1440p")
        preset_1440p.clicked.connect(lambda: self.apply_preset(1440))
        presets_layout.addWidget(preset_1440p)
        
        preset_custom = QPushButton("Auto-detect")
        preset_custom.clicked.connect(self.auto_detect_region)
        presets_layout.addWidget(preset_custom)
        
        region_layout.addLayout(presets_layout, 2, 2, 1, 2)
        
        layout.addWidget(region_group)
        
        # Preview area
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Scrollable preview
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        self.preview_label = QLabel("Click 'Capture Screen' to see preview")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet("border: 2px dashed #ccc; padding: 20px;")
        scroll_area.setWidget(self.preview_label)
        
        preview_layout.addWidget(scroll_area)
        layout.addWidget(preview_group)
        
        self.tab_widget.addTab(tab, "📷 Capture & Select")
    
    def setup_detection_tab(self):
        """Setup the skill detection tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <b>Step 2: Detect Skills</b><br>
        • Select your character class<br>
        • Click "Start Detection" to automatically find skills in the skill bar<br>
        • Review the detection results and adjust settings if needed
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #f0fff0; padding: 10px; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Class and detection controls
        controls_group = QGroupBox("Detection Controls")
        controls_layout = QGridLayout(controls_group)
        
        # Class selection
        controls_layout.addWidget(QLabel("Character Class:"), 0, 0)
        self.class_combo = QComboBox()
        self.class_combo.currentTextChanged.connect(self.on_class_changed)
        controls_layout.addWidget(self.class_combo, 0, 1)
        
        # Detection settings
        controls_layout.addWidget(QLabel("Detection Accuracy:"), 1, 0)
        self.accuracy_slider = QSlider(Qt.Horizontal)
        self.accuracy_slider.setRange(60, 95)
        self.accuracy_slider.setValue(85)
        self.accuracy_slider.valueChanged.connect(self.update_accuracy_label)
        controls_layout.addWidget(self.accuracy_slider, 1, 1)
        self.accuracy_label = QLabel("85%")
        controls_layout.addWidget(self.accuracy_label, 1, 2)
        
        # Detection button
        self.detect_btn = QPushButton("🔍 Start Detection")
        self.detect_btn.clicked.connect(self.start_detection)
        self.detect_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #218838; }
        """)
        controls_layout.addWidget(self.detect_btn, 0, 3, 2, 1)
        
        layout.addWidget(controls_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Results area
        results_group = QGroupBox("Detection Results")
        results_layout = QVBoxLayout(results_group)
        
        # Results summary
        self.results_summary = QLabel("No detection performed yet")
        self.results_summary.setStyleSheet("font-weight: bold; padding: 5px;")
        results_layout.addWidget(self.results_summary)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "🔍 Detect Skills")
    
    def setup_preview_tab(self):
        """Setup the final preview and confirmation tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Instructions
        instructions = QLabel("""
        <b>Step 3: Confirm & Apply</b><br>
        • Review the final configuration<br>
        • Test the skill detection if desired<br>
        • Click "Apply Configuration" to save settings
        """)
        instructions.setWordWrap(True)
        instructions.setStyleSheet("background-color: #fff8dc; padding: 10px; border-radius: 5px;")
        layout.addWidget(instructions)
        
        # Configuration summary
        summary_group = QGroupBox("Configuration Summary")
        summary_layout = QGridLayout(summary_group)
        
        summary_layout.addWidget(QLabel("Skill Bar Region:"), 0, 0)
        self.summary_region_label = QLabel("Not set")
        summary_layout.addWidget(self.summary_region_label, 0, 1)
        
        summary_layout.addWidget(QLabel("Number of Slots:"), 1, 0)
        self.summary_slots_label = QLabel("Not set")
        summary_layout.addWidget(self.summary_slots_label, 1, 1)
        
        summary_layout.addWidget(QLabel("Character Class:"), 2, 0)
        self.summary_class_label = QLabel("Not set")
        summary_layout.addWidget(self.summary_class_label, 2, 1)
        
        summary_layout.addWidget(QLabel("Skills Detected:"), 3, 0)
        self.summary_detected_label = QLabel("0")
        summary_layout.addWidget(self.summary_detected_label, 3, 1)
        
        layout.addWidget(summary_group)
        
        # Test buttons
        test_group = QGroupBox("Testing")
        test_layout = QHBoxLayout(test_group)
        
        self.test_detection_btn = QPushButton("🧪 Test Detection")
        self.test_detection_btn.clicked.connect(self.test_detection)
        test_layout.addWidget(self.test_detection_btn)
        
        self.test_execution_btn = QPushButton("⚡ Test Execution")
        self.test_execution_btn.clicked.connect(self.test_execution)
        test_layout.addWidget(self.test_execution_btn)
        
        test_layout.addStretch()
        layout.addWidget(test_group)
        
        # Final preview
        final_preview_group = QGroupBox("Final Preview")
        final_preview_layout = QVBoxLayout(final_preview_group)
        
        self.final_preview_label = QLabel("Configure region and detection first")
        self.final_preview_label.setAlignment(Qt.AlignCenter)
        self.final_preview_label.setMinimumHeight(200)
        self.final_preview_label.setStyleSheet("border: 2px solid #ddd; background-color: #fafafa;")
        final_preview_layout.addWidget(self.final_preview_label)
        
        layout.addWidget(final_preview_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "✅ Confirm")
    
    def setup_footer(self, layout):
        """Setup footer with action buttons"""
        footer_layout = QHBoxLayout()
        
        # Status
        self.status_label = QLabel("Ready to configure skill bar region")
        footer_layout.addWidget(self.status_label)
        
        footer_layout.addStretch()
        
        # Action buttons
        self.save_preset_btn = QPushButton("💾 Save as Preset")
        self.save_preset_btn.clicked.connect(self.save_preset)
        footer_layout.addWidget(self.save_preset_btn)
        
        self.apply_btn = QPushButton("✅ Apply Configuration")
        self.apply_btn.clicked.connect(self.apply_configuration)
        self.apply_btn.setStyleSheet("""
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
        footer_layout.addWidget(self.apply_btn)
        
        self.close_btn = QPushButton("❌ Close")
        self.close_btn.clicked.connect(self.reject)
        footer_layout.addWidget(self.close_btn)
        
        layout.addLayout(footer_layout)
    
    def load_current_settings(self):
        """Load current settings from configuration"""
        try:
            # Load available classes
            self.class_combo.clear()
            classes = self.visual_system.class_manager.get_available_classes()
            for class_name, display_name in classes:
                self.class_combo.addItem(display_name, class_name)
            
            # Set current class
            current_class = self.visual_system.class_manager.current_class
            if current_class:
                for i in range(self.class_combo.count()):
                    if self.class_combo.itemData(i) == current_class:
                        self.class_combo.setCurrentIndex(i)
                        break
            
            self.status_label.setText("Settings loaded successfully")
            
        except Exception as e:
            self.status_label.setText(f"Error loading settings: {e}")
    
    def capture_screen(self):
        """Capture the current screen"""
        try:
            if not self.bot_engine.window_manager.target_window:
                QMessageBox.warning(self, "Warning", "Please select a game window first")
                return
            
            # Capture screen using the existing pixel analyzer
            capture_area = (0, 0, 1920, 1080)  # Full HD capture
            self.current_capture = self.bot_engine.pixel_analyzer.capture_region(capture_area)
            
            if self.current_capture:
                self.update_preview()
                self.status_label.setText("Screen captured successfully")
            else:
                QMessageBox.critical(self, "Error", "Failed to capture screen")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Screen capture failed: {e}")
    
    def update_preview(self):
        """Update the preview with current region selection"""
        if not self.current_capture:
            return
        
        try:
            # Get current region settings
            x = self.region_x_spin.value()
            y = self.region_y_spin.value()
            w = self.region_w_spin.value()
            h = self.region_h_spin.value()
            slots = self.slots_spin.value()
            zoom = self.zoom_slider.value()
            
            # Update zoom label
            self.zoom_label.setText(f"{zoom}%")
            
            # Create preview image
            preview_img = self.current_capture.copy()
            draw = ImageDraw.Draw(preview_img)
            
            # Draw skill bar region
            draw.rectangle([x, y, x + w, y + h], outline="red", width=3)
            
            # Draw slot divisions
            slot_width = w // slots
            for i in range(1, slots):
                slot_x = x + (i * slot_width)
                draw.line([slot_x, y, slot_x, y + h], fill="blue", width=2)
            
            # Draw slot numbers
            try:
                font = ImageFont.load_default()
                for i in range(slots):
                    slot_x = x + (i * slot_width) + slot_width // 2
                    slot_y = y + h // 2
                    draw.text((slot_x, slot_y), str(i + 1), fill="yellow", font=font)
            except:
                pass  # Font loading might fail, ignore
            
            # Crop to show relevant area
            margin = 50
            crop_x1 = max(0, x - margin)
            crop_y1 = max(0, y - margin)
            crop_x2 = min(preview_img.width, x + w + margin)
            crop_y2 = min(preview_img.height, y + h + margin)
            
            cropped = preview_img.crop((crop_x1, crop_y1, crop_x2, crop_y2))
            
            # Apply zoom
            zoom_factor = zoom / 100.0
            new_width = int(cropped.width * zoom_factor)
            new_height = int(cropped.height * zoom_factor)
            zoomed = cropped.resize((new_width, new_height), Image.NEAREST)
            
            # Convert to QPixmap
            q_image = QImage(
                zoomed.tobytes("raw", "RGB"),
                zoomed.width,
                zoomed.height,
                QImage.Format_RGB888
            )
            pixmap = QPixmap.fromImage(q_image)
            
            self.preview_label.setPixmap(pixmap)
            self.preview_label.setFixedSize(pixmap.size())
            
            # Update stored region
            self.selected_region = (x, y, w, h)
            
        except Exception as e:
            self.status_label.setText(f"Preview update failed: {e}")
    
    def apply_preset(self, resolution):
        """Apply preset configuration for different resolutions"""
        if resolution == 1080:
            self.region_x_spin.setValue(300)
            self.region_y_spin.setValue(1020)
            self.region_w_spin.setValue(720)
            self.region_h_spin.setValue(60)
        elif resolution == 1440:
            self.region_x_spin.setValue(400)
            self.region_y_spin.setValue(1360)
            self.region_w_spin.setValue(960)
            self.region_h_spin.setValue(80)
        
        self.update_preview()
        self.status_label.setText(f"Applied {resolution}p preset")
    
    def auto_detect_region(self):
        """Attempt to automatically detect skill bar region"""
        QMessageBox.information(
            self, "Auto-detect", 
            "Auto-detection not implemented yet. Please configure manually."
        )
    
    def toggle_auto_refresh(self, checked):
        """Toggle auto-refresh of screen capture"""
        if checked:
            self.refresh_timer.start(1000)  # 1 second
            self.status_label.setText("Auto-refresh enabled")
        else:
            self.refresh_timer.stop()
            self.status_label.setText("Auto-refresh disabled")
    
    def auto_refresh(self):
        """Auto-refresh screen capture"""
        if self.current_capture:
            self.capture_screen()
    
    def on_class_changed(self):
        """Handle class selection change"""
        class_name = self.class_combo.currentData()
        if class_name:
            try:
                self.visual_system.class_manager.set_current_class(class_name)
                self.status_label.setText(f"Class changed to {self.class_combo.currentText()}")
                self.update_summary()
            except Exception as e:
                self.status_label.setText(f"Failed to change class: {e}")
    
    def update_accuracy_label(self):
        """Update accuracy label"""
        self.accuracy_label.setText(f"{self.accuracy_slider.value()}%")
    
    def start_detection(self):
        """Start skill detection in background"""
        if not self.selected_region:
            QMessageBox.warning(self, "Warning", "Please select a skill bar region first")
            self.tab_widget.setCurrentIndex(0)  # Switch to capture tab
            return
        
        if not self.visual_system.class_manager.current_class:
            QMessageBox.warning(self, "Warning", "Please select a character class first")
            return
        
        # Initialize visual system for current class
        try:
            skill_bar_regions = [self.selected_region]
            success = self.visual_system.initialize_class(
                self.visual_system.class_manager.current_class,
                skill_bar_regions
            )
            
            if not success:
                QMessageBox.critical(self, "Error", "Failed to initialize visual system")
                return
            
            # Update detection settings
            detection_settings = self.visual_system.class_manager.get_current_profile().detection_settings
            detection_settings.template_threshold = self.accuracy_slider.value() / 100.0
            
            # Start detection thread
            self.detection_thread = SkillBarDetectionThread(
                self.visual_system, self.selected_region, self
            )
            self.detection_thread.detection_progress.connect(self.on_detection_progress)
            self.detection_thread.detection_result.connect(self.on_detection_result)
            self.detection_thread.detection_error.connect(self.on_detection_error)
            
            self.progress_bar.setVisible(True)
            self.detect_btn.setEnabled(False)
            self.status_label.setText("Detecting skills...")
            
            self.detection_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Detection setup failed: {e}")
    
    @pyqtSlot(int)
    def on_detection_progress(self, progress):
        """Handle detection progress update"""
        self.progress_bar.setValue(progress)
    
    @pyqtSlot(object)
    def on_detection_result(self, result):
        """Handle detection completion"""
        self.progress_bar.setVisible(False)
        self.detect_btn.setEnabled(True)
        
        mapping = result['mapping']
        results = result['results']
        skills_found = result['skills_found']
        
        self.skill_bar_mapping = mapping
        self.detection_results = results
        
        # Update UI
        self.results_summary.setText(f"✅ Detection completed! Found {skills_found} skills")
        
        # Update results text
        results_text = f"Detection Results:\n"
        results_text += f"Skills detected: {skills_found}\n"
        results_text += f"Total slots scanned: {len(mapping.slot_regions)}\n\n"
        
        for slot_index, detection_result in results.items():
            if detection_result.detected_skill:
                skill = detection_result.detected_skill
                confidence = detection_result.confidence
                results_text += f"Slot {slot_index + 1}: {skill.name} ({confidence:.1%} confidence)\n"
        
        self.results_text.setText(results_text)
        self.update_summary()
        self.status_label.setText(f"Detection completed - {skills_found} skills found")
    
    @pyqtSlot(str)
    def on_detection_error(self, error):
        """Handle detection error"""
        self.progress_bar.setVisible(False)
        self.detect_btn.setEnabled(True)
        
        self.results_summary.setText(f"❌ Detection failed: {error}")
        self.results_text.setText(f"Error: {error}")
        self.status_label.setText("Detection failed")
    
    def update_summary(self):
        """Update the configuration summary"""
        try:
            if self.selected_region:
                x, y, w, h = self.selected_region
                self.summary_region_label.setText(f"({x}, {y}, {w}, {h})")
            
            self.summary_slots_label.setText(str(self.slots_spin.value()))
            self.summary_class_label.setText(self.class_combo.currentText())
            
            detected_count = len(self.detection_results) if self.detection_results else 0
            self.summary_detected_label.setText(str(detected_count))
            
        except Exception as e:
            self.status_label.setText(f"Summary update failed: {e}")
    
    def test_detection(self):
        """Test the current detection setup"""
        if not self.skill_bar_mapping:
            QMessageBox.warning(self, "Warning", "Please run detection first")
            return
        
        QMessageBox.information(
            self, "Test Detection",
            f"Detection test would be performed here.\n"
            f"Skills found: {len(self.detection_results)}\n"
            f"Skill bar region: {self.selected_region}"
        )
    
    def test_execution(self):
        """Test skill execution"""
        if not self.detection_results:
            QMessageBox.warning(self, "Warning", "Please run detection first")
            return
        
        QMessageBox.information(
            self, "Test Execution",
            "Execution test would be performed here.\n"
            "This would simulate pressing skill keys."
        )
    
    def save_preset(self):
        """Save current configuration as preset"""
        QMessageBox.information(
            self, "Save Preset",
            "Preset saving not implemented yet."
        )
    
    def apply_configuration(self):
        """Apply the current configuration"""
        if not self.selected_region:
            QMessageBox.warning(self, "Warning", "Please configure a skill bar region first")
            return
        
        try:
            # Emit the selected region
            self.region_selected.emit(self.selected_region)
            
            # Show success message
            QMessageBox.information(
                self, "Success",
                f"Skill bar configuration applied successfully!\n\n"
                f"Region: {self.selected_region}\n"
                f"Slots: {self.slots_spin.value()}\n"
                f"Class: {self.class_combo.currentText()}\n"
                f"Skills detected: {len(self.detection_results)}"
            )
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply configuration: {e}")
    
    def closeEvent(self, event):
        """Handle close event"""
        # Stop any running detection
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
            self.detection_thread.wait(1000)
        
        # Stop auto-refresh
        self.refresh_timer.stop()
        
        event.accept()