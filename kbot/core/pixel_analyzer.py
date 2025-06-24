# kbot/core/pixel_analyzer.py

import numpy as np
import re
import time
import hashlib
import win32gui
import win32ui
import win32con
from functools import lru_cache
from typing import Dict, Tuple, Optional
from collections import OrderedDict
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont
import pytesseract
import cv2
from utils.exceptions import AnalysisError
from utils.logger import BotLogger

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


class LRUCache:
    """Simple LRU cache implementation for OCR results"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = OrderedDict()
    
    def get(self, key: str) -> Optional[str]:
        if key in self.cache:
            # Move to end (most recently used)
            value = self.cache.pop(key)
            self.cache[key] = value
            return value
        return None
    
    def put(self, key: str, value: str) -> None:
        if key in self.cache:
            # Update existing key
            self.cache.pop(key)
        elif len(self.cache) >= self.max_size:
            # Remove least recently used
            self.cache.popitem(last=False)
        
        self.cache[key] = value
    
    def clear(self) -> None:
        self.cache.clear()


class PixelAnalyzer:
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("PixelAnalyzer")
        self.target_hwnd: Optional[int] = None
        
        # Performance optimization caches
        self._image_hash_cache = {}  # Hash -> processed results
        self._ocr_cache = LRUCache(max_size=50)  # OCR results cache
        self._last_capture_time = 0
        self._last_image_hash = None
        self._last_target_name = ""
        self._stable_target_count = 0
        self._capture_cache = None  # Cache for screen captures
        self._cache_timestamp = 0
        
        # Character correction map and color thresholds
        self.char_map = { 'J': 'Z', 'i': 'l', '1': 'l', '0': 'O', '5': 'S', '8': 'B', ' ': '' }
        self.color_thresholds = {
            'hp': {'r_min': 150, 'g_max': 100, 'b_max': 100},
            'mp': {'b_min': 150, 'r_max': 100, 'g_max': 100},
            'bright_threshold': 200
        }

    def _calculate_image_hash(self, img: Image.Image) -> str:
        """Calculate MD5 hash of image for caching purposes"""
        try:
            img_bytes = img.tobytes()
            return hashlib.md5(img_bytes).hexdigest()
        except Exception:
            return str(time.time())  # Fallback to timestamp

    def _get_cached_capture(self, cache_duration: float = 0.1) -> Optional[Image.Image]:
        """Return cached screen capture if within cache duration"""
        current_time = time.time()
        if (self._capture_cache is not None and 
            current_time - self._cache_timestamp < cache_duration):
            return self._capture_cache
        return None

    def _cache_capture(self, img: Image.Image) -> None:
        """Cache screen capture with timestamp"""
        self._capture_cache = img
        self._cache_timestamp = time.time()

    def _cleanup_cache(self) -> None:
        """Clean up memory-intensive cached objects"""
        try:
            # Clear old cached captures
            if self._capture_cache is not None:
                current_time = time.time()
                if current_time - self._cache_timestamp > 1.0:  # 1 second expiry
                    self._capture_cache = None
                    
            # Limit image hash cache size
            if len(self._image_hash_cache) > 20:
                # Remove oldest entries
                keys_to_remove = list(self._image_hash_cache.keys())[:-10]
                for key in keys_to_remove:
                    del self._image_hash_cache[key]
                    
        except Exception as e:
            self.logger.debug(f"Cache cleanup error: {e}")

    def preprocess_name_image(self, img: Image.Image) -> Image.Image:
        """
        Preprocesa la imagen usando filtrado de color HSV para aislar el texto.
        """
        try:
            open_cv_image = np.array(img); open_cv_image = open_cv_image[:, :, ::-1].copy()
            scale_factor = 4
            resized = cv2.resize(open_cv_image, (int(img.width*scale_factor), int(img.height*scale_factor)), interpolation=cv2.INTER_LANCZOS4)
            hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            lower_white = np.array([0, 0, 150]); upper_white = np.array([179, 50, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            kernel = np.ones((2,2), np.uint8)
            dilated_mask = cv2.dilate(mask, kernel, iterations=1)
            return Image.fromarray(dilated_mask)
        except Exception as e:
            self.logger.error(f"Fallo en el preprocesamiento de imagen para OCR: {e}")
            return img

    def extract_target_name_from_image(self, img: Image.Image, name_region: Tuple[int, int, int, int]) -> str:
        """
        Optimized OCR extraction with caching and hash checking to avoid reprocessing identical images.
        """
        try:
            # Crop the name region first
            name_img = img.crop(name_region)
            
            # Calculate hash of the cropped image for caching
            img_hash = self._calculate_image_hash(name_img)
            
            # Check OCR cache first
            cached_result = self._ocr_cache.get(img_hash)
            if cached_result is not None:
                return cached_result
            
            # Check if target name has been stable (optimization for stable targets)
            if (self._last_image_hash == img_hash and 
                self._last_target_name and 
                self._stable_target_count < 10):  # Skip OCR for stable targets
                self._stable_target_count += 1
                return self._last_target_name
            
            # Reset stable count if image changed
            if self._last_image_hash != img_hash:
                self._stable_target_count = 0
            
            # Perform OCR processing
            processed_img = self.preprocess_name_image(name_img)
            custom_config = r'--psm 8 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            raw_name = pytesseract.image_to_string(processed_img, config=custom_config).strip()
            corrected_name = self.correct_ocr_mistakes(raw_name)
            
            # Cache the result
            self._ocr_cache.put(img_hash, corrected_name)
            
            # Update tracking variables
            self._last_image_hash = img_hash
            self._last_target_name = corrected_name
            
            # Clean up processed image to free memory
            del processed_img
            
            return corrected_name
            
        except Exception as e:
            self.logger.error(f"OCR extraction failed: {e}")
            return ""

    def analyze_vitals(self, regions: Dict[str, Tuple[int, int, int, int]]):
        """
        Optimized vitals analysis with caching and reduced OCR frequency.
        """
        try:
            # Try to use cached capture first
            img = self._get_cached_capture()
            if img is None:
                img = self.capture_screen()
                self._cache_capture(img)
            
            # Calculate vitals from pixel data
            hp_pixels = self.get_region_pixels(img, regions['hp'])
            mp_pixels = self.get_region_pixels(img, regions['mp'])
            target_pixels = self.get_region_pixels(img, regions['target'])
            
            hp_percent = self.calculate_health_percentage(hp_pixels, 'hp')
            mp_percent = self.calculate_health_percentage(mp_pixels, 'mp')
            target_health = self.calculate_health_percentage(target_pixels, 'target')
            target_exists = target_health > 5
            
            target_name = ""
            if target_exists:
                # Only run OCR if we have a target
                target_name = self.extract_target_name_from_image(img, regions['target_name'])
            else:
                # Reset tracking when no target
                self._last_target_name = ""
                self._stable_target_count = 0
            
            # Periodic cache cleanup to prevent memory leaks
            if time.time() - self._last_capture_time > 5.0:
                self._cleanup_cache()
                self._last_capture_time = time.time()
            
            # Clean up pixel arrays
            del hp_pixels, mp_pixels, target_pixels
            
            return {
                'hp': hp_percent, 
                'mp': mp_percent, 
                'target_exists': target_exists, 
                'target_health': target_health, 
                'target_name': target_name, 
                'timestamp': self._get_timestamp()
            }
            
        except Exception as e:
            self.logger.error(f"Vitals analysis failed: {e}")
            return {
                'hp': 100, 
                'mp': 100, 
                'target_exists': False, 
                'target_health': 0, 
                'target_name': '', 
                'timestamp': self._get_timestamp()
            }

    def test_ocr_accuracy(self, name_region: Tuple[int, int, int, int]) -> Dict[str, any]:
        """
        Prueba el OCR. AHORA usa la misma lógica unificada.
        """
        try:
            full_window_img = self.capture_screen()
            
            # Recortamos la porción para la imagen "Original"
            name_img_original = full_window_img.crop(name_region)
            
            # Obtenemos la imagen procesada llamando a la misma función que usa analyze_vitals
            processed_img = self.preprocess_name_image(name_img_original)
            
            # Extraemos el texto de la imagen ya procesada
            custom_config = r'--psm 8 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            extracted_name_raw = pytesseract.image_to_string(processed_img, config=custom_config).strip()
            extracted_name = self.correct_ocr_mistakes(extracted_name_raw)

            return {
                'original_image': name_img_original,
                'processed_image': processed_img,
                'extracted_name': extracted_name,
                'region_coords': name_region,
                'success': bool(extracted_name)
            }
        except Exception as e:
            raise AnalysisError(f"La prueba de OCR falló: {e}")

    # --- El resto de métodos no cambian ---
    def set_target_window(self, hwnd: int): self.target_hwnd = hwnd
    def capture_screen(self, region: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        """Optimized screen capture with proper resource cleanup"""
        if not self.target_hwnd: 
            raise AnalysisError("Target window handle (HWND) not configured.")
        
        hwndDC = mfcDC = saveDC = saveBitMap = None
        try:
            # Calculate capture dimensions
            if region: 
                left, top, right, bottom = region
                width = right - left
                height = bottom - top
                src_pos = (left, top)
            else: 
                left, top, right, bottom = win32gui.GetClientRect(self.target_hwnd)
                width = right - left
                height = bottom - top
                src_pos = (0, 0)
            
            if width <= 0 or height <= 0: 
                raise AnalysisError(f"Invalid capture dimensions: {width}x{height}")
            
            # Create device contexts and bitmap
            hwndDC = win32gui.GetWindowDC(self.target_hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            saveBitMap = win32ui.CreateBitmap()
            
            # Setup bitmap and perform screen capture
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            saveDC.BitBlt((0, 0), (width, height), mfcDC, src_pos, win32con.SRCCOPY)
            
            # Extract bitmap data and create image
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            img = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), 
                                 bmpstr, 'raw', 'BGRX', 0, 1)
            
            return img
            
        except Exception as e:
            raise AnalysisError(f"Screen capture failed: {e}")
        finally:
            # Ensure all resources are properly cleaned up
            try:
                if saveDC: saveDC.DeleteDC()
                if mfcDC: mfcDC.DeleteDC()
                if hwndDC: win32gui.ReleaseDC(self.target_hwnd, hwndDC)
                if saveBitMap: win32gui.DeleteObject(saveBitMap.GetHandle())
            except Exception as cleanup_error:
                self.logger.debug(f"Resource cleanup warning: {cleanup_error}")
    def create_debug_image(self, regions: Dict[str, Tuple[int, int, int, int]], capture_area: Optional[Tuple[int, int, int, int]] = None) -> Image.Image:
        try:
            img = self.capture_screen(region=capture_area); draw = ImageDraw.Draw(img)
            region_colors = {"hp": "red", "mp": "blue", "target": "green", "target_name": "yellow"}
            offset_x = capture_area[0] if capture_area else 0; offset_y = capture_area[1] if capture_area else 0
            for name, region_coords in regions.items():
                if capture_area and (region_coords[0] < offset_x or region_coords[1] < offset_y): continue
                x1, y1, x2, y2 = region_coords
                relative_region = (x1 - offset_x, y1 - offset_y, x2 - offset_x, y2 - offset_y)
                color = region_colors.get(name, "white"); draw.rectangle(relative_region, outline=color, width=1)
                label = f"{name.upper()}"; draw.text((relative_region[0], relative_region[1] - 12), label, fill=color)
            return img
        except Exception as e: raise AnalysisError(f"Fallo al crear la imagen de depuración: {e}")
    def get_region_pixels(self, img: Image.Image, region: Tuple[int, int, int, int]) -> np.ndarray:
        try: return np.array(img.crop(region))
        except Exception as e: raise AnalysisError(f"Fallo al extraer píxeles de la región {region}: {e}")
    def calculate_health_percentage(self, pixels: np.ndarray, bar_type: str) -> int:
        if pixels.size == 0: return 0
        if len(pixels.shape) != 3 or pixels.shape[2] < 3: return 0
        height, width, _ = pixels.shape; filled_widths = []
        for y in range(height):
            rightmost = 0
            for x in range(width):
                r, g, b = pixels[y, x][:3]
                if (r > self.color_thresholds['bright_threshold'] and g > self.color_thresholds['bright_threshold'] and b > self.color_thresholds['bright_threshold']): continue
                is_filled = False
                if bar_type in ['hp', 'target']: thresholds = self.color_thresholds['hp']; is_filled = (r > thresholds['r_min'] and g < thresholds['g_max'] and b < thresholds['b_max'])
                elif bar_type == 'mp': thresholds = self.color_thresholds['mp']; is_filled = (b > thresholds['b_min'] and r < thresholds['r_max'] and g < thresholds['g_max'])
                if is_filled and x > rightmost: rightmost = x
            if rightmost > 0: filled_widths.append((rightmost + 1) / width * 100)
        if filled_widths: return min(100, max(0, int(sum(filled_widths) / len(filled_widths))))
        return 0
    def correct_ocr_mistakes(self, text: str) -> str:
        corrected = ''.join(self.char_map.get(char, char) for char in text)
        return re.sub(r'[^a-zA-Z]', '', corrected).strip()
    def set_color_thresholds(self, thresholds: Dict[str, Dict[str, int]]): self.color_thresholds.update(thresholds)
    def get_color_thresholds(self) -> Dict[str, Dict[str, int]]: return self.color_thresholds.copy()
    @staticmethod
    def _get_timestamp() -> float: return time.time()