# skill_system/__init__.py
"""
Visual Skill Detection System for KBOT

This module implements a complete computer vision-based skill detection and execution
system to replace the traditional skill management approach.

Components:
- VisualSkillSystem: Main system coordinator
- SkillDetector: OpenCV-based visual detection
- ClassManager: Resource and class management
- ExecutionEngine: Smart skill execution
- SkillTypes: Data structures and enums
"""

from .visual_system import VisualSkillSystem
from .skill_types import SkillType, SkillState, VisualSkill
from .detector import SkillDetector
from .class_manager import ClassManager
from .execution import ExecutionEngine
from .integration import SkillSystemIntegrator

__version__ = "3.0.0"
__author__ = "KBOT Team"

__all__ = [
    "VisualSkillSystem",
    "SkillDetector", 
    "ClassManager",
    "ExecutionEngine",
    "SkillSystemIntegrator",
    "SkillType",
    "SkillState",
    "VisualSkill"
]