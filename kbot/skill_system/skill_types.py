# skill_system/skill_types.py
"""
Data structures and enums for the Visual Skill System
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
import numpy as np


class SkillType(Enum):
    """Enhanced skill types for visual detection system"""
    VISUAL = "visual"           # Skill with icon and visual cooldown
    TIMED = "timed"            # Buff with duration but no visual cooldown
    MANUAL = "manual"          # Action without icon (items, interactions)
    COMBO = "combo"            # Skills requiring sequence
    INSTANT = "instant"        # Instant cast skills
    CHANNELED = "channeled"    # Channeled abilities
    TOGGLE = "toggle"          # Toggle buffs
    POTION = "potion"          # Consumables


class SkillState(Enum):
    """Visual states of skills"""
    READY = "ready"            # Available for use
    COOLDOWN = "cooldown"      # On cooldown (visual overlay)
    CASTING = "casting"        # Currently being cast
    UNAVAILABLE = "unavailable" # Not usable (no mana, requirements not met)
    NOT_LEARNED = "not_learned" # Skill not learned
    UNKNOWN = "unknown"        # Cannot determine state


class DetectionMethod(Enum):
    """Methods for detecting skill state"""
    TEMPLATE_MATCH = "template_match"
    COLOR_ANALYSIS = "color_analysis"
    COOLDOWN_OVERLAY = "cooldown_overlay"
    TEXT_RECOGNITION = "text_recognition"


@dataclass
class SkillPosition:
    """Position of a skill in the skill bar"""
    slot_index: int             # 0-based slot index
    region: Tuple[int, int, int, int]  # (x, y, width, height)
    bar_type: str = "main"      # main, secondary, etc.


@dataclass
class DetectionConfig:
    """Configuration for visual detection"""
    template_threshold: float = 0.85
    cooldown_threshold: float = 0.7
    scan_interval: float = 0.1
    use_multi_scale: bool = True
    scale_range: Tuple[float, float] = (0.8, 1.2)
    detection_methods: List[DetectionMethod] = field(
        default_factory=lambda: [DetectionMethod.TEMPLATE_MATCH, DetectionMethod.COOLDOWN_OVERLAY]
    )


@dataclass
class VisualSkill:
    """Enhanced skill with visual detection capabilities"""
    
    # Basic properties
    name: str
    key: str
    skill_type: SkillType
    
    # Visual properties
    icon_path: Optional[str] = None
    icon_template: Optional[np.ndarray] = None
    position: Optional[SkillPosition] = None
    
    # Timing properties
    cooldown_duration: float = 0.0
    cast_time: float = 0.0
    last_used: float = 0.0
    
    # Detection properties
    has_visual_cooldown: bool = True
    detection_config: DetectionConfig = field(default_factory=DetectionConfig)
    
    # Game mechanics
    mana_cost: int = 0
    priority: int = 1
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    
    # State tracking
    current_state: SkillState = SkillState.UNKNOWN
    detection_confidence: float = 0.0
    last_detection_time: float = 0.0
    
    # Configuration
    enabled: bool = True
    description: str = ""
    
    # Advanced features
    combo_sequence: List[str] = field(default_factory=list)
    buff_duration: float = 0.0
    recast_prevention: bool = False
    range_check: bool = False
    
    def is_ready(self) -> bool:
        """Check if skill is ready to use"""
        current_time = time.time()
        
        if not self.enabled:
            return False
            
        # Check basic cooldown
        if current_time - self.last_used < self.cooldown_duration:
            return False
            
        # For visual skills, check detected state
        if self.skill_type == SkillType.VISUAL:
            return self.current_state == SkillState.READY
            
        # For timed buffs, check if we should recast
        if self.skill_type == SkillType.TIMED:
            if self.recast_prevention and current_time - self.last_used < self.buff_duration:
                return False
                
        return True
    
    def update_state(self, new_state: SkillState, confidence: float = 1.0):
        """Update skill state from detection"""
        self.current_state = new_state
        self.detection_confidence = confidence
        self.last_detection_time = time.time()
    
    def execute(self) -> bool:
        """Mark skill as executed"""
        if self.is_ready():
            self.last_used = time.time()
            return True
        return False
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time"""
        current_time = time.time()
        elapsed = current_time - self.last_used
        remaining = max(0, self.cooldown_duration - elapsed)
        return remaining


