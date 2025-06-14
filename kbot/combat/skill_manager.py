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
    HP_POTION = "hp_potion"
    MP_POTION = "mp_potion"
    AUTO_ATTACK = "auto_attack"
    ASSIST = "assist"


class TriggerCondition(Enum):
    """Define las condiciones que pueden activar una habilidad."""

    HP_BELOW = "hp_below"  # Mi vida está por debajo de X%
    MP_BELOW = "mp_below"  # Mi maná está por debajo de X%
    TARGET_HP_ABOVE = "target_hp_above"  # La vida del enemigo está por encima de X%
    TARGET_HP_BELOW = "target_hp_below"  # La vida del enemigo está por debajo de X%
    IN_COMBAT = "in_combat"  # Estoy en combate
    OUT_OF_COMBAT = "out_of_combat"  # No estoy en combate


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
    """FIXED: Defines a sequence of skills to execute with proper indexing"""

    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills  # List of skill names
        self.repeat = repeat
        self.current_index = 0  # Start at 0
        self.enabled = True
        self.skills_used = 0  # Track total skills used for debugging

    def get_next_skill(self) -> Optional[str]:
        """FIXED: Get the next skill in the rotation"""
        if not self.enabled or not self.skills:
            return None

        # Get current skill BEFORE advancing
        skill_name = self.skills[self.current_index]

        # Debug info
        print(
            f"DEBUG Rotation '{self.name}': Index {self.current_index} -> Skill '{skill_name}' (Skills: {self.skills})"
        )

        # Advance to next skill AFTER getting current
        self._advance_index()

        # Increment usage counter
        self.skills_used += 1

        return skill_name

    def _advance_index(self) -> None:
        """FIXED: Advance to next skill in rotation"""
        self.current_index += 1

        # If we've reached the end of the rotation
        if self.current_index >= len(self.skills):
            if self.repeat:
                self.current_index = 0  # Reset to beginning
                print(
                    f"DEBUG Rotation '{self.name}': Completed cycle, resetting to index 0"
                )
            else:
                self.enabled = False
                self.current_index = len(self.skills) - 1  # Stay at last skill
                print(f"DEBUG Rotation '{self.name}': Non-repeating rotation completed")

    def reset(self) -> None:
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0
        print(f"DEBUG Rotation '{self.name}': Reset to index 0")

    def get_current_skill(self) -> Optional[str]:
        """Get the current skill without advancing"""
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


# ALSO FIX the set_active_rotation method to ensure proper reset:
def set_active_rotation(self, rotation_name: Optional[str]) -> None:
    """FIXED: Set the active rotation with proper reset"""
    if rotation_name and rotation_name not in self.rotations:
        raise SkillError(f"Rotation '{rotation_name}' not found")

    # If switching rotations, reset the new one
    if rotation_name and rotation_name != self.active_rotation:
        self.rotations[rotation_name].reset()
        print(f"DEBUG: Reset rotation '{rotation_name}' when setting as active")

    self.active_rotation = rotation_name

    if rotation_name:
        rotation = self.rotations[rotation_name]
        print(
            f"DEBUG: Active rotation set to '{rotation_name}' - Skills: {rotation.skills}, Starting at index: {rotation.current_index}"
        )
    else:
        print("DEBUG: Active rotation cleared")

    """ENHANCED: Get the next skill to use based on rotation and priorities"""
    try:
        # If we have an active rotation, use it
        if self.active_rotation and self.active_rotation in self.rotations:
            rotation = self.rotations[self.active_rotation]

            if hasattr(self, "logger"):
                self.logger.debug(
                    f"Using rotation '{self.active_rotation}' - Index: {rotation.current_index}/{len(rotation.skills)}"
                )

            if rotation.enabled and rotation.skills:
                next_skill = rotation.get_next_skill()

                if hasattr(self, "logger"):
                    # Calculate what step we're on (after the skill was used)
                    step = rotation.current_index
                    total = len(rotation.skills)
                    self.logger.debug(
                        f"Rotation returned skill: {next_skill} [Next index will be: {step}/{total}]"
                    )

                # Check if the skill from rotation can be used
                if next_skill and self.can_use_skill(next_skill):
                    return next_skill
                else:
                    if hasattr(self, "logger"):
                        self.logger.debug(
                            f"Rotation skill '{next_skill}' not available, falling back to priority"
                        )

        # Fall back to priority-based selection
        return self._get_priority_skill()

    except Exception as e:
        if hasattr(self, "logger"):
            self.logger.error(f"Error in get_next_skill: {e}")
        return None


