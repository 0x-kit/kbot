# core/window_manager.py
import win32gui
import win32con
from typing import List, Dict, Optional, Tuple
from utils.exceptions import WindowError
from utils.logger import BotLogger

class WindowInfo:
    """Container for window information"""
    
    def __init__(self, hwnd: int, title: str, rect: Tuple[int, int, int, int]):
        self.hwnd = hwnd
        self.title = title
        self.rect = rect  # (left, top, right, bottom)
    
    @property
    def width(self) -> int:
        return self.rect[2] - self.rect[0]
    
    @property
    def height(self) -> int:
        return self.rect[3] - self.rect[1]
    
    def __str__(self) -> str:
        return f"{self.title} (0x{self.hwnd:X})"

class WindowManager:
    """Manages game window detection and interaction"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("WindowManager")
        self.target_window: Optional[WindowInfo] = None
        self.window_cache: Dict[int, WindowInfo] = {}
        self.cache_timeout = 5.0  # Cache windows for 5 seconds
        self.last_refresh = 0.0
    
    def get_all_windows(self, refresh_cache: bool = False) -> List[WindowInfo]:
        """Get all visible windows"""
        import time
        
        current_time = time.time()
        
        # Use cache if it's still valid and not forced refresh
        if (not refresh_cache and 
            self.window_cache and 
            current_time - self.last_refresh < self.cache_timeout):
            return list(self.window_cache.values())
        
        # Refresh window list
        windows = []
        
        def enum_callback(hwnd, _):
            try:
                if win32gui.IsWindowVisible(hwnd):
                    title = win32gui.GetWindowText(hwnd)
                    if title:  # Only include windows with titles
                        rect = win32gui.GetWindowRect(hwnd)
                        window_info = WindowInfo(hwnd, title, rect)
                        windows.append(window_info)
                        self.window_cache[hwnd] = window_info
            except Exception as e:
                self.logger.debug(f"Error processing window {hwnd}: {e}")
            return True
        
        try:
            win32gui.EnumWindows(enum_callback, None)
            self.last_refresh = current_time
            self.logger.debug(f"Found {len(windows)} visible windows")
            return windows
        except Exception as e:
            raise WindowError(f"Failed to enumerate windows: {e}")
    
    def find_windows_by_title(self, title_pattern: str, exact_match: bool = False) -> List[WindowInfo]:
        """Find windows matching a title pattern"""
        windows = self.get_all_windows()
        matches = []
        
        for window in windows:
            if exact_match:
                if window.title == title_pattern:
                    matches.append(window)
            else:
                if title_pattern.lower() in window.title.lower():
                    matches.append(window)
        
        return matches
    
    def set_target_window(self, hwnd: int) -> bool:
        """Set the target window by handle"""
        try:
            # Verify window exists and is valid
            if not win32gui.IsWindow(hwnd):
                raise WindowError(f"Invalid window handle: 0x{hwnd:X}")
            
            title = win32gui.GetWindowText(hwnd)
            rect = win32gui.GetWindowRect(hwnd)
            
            self.target_window = WindowInfo(hwnd, title, rect)
            self.logger.info(f"Target window set: {self.target_window}")
            return True
            
        except Exception as e:
            raise WindowError(f"Failed to set target window: {e}")
    
    def set_target_window_by_title(self, title: str, exact_match: bool = False) -> bool:
        """Set target window by title"""
        windows = self.find_windows_by_title(title, exact_match)
        
        if not windows:
            raise WindowError(f"No window found with title: {title}")
        
        if len(windows) > 1:
            self.logger.warning(f"Multiple windows found with title '{title}', using first one")
        
        return self.set_target_window(windows[0].hwnd)
    
    def bring_to_foreground(self, hwnd: Optional[int] = None) -> bool:
        """Bring window to foreground"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            raise WindowError("No target window specified")
        
        try:
            # First restore the window if minimized
            win32gui.ShowWindow(target_hwnd, win32con.SW_RESTORE)
            
            # Then bring to foreground
            win32gui.SetForegroundWindow(target_hwnd)
            
            self.logger.debug(f"Brought window 0x{target_hwnd:X} to foreground")
            return True
            
        except Exception as e:
            raise WindowError(f"Failed to bring window to foreground: {e}")
    
    def minimize_window(self, hwnd: Optional[int] = None) -> bool:
        """Minimize window"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            raise WindowError("No target window specified")
        
        try:
            win32gui.ShowWindow(target_hwnd, win32con.SW_MINIMIZE)
            self.logger.debug(f"Minimized window 0x{target_hwnd:X}")
            return True
            
        except Exception as e:
            raise WindowError(f"Failed to minimize window: {e}")
    
    def maximize_window(self, hwnd: Optional[int] = None) -> bool:
        """Maximize window"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            raise WindowError("No target window specified")
        
        try:
            win32gui.ShowWindow(target_hwnd, win32con.SW_MAXIMIZE)
            self.logger.debug(f"Maximized window 0x{target_hwnd:X}")
            return True
            
        except Exception as e:
            raise WindowError(f"Failed to maximize window: {e}")
    
    def rename_window(self, new_title: str, hwnd: Optional[int] = None) -> bool:
        """Rename a window"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            raise WindowError("No target window specified")
        
        try:
            old_title = win32gui.GetWindowText(target_hwnd)
            win32gui.SetWindowText(target_hwnd, new_title)
            
            # Update our target window info if it's the same window
            if self.target_window and self.target_window.hwnd == target_hwnd:
                self.target_window.title = new_title
            
            self.logger.info(f"Renamed window from '{old_title}' to '{new_title}'")
            return True
            
        except Exception as e:
            raise WindowError(f"Failed to rename window: {e}")
    
    def get_window_rect(self, hwnd: Optional[int] = None) -> Tuple[int, int, int, int]:
        """Get window rectangle coordinates"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            raise WindowError("No target window specified")
        
        try:
            return win32gui.GetWindowRect(target_hwnd)
        except Exception as e:
            raise WindowError(f"Failed to get window rectangle: {e}")
    
    def is_window_valid(self, hwnd: Optional[int] = None) -> bool:
        """Check if window is still valid"""
        target_hwnd = hwnd or (self.target_window.hwnd if self.target_window else None)
        
        if not target_hwnd:
            return False
        
        try:
            return win32gui.IsWindow(target_hwnd) and win32gui.IsWindowVisible(target_hwnd)
        except:
            return False
    
    def update_target_window_rect(self) -> bool:
        """Update target window rectangle"""
        if not self.target_window:
            return False
        
        try:
            new_rect = win32gui.GetWindowRect(self.target_window.hwnd)
            self.target_window.rect = new_rect
            return True
        except Exception as e:
            self.logger.error(f"Failed to update window rect: {e}")
            return False
    
    def get_target_window_info(self) -> Optional[Dict[str, any]]:
        """Get detailed information about the target window"""
        if not self.target_window:
            return None
        
        return {
            'hwnd': self.target_window.hwnd,
            'title': self.target_window.title,
            'rect': self.target_window.rect,
            'width': self.target_window.width,
            'height': self.target_window.height,
            'is_valid': self.is_window_valid(),
            'is_foreground': self._is_foreground_window()
        }
    
    def _is_foreground_window(self) -> bool:
        """Check if target window is currently in foreground"""
        if not self.target_window:
            return False
        
        try:
            foreground_hwnd = win32gui.GetForegroundWindow()
            return foreground_hwnd == self.target_window.hwnd
        except:
            return False
    
    def find_game_windows(self, game_keywords: List[str] = None) -> List[WindowInfo]:
        """Find potential game windows based on common keywords"""
        if game_keywords is None:
            game_keywords = ['tantra', 'game', 'client', 'launcher']
        
        all_windows = self.get_all_windows()
        game_windows = []
        
        for window in all_windows:
            title_lower = window.title.lower()
            
            # Check for game keywords
            for keyword in game_keywords:
                if keyword.lower() in title_lower:
                    game_windows.append(window)
                    break
            
            # Also check for windows with reasonable game dimensions
            if (window.width >= 800 and window.height >= 600 and 
                not any(exclude in title_lower for exclude in ['desktop', 'taskbar', 'explorer'])):
                if window not in game_windows:
                    game_windows.append(window)
        
        self.logger.info(f"Found {len(game_windows)} potential game windows")
        return game_windows