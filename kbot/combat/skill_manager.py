# combat/skill_manager.py

import time
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass, field
from utils.exceptions import SkillError
from core.input_controller import InputController
from core.pixel_analyzer import PixelAnalyzer
from config.unified_config_manager import UnifiedConfigManager


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
    HP_BELOW = "hp_below"
    MP_BELOW = "mp_below"
    TARGET_HP_ABOVE = "target_hp_above"
    TARGET_HP_BELOW = "target_hp_below"
    IN_COMBAT = "in_combat"
    OUT_OF_COMBAT = "out_of_combat"


@dataclass
class Skill:
    """✅ MODIFICADO: Representa una habilidad con comprobación visual."""

    name: str
    key: str
    cooldown: float  # Reinterpretado como "check_interval"
    skill_type: SkillType
    priority: int = 1
    mana_cost: int = 0
    icon: Optional[str] = None  # ✅ NUEVO: Ruta al icono de la habilidad
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""
    enabled: bool = True


@dataclass
class SkillUsage:
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
    def __init__(self, name: str, skills: List[str], repeat: bool = True):
        self.name = name
        self.skills = skills
        self.repeat = repeat
        self.current_index = 0
        self.enabled = True

    def get_next_skill(self) -> Optional[str]:
        if not self.enabled or not self.skills:
            return None
        skill_name = self.skills[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.skills)
        if not self.repeat and self.current_index == 0:
            self.enabled = False
        return skill_name

    def reset(self):
        self.current_index = 0


