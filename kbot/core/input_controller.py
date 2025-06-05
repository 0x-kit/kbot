# core/input_controller.py
import time
from typing import Optional, List, Dict
import pyautogui
from utils.exceptions import InputError
from utils.logger import BotLogger

class InputController:
    """Handles all keyboard and mouse input for the bot"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("InputController")
        
        # Configure pyautogui
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1  # Small pause between actions
        
        # Track key states to prevent spam
        self.last_key_times: Dict[str, float] = {}
        self.min_key_interval = 0.05  # Minimum time between same key presses
        
        # Input statistics
        self.input_stats = {
            'total_inputs': 0,
            'successful_inputs': 0,
            'failed_inputs': 0
        }
    
    def send_key(self, key: str, hold_time: float = 0.0) -> bool:
        """Send a single key press"""
        try:
            current_time = time.time()
            
            # Check minimum interval for same key
            if key in self.last_key_times:
                time_since_last = current_time - self.last_key_times[key]
                if time_since_last < self.min_key_interval:
                    time.sleep(self.min_key_interval - time_since_last)
            
            # Send the key
            if hold_time > 0:
                pyautogui.keyDown(key)
                time.sleep(hold_time)
                pyautogui.keyUp(key)
            else:
                pyautogui.press(key)
            
            # Update tracking
            self.last_key_times[key] = time.time()
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            
            self.logger.debug(f"Sent key: {key}" + (f" (held for {hold_time}s)" if hold_time > 0 else ""))
            return True
            
        except Exception as e:
            self.input_stats['total_inputs'] += 1
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to send key '{key}': {e}")
            return False
    
    def send_key_combination(self, keys: List[str]) -> bool:
        """Send a key combination (e.g., ctrl+c)"""
        try:
            # Press all keys down
            for key in keys:
                pyautogui.keyDown(key)
            
            # Small delay
            time.sleep(0.05)
            
            # Release all keys in reverse order
            for key in reversed(keys):
                pyautogui.keyUp(key)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            
            self.logger.debug(f"Sent key combination: {'+'.join(keys)}")
            return True
            
        except Exception as e:
            self.input_stats['total_inputs'] += 1
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to send key combination '{'+'.join(keys)}': {e}")
            return False
    
    def send_text(self, text: str, interval: float = 0.0) -> bool:
        """Type text with optional interval between characters"""
        try:
            if interval > 0:
                for char in text:
                    pyautogui.write(char)
                    time.sleep(interval)
            else:
                pyautogui.write(text)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            
            self.logger.debug(f"Sent text: {text}")
            return True
            
        except Exception as e:
            self.input_stats['total_inputs'] += 1
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to send text '{text}': {e}")
            return False
    
    def click_at(self, x: int, y: int, button: str = 'left', clicks: int = 1) -> bool:
        """Click at specific coordinates"""
        try:
            pyautogui.click(x, y, clicks=clicks, button=button)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            
            self.logger.debug(f"Clicked at ({x}, {y}) with {button} button, {clicks} times")
            return True
            
        except Exception as e:
            self.input_stats['total_inputs'] += 1
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to click at ({x}, {y}): {e}")
            return False
    
    def move_mouse(self, x: int, y: int, duration: float = 0.0) -> bool:
        """Move mouse to specific coordinates"""
        try:
            pyautogui.moveTo(x, y, duration=duration)
            self.logger.debug(f"Moved mouse to ({x}, {y})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to move mouse to ({x}, {y}): {e}")
            return False
    
    def hold_key(self, key: str, duration: float) -> bool:
        """Hold a key for specified duration"""
        try:
            pyautogui.keyDown(key)
            time.sleep(duration)
            pyautogui.keyUp(key)
            
            self.input_stats['total_inputs'] += 1
            self.input_stats['successful_inputs'] += 1
            
            self.logger.debug(f"Held key '{key}' for {duration} seconds")
            return True
            
        except Exception as e:
            self.input_stats['total_inputs'] += 1
            self.input_stats['failed_inputs'] += 1
            self.logger.error(f"Failed to hold key '{key}': {e}")
            return False
    
    def get_input_stats(self) -> Dict[str, any]:
        """Get input statistics"""
        total = self.input_stats['total_inputs']
        successful = self.input_stats['successful_inputs']
        
        return {
            'total_inputs': total,
            'successful_inputs': successful,
            'failed_inputs': self.input_stats['failed_inputs'],
            'success_rate': (successful / total * 100) if total > 0 else 0
        }
    
    def reset_stats(self) -> None:
        """Reset input statistics"""
        self.input_stats = {
            'total_inputs': 0,
            'successful_inputs': 0,
            'failed_inputs': 0
        }
    
    def set_min_key_interval(self, interval: float) -> None:
        """Set minimum interval between same key presses"""
        self.min_key_interval = max(0.01, interval)  # Minimum 10ms
    
    def emergency_stop(self) -> None:
        """Emergency stop - release all held keys"""
        try:
            # Release common movement keys
            for key in ['w', 'a', 's', 'd', 'shift', 'ctrl', 'alt']:
                pyautogui.keyUp(key)
            
            self.logger.info("Emergency stop executed - all keys released")
        except Exception as e:
            self.logger.error(f"Emergency stop failed: {e}")
