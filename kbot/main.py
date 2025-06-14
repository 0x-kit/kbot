# main.py - DEBUG VERSION TO FIND THE ERROR
import sys
import os
import traceback
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.logger import BotLogger


def main():
    """Main application entry point with detailed error tracking"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Tantra Bot")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("0xkit")

    # Set application style
    app.setStyle("Fusion")  # Modern look

    # Setup logging
    logger = BotLogger("Application")
    logger.info("Starting Tantra Bot v1.0.0")

    try:
        logger.info("DEBUG: Attempting to import TantraBotMainWindow...")
        from ui.main_window import TantraBotMainWindow

        logger.info("DEBUG: Import successful")

        logger.info("DEBUG: Creating main window instance...")
        main_window = TantraBotMainWindow()
        logger.info("DEBUG: Main window created successfully")

        logger.info("DEBUG: Showing main window...")
        main_window.show()
        logger.info("DEBUG: Main window shown")

        # Run application
        logger.info("DEBUG: Starting application event loop...")
        result = app.exec_()

        logger.info("Application closed")
        return result

    except Exception as e:
        logger.critical(f"Critical error: {e}")
        logger.critical(f"Full traceback:")
        logger.critical(traceback.format_exc())

        # Print to console as well
        print(f"\n=== DETAILED ERROR INFORMATION ===")
        print(f"Error: {e}")
        print(f"Type: {type(e).__name__}")
        print(f"Full traceback:")
        print(traceback.format_exc())
        print(f"=== END ERROR INFORMATION ===\n")

        return 1


if __name__ == "__main__":
    sys.exit(main())
