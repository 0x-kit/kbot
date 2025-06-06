from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QSpinBox, 
                            QLabel, QDialogButtonBox, QPushButton, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import Qt

class RegionConfigDialog(QDialog):
    """Dialog for configuring screen regions"""
    
    def __init__(self, bot_engine, parent=None):
        super().__init__(parent)
        self.bot_engine = bot_engine  # Store bot_engine instead of just pixel_analyzer
        self.setWindowTitle("Configure Screen Regions")
        self.setFixedSize(500, 400)
        
        # Store original regions in case of cancel
        self.original_regions = {}
        
        self._setup_ui()
        self._load_current_regions()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Instructions
        instructions = QLabel("""
        Configure the screen regions for HP/MP bars and target detection.
        Coordinates are relative to the selected game window.
        """)
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        # Region configuration
        regions_group = QGroupBox("Region Coordinates")
        regions_layout = QGridLayout(regions_group)
        
        # Headers
        regions_layout.addWidget(QLabel("<b>Region</b>"), 0, 0)
        regions_layout.addWidget(QLabel("<b>X1</b>"), 0, 1)
        regions_layout.addWidget(QLabel("<b>Y1</b>"), 0, 2)
        regions_layout.addWidget(QLabel("<b>X2</b>"), 0, 3)
        regions_layout.addWidget(QLabel("<b>Y2</b>"), 0, 4)
        
        # Create spinboxes for each region
        self.region_spinboxes = {}
        regions = ['hp', 'mp', 'target', 'target_name']
        region_labels = ['HP Bar', 'MP Bar', 'Target Health', 'Target Name']
        
        for i, (region, label) in enumerate(zip(regions, region_labels), 1):
            regions_layout.addWidget(QLabel(label), i, 0)
            
            spinboxes = []
            for j in range(4):  # x1, y1, x2, y2
                spinbox = QSpinBox()
                spinbox.setRange(0, 2000)
                regions_layout.addWidget(spinbox, i, j + 1)
                spinboxes.append(spinbox)
            
            self.region_spinboxes[region] = spinboxes
        
        layout.addWidget(regions_group)
        
        # Test button
        self.test_btn = QPushButton("Test Current Regions")
        self.test_btn.clicked.connect(self._test_regions)
        layout.addWidget(self.test_btn)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_current_regions(self):
        """Load current region coordinates from config"""
        try:
            # Get regions from config manager
            current_regions = self.bot_engine.config_manager.get_regions()
            
            # Store original values for cancel
            self.original_regions = current_regions.copy()
            
            # Load values into spinboxes
            for region, coords in current_regions.items():
                if region in self.region_spinboxes:
                    spinboxes = self.region_spinboxes[region]
                    for i, coord in enumerate(coords):
                        spinboxes[i].setValue(coord)
            
            print(f"Loaded regions: {current_regions}")  # Debug
            
        except Exception as e:
            QMessageBox.warning(self, "Load Error", f"Failed to load current regions: {e}")
            # Fall back to defaults if loading fails
            self._load_default_regions()
    
    def _load_default_regions(self):
        """Load default regions if current ones can't be loaded"""
        default_regions = {
            'hp': (4, 20, 168, 36),
            'mp': (4, 36, 168, 51),
            'target': (4, 66, 168, 75),
            'target_name': (4, 55, 168, 70)
        }
        
        for region, coords in default_regions.items():
            if region in self.region_spinboxes:
                spinboxes = self.region_spinboxes[region]
                for i, coord in enumerate(coords):
                    spinboxes[i].setValue(coord)
    
    def _test_regions(self):
        """Test the current region configuration"""
        try:
            # Get current values from spinboxes
            regions = self._get_current_regions()
            
            # Temporarily update the pixel analyzer regions for testing
            temp_regions = self.bot_engine.config_manager.get_regions()
            
            # Update config temporarily
            self.bot_engine.config_manager.set_regions(regions)
            
            # Show info about testing
            QMessageBox.information(
                self, "Test Regions", 
                "Region coordinates have been temporarily updated.\n\n"
                "To test:\n"
                "1. Click OK to close this dialog\n"
                "2. Use 'Test Pixel Accuracy' from the main window\n"
                "3. Check if HP/MP bars are detected correctly\n"
                "4. Come back here to adjust if needed"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Failed to test regions: {e}")
    
    def _get_current_regions(self):
        """Get current region values from spinboxes"""
        regions = {}
        for region, spinboxes in self.region_spinboxes.items():
            coords = tuple(spinbox.value() for spinbox in spinboxes)
            regions[region] = coords
        return regions
    
    def accept(self):
        """Accept dialog and save regions"""
        try:
            regions = self._get_current_regions()
            
            # Validate regions
            for region, coords in regions.items():
                x1, y1, x2, y2 = coords
                if x1 >= x2 or y1 >= y2:
                    QMessageBox.warning(
                        self, "Invalid Region", 
                        f"Invalid coordinates for {region}:\n"
                        f"X2 ({x2}) must be greater than X1 ({x1})\n"
                        f"Y2 ({y2}) must be greater than Y1 ({y1})"
                    )
                    return
            
            # Save to config manager
            self.bot_engine.config_manager.set_regions(regions)
            
            # Save config to file
            self.bot_engine.config_manager.save_config()
            
            print(f"Saved regions: {regions}")  # Debug
            
            QMessageBox.information(
                self, "Success", 
                "Region coordinates saved successfully!\n"
                "Use 'Test Pixel Accuracy' to verify the new settings."
            )
            
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save regions: {e}")
    
    def reject(self):
        """Reject dialog and restore original regions"""
        try:
            # Restore original regions if they were changed during testing
            if self.original_regions:
                self.bot_engine.config_manager.set_regions(self.original_regions)
                print("Restored original regions on cancel")
        except Exception as e:
            print(f"Error restoring regions on cancel: {e}")
        
        super().reject()
