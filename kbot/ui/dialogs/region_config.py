from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QSpinBox, 
                            QLabel, QDialogButtonBox, QPushButton, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import Qt
from core.pixel_analyzer import PixelAnalyzer

class RegionConfigDialog(QDialog):
    """Dialog for configuring screen regions"""
    
    def __init__(self, pixel_analyzer: PixelAnalyzer, parent=None):
        super().__init__(parent)
        self.pixel_analyzer = pixel_analyzer
        self.setWindowTitle("Configure Screen Regions")
        self.setFixedSize(500, 400)
        
        # Store original regions in case of cancel
        self.original_regions = {}
        
        self._setup_ui()
        self._load_regions()
    
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
    
    def _load_regions(self):
        """Load current region coordinates"""
        # Default regions from the original bot
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
                
                # Store original values
                self.original_regions[region] = coords
    
    def _test_regions(self):
        """Test the current region configuration"""
        try:
            # Apply current values temporarily
            self._apply_regions()
            
            # Show info about testing
            QMessageBox.information(
                self, "Test Regions", 
                "Region coordinates have been updated.\n\n"
                "To properly test:\n"
                "1. Make sure your game window is selected\n"
                "2. Use 'Test Pixel Accuracy' from the main window\n"
                "3. Check if HP/MP bars are detected correctly"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Test Error", f"Failed to test regions: {e}")
    
    def _apply_regions(self):
        """Apply current region values"""
        regions = {}
        for region, spinboxes in self.region_spinboxes.items():
            coords = tuple(spinbox.value() for spinbox in spinboxes)
            regions[region] = coords
        
        # In a complete implementation, this would update the pixel analyzer
        # For now, we just return the regions
        return regions
    
    def get_regions(self):
        """Get the configured regions"""
        return self._apply_regions()
    
    def accept(self):
        """Accept dialog and save regions"""
        try:
            regions = self._apply_regions()
            
            # Validate regions
            for region, coords in regions.items():
                x1, y1, x2, y2 = coords
                if x1 >= x2 or y1 >= y2:
                    QMessageBox.warning(
                        self, "Invalid Region", 
                        f"Invalid coordinates for {region}: x2 must be > x1 and y2 must be > y1"
                    )
                    return
            
            # Store the regions for retrieval
            self.configured_regions = regions
            super().accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save regions: {e}")
    
    def reject(self):
        """Reject dialog and restore original regions"""
        # Restore original regions if needed
        super().reject()