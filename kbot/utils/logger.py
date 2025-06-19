# utils/logger.py - VERSIÓN ARREGLADA SIN PROBLEMAS DE ENCODING

import logging
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal


class BotLogger(QObject):
    """Custom logger for the bot with Qt signal support - EMOJI SAFE"""

    # Signal for updating UI log display
    log_message = pyqtSignal(str)

    def __init__(self, name: str = "TantraBot", level: int = logging.INFO):
        super().__init__()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Create console handler with UTF-8 encoding
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)

        # Create file handler with UTF-8 encoding to avoid emoji issues
        try:
            file_handler = logging.FileHandler("bot.log", encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)
        except Exception:
            # Fallback: create file handler without encoding specification
            file_handler = logging.FileHandler("bot.log")
            file_handler.setLevel(logging.DEBUG)

        # Create formatter that removes emojis for file logging
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # File formatter that strips emojis to avoid encoding issues
        file_formatter = EmojiSafeFormatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        # Add handlers only if they don't exist
        if not self.logger.handlers:
            self.logger.addHandler(console_handler)
            self.logger.addHandler(file_handler)

    def debug(self, message: str) -> None:
        """Log debug message"""
        safe_message = self._make_message_safe(message)
        self.logger.debug(safe_message)
        self._emit_ui_message("DEBUG", message)  # UI can handle emojis

    def info(self, message: str) -> None:
        """Log info message"""
        safe_message = self._make_message_safe(message)
        self.logger.info(safe_message)
        self._emit_ui_message("INFO", message)  # UI can handle emojis

    def warning(self, message: str) -> None:
        """Log warning message"""
        safe_message = self._make_message_safe(message)
        self.logger.warning(safe_message)
        self._emit_ui_message("WARNING", message)  # UI can handle emojis

    def error(self, message: str) -> None:
        """Log error message"""
        safe_message = self._make_message_safe(message)
        self.logger.error(safe_message)
        self._emit_ui_message("ERROR", message)  # UI can handle emojis

    def critical(self, message: str) -> None:
        """Log critical message"""
        safe_message = self._make_message_safe(message)
        self.logger.critical(safe_message)
        self._emit_ui_message("CRITICAL", message)  # UI can handle emojis

    def _make_message_safe(self, message: str) -> str:
        """Remove emojis and special characters that might cause encoding issues"""
        # This is used for file logging to avoid encoding issues
        import re

        # Remove emojis and other unicode symbols that might cause issues
        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )
        return emoji_pattern.sub("", message)

    def _emit_ui_message(self, level: str, message: str) -> None:
        """Emit signal for UI update - can contain emojis"""
        try:
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.log_message.emit(formatted_message)
        except Exception:
            # If UI emission fails, just continue - don't break logging
            pass


class EmojiSafeFormatter(logging.Formatter):
    """Custom formatter that removes emojis to prevent encoding issues"""

    def format(self, record):
        # Get the original formatted message
        original_message = super().format(record)

        # Remove emojis and problematic unicode characters
        import re

        emoji_pattern = re.compile(
            "["
            "\U0001f600-\U0001f64f"  # emoticons
            "\U0001f300-\U0001f5ff"  # symbols & pictographs
            "\U0001f680-\U0001f6ff"  # transport & map
            "\U0001f1e0-\U0001f1ff"  # flags (iOS)
            "\U00002702-\U000027b0"
            "\U000024c2-\U0001f251"
            "]+",
            flags=re.UNICODE,
        )

        # Replace emojis with text equivalents for file logging
        safe_message = emoji_pattern.sub("", original_message)

        # Replace common emoji text patterns for better readability
        replacements = {
            "🤝": "[HANDSHAKE]",
            "⚡": "[LIGHTNING]",
            "🔄": "[REFRESH]",
            "✅": "[SUCCESS]",
            "❌": "[ERROR]",
            "⚠️": "[WARNING]",
            "🎯": "[TARGET]",
            "📦": "[PACKAGE]",
            "⚔️": "[SWORDS]",
            "🛡️": "[SHIELD]",
            "🚀": "[ROCKET]",
            "🔥": "[FIRE]",
            "📊": "[CHART]",
        }

        for emoji, replacement in replacements.items():
            safe_message = safe_message.replace(emoji, replacement)

        return safe_message
