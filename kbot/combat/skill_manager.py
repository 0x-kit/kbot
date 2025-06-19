# combat/skill_manager.py - VERSIÓN LIMPIA SIN DUPLICACIONES

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
    HP_POTION = "hp_potion"
    MP_POTION = "mp_potion"
    AUTO_ATTACK = "auto_attack"
    ASSIST = "assist"


class TriggerCondition(Enum):
    """Define las condiciones que pueden activar una habilidad."""

    HP_BELOW = "hp_below"
    MP_BELOW = "mp_below"
    TARGET_HP_ABOVE = "target_hp_above"
    TARGET_HP_BELOW = "target_hp_below"
    IN_COMBAT = "in_combat"
    OUT_OF_COMBAT = "out_of_combat"


@dataclass
class Skill:
    """Represents a single skill/action"""

    name: str
    key: str
    cooldown: float
    skill_type: SkillType
    priority: int = 1
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
    """✅ VERSIÓN ÚNICA Y CORREGIDA - Sistema de rotación de skills"""

    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills
        self.repeat = repeat
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0

    def get_next_skill(self) -> Optional[str]:
        """✅ Obtiene el siguiente skill en la rotación"""
        if not self.enabled or not self.skills:
            return None

        # Obtener skill actual
        skill_name = self.skills[self.current_index]

        # Avanzar índice
        self._advance_index()
        self.skills_used += 1

        return skill_name

    def _advance_index(self) -> None:
        """✅ Avanza al siguiente skill en la rotación"""
        self.current_index += 1

        if self.current_index >= len(self.skills):
            if self.repeat:
                self.current_index = 0
            else:
                self.enabled = False
                self.current_index = len(self.skills) - 1

    def reset(self) -> None:
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0

    def get_current_skill(self) -> Optional[str]:
        """Get current skill without advancing"""
        if not self.enabled or not self.skills:
            return None
        return self.skills[self.current_index]

    def get_status(self) -> Dict[str, Any]:
        """Get rotation status for debugging"""
        next_index = (self.current_index + 1) % len(self.skills) if self.skills else 0

        return {
            "name": self.name,
            "current_index": self.current_index,
            "total_skills": len(self.skills),
            "current_skill": self.skills[self.current_index] if self.skills else None,
            "next_skill": self.skills[next_index] if self.skills else None,
            "enabled": self.enabled,
            "repeat": self.repeat,
            "skills_used": self.skills_used,
            "all_skills": self.skills.copy(),
        }


