# core/pixel_analyzer.py
import numpy as np
import re
from typing import Dict, Tuple, Optional
from PIL import ImageGrab, Image, ImageDraw, ImageOps, ImageFilter
import pytesseract
from utils.exceptions import AnalysisError

# Set Tesseract path if needed (uncomment and modify for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PixelAnalyzer:
    """Handles screen capture and pixel analysis for the game"""
    
    def __init__(self):
        # Default monitoring rectangle (top-left 300x150 region)
        self.monitor_rect: Tuple[int, int, int, int] = (0, 0, 300, 150)
        
        # Character mapping for common OCR misreads
        self.char_map = {
            'J': 'Z',  # Map J to Z
            'i': 'l',  # Map i to l
            '1': 'l',  # Map 1 to l
            '0': 'O',  # Map 0 to O
            '5': 'S',  # Map 5 to S
            '8': 'B',  # Map 8 to B
            ' ': ''     # Remove spaces
        }
        
        # Health bar color thresholds
        self.color_thresholds = {
            'hp': {'r_min': 150, 'g_max': 100, 'b_max': 100},
            'mp': {'b_min': 150, 'r_max': 100, 'g_max': 100},
            'bright_threshold': 200  # Skip bright pixels (text/highlights)
        }


    
    def set_monitor_rect(self, rect: Tuple[int, int, int, int]) -> None:
        """Set the window rectangle to monitor"""
        if len(rect) != 4:
            raise AnalysisError("Monitor rectangle must have 4 coordinates")
        
        if any(coord < 0 for coord in rect):
            raise AnalysisError("Monitor rectangle coordinates must be non-negative")
        
        self.monitor_rect = rect
    
    def capture_screen(self) -> Image.Image:
        """Capture the game screen region"""
        try:
            return ImageGrab.grab(bbox=self.monitor_rect)
        except Exception as e:
            raise AnalysisError(f"Failed to capture screen: {e}")
    
    def get_region_pixels(self, img: Image.Image, region: Tuple[int, int, int, int]) -> np.ndarray:
        """Extract pixels for a specific region"""
        try:
            x1, y1, x2, y2 = region
            region_img = img.crop((x1, y1, x2, y2))
            return np.array(region_img)
        except Exception as e:
            raise AnalysisError(f"Failed to extract region pixels: {e}")
    
    def calculate_health_percentage(self, pixels: np.ndarray, bar_type: str) -> int:
        """Calculate health percentage using horizontal scanning"""
        if pixels.size == 0:
            return 0
        
        if len(pixels.shape) != 3 or pixels.shape[2] != 3:
            raise AnalysisError("Invalid pixel array format")
        
        height, width, _ = pixels.shape
        filled_widths = []
        
        for y in range(height):
            rightmost = 0
            for x in range(width):
                r, g, b = pixels[y, x]
                
                # Skip bright pixels (text and highlights)
                if (r > self.color_thresholds['bright_threshold'] and 
                    g > self.color_thresholds['bright_threshold'] and 
                    b > self.color_thresholds['bright_threshold']):
                    continue
                
                # Check pixel based on bar type
                is_filled = False
                if bar_type in ['hp', 'target']:
                    # Red bars: high R, low G, low B
                    thresholds = self.color_thresholds['hp']
                    is_filled = (r > thresholds['r_min'] and 
                               g < thresholds['g_max'] and 
                               b < thresholds['b_max'])
                elif bar_type == 'mp':
                    # Blue bars: low R, low G, high B
                    thresholds = self.color_thresholds['mp']
                    is_filled = (b > thresholds['b_min'] and 
                               r < thresholds['r_max'] and 
                               g < thresholds['g_max'])
                
                if is_filled and x > rightmost:
                    rightmost = x
            
            # Calculate fill percentage for this row
            if rightmost > 0:
                row_fill = (rightmost + 1) / width * 100
                filled_widths.append(row_fill)
        
        # Average fill across all rows
        if filled_widths:
            avg_fill = sum(filled_widths) / len(filled_widths)
            return min(100, max(0, int(avg_fill)))
        return 0
    
    def detect_target_exists(self, pixels: np.ndarray) -> bool:
        """Check if target exists and is alive"""
        health_percent = self.calculate_health_percentage(pixels, 'target')
        return health_percent > 5
    
    def preprocess_name_image(self, img: Image.Image) -> Image.Image:
        """Enhance image for better OCR results"""
        try:
            # Convert to grayscale
            img = img.convert('L')
            
            # Increase contrast
            img = ImageOps.autocontrast(img, cutoff=5)
            
            # Apply threshold to create pure black and white
            threshold = 200
            img = img.point(lambda p: p > threshold and 255)
            
            # Apply slight blur to reduce noise
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
            
            # Scale up for better recognition
            img = img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
            
            return img
        except Exception as e:
            raise AnalysisError(f"Failed to preprocess image: {e}")
    
    def correct_ocr_mistakes(self, text: str) -> str:
        """Fix common OCR misreads"""
        # Apply character mapping
        corrected = ''.join(self.char_map.get(char, char) for char in text)
        
        # Remove non-alphabetic characters except spaces
        corrected = re.sub(r'[^a-zA-Z ]', '', corrected)
        
        # Capitalize properly
        corrected = corrected.title()
        
        return corrected.strip()
    
    def extract_target_name(self, name_region: Tuple[int, int, int, int]) -> str:
        """Extract target name using enhanced OCR"""
        try:
            img = self.capture_screen()
            x1, y1, x2, y2 = name_region
            name_img = img.crop((x1, y1, x2, y2))
            
            # Preprocess image
            processed_img = self.preprocess_name_image(name_img)
            
            # Use Tesseract to extract text
            # First pass with default config
            name = pytesseract.image_to_string(
                processed_img, 
                config='--psm 7 --oem 3'
            ).strip()
            
            # If first pass doesn't give good results, try more aggressive config
            if len(name) < 3 or not name.isalpha():
                name = pytesseract.image_to_string(
                    processed_img, 
                    config='--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                ).strip()
            
            # Correct common OCR mistakes
            name = self.correct_ocr_mistakes(name)
            
            return name
        except Exception as e:
            raise AnalysisError(f"OCR extraction failed: {e}")
    
    def analyze_vitals(self, regions):
        """Get current HP, MP and target status using optimized UI capture"""
        try:
            # Use the optimized UI-only capture
            img = self.capture_ui_only()
            
            hp_pixels = self.get_region_pixels(img, regions['hp'])
            mp_pixels = self.get_region_pixels(img, regions['mp'])
            target_pixels = self.get_region_pixels(img, regions['target'])
            
            # Calculate health percentages
            hp_percent = self.calculate_health_percentage(hp_pixels, 'hp')
            mp_percent = self.calculate_health_percentage(mp_pixels, 'mp')
            target_health = self.calculate_health_percentage(target_pixels, 'target')
            target_exists = self.detect_target_exists(target_pixels)
            
            # Extract target name if target exists
            target_name = ""
            if target_exists:
                target_name = self.extract_target_name(regions['target_name'])
            
            return {
                'hp': hp_percent,
                'mp': mp_percent,
                'target_exists': target_exists,
                'target_health': target_health,
                'target_name': target_name,
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            raise AnalysisError(f"Vitals analysis failed: {e}")
        
    def create_debug_image(self, regions: Dict[str, Tuple[int, int, int, int]]) -> Image.Image:
        """Create test image with regions marked for debugging"""
        try:
            img = self.capture_screen()
            draw = ImageDraw.Draw(img)
            
            # Define colors for different regions
            region_colors = {
                "hp": "red",
                "mp": "blue", 
                "target": "green",
                "target_name": "yellow"
            }
            
            # Draw rectangles around monitored regions
            for name, region in regions.items():
                color = region_colors.get(name, "white")
                draw.rectangle(region, outline=color, width=2)
                
                # Add coordinate labels
                x1, y1, x2, y2 = region
                label = f"{name.upper()}: ({x1},{y1})-({x2},{y2})"
                draw.text((x1, y1 - 15), label, fill=color)
            
            return img
        except Exception as e:
            raise AnalysisError(f"Failed to create debug image: {e}")
    
    def set_color_thresholds(self, thresholds: Dict[str, Dict[str, int]]) -> None:
        """Update color detection thresholds"""
        self.color_thresholds.update(thresholds)
    
    def get_color_thresholds(self) -> Dict[str, Dict[str, int]]:
        """Get current color detection thresholds"""
        return self.color_thresholds.copy()
    
    @staticmethod
    def _get_timestamp() -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def test_ocr_accuracy(self, name_region: Tuple[int, int, int, int]) -> Dict[str, any]:
        """Test OCR accuracy and return debug information"""
        try:
            img = self.capture_screen()
            x1, y1, x2, y2 = name_region
            name_img = img.crop((x1, y1, x2, y2))
            
            # Get both original and processed images
            processed_img = self.preprocess_name_image(name_img)
            
            # Extract text
            extracted_name = self.extract_target_name(name_region)
            
            return {
                'original_image': name_img,
                'processed_image': processed_img,
                'extracted_name': extracted_name,
                'region_coords': name_region,
                'success': bool(extracted_name)
            }
        except Exception as e:
            raise AnalysisError(f"OCR test failed: {e}")
        
    def set_ui_capture_region(self, window_rect):
        """Set capture region to only include the UI area (top-left corner)"""
        # UI is always in top-left corner, typically first 200x100 pixels
        x, y, right, bottom = window_rect
        
        # Define UI region - adjust these values if needed
        ui_width = 200   # Width of UI area
        ui_height = 100  # Height of UI area
        
        # Set monitor rect to only capture UI area
        self.monitor_rect = (x, y, x + ui_width, y + ui_height)

    def capture_ui_only(self):
        """Capture only the UI region (top-left corner)"""
        try:
            return ImageGrab.grab(bbox=self.monitor_rect)
        except Exception as e:
            raise AnalysisError(f"Failed to capture UI region: {e}")

    def create_debug_image_ui(self, regions):
        """Create debug image showing only UI area with regions marked"""
        try:
            img = self.capture_ui_only()
            draw = ImageDraw.Draw(img)
            
            # Define colors for different regions
            region_colors = {
                "hp": "red",
                "mp": "blue", 
                "target": "green",
                "target_name": "yellow"
            }
            
            # Draw rectangles around monitored regions
            for name, region in regions.items():
                color = region_colors.get(name, "white")
                draw.rectangle(region, outline=color, width=2)
                
                # Add coordinate labels
                x1, y1, x2, y2 = region
                label = f"{name.upper()}"
                draw.text((x1, y1 - 15), label, fill=color)
            
            return img
        except Exception as e:
            raise AnalysisError(f"Failed to create debug image: {e}")

        
        