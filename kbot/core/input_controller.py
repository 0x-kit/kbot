# kbot/core/input_controller.py

import time
import win32api
import win32con
import win32gui
from typing import Optional, Dict
from utils.exceptions import InputError
from utils.logger import BotLogger
from core.window_manager import WindowManager

class InputController:
    """
    Handles all keyboard and mouse input by sending direct, realistic messages to the target window.
    This version constructs a proper lParam to better simulate hardware input,
    allowing it to work even when the game window is in the background.
    """

    # Mapping of common keys to Windows Virtual-Key Codes.
    VK_CODE = {
        'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45, 'f': 0x46,
        'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A, 'k': 0x4B, 'l': 0x4C,
        'm': 0x4D, 'n': 0x4E, 'o': 0x4F, 'p': 0x50, 'q': 0x51, 'r': 0x52,
        's': 0x53, 't': 0x54, 'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58,
        'y': 0x59, 'z': 0x5A,
        '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
        '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
        'f1': win32con.VK_F1, 'f2': win32con.VK_F2, 'f3': win32con.VK_F3,
        'f4': win32con.VK_F4, 'f5': win32con.VK_F5, 'f6': win32con.VK_F6,
        'f7': win32con.VK_F7, 'f8': win32con.VK_F8, 'f9': win32con.VK_F9,
        'f10': win32con.VK_F10, 'f11': win32con.VK_F11, 'f12': win32con.VK_F12,
        'space': win32con.VK_SPACE,
        'enter': win32con.VK_RETURN,
    }

    def __init__(self, window_manager: WindowManager, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("InputController")
        self.window_manager = window_manager
        
        self.input_stats = {
            'total_inputs': 0,
            'successful_inputs': 0,
            'failed_inputs': 0
        }

    def _get_target_hwnd(self) -> Optional[int]:
        """Helper method to safely get the target window handle (HWND)."""
        if self.window_manager and self.window_manager.target_window:
            return self.window_manager.target_window.hwnd
        return None

    def send_key(self, key: str) -> bool:
        """Sends a realistic key press (down and up) directly to the target window."""
        hwnd = self._get_target_hwnd()
        if not hwnd:
            self.logger.warning("Attempted to send key, but no target window is selected.")
            self.input_stats['failed_inputs'] += 1
            return False
        
        key_lower = key.lower()
        if key_lower not in self.VK_CODE:
            self.logger.error(f"Key '{key}' is not defined in the Virtual-Key Code map.")
            self.input_stats['failed_inputs'] += 1
            return False
            
        vk_code = self.VK_CODE[key_lower]
        
        try:
            # === MEJORA CLAVE: Construcción de un lParam realista ===
            # Obtenemos el "scan code" de hardware para la tecla virtual. Esto hace que el input parezca más real.
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            
            # El lParam para WM_KEYDOWN se construye con el scan code en los bits 16-23.
            # El bit 0 es el contador de repetición (1 para una sola pulsación).
            lParam_down = 1 | (scan_code << 16)
            
            # El lParam para WM_KEYUP es similar, pero con bits adicionales para indicar que se está soltando la tecla.
            # Bit 30 (previous key state) = 1, Bit 31 (transition state) = 1.
            lParam_up = lParam_down | (1 << 30) | (1 << 31)

            # Usamos PostMessage para no bloquear el bot. Si esto falla, el siguiente paso sería probar SendMessage.
            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lParam_down)
            time.sleep(0.05)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lParam_up)

            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            # self.logger.debug(f"Sent key '{key}' to window 0x{hwnd:X} with realistic lParam.")
            return True
        except Exception as e:
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to send key '{key}' to window 0x{hwnd:X}: {e}")
            return False

    def hold_key(self, key: str, duration: float) -> bool:
        """Holds a key down for a specific duration in the target window."""
        hwnd = self._get_target_hwnd()
        if not hwnd: return False

        key_lower = key.lower()
        if key_lower not in self.VK_CODE: return False

        vk_code = self.VK_CODE[key_lower]
        
        try:
            scan_code = win32api.MapVirtualKey(vk_code, 0)
            lParam_down = 1 | (scan_code << 16)
            lParam_up = lParam_down | (1 << 30) | (1 << 31)

            win32api.PostMessage(hwnd, win32con.WM_KEYDOWN, vk_code, lParam_down)
            time.sleep(duration)
            win32api.PostMessage(hwnd, win32con.WM_KEYUP, vk_code, lParam_up)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            self.logger.debug(f"Held key '{key}' for {duration:.2f}s on window 0x{hwnd:X}")
            return True
        except Exception as e:
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to hold key '{key}': {e}")
            return False

    def click_at(self, x: int, y: int, button: str = 'left') -> bool:
        """Sends a click to specific screen coordinates within the target window."""
        hwnd = self._get_target_hwnd()
        if not hwnd: return False
        
        try:
            screen_coords = win32gui.GetWindowRect(hwnd)
            client_x = x - screen_coords[0]
            client_y = y - screen_coords[1]
            lParam = win32api.MAKELONG(client_x, client_y)

            if button.lower() == 'left':
                down_msg = win32con.WM_LBUTTONDOWN
                up_msg = win32con.WM_LBUTTONUP
                wparam = win32con.MK_LBUTTON
            else:
                down_msg = win32con.WM_RBUTTONDOWN
                up_msg = win32con.WM_RBUTTONUP
                wparam = win32con.MK_RBUTTON
            
            win32api.PostMessage(hwnd, down_msg, wparam, lParam)
            time.sleep(0.05)
            win32api.PostMessage(hwnd, up_msg, 0, lParam)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            self.logger.debug(f"Sent {button} click at screen ({x}, {y}) to window 0x{hwnd:X}")
            return True
        except Exception as e:
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to send click at ({x},{y}): {e}")
            return False

    def get_input_stats(self) -> Dict[str, any]:
        """Get input statistics."""
        total = self.input_stats['total_inputs']
        successful = self.input_stats['successful_inputs']
        return {
            'total_inputs': total,
            'successful_inputs': successful,
            'failed_inputs': self.input_stats['failed_inputs'],
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    
    def reset_stats(self) -> None:
        """Reset input statistics."""
        self.input_stats = { 'total_inputs': 0, 'successful_inputs': 0, 'failed_inputs': 0 }
    
    def emergency_stop(self) -> None:
        """Logs an emergency stop event."""
        self.logger.info("InputController emergency stop called.")