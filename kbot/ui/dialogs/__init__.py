# FILE: ui/dialogs/__init__.py
"""UI dialogs module for Tantra Bot"""

from .window_selector import WindowSelectorDialog
from .region_config import RegionConfigDialog
from .skill_config import SkillConfigDialog

__all__ = [
    'WindowSelectorDialog',
    'RegionConfigDialog', 
    'SkillConfigDialog'
]