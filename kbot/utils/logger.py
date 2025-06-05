# utils/logger.py
import logging
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

class BotLogger(QObject):
    """Custom logger for the bot with Qt signal support"""
    
    # Signal for updating UI log display
    log_message = pyqtSignal(str)
    
    def __init__(self, name: str = "TantraBot", level: int = logging.INFO):
        super().__init__()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Create file handler
        file_handler = logging.FileHandler('bot.log')
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)
    
    def debug(self, message: str) -> None:
        """Log debug message"""
        self.logger.debug(message)
        self._emit_ui_message("DEBUG", message)
    
    def info(self, message: str) -> None:
        """Log info message"""
        self.logger.info(message)
        self._emit_ui_message("INFO", message)
    
    def warning(self, message: str) -> None:
        """Log warning message"""
        self.logger.warning(message)
        self._emit_ui_message("WARNING", message)
    
    def error(self, message: str) -> None:
        """Log error message"""
        self.logger.error(message)
        self._emit_ui_message("ERROR", message)
    
    def critical(self, message: str) -> None:
        """Log critical message"""
        self.logger.critical(message)
        self._emit_ui_message("CRITICAL", message)
    
    def _emit_ui_message(self, level: str, message: str) -> None:
        """Emit signal for UI update"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_message.emit(formatted_message)