class SkillRotation:
    """FIXED: Defines a sequence of skills to execute with proper indexing"""

    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills  # List of skill names
        self.repeat = repeat
        self.current_index = 0  # Start at 0
        self.enabled = True
        self.skills_used = 0  # Track total skills used for debugging

    def get_next_skill(self) -> Optional[str]:
        """FIXED: Get the next skill in the rotation"""
        if not self.enabled or not self.skills:
            return None

        # Get current skill BEFORE advancing
        skill_name = self.skills[self.current_index]

        # Debug info
        print(
            f"DEBUG Rotation '{self.name}': Index {self.current_index} -> Skill '{skill_name}' (Skills: {self.skills})"
        )

        # Advance to next skill AFTER getting current
        self._advance_index()

        # Increment usage counter
        self.skills_used += 1

        return skill_name

    def _advance_index(self) -> None:
        """FIXED: Advance to next skill in rotation"""
        self.current_index += 1

        # If we've reached the end of the rotation
        if self.current_index >= len(self.skills):
            if self.repeat:
                self.current_index = 0  # Reset to beginning
                print(
                    f"DEBUG Rotation '{self.name}': Completed cycle, resetting to index 0"
                )
            else:
                self.enabled = False
                self.current_index = len(self.skills) - 1  # Stay at last skill
                print(f"DEBUG Rotation '{self.name}': Non-repeating rotation completed")

    def reset(self) -> None:
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0
        print(f"DEBUG Rotation '{self.name}': Reset to index 0")

    def get_current_skill(self) -> Optional[str]:
        """Get the current skill without advancing"""
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

    """FIXED: Defines a sequence of skills to execute with proper indexing"""

    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills  # List of skill names
        self.repeat = repeat
        self.current_index = 0  # Start at 0
        self.enabled = True
        self.skills_used = 0  # Track total skills used for debugging

    def get_next_skill(self) -> Optional[str]:
        """FIXED: Get the next skill in the rotation"""
        if not self.enabled or not self.skills:
            return None

        # Get current skill BEFORE advancing
        skill_name = self.skills[self.current_index]

        # Debug info
        print(
            f"DEBUG Rotation '{self.name}': Index {self.current_index} -> Skill '{skill_name}' (Skills: {self.skills})"
        )

        # Advance to next skill AFTER getting current
        self._advance_index()

        # Increment usage counter
        self.skills_used += 1

        return skill_name

    def _advance_index(self) -> None:
        """FIXED: Advance to next skill in rotation"""
        self.current_index += 1

        # If we've reached the end of the rotation
        if self.current_index >= len(self.skills):
            if self.repeat:
                self.current_index = 0  # Reset to beginning
                print(
                    f"DEBUG Rotation '{self.name}': Completed cycle, resetting to index 0"
                )
            else:
                self.enabled = False
                self.current_index = len(self.skills) - 1  # Stay at last skill
                print(f"DEBUG Rotation '{self.name}': Non-repeating rotation completed")

    def reset(self) -> None:
        """Reset rotation to beginning"""
        self.current_index = 0
        self.enabled = True
        self.skills_used = 0
        print(f"DEBUG Rotation '{self.name}': Reset to index 0")

    def get_current_skill(self) -> Optional[str]:
        """Get the current skill without advancing"""
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


# ALSO FIX the set_active_rotation method to ensure proper reset:
def set_active_rotation(self, rotation_name: Optional[str]) -> None:
    """FIXED: Set the active rotation with proper reset"""
    if rotation_name and rotation_name not in self.rotations:
        raise SkillError(f"Rotation '{rotation_name}' not found")

    # If switching rotations, reset the new one
    if rotation_name and rotation_name != self.active_rotation:
        self.rotations[rotation_name].reset()
        print(f"DEBUG: Reset rotation '{rotation_name}' when setting as active")

    self.active_rotation = rotation_name

    if rotation_name:
        rotation = self.rotations[rotation_name]
        print(
            f"DEBUG: Active rotation set to '{rotation_name}' - Skills: {rotation.skills}, Starting at index: {rotation.current_index}"
        )
    else:
        print("DEBUG: Active rotation cleared")


