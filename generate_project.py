## Files that need code copied from artifacts:

### ✅ Ready (have complete content):


### 📋 Need implementation from artifacts:

#### Config Module:
- [ ] **config/config_manager.py** → Copy from "config_manager" artifact

#### Core Module:
- [ ] **core/bot_engine.py** → Copy from "bot_engine" artifact
- [ ] **core/pixel_analyzer.py** → Copy from "pixel_analyzer" artifact  
- [ ] **core/window_manager.py** → Copy from "utils_modules" artifact
- [ ] **core/input_controller.py** → Copy from "utils_modules" artifact

#### Combat Module:
- [ ] **combat/combat_manager.py** → Copy from "bot_engine" artifact
- [ ] **combat/skill_manager.py** → Copy from "skill_manager" artifact

#### UI Module:
- [ ] **ui/main_window.py** → Copy from "main_application" artifact
- [ ] **ui/dialogs/region_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/dialogs/skill_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/log_widget.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/status_widget.py** → Copy from "ui_widgets_dialogs" artifact

#### Utils Module:
- [ ] **utils/logger.py** → Copy from "utils_modules" artifact
- [ ] **utils/timer_manager.py** → Copy from "#!/usr/bin/env python3
"""
Tantra Bot v2.0 Project Structure Generator
Generates complete project structure with empty files ready for code copying
"""

import os
from pathlib import Path

