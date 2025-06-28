# kbot/utils/logger.py

import logging
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal
import traceback


class BotLogger(QObject):
    log_message = pyqtSignal(str)

    def __init__(self, name: str = "TantraBot", level: int = logging.INFO):
        super().__init__()
        # Evitar duplicar handlers si la clase se instancia varias veces
        if logging.getLogger(name).hasHandlers():
            self.logger = logging.getLogger(name)
        else:
            self.logger = logging.getLogger(name)
            self.logger.setLevel(level)

            # Formateador
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )

            # Handler de consola
            ch = logging.StreamHandler()
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

            # Handler de fichero
            try:
                fh = logging.FileHandler("bot.log", encoding="utf-8")
                fh.setFormatter(formatter)
                self.logger.addHandler(fh)
            except Exception as e:
                print(f"Could not create file handler for logger: {e}")

    def _log(self, level, message, exc_info=False):
        """Método de log interno para manejar exc_info."""
        log_func = getattr(self.logger, level)
        log_func(message, exc_info=exc_info)

        ui_message = message
        if exc_info:
            ui_message += "\n" + traceback.format_exc()

        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_message.emit(f"[{timestamp}] [{level.upper()}] {ui_message}")

    def debug(self, message: str, exc_info=False):
        self._log("debug", message, exc_info)

    def info(self, message: str, exc_info=False):
        self._log("info", message, exc_info)

    def warning(self, message: str, exc_info=False):
        self._log("warning", message, exc_info)

    def error(self, message: str, exc_info=False):
        """✅ CORREGIDO: Acepta exc_info para trazas de error completas."""
        self._log("error", message, exc_info)

    def critical(self, message: str, exc_info=False):
        self._log("critical", message, exc_info)