@dataclass
class SkillBarMapping:
    """Mapping of skill bar positions to detected skills"""
    bar_region: Tuple[int, int, int, int]  # Overall skill bar region
    slot_regions: List[Tuple[int, int, int, int]]  # Individual slot regions
    detected_skills: Dict[int, VisualSkill] = field(default_factory=dict)  # slot_index -> skill
    last_scan_time: float = 0.0
    scan_interval: float = 1.0  # How often to rescan
    
    def needs_rescan(self) -> bool:
        """Check if skill bar needs to be rescanned"""
        current_time = time.time()
        return current_time - self.last_scan_time > self.scan_interval
    
    def update_scan_time(self):
        """Update last scan time"""
        self.last_scan_time = time.time()


@dataclass
class VisualRotation:
    """Enhanced rotation with visual state awareness"""
    name: str
    skill_names: List[str]
    current_index: int = 0
    repeat: bool = True
    enabled: bool = True
    
    # Visual features
    adaptive: bool = True  # Adapt based on skill availability
    priority_override: bool = True  # Allow high-priority skills to interrupt
    
    # State tracking
    skills_used: int = 0
    last_skill_time: float = 0.0
    
    def get_next_skill(self, available_skills: Dict[str, VisualSkill]) -> Optional[str]:
        """Get next skill considering visual states"""
        if not self.enabled or not self.skill_names:
            return None
            
        # If adaptive, find next available skill
        if self.adaptive:
            attempts = 0
            while attempts < len(self.skill_names):
                skill_name = self.skill_names[self.current_index]
                skill = available_skills.get(skill_name)
                
                if skill and skill.is_ready():
                    self._advance_index()
                    self.skills_used += 1
                    self.last_skill_time = time.time()
                    return skill_name
                    
                self._advance_index()
                attempts += 1
                
            return None
        else:
            # Traditional rotation - return next skill regardless of state
            skill_name = self.skill_names[self.current_index]
            self._advance_index()
            self.skills_used += 1
            self.last_skill_time = time.time()
            return skill_name
    
    def _advance_index(self):
        """Advance to next skill in rotation"""
        self.current_index += 1
        if self.current_index >= len(self.skill_names):
            if self.repeat:
                self.current_index = 0
            else:
                self.enabled = False
                self.current_index = len(self.skill_names) - 1
    
    def reset(self):
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0


@dataclass
class ClassProfile:
    """Profile for a specific character class"""
    class_name: str
    display_name: str
    resource_path: str
    skills: Dict[str, VisualSkill] = field(default_factory=dict)
    rotations: Dict[str, VisualRotation] = field(default_factory=dict)
    active_rotation: Optional[str] = None
    skill_bar_mapping: Optional[SkillBarMapping] = None
    
    # Class-specific settings
    detection_settings: DetectionConfig = field(default_factory=DetectionConfig)
    auto_detect_enabled: bool = True
    
    def get_skill_by_key(self, key: str) -> Optional[VisualSkill]:
        """Find skill by hotkey"""
        for skill in self.skills.values():
            if skill.key.lower() == key.lower():
                return skill
        return None
    
    def get_ready_skills(self) -> List[VisualSkill]:
        """Get all skills that are ready to use"""
        return [skill for skill in self.skills.values() if skill.is_ready()]


@dataclass
class DetectionResult:
    """Result of a skill detection operation"""
    position: SkillPosition
    detected_skill: Optional[VisualSkill]
    state: SkillState
    confidence: float
    detection_time: float
    method_used: DetectionMethod
    
    @property
    def is_valid(self) -> bool:
        """Check if detection result is valid"""
        return self.confidence > 0.5 and self.detected_skill is not None


@dataclass
class SkillExecutionResult:
    """Result of skill execution attempt"""
    skill_name: str
    success: bool
    execution_time: float
    error_message: Optional[str] = None
    verification_passed: bool = False
    
    # Performance metrics
    input_delay: float = 0.0
    verification_delay: float = 0.0