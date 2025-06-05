# combat/skill_manager.py
import time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass
from utils.exceptions import SkillError
from core.input_controller import InputController

class SkillType(Enum):
    OFFENSIVE = "offensive"
    DEFENSIVE = "defensive"
    BUFF = "buff"
    DEBUFF = "debuff"
    UTILITY = "utility"
    POTION = "potion"

class TriggerCondition(Enum):
    HP_BELOW = "hp_below"
    MP_BELOW = "mp_below"
    TARGET_HP_BELOW = "target_hp_below"
    COOLDOWN_READY = "cooldown_ready"
    COMBAT_START = "combat_start"
    NO_TARGET = "no_target"
    CUSTOM = "custom"

@dataclass
class Skill:
    """Represents a single skill/action"""
    name: str
    key: str  # Keyboard key or key combination
    cooldown: float  # Cooldown in seconds
    skill_type: SkillType
    priority: int = 1  # Higher number = higher priority
    mana_cost: int = 0
    conditions: List[Dict[str, Any]] = None
    description: str = ""
    enabled: bool = True
    
    def __post_init__(self):
        if self.conditions is None:
            self.conditions = []

@dataclass
class SkillUsage:
    """Tracks skill usage statistics"""
    last_used: float = 0.0
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_uses == 0:
            return 0.0
        return self.successful_uses / self.total_uses

class SkillRotation:
    """Defines a sequence of skills to execute"""
    
    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills  # List of skill names
        self.repeat = repeat
        self.current_index = 0
        self.enabled = True
    
    def get_next_skill(self) -> Optional[str]:
        """Get the next skill in the rotation"""
        if not self.enabled or not self.skills:
            return None
        
        skill_name = self.skills[self.current_index]
        self._advance_index()
        return skill_name
    
    def _advance_index(self) -> None:
        """Advance to next skill in rotation"""
        self.current_index += 1
        if self.current_index >= len(self.skills):
            if self.repeat:
                self.current_index = 0
            else:
                self.enabled = False
    
    def reset(self) -> None:
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True

