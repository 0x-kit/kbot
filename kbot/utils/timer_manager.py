# utils/timer_manager.py
import time
from typing import Dict, Callable, Optional
from PyQt5.QtCore import QTimer, QObject

class TimerManager(QObject):
    """Manages multiple timers with different intervals"""
    
    def __init__(self):
        super().__init__()
        self.timers: Dict[str, QTimer] = {}
        self.callbacks: Dict[str, Callable] = {}
        self.intervals: Dict[str, int] = {}
        self.active_timers: set = set()
    
    def create_timer(self, name: str, interval: float, callback: Callable, 
                    single_shot: bool = False) -> None:
        """Create a new timer"""
        if name in self.timers:
            self.remove_timer(name)
        
        timer = QTimer()
        timer.timeout.connect(callback)
        timer.setSingleShot(single_shot)
        
        self.timers[name] = timer
        self.callbacks[name] = callback
        self.intervals[name] = int(interval * 1000)  # Convert to milliseconds
    
    def start_timer(self, name: str) -> bool:
        """Start a specific timer"""
        if name not in self.timers:
            return False
        
        timer = self.timers[name]
        interval = self.intervals[name]
        
        timer.start(interval)
        self.active_timers.add(name)
        return True
    
    def stop_timer(self, name: str) -> bool:
        """Stop a specific timer"""
        if name not in self.timers:
            return False
        
        self.timers[name].stop()
        self.active_timers.discard(name)
        return True
    
    def restart_timer(self, name: str) -> bool:
        """Restart a specific timer"""
        if name not in self.timers:
            return False
        
        self.stop_timer(name)
        return self.start_timer(name)
    
    def update_interval(self, name: str, new_interval: float) -> bool:
        """Update timer interval"""
        if name not in self.timers:
            return False
        
        was_active = name in self.active_timers
        self.stop_timer(name)
        
        self.intervals[name] = int(new_interval * 1000)
        
        if was_active:
            self.start_timer(name)
        
        return True
    
    def remove_timer(self, name: str) -> bool:
        """Remove a timer completely"""
        if name not in self.timers:
            return False
        
        self.stop_timer(name)
        del self.timers[name]
        del self.callbacks[name]
        del self.intervals[name]
        return True
    
    def stop_all_timers(self) -> None:
        """Stop all active timers"""
        for name in list(self.active_timers):
            self.stop_timer(name)
    
    def start_all_timers(self) -> None:
        """Start all timers"""
        for name in self.timers:
            self.start_timer(name)
    
    def get_timer_status(self, name: str) -> Optional[Dict[str, any]]:
        """Get status information about a timer"""
        if name not in self.timers:
            return None
        
        timer = self.timers[name]
        return {
            'name': name,
            'active': name in self.active_timers,
            'interval': self.intervals[name] / 1000.0,  # Convert back to seconds
            'single_shot': timer.isSingleShot(),
            'remaining_time': timer.remainingTime() / 1000.0 if timer.isActive() else 0
        }
    
    def get_all_timer_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all timers"""
        return {name: self.get_timer_status(name) for name in self.timers}