def create_project_structure():
    """Create the complete project structure with all files"""
    
    project_name = "tantra_bot_v2"
    
    # Define all files and their content templates
    files = {
        # Root files
        "main.py": '''import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import TantraBotMainWindow
from utils.logger import BotLogger

def main():
    """Main application entry point"""
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Tantra Bot")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("cursebox")
    
    # Set application style
    app.setStyle('Fusion')  # Modern look
    
    # Setup logging
    logger = BotLogger("Application")
    logger.info("Starting Tantra Bot v2.0.0")
    
    try:
        # Create main window
        main_window = TantraBotMainWindow()
        main_window.show()
        
        # Run application
        result = app.exec_()
        
        logger.info("Application closed")
        return result
        
    except Exception as e:
        logger.critical(f"Critical error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
''',

        "requirements.txt": '''PyQt5>=5.15.0
Pillow>=8.0.0
numpy>=1.20.0
pytesseract>=0.3.8
pyautogui>=0.9.52
pywin32>=227
''',

        "README.md": '''# Tantra Bot v2.0.0

Advanced automation bot for Tantra Online with modular architecture.

## Features

- **Intelligent Combat System**: Advanced targeting and skill rotation
- **OCR Target Recognition**: Smart mob detection and validation
- **Configurable Skills**: Flexible skill management with priorities and conditions
- **Auto-Potion System**: Smart health and mana management
- **Window Management**: Easy game window selection and management
- **Real-time Monitoring**: Live vitals and statistics tracking

## Installation

1. Install Python 3.7 or higher
2. Install required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Install Tesseract OCR and update path in core/pixel_analyzer.py if needed
4. Run the bot:
   ```bash
   python main.py
   ```

## Quick Start

1. **Select Game Window**: Use "Select Game Window" to attach to your game
2. **Configure Regions**: Set up HP/MP bar detection areas
3. **Set Whitelist**: Define which mobs to attack
4. **Configure Skills**: Set up skill rotations and priorities
5. **Start Bot**: Click "Start Bot" to begin automation

## Project Structure

```
tantra_bot_v2/
├── config/          # Configuration management
├── core/            # Core functionality
├── combat/          # Combat logic and skills
├── ui/              # User interface
├── utils/           # Utilities and helpers
└── main.py          # Entry point
```

## Safety Features

- Emergency stop functionality
- Input validation and error handling
- Comprehensive logging
- Configurable timing to avoid detection

Created by cursebox. For educational purposes.
''',

        ".gitignore": '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Bot specific
bot_config.ini
*.log
screenshots/
debug/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
''',

        # Config module
        "config/__init__.py": '''"""Configuration management module for Tantra Bot"""

from .config_manager import ConfigManager

__all__ = ['ConfigManager']
''',
        "config/config_manager.py": '''# config/config_manager.py
# Copy the ConfigManager class from the "config_manager" artifact
# This file handles all bot configuration settings

import configparser
import ast
import os
from typing import Dict, Any, Tuple, List
from utils.exceptions import ConfigError

class ConfigManager:
    """Manages all bot configuration settings"""
    
    def __init__(self, config_file: str = "bot_config.ini"):
        # TODO: Copy implementation from config_manager artifact
        pass

# TODO: Copy the complete ConfigManager implementation from the artifact
''',

        "config/default_config.ini": '''[Slots]
slot1 = 1
slot2 = 1
slot3 = 1
slot4 = 150
slot5 = 1
slot6 = 1
slot7 = 150
slot8 = 600
slotF1 = 120
slotF2 = 120
slotF3 = 120
slotF4 = 120
slotF5 = 120
slotF6 = 120
slotF7 = 120
slotF8 = 120
slotF9 = 120
slotF10 = 120

[Whitelist]
mobs = Byokbo

[Options]
auto_pots = True
potion_threshold = 70

[Regions]
hp = (4, 20, 168, 36)
mp = (4, 36, 168, 51)
target = (4, 66, 168, 75)
target_name = (4, 55, 168, 70)

[Timing]
combat_check = 1.0
attack = 1.5
target_switch = 0.7
potion = 0.5

[Skills]
rotations = []
priorities = {}
cooldowns = {}
conditions = {}
''',

        # Core module
        "core/__init__.py": '''"""Core functionality module for Tantra Bot"""

# Import core classes when they are implemented
# from .bot_engine import BotEngine, BotState
# from .pixel_analyzer import PixelAnalyzer
# from .window_manager import WindowManager, WindowInfo
# from .input_controller import InputController

# For now, empty until classes are implemented
__all__ = []
''',
        "core/bot_engine.py": '''# core/bot_engine.py
# Copy the BotEngine class from the "bot_engine" artifact
# This is the main bot controller that coordinates all subsystems

import time
from typing import Dict, Any, Optional, Callable
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

# TODO: Copy all imports and BotEngine implementation from bot_engine artifact

class BotState(Enum):
    """Bot execution states"""
    # TODO: Copy from artifact
    pass

class BotEngine(QObject):
    """Main bot engine that coordinates all subsystems"""
    
    def __init__(self):
        # TODO: Copy complete implementation from bot_engine artifact
        pass

# TODO: Copy the complete BotEngine implementation from the artifact
''',

        "core/pixel_analyzer.py": '''# core/pixel_analyzer.py
# Copy the PixelAnalyzer class from the "pixel_analyzer" artifact
# This handles screen capture and pixel analysis for the game

import numpy as np
import re
from typing import Dict, Tuple, Optional
from PIL import ImageGrab, Image, ImageDraw, ImageOps, ImageFilter
import pytesseract
from utils.exceptions import AnalysisError

# Set Tesseract path if needed (uncomment and modify for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\\Program Files\\Tesseract-OCR\\tesseract.exe'

class PixelAnalyzer:
    """Handles screen capture and pixel analysis for the game"""
    
    def __init__(self):
        # TODO: Copy complete implementation from pixel_analyzer artifact
        pass

# TODO: Copy the complete PixelAnalyzer implementation from the artifact
''',

        "core/window_manager.py": '''# core/window_manager.py
# Copy the WindowManager class from the "utils_modules" artifact
# This handles game window detection and interaction

import win32gui
import win32con
from typing import List, Dict, Optional, Tuple
from utils.exceptions import WindowError
from utils.logger import BotLogger

class WindowInfo:
    """Container for window information"""
    # TODO: Copy from utils_modules artifact
    pass

class WindowManager:
    """Manages game window detection and interaction"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        # TODO: Copy complete implementation from utils_modules artifact
        pass

# TODO: Copy the complete WindowManager implementation from the artifact
''',

        "core/input_controller.py": '''# core/input_controller.py
# Copy the InputController class from the "utils_modules" artifact
# This handles all keyboard and mouse input for the bot

import time
from typing import Optional, List, Dict
import pyautogui
from utils.exceptions import InputError
from utils.logger import BotLogger

class InputController:
    """Handles all keyboard and mouse input for the bot"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        # TODO: Copy complete implementation from utils_modules artifact
        pass

# TODO: Copy the complete InputController implementation from the artifact
''',

        # Combat module
        "combat/__init__.py": '''"""Combat system module for Tantra Bot"""

# Target validator is complete
from .target_validator import TargetValidator

# Import other combat classes when they are implemented
# from .combat_manager import CombatManager, CombatState
# from .skill_manager import SkillManager, Skill, SkillType, TriggerCondition

__all__ = ['TargetValidator']
''',
        "combat/combat_manager.py": '''# combat/combat_manager.py
# Copy the CombatManager class from the "bot_engine" artifact
# This manages combat logic and target selection

import time
from typing import Optional, List, Dict, Any
from enum import Enum

# TODO: Copy all imports from bot_engine artifact

class CombatState(Enum):
    """Combat execution states"""
    # TODO: Copy from bot_engine artifact
    pass

class CombatManager:
    """Manages combat logic and target selection"""
    
    def __init__(self, pixel_analyzer, skill_manager, input_controller, logger):
        # TODO: Copy complete implementation from bot_engine artifact
        pass

# TODO: Copy the complete CombatManager implementation from the artifact
''',

        "combat/skill_manager.py": '''# combat/skill_manager.py
# Copy the SkillManager class from the "skill_manager" artifact
# This handles advanced skill management with rotations and conditions

import time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from utils.exceptions import SkillError

# TODO: Copy all imports and classes from skill_manager artifact

class SkillType(Enum):
    """Types of skills"""
    # TODO: Copy from skill_manager artifact
    pass

class TriggerCondition(Enum):
    """Skill trigger conditions"""
    # TODO: Copy from skill_manager artifact
    pass

@dataclass
class Skill:
    """Represents a single skill/action"""
    # TODO: Copy from skill_manager artifact
    pass

class SkillManager:
    """Advanced skill management system"""
    
    def __init__(self, input_controller):
        # TODO: Copy complete implementation from skill_manager artifact
        pass

# TODO: Copy the complete SkillManager implementation from the artifact
''',

        "combat/target_validator.py": '''# combat/target_validator.py
import re
from typing import List, Dict, Any, Optional
from utils.logger import BotLogger

class TargetValidator:
    """Validates targets against whitelist and other criteria"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("TargetValidator")
        self.whitelist: List[str] = []
        self.blacklist: List[str] = []
        self.validation_rules: Dict[str, Any] = {}
        
        # Default validation rules
        self.default_rules = {
            'min_name_length': 2,
            'max_name_length': 50,
            'allow_special_chars': False,
            'case_sensitive': False
        }
        self.validation_rules.update(self.default_rules)
    
    def set_whitelist(self, whitelist: List[str]) -> None:
        """Set the mob whitelist"""
        self.whitelist = [name.strip() for name in whitelist if name.strip()]
        self.logger.info(f"Whitelist updated with {len(self.whitelist)} entries")
    
    def set_blacklist(self, blacklist: List[str]) -> None:
        """Set the mob blacklist"""
        self.blacklist = [name.strip() for name in blacklist if name.strip()]
        self.logger.info(f"Blacklist updated with {len(self.blacklist)} entries")
    
    def add_to_whitelist(self, name: str) -> None:
        """Add a name to whitelist"""
        name = name.strip()
        if name and name not in self.whitelist:
            self.whitelist.append(name)
            self.logger.info(f"Added '{name}' to whitelist")
    
    def remove_from_whitelist(self, name: str) -> None:
        """Remove a name from whitelist"""
        if name in self.whitelist:
            self.whitelist.remove(name)
            self.logger.info(f"Removed '{name}' from whitelist")
    
    def add_to_blacklist(self, name: str) -> None:
        """Add a name to blacklist"""
        name = name.strip()
        if name and name not in self.blacklist:
            self.blacklist.append(name)
            self.logger.info(f"Added '{name}' to blacklist")
    
    def remove_from_blacklist(self, name: str) -> None:
        """Remove a name from blacklist"""
        if name in self.blacklist:
            self.blacklist.remove(name)
            self.logger.info(f"Removed '{name}' from blacklist")
    
    def is_valid_target(self, target_name: str) -> bool:
        """Check if target is valid according to all rules"""
        if not target_name:
            return False
        
        # Basic validation
        if not self._basic_validation(target_name):
            return False
        
        # Blacklist check (takes priority)
        if self._is_blacklisted(target_name):
            self.logger.debug(f"Target '{target_name}' is blacklisted")
            return False
        
        # Whitelist check
        if self.whitelist and not self._is_whitelisted(target_name):
            self.logger.debug(f"Target '{target_name}' not in whitelist")
            return False
        
        return True
    
    def _basic_validation(self, target_name: str) -> bool:
        """Perform basic validation checks"""
        # Length check
        if (len(target_name) < self.validation_rules['min_name_length'] or
            len(target_name) > self.validation_rules['max_name_length']):
            return False
        
        # Special characters check
        if not self.validation_rules['allow_special_chars']:
            if not re.match(r'^[a-zA-Z0-9\\s]+

        # UI module
        "ui/__init__.py": "# UI module",
        "ui/main_window.py": '''# ui/main_window.py
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt

class TantraBotMainWindow(QMainWindow):
    """Main application window - Minimal version for testing"""
    
    def __init__(self):
        super().__init__()  # ← THIS FIXES THE SUPER-CLASS INIT ERROR!
        
        self.setWindowTitle("Tantra Bot v2.0.0 - by cursebox")
        self.setMinimumSize(400, 300)
        
        # Create minimal UI for testing
        self._setup_minimal_ui()
    
    def _setup_minimal_ui(self):
        """Setup minimal UI for testing"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # Title
        title = QLabel("<h1>Tantra Bot v2.0.0</h1>")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Status
        status = QLabel("Bot is ready (minimal mode)")
        status.setAlignment(Qt.AlignCenter)
        layout.addWidget(status)
        
        # Test button
        test_btn = QPushButton("Test Application")
        test_btn.clicked.connect(self._test_application)
        layout.addWidget(test_btn)
        
        # Info
        info = QLabel("""
        <p><b>Setup Status:</b></p>
        <p>✅ Application starts successfully</p>
        <p>⚠️  Need to copy implementation code from artifacts</p>
        <p>📋 See TODO.md for copy instructions</p>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
    
    def _test_application(self):
        """Test application functionality"""
        QMessageBox.information(
            self, "Test", 
            "Application is working!\\n\\n"
            "Next steps:\\n"
            "1. Copy code from artifacts\\n"
            "2. Install dependencies\\n"
            "3. Configure bot settings"
        )

# TODO: Replace this minimal version with the complete implementation
# from the "main_application" artifact once all dependencies are ready
''',

        # UI dialogs
        "ui/dialogs/__init__.py": "# Dialogs module",
        "ui/dialogs/window_selector.py": '''# ui/dialogs/window_selector.py
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QPushButton, QGroupBox, QLineEdit, QLabel, 
                            QDialogButtonBox, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt
from core.window_manager import WindowManager
from utils.exceptions import WindowError

class WindowSelectorDialog(QDialog):
    """Dialog for selecting and managing game windows"""
    
    def __init__(self, window_manager: WindowManager, parent=None):
        super().__init__(parent)
        self.window_manager = window_manager
        self.setWindowTitle("Select Game Window")
        self.setFixedSize(500, 600)
        self._setup_ui()
        self._refresh_windows()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Window renamer section
        renamer_group = QGroupBox("Window Renamer")
        renamer_layout = QVBoxLayout(renamer_group)
        
        renamer_layout.addWidget(QLabel("Current window title:"))
        self.current_title_edit = QLineEdit()
        self.current_title_edit.setPlaceholderText("Enter exact window title to rename")
        renamer_layout.addWidget(self.current_title_edit)
        
        renamer_layout.addWidget(QLabel("New window title:"))
        self.new_title_edit = QLineEdit()
        self.new_title_edit.setPlaceholderText("Enter new window title")
        renamer_layout.addWidget(self.new_title_edit)
        
        self.rename_btn = QPushButton("Rename Window")
        self.rename_btn.clicked.connect(self._rename_window)
        renamer_layout.addWidget(self.rename_btn)
        
        layout.addWidget(renamer_group)
        
        # Window selector section
        selector_group = QGroupBox("Available Windows")
        selector_layout = QVBoxLayout(selector_group)
        
        self.window_list = QListWidget()
        self.window_list.itemDoubleClicked.connect(self.accept)
        selector_layout.addWidget(self.window_list)
        
        # Refresh button
        self.refresh_btn = QPushButton("Refresh Window List")
        self.refresh_btn.clicked.connect(self._refresh_windows)
        selector_layout.addWidget(self.refresh_btn)
        
        layout.addWidget(selector_group)
        
        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _refresh_windows(self):
        """Refresh the list of available windows"""
        self.window_list.clear()
        
        try:
            windows = self.window_manager.get_all_windows(refresh_cache=True)
            
            for window in windows:
                item = QListWidgetItem(f"{window.title} (0x{window.hwnd:X})")
                item.setData(Qt.UserRole, window.hwnd)
                self.window_list.addItem(item)
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to refresh windows: {e}")
    
    def _rename_window(self):
        """Rename a window"""
        current_title = self.current_title_edit.text().strip()
        new_title = self.new_title_edit.text().strip()
        
        if not current_title or not new_title:
            QMessageBox.warning(self, "Error", "Both current and new titles must be specified")
            return
        
        try:
            # Find window by title
            windows = self.window_manager.get_all_windows()
            target_window = None
            
            for window in windows:
                if window.title == current_title:
                    target_window = window
                    break
            
            if not target_window:
                QMessageBox.warning(self, "Error", f"Window with title '{current_title}' not found")
                return
            
            # Rename the window
            if self.window_manager.rename_window(new_title, target_window.hwnd):
                QMessageBox.information(self, "Success", "Window renamed successfully!")
                self._refresh_windows()
                self.current_title_edit.clear()
                self.new_title_edit.clear()
            
        except WindowError as e:
            QMessageBox.critical(self, "Error", f"Failed to rename window: {e}")
    
    def get_selected_window_hwnd(self):
        """Get the selected window handle"""
        current_item = self.window_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
    
    def accept(self):
        """Accept dialog and set target window"""
        hwnd = self.get_selected_window_hwnd()
        if hwnd:
            try:
                if self.window_manager.set_target_window(hwnd):
                    super().accept()
                else:
                    QMessageBox.warning(self, "Error", "Failed to set target window")
            except WindowError as e:
                QMessageBox.critical(self, "Error", f"Failed to set target window: {e}")
        else:
            QMessageBox.warning(self, "Error", "Please select a window")
''',

        "ui/dialogs/region_config.py": '''# ui/dialogs/region_config.py
# Copy the RegionConfigDialog class from the "ui_widgets_dialogs" artifact
# This dialog handles screen region configuration

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QSpinBox, 
                            QLabel, QDialogButtonBox, QPushButton, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import Qt

class RegionConfigDialog(QDialog):
    """Dialog for configuring screen regions"""
    
    def __init__(self, pixel_analyzer, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete RegionConfigDialog implementation from the artifact
''',

        "ui/dialogs/skill_config.py": '''# ui/dialogs/skill_config.py
# Copy the SkillConfigDialog class from the "ui_widgets_dialogs" artifact
# This dialog handles advanced skill configuration

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                            QTreeWidgetItem, QPushButton, QGroupBox, QLineEdit,
                            QSpinBox, QComboBox, QCheckBox, QTextEdit, QLabel,
                            QDialogButtonBox, QMessageBox, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt

class SkillConfigDialog(QDialog):
    """Advanced skill configuration dialog"""
    
    def __init__(self, skill_manager, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete SkillConfigDialog implementation from the artifact
''',

        # UI widgets
        "ui/widgets/__init__.py": "# Widgets module",
        "ui/widgets/log_widget.py": '''# ui/widgets/log_widget.py
# Copy the LogWidget class from the "ui_widgets_dialogs" artifact
# This widget displays bot logs with auto-scroll

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QTextCursor, QFont

class LogWidget(QWidget):
    """Widget for displaying bot logs"""
    
    def __init__(self, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete LogWidget implementation from the artifact
''',

        "ui/widgets/status_widget.py": '''# ui/widgets/status_widget.py
# Copy the StatusWidget class from the "ui_widgets_dialogs" artifact
# This widget displays bot status and vitals

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QProgressBar, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any

class StatusWidget(QWidget):
    """Widget for displaying bot status and vitals"""
    
    def __init__(self, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete StatusWidget implementation from the artifact
''',

        # Utils module
        "utils/__init__.py": "# Utils module",
        "utils/exceptions.py": '''# utils/exceptions.py
# Copy the exception classes from the "utils_modules" artifact
# This defines custom exceptions for error handling

class BotError(Exception):
    """Base exception for bot-related errors"""
    pass

class ConfigError(BotError):
    """Configuration-related errors"""
    pass

class AnalysisError(BotError):
    """Pixel analysis and OCR errors"""
    pass

class SkillError(BotError):
    """Skill management errors"""
    pass

class WindowError(BotError):
    """Window management errors"""
    pass

class InputError(BotError):
    """Input/control errors"""
    pass

# TODO: Copy any additional exception classes from utils_modules artifact
''',

        "utils/logger.py": '''# utils/logger.py
import logging
from datetime import datetime
from PyQt5.QtCore import QObject, pyqtSignal

class BotLogger(QObject):
    """Minimal logger for testing"""
    
    log_message = pyqtSignal(str)
    
    def __init__(self, name: str = "TantraBot"):
        super().__init__()
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
    
    def debug(self, message: str):
        self.logger.debug(message)
        self._emit_ui_message("DEBUG", message)
    
    def info(self, message: str):
        self.logger.info(message)
        self._emit_ui_message("INFO", message)
    
    def warning(self, message: str):
        self.logger.warning(message)
        self._emit_ui_message("WARNING", message)
    
    def error(self, message: str):
        self.logger.error(message)
        self._emit_ui_message("ERROR", message)
    
    def critical(self, message: str):
        self.logger.critical(message)
        self._emit_ui_message("CRITICAL", message)
    
    def _emit_ui_message(self, level: str, message: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        self.log_message.emit(formatted_message)

# TODO: Replace this minimal version with the complete implementation
# from the "utils_modules" artifact
''',

        "utils/timer_manager.py": '''# utils/timer_manager.py
# Copy the TimerManager class from the "utils_modules" artifact
# This manages multiple timers with different intervals

import time
from typing import Dict, Callable, Optional
from PyQt5.QtCore import QTimer, QObject

class TimerManager(QObject):
    """Manages multiple timers with different intervals"""
    
    def __init__(self):
        # TODO: Copy complete implementation from utils_modules artifact
        pass

# TODO: Copy the complete TimerManager implementation from the artifact
''',

        # Documentation
        "INSTALLATION.md": '''# Installation Guide

## Prerequisites

1. **Python 3.7+**: Download from https://python.org
2. **Tesseract OCR**: Required for text recognition
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

## Installation Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Tesseract path** (Windows):
   - Edit `core/pixel_analyzer.py`
   - Update the `tesseract_cmd` path to match your installation

3. **Run the bot**:
   ```bash
   python main.py
   ```

## First Time Setup

1. Select your game window using "Select Game Window"
2. Configure screen regions for HP/MP bars using "Configure Regions"
3. Set up your mob whitelist in the Control tab
4. Configure skill slots and timing in the Skills tab
5. Test pixel accuracy and OCR using the test buttons
6. Start the bot!

## Troubleshooting

- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **OCR not working**: Check Tesseract installation and path configuration
- **Window not detected**: Try running as administrator
- **Permission errors**: Check antivirus settings for PyAutoGUI

For more help, check the application logs.
''',

        "TODO.md": '''# Implementation TODO List

## Files that need code copied from artifacts:

### ✅ Ready (have content):
- [x] main.py
- [x] requirements.txt
- [x] README.md
- [x] config/default_config.ini
- [x] utils/exceptions.py (basic structure)

### 📋 Need implementation from artifacts:

#### Config Module:
- [ ] **config/config_manager.py** → Copy from "config_manager" artifact

#### Core Module:
- [ ] **core/bot_engine.py** → Copy from "bot_engine" artifact
- [ ] **core/pixel_analyzer.py** → Copy from "pixel_analyzer" artifact  
- [ ] **core/window_manager.py** → Copy from "utils_modules" artifact
- [ ] **core/input_controller.py** → Copy from "utils_modules" artifact

#### Combat Module:
- [ ] **combat/combat_manager.py** → Copy from "bot_engine" artifact
- [ ] **combat/skill_manager.py** → Copy from "skill_manager" artifact
- [ ] **combat/target_validator.py** → Copy from "bot_engine" artifact

#### UI Module:
- [ ] **ui/main_window.py** → Copy from "main_application" artifact
- [ ] **ui/dialogs/window_selector.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/dialogs/region_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/dialogs/skill_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/log_widget.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/status_widget.py** → Copy from "ui_widgets_dialogs" artifact

#### Utils Module:
- [ ] **utils/logger.py** → Copy from "utils_modules" artifact
- [ ] **utils/timer_manager.py** → Copy from "utils_modules" artifact

## After copying all code:

1. Install dependencies: `pip install -r requirements.txt`
2. Install and configure Tesseract OCR
3. Test the application: `python main.py`
4. Configure the bot for your game setup

## Notes:
- Each file has TODO comments indicating what needs to be copied
- The artifact names are specified in each file
- All imports and basic structure are already in place
- Just copy the class implementations from the corresponding artifacts
'''
    }
    
    return project_name, files

def main():
    """Generate the complete project structure"""
    print("🚀 Generating Tantra Bot v2.0 Project Structure...")
    print("=" * 60)
    
    project_name, files = create_project_structure()
    
    # Create project directory
    project_path = Path(project_name)
    if project_path.exists():
        print(f"⚠️  Directory '{project_name}' already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if response != 'y':
            print("❌ Cancelled.")
            return
        
        # Remove existing directory
        import shutil
        shutil.rmtree(project_path)
    
    project_path.mkdir()
    print(f"📁 Created directory: {project_path.absolute()}")
    
    # Create all files and directories
    created_files = 0
    created_dirs = set()
    
    for file_path, content in files.items():
        full_path = project_path / file_path
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if full_path.parent != project_path:
            created_dirs.add(str(full_path.parent.relative_to(project_path)))
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        created_files += 1
        print(f"📄 Created: {file_path}")
    
    print("=" * 60)
    print("✅ Project structure created successfully!")
    print(f"📊 Statistics:")
    print(f"   • Project directory: {project_path.absolute()}")
    print(f"   • Files created: {created_files}")
    print(f"   • Directories created: {len(created_dirs)}")
    
    print(f"\n📋 Directory structure:")
    print(f"{project_name}/")
    for dir_name in sorted(created_dirs):
        level = dir_name.count(os.sep)
        indent = "  " * (level + 1)
        base_name = os.path.basename(dir_name)
        print(f"{indent}{base_name}/")
    
    print(f"\n🎯 Next steps:")
    print(f"1. cd {project_name}")
    print(f"2. Copy code from artifacts to each file (see TODO.md)")
    print(f"3. pip install -r requirements.txt")
    print(f"4. Install Tesseract OCR")
    print(f"5. python main.py")
    
    print(f"\n📝 Files ready for code copying:")
    copy_needed = [f for f in files.keys() if "TODO: Copy" in files[f]]
    for file_path in copy_needed:
        print(f"   • {file_path}")
    
    print(f"\n✨ All files are ready with proper structure and TODO comments!")
    print(f"   Check TODO.md for detailed copy instructions.")

if __name__ == "__main__":
    main()
, target_name):
                return False
        
        return True
    
    def _is_whitelisted(self, target_name: str) -> bool:
        """Check if target is in whitelist"""
        if not self.whitelist:
            return True  # Empty whitelist means all targets allowed
        
        case_sensitive = self.validation_rules['case_sensitive']
        
        for allowed_name in self.whitelist:
            if case_sensitive:
                if allowed_name in target_name:
                    return True
            else:
                if allowed_name.lower() in target_name.lower():
                    return True
        
        return False
    
    def _is_blacklisted(self, target_name: str) -> bool:
        """Check if target is in blacklist"""
        if not self.blacklist:
            return False  # Empty blacklist means no targets forbidden
        
        case_sensitive = self.validation_rules['case_sensitive']
        
        for forbidden_name in self.blacklist:
            if case_sensitive:
                if forbidden_name in target_name:
                    return True
            else:
                if forbidden_name.lower() in target_name.lower():
                    return True
        
        return False
    
    def get_match_score(self, target_name: str) -> float:
        """Get a score indicating how well the target matches criteria"""
        if not self.is_valid_target(target_name):
            return 0.0
        
        score = 1.0
        
        # Bonus for exact whitelist matches
        case_sensitive = self.validation_rules['case_sensitive']
        for allowed_name in self.whitelist:
            if case_sensitive:
                if target_name == allowed_name:
                    score += 0.5
                elif allowed_name in target_name:
                    score += 0.2
            else:
                if target_name.lower() == allowed_name.lower():
                    score += 0.5
                elif allowed_name.lower() in target_name.lower():
                    score += 0.2
        
        return min(2.0, score)  # Cap at 2.0
    
    def set_validation_rule(self, rule_name: str, value: Any) -> None:
        """Set a validation rule"""
        self.validation_rules[rule_name] = value
        self.logger.debug(f"Validation rule '{rule_name}' set to {value}")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules"""
        return self.validation_rules.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset validation rules to defaults"""
        self.validation_rules.clear()
        self.validation_rules.update(self.default_rules)
        self.logger.info("Validation rules reset to defaults")
    
    def export_config(self) -> Dict[str, Any]:
        """Export validator configuration"""
        return {
            'whitelist': self.whitelist.copy(),
            'blacklist': self.blacklist.copy(),
            'validation_rules': self.validation_rules.copy()
        }
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """Import validator configuration"""
        if 'whitelist' in config:
            self.set_whitelist(config['whitelist'])
        
        if 'blacklist' in config:
            self.set_blacklist(config['blacklist'])
        
        if 'validation_rules' in config:
            self.validation_rules.update(config['validation_rules'])
        
        self.logger.info("Validator configuration imported")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validator statistics"""
        return {
            'whitelist_entries': len(self.whitelist),
            'blacklist_entries': len(self.blacklist),
            'validation_rules': len(self.validation_rules),
            'whitelist': self.whitelist.copy(),
            'blacklist': self.blacklist.copy()
        }
''',

        # UI module
        "ui/__init__.py": "# UI module",
        "ui/main_window.py": '''# ui/main_window.py
# Copy the TantraBotMainWindow class from the "main_application" artifact
# This is the main application window with tabbed interface

import sys
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QGroupBox, QLabel, QPushButton, QCheckBox, QSpinBox, QTextEdit,
    QTabWidget, QSplitter, QStatusBar, QMenuBar, QAction, QMessageBox,
    QProgressBar, QFrame
)
from PyQt5.QtCore import Qt, QTimer, pyqtSlot
from PyQt5.QtGui import QFont, QIcon

# TODO: Copy all imports from main_application artifact

class TantraBotMainWindow(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        # TODO: Copy complete implementation from main_application artifact
        pass

# TODO: Copy the complete TantraBotMainWindow implementation from the artifact
''',

        # UI dialogs
        "ui/dialogs/__init__.py": "# Dialogs module",
        "ui/dialogs/window_selector.py": '''# ui/dialogs/window_selector.py
# Copy the WindowSelectorDialog class from the "ui_widgets_dialogs" artifact
# This dialog handles window selection and renaming

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                            QPushButton, QGroupBox, QLineEdit, QLabel, 
                            QDialogButtonBox, QMessageBox, QListWidgetItem)
from PyQt5.QtCore import Qt

# TODO: Copy all imports from ui_widgets_dialogs artifact

class WindowSelectorDialog(QDialog):
    """Dialog for selecting and managing game windows"""
    
    def __init__(self, window_manager, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete WindowSelectorDialog implementation from the artifact
''',

        "ui/dialogs/region_config.py": '''# ui/dialogs/region_config.py
# Copy the RegionConfigDialog class from the "ui_widgets_dialogs" artifact
# This dialog handles screen region configuration

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QGridLayout, QSpinBox, 
                            QLabel, QDialogButtonBox, QPushButton, QGroupBox,
                            QMessageBox)
from PyQt5.QtCore import Qt

class RegionConfigDialog(QDialog):
    """Dialog for configuring screen regions"""
    
    def __init__(self, pixel_analyzer, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete RegionConfigDialog implementation from the artifact
''',

        "ui/dialogs/skill_config.py": '''# ui/dialogs/skill_config.py
# Copy the SkillConfigDialog class from the "ui_widgets_dialogs" artifact
# This dialog handles advanced skill configuration

from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, 
                            QTreeWidgetItem, QPushButton, QGroupBox, QLineEdit,
                            QSpinBox, QComboBox, QCheckBox, QTextEdit, QLabel,
                            QDialogButtonBox, QMessageBox, QSplitter, QTabWidget)
from PyQt5.QtCore import Qt

class SkillConfigDialog(QDialog):
    """Advanced skill configuration dialog"""
    
    def __init__(self, skill_manager, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete SkillConfigDialog implementation from the artifact
''',

        # UI widgets
        "ui/widgets/__init__.py": "# Widgets module",
        "ui/widgets/log_widget.py": '''# ui/widgets/log_widget.py
# Copy the LogWidget class from the "ui_widgets_dialogs" artifact
# This widget displays bot logs with auto-scroll

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QCheckBox
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtGui import QTextCursor, QFont

class LogWidget(QWidget):
    """Widget for displaying bot logs"""
    
    def __init__(self, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete LogWidget implementation from the artifact
''',

        "ui/widgets/status_widget.py": '''# ui/widgets/status_widget.py
# Copy the StatusWidget class from the "ui_widgets_dialogs" artifact
# This widget displays bot status and vitals

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGridLayout, QLabel, QProgressBar, QGroupBox
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from typing import Dict, Any

class StatusWidget(QWidget):
    """Widget for displaying bot status and vitals"""
    
    def __init__(self, parent=None):
        # TODO: Copy complete implementation from ui_widgets_dialogs artifact
        pass

# TODO: Copy the complete StatusWidget implementation from the artifact
''',

        # Utils module
        "utils/__init__.py": "# Utils module",
        "utils/exceptions.py": '''# utils/exceptions.py
# Copy the exception classes from the "utils_modules" artifact
# This defines custom exceptions for error handling

class BotError(Exception):
    """Base exception for bot-related errors"""
    pass

class ConfigError(BotError):
    """Configuration-related errors"""
    pass

class AnalysisError(BotError):
    """Pixel analysis and OCR errors"""
    pass

class SkillError(BotError):
    """Skill management errors"""
    pass

class WindowError(BotError):
    """Window management errors"""
    pass

class InputError(BotError):
    """Input/control errors"""
    pass

# TODO: Copy any additional exception classes from utils_modules artifact
''',

        "utils/logger.py": '''# utils/logger.py
# Copy the BotLogger class from the "utils_modules" artifact
# This provides comprehensive logging with Qt signal support

import logging
import time
from datetime import datetime
from typing import Optional
from PyQt5.QtCore import QObject, pyqtSignal

class BotLogger(QObject):
    """Custom logger for the bot with Qt signal support"""
    
    def __init__(self, name: str = "TantraBot", level: int = logging.INFO):
        # TODO: Copy complete implementation from utils_modules artifact
        pass

# TODO: Copy the complete BotLogger implementation from the artifact
''',

        "utils/timer_manager.py": '''# utils/timer_manager.py
# Copy the TimerManager class from the "utils_modules" artifact
# This manages multiple timers with different intervals

import time
from typing import Dict, Callable, Optional
from PyQt5.QtCore import QTimer, QObject

class TimerManager(QObject):
    """Manages multiple timers with different intervals"""
    
    def __init__(self):
        # TODO: Copy complete implementation from utils_modules artifact
        pass

# TODO: Copy the complete TimerManager implementation from the artifact
''',

        # Documentation
        "INSTALLATION.md": '''# Installation Guide

## Prerequisites

1. **Python 3.7+**: Download from https://python.org
2. **Tesseract OCR**: Required for text recognition
   - Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`

## Installation Steps

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Tesseract path** (Windows):
   - Edit `core/pixel_analyzer.py`
   - Update the `tesseract_cmd` path to match your installation

3. **Run the bot**:
   ```bash
   python main.py
   ```

## First Time Setup

1. Select your game window using "Select Game Window"
2. Configure screen regions for HP/MP bars using "Configure Regions"
3. Set up your mob whitelist in the Control tab
4. Configure skill slots and timing in the Skills tab
5. Test pixel accuracy and OCR using the test buttons
6. Start the bot!

## Troubleshooting

- **Import errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
- **OCR not working**: Check Tesseract installation and path configuration
- **Window not detected**: Try running as administrator
- **Permission errors**: Check antivirus settings for PyAutoGUI

For more help, check the application logs.
''',

        "TODO.md": '''# Implementation TODO List

## Files that need code copied from artifacts:

### ✅ Ready (have content):
- [x] main.py
- [x] requirements.txt
- [x] README.md
- [x] config/default_config.ini
- [x] utils/exceptions.py (basic structure)

### 📋 Need implementation from artifacts:

#### Config Module:
- [ ] **config/config_manager.py** → Copy from "config_manager" artifact

#### Core Module:
- [ ] **core/bot_engine.py** → Copy from "bot_engine" artifact
- [ ] **core/pixel_analyzer.py** → Copy from "pixel_analyzer" artifact  
- [ ] **core/window_manager.py** → Copy from "utils_modules" artifact
- [ ] **core/input_controller.py** → Copy from "utils_modules" artifact

#### Combat Module:
- [ ] **combat/combat_manager.py** → Copy from "bot_engine" artifact
- [ ] **combat/skill_manager.py** → Copy from "skill_manager" artifact
- [ ] **combat/target_validator.py** → Copy from "bot_engine" artifact

#### UI Module:
- [ ] **ui/main_window.py** → Copy from "main_application" artifact
- [ ] **ui/dialogs/window_selector.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/dialogs/region_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/dialogs/skill_config.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/log_widget.py** → Copy from "ui_widgets_dialogs" artifact
- [ ] **ui/widgets/status_widget.py** → Copy from "ui_widgets_dialogs" artifact

#### Utils Module:
- [ ] **utils/logger.py** → Copy from "utils_modules" artifact
- [ ] **utils/timer_manager.py** → Copy from "utils_modules" artifact

## After copying all code:

1. Install dependencies: `pip install -r requirements.txt`
2. Install and configure Tesseract OCR
3. Test the application: `python main.py`
4. Configure the bot for your game setup

## Notes:
- Each file has TODO comments indicating what needs to be copied
- The artifact names are specified in each file
- All imports and basic structure are already in place
- Just copy the class implementations from the corresponding artifacts
'''
    }
    
    return project_name, files

def main():
    """Generate the complete project structure"""
    print("🚀 Generating Tantra Bot v2.0 Project Structure...")
    print("=" * 60)
    
    project_name, files = create_project_structure()
    
    # Create project directory
    project_path = Path(project_name)
    if project_path.exists():
        print(f"⚠️  Directory '{project_name}' already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower().strip()
        if response != 'y':
            print("❌ Cancelled.")
            return
        
        # Remove existing directory
        import shutil
        shutil.rmtree(project_path)
    
    project_path.mkdir()
    print(f"📁 Created directory: {project_path.absolute()}")
    
    # Create all files and directories
    created_files = 0
    created_dirs = set()
    
    for file_path, content in files.items():
        full_path = project_path / file_path
        
        # Create parent directories
        full_path.parent.mkdir(parents=True, exist_ok=True)
        if full_path.parent != project_path:
            created_dirs.add(str(full_path.parent.relative_to(project_path)))
        
        # Write file
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        created_files += 1
        print(f"📄 Created: {file_path}")
    
    print("=" * 60)
    print("✅ Project structure created successfully!")
    print(f"📊 Statistics:")
    print(f"   • Project directory: {project_path.absolute()}")
    print(f"   • Files created: {created_files}")
    print(f"   • Directories created: {len(created_dirs)}")
    
    print(f"\n📋 Directory structure:")
    print(f"{project_name}/")
    for dir_name in sorted(created_dirs):
        level = dir_name.count(os.sep)
        indent = "  " * (level + 1)
        base_name = os.path.basename(dir_name)
        print(f"{indent}{base_name}/")
    
    print(f"\n🎯 Next steps:")
    print(f"1. cd {project_name}")
    print(f"2. Copy code from artifacts to each file (see TODO.md)")
    print(f"3. pip install -r requirements.txt")
    print(f"4. Install Tesseract OCR")
    print(f"5. python main.py")
    
    print(f"\n📝 Files ready for code copying:")
    copy_needed = [f for f in files.keys() if "TODO: Copy" in files[f]]
    for file_path in copy_needed:
        print(f"   • {file_path}")
    
    print(f"\ All files are ready with proper structure and TODO comments!")
    print(f"   Check TODO.md for detailed copy instructions.")

if __name__ == "__main__":
    main()