class SkillManager:
    """Advanced skill management system"""
    
    def __init__(self, input_controller: InputController):
        self.input_controller = input_controller
        self.skills: Dict[str, Skill] = {}
        self.rotations: Dict[str, SkillRotation] = {}
        self.usage_stats: Dict[str, SkillUsage] = {}
        self.active_rotation: Optional[str] = None
        self.global_cooldown = 0.5  # Global cooldown between any skills
        self.last_skill_used = 0.0
        
        # Condition evaluators
        self.condition_evaluators: Dict[TriggerCondition, Callable] = {
            TriggerCondition.HP_BELOW: self._eval_hp_below,
            TriggerCondition.MP_BELOW: self._eval_mp_below,
            TriggerCondition.TARGET_HP_BELOW: self._eval_target_hp_below,
            TriggerCondition.COOLDOWN_READY: self._eval_cooldown_ready,
            TriggerCondition.COMBAT_START: self._eval_combat_start,
            TriggerCondition.NO_TARGET: self._eval_no_target,
            TriggerCondition.CUSTOM: self._eval_custom
        }
        
        # Game state (updated externally)
        self.game_state = {
            'hp': 100,
            'mp': 100,
            'target_hp': 0,
            'target_exists': False,
            'in_combat': False
        }
    
    def register_skill(self, skill: Skill) -> None:
        """Register a new skill"""
        if skill.name in self.skills:
            raise SkillError(f"Skill '{skill.name}' already exists")
        
        self.skills[skill.name] = skill
        self.usage_stats[skill.name] = SkillUsage()
    
    def remove_skill(self, skill_name: str) -> None:
        """Remove a skill"""
        if skill_name in self.skills:
            del self.skills[skill_name]
            del self.usage_stats[skill_name]
    
    def create_rotation(self, name: str, skill_names: List[str], repeat: bool = True) -> None:
        """Create a new skill rotation"""
        # Validate that all skills exist
        for skill_name in skill_names:
            if skill_name not in self.skills:
                raise SkillError(f"Skill '{skill_name}' not found")
        
        self.rotations[name] = SkillRotation(name, skill_names, repeat)
    
    def set_active_rotation(self, rotation_name: Optional[str]) -> None:
        """Set the active rotation"""
        if rotation_name and rotation_name not in self.rotations:
            raise SkillError(f"Rotation '{rotation_name}' not found")
        
        self.active_rotation = rotation_name
        if rotation_name:
            self.rotations[rotation_name].reset()
    
    def update_game_state(self, state: Dict[str, Any]) -> None:
        """Update current game state for condition evaluation"""
        self.game_state.update(state)
    
    def can_use_skill(self, skill_name: str) -> bool:
        """Check if a skill can be used"""
        if skill_name not in self.skills:
            return False
        
        skill = self.skills[skill_name]
        
        # Check if skill is enabled
        if not skill.enabled:
            return False
        
        # Check global cooldown
        current_time = time.time()
        if current_time - self.last_skill_used < self.global_cooldown:
            return False
        
        # Check skill-specific cooldown
        usage = self.usage_stats[skill_name]
        if current_time - usage.last_used < skill.cooldown:
            return False
        
        # Check mana cost
        if skill.mana_cost > self.game_state.get('mp', 0):
            return False
        
        # Check conditions
        return self._evaluate_conditions(skill)
    
    def use_skill(self, skill_name: str, force: bool = False) -> bool:
        """Execute a skill"""
        if skill_name not in self.skills:
            raise SkillError(f"Skill '{skill_name}' not found")
        
        skill = self.skills[skill_name]
        usage = self.usage_stats[skill_name]
        
        # Check if skill can be used (unless forced)
        if not force and not self.can_use_skill(skill_name):
            usage.failed_uses += 1
            return False
        
        try:
            # Execute the skill
            success = self.input_controller.send_key(skill.key)
            
            # Update usage statistics
            current_time = time.time()
            usage.last_used = current_time
            usage.total_uses += 1
            self.last_skill_used = current_time
            
            if success:
                usage.successful_uses += 1
                return True
            else:
                usage.failed_uses += 1
                return False
                
        except Exception as e:
            usage.failed_uses += 1
            raise SkillError(f"Failed to execute skill '{skill_name}': {e}")
    
    def get_next_skill(self) -> Optional[str]:
        """Get the next skill to use based on rotation and priorities"""
        # If we have an active rotation, use it
        if self.active_rotation and self.active_rotation in self.rotations:
            rotation = self.rotations[self.active_rotation]
            next_skill = rotation.get_next_skill()
            
            # Check if the skill from rotation can be used
            if next_skill and self.can_use_skill(next_skill):
                return next_skill
        
        # Fall back to priority-based selection
        return self._get_priority_skill()
    
    def _get_priority_skill(self) -> Optional[str]:
        """Get highest priority skill that can be used"""
        available_skills = []
        
        for skill_name, skill in self.skills.items():
            if self.can_use_skill(skill_name):
                available_skills.append((skill.priority, skill_name))
        
        if available_skills:
            # Sort by priority (highest first) and return the skill name
            available_skills.sort(reverse=True)
            return available_skills[0][1]
        
        return None
    
    def _evaluate_conditions(self, skill: Skill) -> bool:
        """Evaluate all conditions for a skill"""
        if not skill.conditions:
            return True
        
        for condition in skill.conditions:
            condition_type = TriggerCondition(condition['type'])
            evaluator = self.condition_evaluators.get(condition_type)
            
            if evaluator and not evaluator(condition):
                return False
        
        return True
    
    def _eval_hp_below(self, condition: Dict[str, Any]) -> bool:
        """Evaluate HP below condition"""
        threshold = condition.get('value', 50)
        return self.game_state.get('hp', 100) < threshold
    
    def _eval_mp_below(self, condition: Dict[str, Any]) -> bool:
        """Evaluate MP below condition"""
        threshold = condition.get('value', 50)
        return self.game_state.get('mp', 100) < threshold
    
    def _eval_target_hp_below(self, condition: Dict[str, Any]) -> bool:
        """Evaluate target HP below condition"""
        threshold = condition.get('value', 50)
        return (self.game_state.get('target_exists', False) and 
                self.game_state.get('target_hp', 0) < threshold)
    
    def _eval_cooldown_ready(self, condition: Dict[str, Any]) -> bool:
        """Evaluate cooldown ready condition"""
        skill_name = condition.get('skill')
        if not skill_name or skill_name not in self.skills:
            return False
        
        usage = self.usage_stats[skill_name]
        skill = self.skills[skill_name]
        current_time = time.time()
        
        return current_time - usage.last_used >= skill.cooldown
    
    def _eval_combat_start(self, condition: Dict[str, Any]) -> bool:
        """Evaluate combat start condition"""
        return self.game_state.get('in_combat', False)
    
    def _eval_no_target(self, condition: Dict[str, Any]) -> bool:
        """Evaluate no target condition"""
        return not self.game_state.get('target_exists', False)
    
    def _eval_custom(self, condition: Dict[str, Any]) -> bool:
        """Evaluate custom condition"""
        # For custom conditions, we expect a function name and parameters
        func_name = condition.get('function')
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            return func(condition.get('params', {}))
        return False
    
    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Get detailed information about a skill"""
        if skill_name not in self.skills:
            raise SkillError(f"Skill '{skill_name}' not found")
        
        skill = self.skills[skill_name]
        usage = self.usage_stats[skill_name]
        current_time = time.time()
        
        return {
            'name': skill.name,
            'key': skill.key,
            'type': skill.skill_type.value,
            'priority': skill.priority,
            'cooldown': skill.cooldown,
            'mana_cost': skill.mana_cost,
            'enabled': skill.enabled,
            'description': skill.description,
            'can_use': self.can_use_skill(skill_name),
            'cooldown_remaining': max(0, skill.cooldown - (current_time - usage.last_used)),
            'usage_stats': {
                'total_uses': usage.total_uses,
                'successful_uses': usage.successful_uses,
                'failed_uses': usage.failed_uses,
                'success_rate': usage.success_rate,
                'last_used': usage.last_used
            }
        }
    
    def get_all_skills_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all skills"""
        return {name: self.get_skill_info(name) for name in self.skills.keys()}
    
    def reset_usage_stats(self, skill_name: Optional[str] = None) -> None:
        """Reset usage statistics"""
        if skill_name:
            if skill_name in self.usage_stats:
                self.usage_stats[skill_name] = SkillUsage()
        else:
            for name in self.usage_stats:
                self.usage_stats[name] = SkillUsage()
    
    def export_config(self) -> Dict[str, Any]:
        """Export skill configuration"""
        skills_data = {}
        for name, skill in self.skills.items():
            skills_data[name] = {
                'key': skill.key,
                'cooldown': skill.cooldown,
                'skill_type': skill.skill_type.value,
                'priority': skill.priority,
                'mana_cost': skill.mana_cost,
                'conditions': skill.conditions,
                'description': skill.description,
                'enabled': skill.enabled
            }
        
        rotations_data = {}
        for name, rotation in self.rotations.items():
            rotations_data[name] = {
                'skills': rotation.skills,
                'repeat': rotation.repeat,
                'enabled': rotation.enabled
            }
        
        return {
            'skills': skills_data,
            'rotations': rotations_data,
            'active_rotation': self.active_rotation,
            'global_cooldown': self.global_cooldown
        }
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """Import skill configuration"""
        # Clear existing configuration
        self.skills.clear()
        self.rotations.clear()
        self.usage_stats.clear()
        
        # Import skills
        skills_data = config.get('skills', {})
        for name, skill_data in skills_data.items():
            skill = Skill(
                name=name,
                key=skill_data['key'],
                cooldown=skill_data['cooldown'],
                skill_type=SkillType(skill_data['skill_type']),
                priority=skill_data.get('priority', 1),
                mana_cost=skill_data.get('mana_cost', 0),
                conditions=skill_data.get('conditions', []),
                description=skill_data.get('description', ''),
                enabled=skill_data.get('enabled', True)
            )
            self.register_skill(skill)
        
        # Import rotations
        rotations_data = config.get('rotations', {})
        for name, rotation_data in rotations_data.items():
            self.create_rotation(
                name,
                rotation_data['skills'],
                rotation_data.get('repeat', True)
            )
            self.rotations[name].enabled = rotation_data.get('enabled', True)
        
        # Set active rotation
        self.active_rotation = config.get('active_rotation')
        self.global_cooldown = config.get('global_cooldown', 0.5)

