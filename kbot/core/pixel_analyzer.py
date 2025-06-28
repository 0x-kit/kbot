# kbot/core/pixel_analyzer.py

import numpy as np
import re
import time
import win32gui
import win32ui
import win32con
from typing import Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont
import pytesseract
import cv2  # OpenCV es clave aquí
from utils.exceptions import AnalysisError
from utils.logger import BotLogger

# Ya no necesitamos scikit-image
# try:
#     from skimage.metrics import structural_similarity as ssim
#     SCIKIT_AVAILABLE = True
# except ImportError:
#     SCIKIT_AVAILABLE = False

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class PixelAnalyzer:
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("PixelAnalyzer")
        self.target_hwnd: Optional[int] = None
        self._skill_icon_cache: Dict[str, Optional[np.ndarray]] = (
            {}
        )  # Guardaremos iconos como arrays de OpenCV

    def set_target_window(self, hwnd: int):
        self.target_hwnd = hwnd

    def capture_screen(
        self, region: Optional[Tuple[int, int, int, int]] = None
    ) -> Image.Image:
        """
        ✅ CORREGIDO: Captura el área cliente completa o una región específica de ella.
        """
        if not self.target_hwnd:
            raise AnalysisError("Target window handle (HWND) no configurado.")

        try:
            # Obtener el DC del área cliente
            hwnd_dc = win32gui.GetDC(self.target_hwnd)
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Determinar el área a capturar
            if region:
                # La región se da en coordenadas de pantalla. La convertimos a cliente.
                client_left, client_top = win32gui.ClientToScreen(
                    self.target_hwnd, (0, 0)
                )
                x = region[0] - client_left
                y = region[1] - client_top
                width = region[2] - region[0]
                height = region[3] - region[1]
            else:
                # Si no hay región, se captura toda el área cliente.
                left, top, right, bot = win32gui.GetClientRect(self.target_hwnd)
                x, y = 0, 0
                width = right - left
                height = bot - top

            if width <= 0 or height <= 0:
                raise AnalysisError(
                    f"Dimensiones de captura inválidas: {width}x{height}."
                )

            # Crear el bitmap y copiar los píxeles
            save_bitmap = win32ui.CreateBitmap()
            save_bitmap.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bitmap)
            save_dc.BitBlt((0, 0), (width, height), mfc_dc, (x, y), win32con.SRCCOPY)

            # Convertir a imagen PIL
            bmp_str = save_bitmap.GetBitmapBits(True)
            img = Image.frombuffer("RGB", (width, height), bmp_str, "raw", "BGRX", 0, 1)

            # Liberar recursos
            win32gui.DeleteObject(save_bitmap.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.target_hwnd, hwnd_dc)

            return img
        except Exception as e:
            raise AnalysisError(f"Fallo en la captura de pantalla: {e}")

    def _get_skill_icon(self, icon_path: str) -> Optional[np.ndarray]:
        """Carga un icono de skill y lo convierte a formato OpenCV, usando caché."""
        if not icon_path:
            return None
        if icon_path in self._skill_icon_cache:
            return self._skill_icon_cache[icon_path]
        try:
            # Carga con OpenCV directamente
            icon = cv2.imread(icon_path, cv2.IMREAD_GRAYSCALE)
            if icon is None:
                raise FileNotFoundError(f"OpenCV no pudo cargar la imagen: {icon_path}")
            self._skill_icon_cache[icon_path] = icon
            return icon
        except Exception as e:
            self.logger.error(
                f"Icono de skill no encontrado o inválido en la ruta: {e}"
            )
            self._skill_icon_cache[icon_path] = None
            return None

    def is_skill_ready(
        self,
        slot_region: Tuple[int, int, int, int],
        ready_icon_path: str,
        threshold: float,
    ) -> bool:
        """
        ✅ SOLUCIÓN DEFINITIVA: Usa Template Matching de OpenCV para encontrar el icono.
        Es robusto a pequeñas deformaciones de perspectiva.
        """
        template_icon = self._get_skill_icon(ready_icon_path)
        if template_icon is None:
            self.logger.warning(
                f"No se pudo cargar el icono de plantilla {ready_icon_path}. Asumiendo que el skill está listo."
            )
            return True

        try:
            full_capture_pil = self.capture_screen()
            full_capture_cv = cv2.cvtColor(
                np.array(full_capture_pil), cv2.COLOR_RGB2GRAY
            )

            client_left, client_top = win32gui.ClientToScreen(self.target_hwnd, (0, 0))
            x1, y1, x2, y2 = (
                slot_region[0] - client_left,
                slot_region[1] - client_top,
                slot_region[2] - client_left,
                slot_region[3] - client_top,
            )

            # Recorta el área del slot de la captura completa
            slot_image_cv = full_capture_cv[y1:y2, x1:x2]

            if (
                slot_image_cv.shape[0] < template_icon.shape[0]
                or slot_image_cv.shape[1] < template_icon.shape[1]
            ):
                self.logger.warning(
                    "La región del slot es más pequeña que el icono de plantilla. No se puede comparar."
                )
                return True

            # Realiza el template matching
            res = cv2.matchTemplate(slot_image_cv, template_icon, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)

            # Si el valor máximo de coincidencia es alto, significa que el icono "listo" está presente.
            is_ready = max_val >= threshold
            self.logger.debug(
                f"Template matching para {ready_icon_path}: Confianza={max_val:.2f}, Umbral={threshold}, Listo={is_ready}"
            )

            return is_ready

        except Exception as e:
            self.logger.error(f"Error durante el template matching del skill: {e}")
            return True  # En caso de error, es más seguro asumir que está listo.

    def analyze_vitals(self, regions: Dict[str, Tuple[int, int, int, int]]):
        try:
            img = self.capture_screen()
            client_left, client_top = win32gui.ClientToScreen(self.target_hwnd, (0, 0))

            def to_relative(coords):
                return (
                    coords[0] - client_left,
                    coords[1] - client_top,
                    coords[2] - client_left,
                    coords[3] - client_top,
                )

            hp_pixels = np.array(img.crop(to_relative(regions["hp"])))
            mp_pixels = np.array(img.crop(to_relative(regions["mp"])))
            target_pixels = np.array(img.crop(to_relative(regions["target"])))
            hp_percent = self.calculate_health_percentage(hp_pixels, "hp")
            mp_percent = self.calculate_health_percentage(mp_pixels, "mp")
            target_health = self.calculate_health_percentage(target_pixels, "target")
            target_exists = target_health > 5
            target_name = ""
            if target_exists:
                target_name = self.extract_target_name_from_image(
                    img, to_relative(regions["target_name"])
                )
            return {
                "hp": hp_percent,
                "mp": mp_percent,
                "target_exists": target_exists,
                "target_health": target_health,
                "target_name": target_name,
            }
        except Exception as e:
            self.logger.error(f"Análisis de vitals fallido: {e}")
            return {
                "hp": 100,
                "mp": 100,
                "target_exists": False,
                "target_health": 0,
                "target_name": "",
            }

    def preprocess_name_image(self, img: Image.Image) -> Image.Image:
        try:
            open_cv_image = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
            scale_factor = 4
            resized = cv2.resize(
                open_cv_image,
                (img.width * scale_factor, img.height * scale_factor),
                interpolation=cv2.INTER_LANCZOS4,
            )
            hsv = cv2.cvtColor(resized, cv2.COLOR_BGR2HSV)
            lower_white, upper_white = np.array([0, 0, 150]), np.array([179, 50, 255])
            mask = cv2.inRange(hsv, lower_white, upper_white)
            kernel = np.ones((2, 2), np.uint8)
            dilated_mask = cv2.dilate(mask, kernel, iterations=1)
            return Image.fromarray(dilated_mask)
        except Exception as e:
            self.logger.error(f"Fallo en el preprocesamiento de OCR: {e}")
            return img

    def extract_target_name_from_image(
        self, img: Image.Image, name_region_relative: Tuple[int, int, int, int]
    ) -> str:
        try:
            name_img = img.crop(name_region_relative)
            processed_img = self.preprocess_name_image(name_img)
            custom_config = r"--psm 8 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            raw_name = pytesseract.image_to_string(
                processed_img, config=custom_config
            ).strip()
            return self.correct_ocr_mistakes(raw_name)
        except Exception as e:
            self.logger.error(f"Fallo en la extracción OCR: {e}")
            return ""

    def calculate_health_percentage(self, pixels: np.ndarray, bar_type: str) -> int:
        if pixels.size == 0:
            return 0
        height, width, _ = pixels.shape
        filled_widths = []
        for y in range(height):
            rightmost = 0
            for x in range(width):
                r, g, b = pixels[y, x][:3]
                is_filled = False
                if bar_type in ["hp", "target"]:
                    is_filled = r > 150 and g < 100 and b < 100
                elif bar_type == "mp":
                    is_filled = b > 150 and r < 100 and g < 100
                if is_filled and x > rightmost:
                    rightmost = x
            if rightmost > 0:
                filled_widths.append((rightmost + 1) / width * 100)
        return (
            min(100, max(0, int(sum(filled_widths) / len(filled_widths))))
            if filled_widths
            else 0
        )

    def correct_ocr_mistakes(self, text: str) -> str:
        char_map = {"J": "Z", "i": "l", "1": "l", "0": "O", "5": "S", "8": "B", " ": ""}
        corrected = "".join(char_map.get(char, char) for char in text)
        return re.sub(r"[^a-zA-Z]", "", corrected).strip()

    def test_ocr_accuracy(
        self, name_region: Tuple[int, int, int, int]
    ) -> Dict[str, any]:
        try:
            full_capture = self.capture_screen()
            client_left, client_top = win32gui.ClientToScreen(self.target_hwnd, (0, 0))
            relative_region = (
                name_region[0] - client_left,
                name_region[1] - client_top,
                name_region[2] - client_left,
                name_region[3] - client_top,
            )
            original_image = full_capture.crop(relative_region)
            processed_image = self.preprocess_name_image(original_image)
            custom_config = r"--psm 8 --oem 1 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
            raw_name = pytesseract.image_to_string(
                processed_image, config=custom_config
            ).strip()
            extracted_name = self.correct_ocr_mistakes(raw_name)
            return {
                "original_image": original_image,
                "processed_image": processed_image,
                "extracted_name": extracted_name,
                "region_coords": name_region,
                "success": bool(extracted_name),
            }
        except Exception as e:
            raise AnalysisError(f"La prueba de OCR falló: {e}")

    def create_debug_image(
        self,
        all_regions_config: Dict,
        capture_area: Optional[Tuple[int, int, int, int]] = None,
    ) -> Image.Image:
        """
        ✅ ADAPTADO: Dibuja las regiones de vitals y los slots de la skill_bar.
        """
        try:
            # Si no se define un área de captura, se usa la ventana completa.
            if capture_area is None:
                if not self.target_hwnd:
                    raise AnalysisError("No hay ventana objetivo para capturar.")
                capture_area = win32gui.GetWindowRect(self.target_hwnd)

            img = self.capture_screen(region=capture_area)
            draw = ImageDraw.Draw(img)

            offset_x, offset_y = capture_area[0], capture_area[1]

            # --- 1. Dibuja las regiones de Vitals (tu lógica original) ---
            vitals_regions = all_regions_config.get("regions", {})
            region_colors = {
                "hp": "red",
                "mp": "blue",
                "target": "green",
                "target_name": "yellow",
            }
            for name, coords in vitals_regions.items():
                if (
                    coords[0] < capture_area[2]
                    and coords[2] > capture_area[0]
                    and coords[1] < capture_area[3]
                    and coords[3] > capture_area[1]
                ):

                    relative_coords = (
                        coords[0] - offset_x,
                        coords[1] - offset_y,
                        coords[2] - offset_x,
                        coords[3] - offset_y,
                    )
                    color = region_colors.get(name, "white")
                    draw.rectangle(relative_coords, outline=color, width=1)
                    label = name.upper()
                    draw.text(
                        (relative_coords[0], relative_coords[1] - 12), label, fill=color
                    )

            # --- 2. Añade el dibujado de los slots de la Skill Bar ---
            skill_bar_slots = all_regions_config.get("skill_bar", {}).get("slots", [])
            for i, coords in enumerate(skill_bar_slots):
                if (
                    coords[0] < capture_area[2]
                    and coords[2] > capture_area[0]
                    and coords[1] < capture_area[3]
                    and coords[3] > capture_area[1]
                ):

                    relative_coords = (
                        coords[0] - offset_x,
                        coords[1] - offset_y,
                        coords[2] - offset_x,
                        coords[3] - offset_y,
                    )
                    color = "cyan"  # Color distintivo para los slots.
                    draw.rectangle(relative_coords, outline=color, width=1)
                    label = f"S{i+1}"
                    draw.text(
                        (relative_coords[0] + 2, relative_coords[1] + 2),
                        label,
                        fill=color,
                    )

            return img
        except Exception as e:
            raise AnalysisError(f"Fallo al crear la imagen de depuración: {e}")