class SkillManager:
    """✅ MODIFICADO: Gestión de habilidades con comprobación visual."""

    def __init__(
        self,
        input_controller: InputController,
        pixel_analyzer: PixelAnalyzer,
        config_manager: UnifiedConfigManager,
        logger=None,
    ):
        self.input_controller = input_controller
        self.pixel_analyzer = pixel_analyzer  # ✅ NUEVO
        self.config_manager = config_manager  # ✅ NUEVO
        self.logger = logger or BotLogger("SkillManager")

        self.skills: Dict[str, Skill] = {}
        self.rotations: Dict[str, SkillRotation] = {}
        self.usage_stats: Dict[str, SkillUsage] = {}
        self.active_rotation: Optional[str] = None
        self.global_cooldown = 0.15
        self.last_skill_used = 0.0

        self.game_state: Dict[str, Any] = {
            "hp": 100,
            "mp": 100,
            "target_hp": 0,
            "target_exists": False,
            "in_combat": False,
        }

        # Mapeo de teclas de skill a índices de slot (0-9)
        self.key_to_slot_map = {str(i): i - 1 for i in range(1, 10)}
        self.key_to_slot_map["0"] = 9

    def register_skill(self, skill: Skill):
        if skill.name in self.skills:
            raise SkillError(f"Skill '{skill.name}' already exists")
        self.skills[skill.name] = skill
        self.usage_stats[skill.name] = SkillUsage()

    def create_rotation(self, name: str, skill_names: List[str], repeat: bool = True):
        for skill_name in skill_names:
            if skill_name not in self.skills:
                raise SkillError(f"Skill '{skill_name}' not found")
        self.rotations[name] = SkillRotation(name, skill_names, repeat)

    def set_active_rotation(self, rotation_name: Optional[str]):
        if rotation_name and rotation_name not in self.rotations:
            raise SkillError(f"Rotation '{rotation_name}' not found")
        self.active_rotation = rotation_name
        if rotation_name:
            self.rotations[rotation_name].reset()

    def update_game_state(self, state: Dict[str, Any]):
        self.game_state.update(state)

    def can_use_skill(self, skill_name: str) -> bool:
        """✅ MODIFICADO: Comprueba si un skill se puede usar, usando análisis visual."""
        if skill_name not in self.skills:
            return False
        skill = self.skills[skill_name]
        if not skill.enabled:
            return False

        current_time = time.time()
        # Comprobación de Global Cooldown
        if current_time - self.last_skill_used < self.global_cooldown:
            return False

        # Comprobación de intervalo mínimo (antes `cooldown`) para no spamear el análisis
        usage = self.usage_stats[skill_name]
        if current_time - usage.last_used < skill.cooldown:
            return False

        # Comprobación de maná
        if skill.mana_cost > self.game_state.get("mp", 0):
            return False

        # ✅ NUEVA LÓGICA DE COMPROBACIÓN VISUAL
        if skill.icon:
            slot_index = self.key_to_slot_map.get(skill.key.lower())
            if slot_index is not None:
                skill_bar_config = self.config_manager.config_data.get("skill_bar", {})
                slots = skill_bar_config.get("slots", [])
                threshold = skill_bar_config.get("cooldown_similarity_threshold", 0.7)

                if slot_index < len(slots):
                    slot_region = tuple(slots[slot_index])
                    if not self.pixel_analyzer.is_skill_ready(
                        slot_region, skill.icon, threshold
                    ):
                        self.logger.debug(f"Skill '{skill.name}' en cooldown (visual).")
                        return False
                else:
                    self.logger.warning(
                        f"Índice de slot {slot_index} para skill '{skill.name}' fuera de rango."
                    )
            else:
                self.logger.debug(
                    f"Skill '{skill.name}' con tecla '{skill.key}' no mapeada a un slot, no se puede comprobar visualmente."
                )

        # Comprobación de condiciones (sin cambios)
        # if not self._evaluate_conditions(skill): return False

        return True

    def use_skill(self, skill_name: str, force: bool = False) -> bool:
        """✅ MODIFICADO: El log se imprime aquí para máxima precisión."""
        if skill_name not in self.skills:
            raise SkillError(f"Skill '{skill_name}' not found")

        skill = self.skills[skill_name]
        usage = self.usage_stats[skill_name]

        if not force and not self.can_use_skill(skill_name):
            usage.failed_uses += 1
            return False

        try:
            # ✅ Log justo antes de la acción
            self.logger.info(f"🔥 Using skill: {skill.name}")
            success = self.input_controller.send_key(skill.key)

            # El resto de las estadísticas se actualizan después
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
        # Prioridad para pociones
        if self.game_state["hp"] < self.config_manager.get_combat_behavior().get(
            "potion_threshold", 50
        ):
            hp_potion = self.find_skill_by_type(SkillType.HP_POTION)
            if hp_potion and self.can_use_skill(hp_potion.name):
                return hp_potion.name

        if self.game_state["mp"] < self.config_manager.get_combat_behavior().get(
            "potion_threshold", 50
        ):
            mp_potion = self.find_skill_by_type(SkillType.MP_POTION)
            if mp_potion and self.can_use_skill(mp_potion.name):
                return mp_potion.name

        # Usar rotación si está activa
        if self.active_rotation and self.active_rotation in self.rotations:
            rotation = self.rotations[self.active_rotation]
            if rotation.enabled and rotation.skills:
                # Intentar encontrar un skill de la rotación que esté listo
                for _ in range(len(rotation.skills)):
                    next_skill_name = rotation.get_next_skill()
                    if next_skill_name and self.can_use_skill(next_skill_name):
                        return next_skill_name
        else:
            # Si no hay rotación activa, usar sistema de prioridades
            # Obtener skills habilitados ordenados por prioridad (mayor número = mayor prioridad)
            available_skills = [
                skill for skill in self.skills.values() 
                if skill.enabled and skill.skill_type not in [SkillType.HP_POTION, SkillType.MP_POTION, SkillType.AUTO_ATTACK]
                and self.can_use_skill(skill.name)
            ]
            
            if available_skills:
                # Ordenar por prioridad descendente (mayor número = mayor prioridad)
                available_skills.sort(key=lambda s: s.priority, reverse=True)
                return available_skills[0].name

        # Fallback a ataque básico si la rotación falla o no hay skills disponibles
        auto_attack = self.find_skill_by_type(SkillType.AUTO_ATTACK)
        if auto_attack and self.can_use_skill(auto_attack.name):
            return auto_attack.name

        return None

    def find_skill_by_type(self, skill_type: SkillType) -> Optional[Skill]:
        for skill in self.skills.values():
            if skill.skill_type == skill_type and skill.enabled:
                return skill
        return None

    def export_config(self) -> Dict[str, Any]:
        skills_data = {}
        for name, skill in self.skills.items():
            skills_data[name] = {
                "key": skill.key,
                "cooldown": skill.cooldown,
                "skill_type": skill.skill_type.value,
                "priority": skill.priority,
                "mana_cost": skill.mana_cost,
                "icon": skill.icon,
                "conditions": skill.conditions,
                "description": skill.description,
                "enabled": skill.enabled,
            }

        rotations_data = {}
        for name, rotation in self.rotations.items():
            rotations_data[name] = {
                "skills": rotation.skills,
                "repeat": rotation.repeat,
            }

        return {
            "definitions": skills_data,
            "rotations": rotations_data,
            "active_rotation": self.active_rotation,
            "global_cooldown": self.global_cooldown,
        }

    def import_config(self, config: Dict[str, Any]) -> None:
        self.skills.clear()
        self.rotations.clear()
        self.usage_stats.clear()

        skills_data = config.get("definitions", {})
        for name, skill_data in skills_data.items():
            try:
                skill = Skill(
                    name=name,
                    key=skill_data["key"],
                    cooldown=skill_data.get("cooldown", 1.0),
                    skill_type=SkillType(skill_data["skill_type"]),
                    priority=skill_data.get("priority", 1),
                    mana_cost=skill_data.get("mana_cost", 0),
                    icon=skill_data.get("icon"),  # ✅ NUEVO
                    conditions=skill_data.get("conditions", []),
                    description=skill_data.get("description", ""),
                    enabled=skill_data.get("enabled", True),
                )
                self.register_skill(skill)
            except Exception as e:
                self.logger.error(f"Failed to import skill '{name}': {e}")

        rotations_data = config.get("rotations", {})
        for name, rotation_data in rotations_data.items():
            self.create_rotation(
                name, rotation_data["skills"], rotation_data.get("repeat", True)
            )

        self.active_rotation = config.get("active_rotation")
        self.global_cooldown = config.get("global_cooldown", 0.15)
        self.logger.info(
            f"Imported {len(self.skills)} skills and {len(self.rotations)} rotations."
        )

    def reset_usage_stats(self):
        self.usage_stats.clear()
        for name in self.skills:
            self.usage_stats[name] = SkillUsage()

    def reset_active_rotation(self):
        if self.active_rotation and self.active_rotation in self.rotations:
            self.rotations[self.active_rotation].reset()