# Predefined skill templates for common Tantra skills
class TantraSkillTemplates:
    """Common Tantra skill templates"""
    
    @staticmethod
    def create_basic_skills() -> List[Skill]:
        """Create basic Tantra skills"""
        return [
            # Attack skills
            Skill("Basic Attack", "r", 1.5, SkillType.OFFENSIVE, priority=1),
            
            # Potions
            Skill("HP Potion", "0", 0.5, SkillType.UTILITY, priority=10,
                  conditions=[{'type': 'hp_below', 'value': 70}]),
            Skill("MP Potion", "9", 0.5, SkillType.UTILITY, priority=10,
                  conditions=[{'type': 'mp_below', 'value': 70}]),
            
            # Function key skills (F1-F10 with default 120 second cooldowns)
            *[Skill(f"Skill F{i}", f"f{i}", 120.0, SkillType.OFFENSIVE, priority=5)
              for i in range(1, 11)],
            
            # Number key skills (1-8)
            Skill("Skill 1", "1", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 2", "2", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 3", "3", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 4", "4", 150.0, SkillType.OFFENSIVE, priority=7),
            Skill("Skill 5", "5", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 6", "6", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 7", "7", 150.0, SkillType.OFFENSIVE, priority=7),
            Skill("Skill 8", "8", 600.0, SkillType.OFFENSIVE, priority=9),
        ]