class SkillManager:
    """✅ VERSIÓN OPTIMIZADA - Advanced skill management system"""

    def __init__(self, input_controller: InputController, logger=None):
        self.input_controller = input_controller

        if logger:
            self.logger = logger
        else:
            from utils.logger import BotLogger

            self.logger = BotLogger("SkillManager")

        self.skills: Dict[str, Skill] = {}
        self.rotations: Dict[str, SkillRotation] = {}
        self.usage_stats: Dict[str, SkillUsage] = {}
        self.active_rotation: Optional[str] = None

        # ✅ TIMING OPTIMIZADO
        self.global_cooldown = 0.15  # Reducido de 0.2s
        self.last_skill_used = 0.0

        # Game state (updated externally)
        self.game_state = {
            "hp": 100,
            "mp": 100,
            "target_hp": 0,
            "target_exists": False,
            "in_combat": False,
        }

        self.condition_evaluators: Dict[TriggerCondition, Callable] = {
            TriggerCondition.HP_BELOW: self._eval_hp_below,
            TriggerCondition.MP_BELOW: self._eval_mp_below,
            TriggerCondition.TARGET_HP_ABOVE: self._eval_target_hp_above,
            TriggerCondition.TARGET_HP_BELOW: self._eval_target_hp_below,
            TriggerCondition.IN_COMBAT: self._eval_in_combat,
            TriggerCondition.OUT_OF_COMBAT: self._eval_out_of_combat,
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

    def create_rotation(
        self, name: str, skill_names: List[str], repeat: bool = True
    ) -> None:
        """Create a new skill rotation"""
        for skill_name in skill_names:
            if skill_name not in self.skills:
                raise SkillError(f"Skill '{skill_name}' not found")

        self.rotations[name] = SkillRotation(name, skill_names, repeat)

    def set_active_rotation(self, rotation_name: Optional[str]) -> None:
        """✅ Set active rotation with proper reset"""
        if rotation_name and rotation_name not in self.rotations:
            raise SkillError(f"Rotation '{rotation_name}' not found")

        # Reset new rotation if switching
        if rotation_name and rotation_name != self.active_rotation:
            self.rotations[rotation_name].reset()

        self.active_rotation = rotation_name

    def update_game_state(self, state: Dict[str, Any]) -> None:
        """Update current game state for condition evaluation"""
        self.game_state.update(state)

    def can_use_skill(self, skill_name: str) -> bool:
        """✅ Optimized skill availability check"""
        if skill_name not in self.skills:
            return False

        skill = self.skills[skill_name]
        if not skill.enabled:
            return False

        current_time = time.time()

        # Global cooldown check
        if current_time - self.last_skill_used < self.global_cooldown:
            return False

        # Skill-specific cooldown check
        usage = self.usage_stats[skill_name]
        if current_time - usage.last_used < skill.cooldown:
            return False

        # Mana cost check
        if skill.mana_cost > self.game_state.get("mp", 0):
            return False

        # Conditions check
        if not self._evaluate_conditions(skill):
            return False

        return True

    def use_skill(self, skill_name: str, force: bool = False) -> bool:
        """✅ Optimized skill execution"""
        if skill_name not in self.skills:
            raise SkillError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]
        usage = self.usage_stats[skill_name]

        # Check availability unless forced
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
        """✅ SISTEMA DE DECISIÓN OPTIMIZADO - Prioridades + Rotación"""

        # Paso 1: Buscar skills de emergencia/alta prioridad
        emergency_skills = []
        for skill_name, skill in self.skills.items():
            # Excluir pociones del sistema normal (se manejan en vitals)
            if skill.skill_type in [SkillType.HP_POTION, SkillType.MP_POTION]:
                continue

            if self.can_use_skill(skill_name) and skill.priority > 5:
                emergency_skills.append(skill)

        # Si hay skills de emergencia, usar el de mayor prioridad
        if emergency_skills:
            emergency_skills.sort(key=lambda s: s.priority, reverse=True)
            return emergency_skills[0].name

        # Paso 2: Usar rotación activa
        if self.active_rotation and self.active_rotation in self.rotations:
            rotation = self.rotations[self.active_rotation]
            if rotation.enabled and rotation.skills:
                next_skill = rotation.get_next_skill()

                # Verificar si el skill de la rotación está disponible
                if next_skill and self.can_use_skill(next_skill):
                    return next_skill

        # Paso 3: Fallback a skills de baja prioridad disponibles
        fallback_skills = []
        for skill_name, skill in self.skills.items():
            if (
                skill.skill_type not in [SkillType.HP_POTION, SkillType.MP_POTION]
                and self.can_use_skill(skill_name)
                and skill.priority <= 5
            ):
                fallback_skills.append(skill)

        if fallback_skills:
            fallback_skills.sort(key=lambda s: s.priority, reverse=True)
            return fallback_skills[0].name

        return None

    def _evaluate_conditions(self, skill: Skill) -> bool:
        """✅ Optimized condition evaluation"""
        if not skill.conditions:
            return True

        for condition in skill.conditions:
            try:
                cond_type = TriggerCondition(condition["type"])
                evaluator = self.condition_evaluators.get(cond_type)

                if not evaluator or not evaluator(condition.get("value")):
                    return False
            except (ValueError, KeyError):
                self.logger.warning(
                    f"Invalid condition in skill '{skill.name}': {condition}"
                )
                return False

        return True

    # ✅ CONDITION EVALUATORS
    def _eval_hp_below(self, value: int) -> bool:
        return self.game_state.get("hp", 100) < value

    def _eval_mp_below(self, value: int) -> bool:
        return self.game_state.get("mp", 100) < value

    def _eval_target_hp_above(self, value: int) -> bool:
        return (
            self.game_state.get("target_exists", False)
            and self.game_state.get("target_hp", 0) > value
        )

    def _eval_target_hp_below(self, value: int) -> bool:
        return (
            self.game_state.get("target_exists", False)
            and self.game_state.get("target_hp", 0) < value
        )

    def _eval_in_combat(self, value: Any) -> bool:
        return self.game_state.get("in_combat", False)

    def _eval_out_of_combat(self, value: Any) -> bool:
        return not self.game_state.get("in_combat", False)

    def find_skill_by_type(self, skill_type: SkillType) -> Optional[Skill]:
        """✅ Find first enabled skill of given type"""
        for skill in self.skills.values():
            if skill.skill_type == skill_type and skill.enabled:
                return skill
        return None

    def get_buffs_to_refresh(self) -> List[str]:
        """✅ Get buffs that need refreshing (optimized)"""
        buffs_to_cast = []
        current_time = time.time()

        for skill_name, skill in self.skills.items():
            if (
                skill.skill_type in [SkillType.BUFF, SkillType.UTILITY]
                and skill.enabled
            ):
                usage = self.usage_stats.get(skill_name)
                if usage and current_time - usage.last_used >= skill.cooldown:
                    buffs_to_cast.append(skill_name)

        return buffs_to_cast

    def reset_active_rotation(self):
        """✅ Reset current rotation"""
        if self.active_rotation and self.active_rotation in self.rotations:
            self.rotations[self.active_rotation].reset()
            self.logger.debug(f"Reset rotation: {self.active_rotation}")

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Get detailed skill information"""
        if skill_name not in self.skills:
            raise SkillError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]
        usage = self.usage_stats[skill_name]
        current_time = time.time()

        return {
            "name": skill.name,
            "key": skill.key,
            "type": skill.skill_type.value,
            "priority": skill.priority,
            "cooldown": skill.cooldown,
            "mana_cost": skill.mana_cost,
            "enabled": skill.enabled,
            "description": skill.description,
            "can_use": self.can_use_skill(skill_name),
            "cooldown_remaining": max(
                0, skill.cooldown - (current_time - usage.last_used)
            ),
            "usage_stats": {
                "total_uses": usage.total_uses,
                "successful_uses": usage.successful_uses,
                "failed_uses": usage.failed_uses,
                "success_rate": usage.success_rate,
                "last_used": usage.last_used,
            },
        }

    def export_config(self) -> Dict[str, Any]:
        """Export skill configuration"""
        skills_data = {}
        for name, skill in self.skills.items():
            skills_data[name] = {
                "key": skill.key,
                "cooldown": skill.cooldown,
                "skill_type": skill.skill_type.value,
                "priority": skill.priority,
                "mana_cost": skill.mana_cost,
                "conditions": skill.conditions,
                "description": skill.description,
                "enabled": skill.enabled,
            }

        rotations_data = {}
        for name, rotation in self.rotations.items():
            rotations_data[name] = {
                "skills": rotation.skills,
                "repeat": rotation.repeat,
                "enabled": rotation.enabled,
            }

        return {
            "skills": skills_data,
            "rotations": rotations_data,
            "active_rotation": self.active_rotation,
            "global_cooldown": self.global_cooldown,
        }

    def import_config(self, config: Dict[str, Any]) -> None:
        """✅ Import configuration with better error handling"""
        # Clear existing
        self.skills.clear()
        self.rotations.clear()
        self.usage_stats.clear()

        # Import skills
        skills_data = config.get("skills", {})
        for name, skill_data in skills_data.items():
            try:
                skill = Skill(
                    name=name,
                    key=skill_data["key"],
                    cooldown=skill_data["cooldown"],
                    skill_type=SkillType(skill_data["skill_type"]),
                    priority=skill_data.get("priority", 1),
                    mana_cost=skill_data.get("mana_cost", 0),
                    conditions=skill_data.get("conditions", []),
                    description=skill_data.get("description", ""),
                    enabled=skill_data.get("enabled", True),
                )
                self.register_skill(skill)
            except Exception as e:
                self.logger.error(f"Failed to import skill '{name}': {e}")

        # Import rotations
        rotations_data = config.get("rotations", {})
        for name, rotation_data in rotations_data.items():
            try:
                self.create_rotation(
                    name, rotation_data["skills"], rotation_data.get("repeat", True)
                )
                self.rotations[name].enabled = rotation_data.get("enabled", True)
            except Exception as e:
                self.logger.error(f"Failed to import rotation '{name}': {e}")

        # Set active rotation
        active_rotation = config.get("active_rotation")
        if active_rotation and active_rotation in self.rotations:
            self.set_active_rotation(active_rotation)

        # Set global cooldown
        self.global_cooldown = config.get("global_cooldown", 0.15)

        self.logger.info(
            f"Imported {len(self.skills)} skills and {len(self.rotations)} rotations"
        )

    def reset_usage_stats(self, skill_name: Optional[str] = None) -> None:
        """Reset usage statistics"""
        if skill_name:
            if skill_name in self.usage_stats:
                self.usage_stats[skill_name] = SkillUsage()
        else:
            for name in self.usage_stats:
                self.usage_stats[name] = SkillUsage()

    def get_all_skills_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all skills"""
        return {name: self.get_skill_info(name) for name in self.skills.keys()}


