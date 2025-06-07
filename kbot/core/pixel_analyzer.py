# kbot/core/pixel_analyzer.py

import numpy as np
import re
import time
import win32gui
import win32ui
import win32con
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageFont
import pytesseract
from utils.exceptions import AnalysisError
from utils.logger import BotLogger

# Configura la ruta a Tesseract si no está en el PATH del sistema
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PixelAnalyzer:
    """
    Maneja la captura de pantalla y el análisis de píxeles para el juego, utilizando un método robusto
    para capturar el contenido de la ventana incluso cuando está en segundo plano.
    """
    
    def __init__(self, logger: Optional[BotLogger] = None):
        """
        Inicializa el PixelAnalyzer.
        """
        # --- CORRECCIÓN CLAVE: Se inicializa el logger aquí ---
        # Si se pasa un logger, lo usa. Si no, crea uno por defecto.
        self.logger = logger or BotLogger("PixelAnalyzer")
        
        # El HWND de la ventana objetivo es ahora la pieza central de información.
        self.target_hwnd: Optional[int] = None
        
        # Mapeos y umbrales de configuración.
        self.char_map = { 'J': 'Z', 'i': 'l', '1': 'l', '0': 'O', '5': 'S', '8': 'B', ' ': '' }
        self.color_thresholds = {
            'hp': {'r_min': 150, 'g_max': 100, 'b_max': 100},
            'mp': {'b_min': 150, 'r_max': 100, 'g_max': 100},
            'bright_threshold': 200
        }

    def set_target_window(self, hwnd: int):
        """
        Establece el handle (HWND) de la ventana que se va a analizar.
        Este método es el punto de entrada para configurar el analizador.
        """
        self.target_hwnd = hwnd

    def capture_screen(self) -> Image.Image:
        """
        Captura el contenido de la ventana objetivo usando la API de win32,
        lo que permite la captura incluso si la ventana está en segundo plano.
        """
        if not self.target_hwnd:
            raise AnalysisError("El handle (HWND) de la ventana objetivo no está configurado para PixelAnalyzer.")

        try:
            # Obtener las dimensiones del área cliente de la ventana (sin bordes ni barra de título)
            left, top, right, bottom = win32gui.GetClientRect(self.target_hwnd)
            width = right - left
            height = bottom - top

            if width <= 0 or height <= 0:
                raise AnalysisError(f"Dimensiones de ventana inválidas: {width}x{height}. ¿Está minimizada?")

            # Obtener el contexto de dispositivo (DC) de la ventana
            hwndDC = win32gui.GetWindowDC(self.target_hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()

            # Crear un mapa de bits en memoria para guardar la imagen
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)

            # Copiar los datos de píxeles de la ventana a nuestro mapa de bits en memoria.
            # Esta es la operación clave que funciona en segundo plano.
            saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)

            # Convertir el mapa de bits a un objeto de imagen de la librería Pillow (PIL)
            bmpinfo = saveBitMap.GetInfo()
            bmpstr = saveBitMap.GetBitmapBits(True)
            im = Image.frombuffer('RGB', (bmpinfo['bmWidth'], bmpinfo['bmHeight']), bmpstr, 'raw', 'BGRX', 0, 1)

            return im
        except Exception as e:
            raise AnalysisError(f"Fallo al capturar contenido de la ventana vía win32 API: {e}")
        finally:
            # Es crucial liberar todos los manejadores de Windows para evitar fugas de memoria.
            if 'saveDC' in locals() and saveDC: saveDC.DeleteDC()
            if 'mfcDC' in locals() and mfcDC: mfcDC.DeleteDC()
            if 'hwndDC' in locals() and hwndDC: win32gui.ReleaseDC(self.target_hwnd, hwndDC)
            if 'saveBitMap' in locals() and saveBitMap: win32gui.DeleteObject(saveBitMap.GetHandle())

    def analyze_vitals(self, regions: Dict[str, Tuple[int, int, int, int]]):
        """Obtiene el estado actual de HP, MP y objetivo usando el método de captura en segundo plano."""
        try:
            img = self.capture_screen()
            
            hp_pixels = self.get_region_pixels(img, regions['hp'])
            mp_pixels = self.get_region_pixels(img, regions['mp'])
            target_pixels = self.get_region_pixels(img, regions['target'])
            
            hp_percent = self.calculate_health_percentage(hp_pixels, 'hp')
            mp_percent = self.calculate_health_percentage(mp_pixels, 'mp')
            target_health = self.calculate_health_percentage(target_pixels, 'target')
            target_exists = target_health > 5

            target_name = ""
            if target_exists:
                target_name = self.extract_target_name_from_image(img, regions['target_name'])

            return {
                'hp': hp_percent, 'mp': mp_percent, 'target_exists': target_exists,
                'target_health': target_health, 'target_name': target_name,
                'timestamp': self._get_timestamp()
            }
        except Exception as e:
            # Con el logger ya inicializado, esta línea ahora funciona correctamente.
            self.logger.error(f"El análisis de vitales falló: {e}")
            return {
                'hp': 100, 'mp': 100, 'target_exists': False, 
                'target_health': 0, 'target_name': '', 'timestamp': self._get_timestamp()
            }

    # --- MÉTODOS RESTAURADOS Y FUNCIONALES ---

    def create_debug_image(self, regions: Dict[str, Tuple[int, int, int, int]]) -> Image.Image:
        """Crea una imagen de prueba con las regiones marcadas para depuración."""
        try:
            img = self.capture_screen()
            draw = ImageDraw.Draw(img)
            region_colors = {"hp": "red", "mp": "blue", "target": "green", "target_name": "yellow"}
            
            for name, region in regions.items():
                color = region_colors.get(name, "white")
                draw.rectangle(region, outline=color, width=2)
                x1, y1, _, _ = region
                label = f"{name.upper()}: {region}"
                try:
                    font = ImageFont.load_default()
                    draw.text((x1, y1 - 15), label, fill=color, font=font)
                except IOError: # Fallback si la fuente por defecto no se encuentra
                    draw.text((x1, y1 - 15), label, fill=color)
            return img
        except Exception as e:
            raise AnalysisError(f"Fallo al crear la imagen de depuración: {e}")

    def test_ocr_accuracy(self, name_region: Tuple[int, int, int, int]) -> Dict[str, any]:
        """Prueba la precisión del OCR y devuelve información de depuración."""
        try:
            img = self.capture_screen()
            name_img = img.crop(name_region)
            processed_img = self.preprocess_name_image(name_img)
            extracted_name = self.extract_target_name_from_image(img, name_region)
            return {
                'original_image': name_img, 'processed_image': processed_img,
                'extracted_name': extracted_name, 'region_coords': name_region,
                'success': bool(extracted_name)
            }
        except Exception as e:
            raise AnalysisError(f"La prueba de OCR falló: {e}")
            
    # --- MÉTODOS AUXILIARES (SIN CAMBIOS) ---

    def get_region_pixels(self, img: Image.Image, region: Tuple[int, int, int, int]) -> np.ndarray:
        try:
            return np.array(img.crop(region))
        except Exception as e:
            raise AnalysisError(f"Fallo al extraer píxeles de la región {region}: {e}")

    def extract_target_name_from_image(self, img: Image.Image, name_region: Tuple[int, int, int, int]) -> str:
        try:
            name_img = img.crop(name_region)
            processed_img = self.preprocess_name_image(name_img)
            config = '--psm 7 --oem 3'
            raw_name = pytesseract.image_to_string(processed_img, config=config).strip()
            if len(raw_name) < 3:
                config = '--psm 8 --oem 3 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
                raw_name = pytesseract.image_to_string(processed_img, config=config).strip()
            return self.correct_ocr_mistakes(raw_name)
        except Exception as e:
            raise AnalysisError(f"La extracción de OCR desde la imagen falló: {e}")

    def calculate_health_percentage(self, pixels: np.ndarray, bar_type: str) -> int:
        if pixels.size == 0: return 0
        if len(pixels.shape) != 3 or pixels.shape[2] < 3: return 0
        height, width, _ = pixels.shape
        filled_widths = []
        for y in range(height):
            rightmost = 0
            for x in range(width):
                r, g, b = pixels[y, x][:3]
                if (r > self.color_thresholds['bright_threshold'] and g > self.color_thresholds['bright_threshold'] and b > self.color_thresholds['bright_threshold']): continue
                is_filled = False
                if bar_type in ['hp', 'target']:
                    thresholds = self.color_thresholds['hp']
                    is_filled = (r > thresholds['r_min'] and g < thresholds['g_max'] and b < thresholds['b_max'])
                elif bar_type == 'mp':
                    thresholds = self.color_thresholds['mp']
                    is_filled = (b > thresholds['b_min'] and r < thresholds['r_max'] and g < thresholds['g_max'])
                if is_filled and x > rightmost: rightmost = x
            if rightmost > 0: filled_widths.append((rightmost + 1) / width * 100)
        if filled_widths: return min(100, max(0, int(sum(filled_widths) / len(filled_widths))))
        return 0

    def preprocess_name_image(self, img: Image.Image) -> Image.Image:
        try:
            img = img.convert('L')
            img = ImageOps.autocontrast(img, cutoff=5)
            img = img.point(lambda p: p > 200 and 255)
            img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
            return img.resize((img.width * 2, img.height * 2), Image.LANCZOS)
        except Exception as e:
            raise AnalysisError(f"Fallo al preprocesar la imagen: {e}")

    def correct_ocr_mistakes(self, text: str) -> str:
        corrected = ''.join(self.char_map.get(char, char) for char in text)
        return re.sub(r'[^a-zA-Z]', '', corrected).strip()

    def set_color_thresholds(self, thresholds: Dict[str, Dict[str, int]]) -> None:
        self.color_thresholds.update(thresholds)

    def get_color_thresholds(self) -> Dict[str, Dict[str, int]]:
        return self.color_thresholds.copy()

    @staticmethod
    def _get_timestamp() -> float:
        return time.time()