class SkillManager:
    """Advanced skill management system"""

    def __init__(self, input_controller: InputController, logger=None):
        self.input_controller = input_controller

        # Add logger support
        if logger:
            self.logger = logger
        else:
            from utils.logger import BotLogger

            self.logger = BotLogger("SkillManager")

        self.skills: Dict[str, Skill] = {}
        self.rotations: Dict[str, SkillRotation] = {}
        self.usage_stats: Dict[str, SkillUsage] = {}
        self.active_rotation: Optional[str] = None
        self.global_cooldown = 0.2  # Global cooldown between any skills
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
        """Revisa si un skill se puede usar (cooldown, maná Y CONDICIONES)."""
        if skill_name not in self.skills:
            return False
        skill = self.skills[skill_name]
        if not skill.enabled:
            return False

        current_time = time.time()
        if current_time - self.last_skill_used < self.global_cooldown:
            return False

        usage = self.usage_stats[skill_name]
        if current_time - usage.last_used < skill.cooldown:
            return False

        if skill.mana_cost > self.game_state.get("mp", 0):
            return False

        # --- LÍNEA CLAVE AÑADIDA ---
        if not self._evaluate_conditions(skill):
            return False

        return True

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
        """Comprueba si todas las condiciones de un skill se cumplen."""
        if not skill.conditions:
            return True  # Si no hay condiciones, siempre es válido.

        for condition in skill.conditions:
            try:
                cond_type = TriggerCondition(condition["type"])
                evaluator = self.condition_evaluators.get(cond_type)

                # Si la condición no se cumple, el skill no se puede usar.
                if not evaluator or not evaluator(condition.get("value")):
                    return False
            except (ValueError, KeyError):
                self.logger.warning(
                    f"Condición desconocida o mal formada en skill '{skill.name}': {condition}"
                )
                return False

        return True  # Todas las condiciones se cumplieron.

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

    def _eval_in_combat(self, value: Any) -> bool:  # value no se usa aquí
        return self.game_state.get("in_combat", False)

    def _eval_out_of_combat(self, value: Any) -> bool:  # value no se usa aquí
        return not self.game_state.get("in_combat", False)
        """Evaluate custom condition"""
        # For custom conditions, we expect a function name and parameters
        func_name = condition.get("function")
        if hasattr(self, func_name):
            func = getattr(self, func_name)
            return func(condition.get("params", {}))
        return False

    def get_skill_info(self, skill_name: str) -> Dict[str, Any]:
        """Get detailed information about a skill"""
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

    def get_next_skill(self) -> Optional[str]:
        """
        NUEVO MÉTODO DE DECISIÓN POR CAPAS:
        1. Busca skills condicionales de alta prioridad.
        2. Si no hay, ejecuta la rotación normal.
        """
        # --- Capa 1 y 2: Emergencia y Oportunidad ---
        # Obtenemos TODOS los skills disponibles (que cumplen cooldown, maná, condiciones, etc.)
        available_skills = []
        for name in self.skills:
            # --- CAMBIO CLAVE: AÑADIMOS LA CONDICIÓN DE FILTRADO ---
            skill = self.skills[name]
            if skill.skill_type not in [SkillType.HP_POTION, SkillType.MP_POTION]:
                if self.can_use_skill(name):
                    available_skills.append(skill)

        # Si hay skills disponibles, los ordenamos por prioridad para encontrar el más importante.
        if available_skills:
            # Ordenamos de mayor a menor prioridad
            available_skills.sort(key=lambda s: s.priority, reverse=True)
            highest_priority_skill = available_skills[0]

            # Si el skill de mayor prioridad NO es de la rotación base (prioridad > 5), lo usamos.
            # Esto permite que un skill de emergencia/oportunidad interrumpa el combo.
            if highest_priority_skill.priority > 5:
                self.logger.debug(
                    f"Interrupción por skill prioritario: '{highest_priority_skill.name}' (Prioridad: {highest_priority_skill.priority})"
                )
                return highest_priority_skill.name

        # --- Capa 3: Rotación Base ---
        # Si no hubo interrupciones, continuamos con la rotación.
        if self.active_rotation and self.active_rotation in self.rotations:
            rotation = self.rotations[self.active_rotation]
            if rotation.enabled and rotation.skills:
                # Obtenemos el nombre del siguiente skill en la rotación
                next_in_rotation_name = rotation.get_next_skill()

                # Comprobamos si JUSTO ESE skill se puede usar ahora
                if next_in_rotation_name and self.can_use_skill(next_in_rotation_name):
                    return next_in_rotation_name
                else:
                    # Si no se puede (ej. en CD), no hacemos nada y esperamos al siguiente ciclo.
                    # El `get_next_skill` de la rotación ya avanzó el índice, así que en el siguiente
                    # ciclo probará con el siguiente skill del combo.
                    self.logger.debug(
                        f"Skill de rotación '{next_in_rotation_name}' no disponible. Esperando."
                    )

        # Si no hay rotación o el skill de la rotación no estaba listo, puede que haya un skill
        # de baja prioridad disponible (ej. ataque básico con condiciones).
        if available_skills and available_skills[0].priority <= 5:
            return available_skills[0].name

        return None

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

    def debug_rotation_state(self) -> None:
        """Debug method to log current rotation state"""
        if not self.active_rotation:
            self.logger.debug("DEBUG: No active rotation set")
            return

        if self.active_rotation not in self.rotations:
            self.logger.debug(
                f"DEBUG: Active rotation '{self.active_rotation}' not found in rotations"
            )
            return

        rotation = self.rotations[self.active_rotation]
        status = rotation.get_status()

        self.logger.debug(f"DEBUG: Rotation Status:")
        self.logger.debug(f"  Name: {status['name']}")
        self.logger.debug(f"  Enabled: {status['enabled']}")
        self.logger.debug(
            f"  Current Index: {status['current_index']}/{status['total_skills']}"
        )
        self.logger.debug(f"  Current Skill: {status['current_skill']}")
        self.logger.debug(f"  Next Skill: {status['next_skill']}")
        self.logger.debug(f"  All Skills: {status['all_skills']}")

        # Also check if current skill can be used
        current_skill = status["current_skill"]
        if current_skill:
            can_use = self.can_use_skill(current_skill)
            skill_info = self.get_skill_info(current_skill)
            self.logger.debug(
                f"  Current skill '{current_skill}' can be used: {can_use}"
            )
            if not can_use:
                self.logger.debug(
                    f"    Cooldown remaining: {skill_info['cooldown_remaining']:.1f}s"
                )
                self.logger.debug(f"    Enabled: {skill_info['enabled']}")

    def import_config(self, config: Dict[str, Any]) -> None:
        """FIXED: Import skill configuration with better rotation handling"""
        # Clear existing configuration
        self.skills.clear()
        self.rotations.clear()
        self.usage_stats.clear()

        # Import skills
        skills_data = config.get("skills", {})
        for name, skill_data in skills_data.items():
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

        # Import rotations
        rotations_data = config.get("rotations", {})
        for name, rotation_data in rotations_data.items():
            try:
                self.create_rotation(
                    name, rotation_data["skills"], rotation_data.get("repeat", True)
                )
                self.rotations[name].enabled = rotation_data.get("enabled", True)
                self.logger.debug(
                    f"Imported rotation '{name}': {rotation_data['skills']}"
                )
            except Exception as e:
                self.logger.error(f"Failed to import rotation '{name}': {e}")

        # Set active rotation - IMPORTANT FIX
        active_rotation = config.get("active_rotation")
        if active_rotation and active_rotation in self.rotations:
            self.set_active_rotation(active_rotation)
            self.logger.info(f"Set active rotation from import: {active_rotation}")
        elif self.rotations:
            # If no active rotation specified but we have rotations, set the first one
            first_rotation = list(self.rotations.keys())[0]
            self.set_active_rotation(first_rotation)
            self.logger.info(f"Auto-set first available rotation: {first_rotation}")

        # Set global cooldown
        self.global_cooldown = config.get("global_cooldown", 0.2)

        self.logger.info(
            f"Imported {len(self.skills)} skills and {len(self.rotations)} rotations"
        )
        if self.active_rotation:
            self.debug_rotation_state()  # Debug the imported rotation

    def reset_active_rotation(self):
        """
        MÉTODO MEJORADO: Ahora es público para que el CombatManager pueda llamarlo.
        Resetea la rotación activa a su estado inicial.
        """
        if self.active_rotation and self.active_rotation in self.rotations:
            self.rotations[self.active_rotation].reset()
            self.logger.info(
                f"Active rotation '{self.active_rotation}' has been reset."
            )

    def get_buffs_to_refresh(self) -> List[str]:
        """
        MÉTODO MEJORADO: Ahora solo busca BUFF y UTILITY, no otros tipos.
        """
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

    def find_skill_by_type(self, skill_type: SkillType) -> Optional[Skill]:
        """
        NUEVO MÉTODO: Busca el primer skill habilitado que coincida con el tipo dado.
        Es útil para encontrar acciones genéricas como el ataque básico o las pociones.
        """
        for skill in self.skills.values():
            if skill.skill_type == skill_type and skill.enabled:
                return skill
        return None


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
            Skill(
                "HP Potion",
                "0",
                0.5,
                SkillType.UTILITY,
                priority=10,
                conditions=[{"type": "hp_below", "value": 70}],
            ),
            Skill(
                "MP Potion",
                "9",
                0.5,
                SkillType.UTILITY,
                priority=10,
                conditions=[{"type": "mp_below", "value": 70}],
            ),
            # Number key skills (1-8)
            Skill("Skill 1", "1", 1.0, SkillType.OFFENSIVE, priority=3),
            Skill("Skill 2", "2", 1.0, SkillType.OFFENSIVE, priority=3),
        ]