class TantraSkillTemplates:
    """✅ PLANTILLAS OPTIMIZADAS para skills comunes de Tantra"""

    @staticmethod
    def create_basic_skills() -> List[Skill]:
        """Create optimized basic Tantra skills"""
        return [
            # Attack skills
            Skill("Basic Attack", "r", 1.0, SkillType.AUTO_ATTACK, priority=1),
            # Potions (alta prioridad para emergencias)
            Skill(
                "HP Potion",
                "0",
                0.3,
                SkillType.HP_POTION,
                priority=10,
                conditions=[{"type": "hp_below", "value": 70}],
            ),
            Skill(
                "MP Potion",
                "9",
                0.3,
                SkillType.MP_POTION,
                priority=10,
                conditions=[{"type": "mp_below", "value": 70}],
            ),
            # Skills numericos (prioridad media para rotaciones)
            Skill("Skill 1", "1", 0.8, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 2", "2", 0.8, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 3", "3", 0.8, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 4", "4", 0.8, SkillType.OFFENSIVE, priority=3),
            # Assist skill
            Skill("Assist", "q", 0.5, SkillType.ASSIST, priority=1),
        ]

    @staticmethod
    def create_optimized_rotation(skill_names: List[str]) -> SkillRotation:
        """Create an optimized skill rotation"""
        return SkillRotation("Combat Rotation", skill_names, repeat=True)
