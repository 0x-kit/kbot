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
    BUFF = "buff"
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
    check_interval: float  # Intervalo mínimo entre verificaciones de disponibilidad
    skill_type: SkillType
    priority: int = 1
    mana_cost: int = 0
    icon: Optional[str] = None  # ✅ NUEVO: Ruta al icono de la habilidad
    duration: float = 0.0  # ✅ NUEVO: Duración del buff en segundos (0 = no es buff)
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    description: str = ""
    enabled: bool = True


@dataclass
class SkillUsage:
    last_used: float = 0.0
    total_uses: int = 0
    successful_uses: int = 0
    failed_uses: int = 0
    buff_expires_at: float = 0.0  # ✅ NUEVO: Timestamp cuando expira el buff

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
        self.logger.info(f"Active rotation set to: {rotation_name}")
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
            if skill_name in ["Amada", "Biz"]:  # DEBUG específico
                self.logger.debug(f"Skill '{skill.name}' blocked by global cooldown: {current_time - self.last_skill_used:.2f}s < {self.global_cooldown}s")
            return False

        # Comprobación de intervalo mínimo para no spamear el análisis visual
        usage = self.usage_stats[skill_name]
        time_since_last_use = current_time - usage.last_used
        if time_since_last_use < skill.check_interval:
            if skill_name in ["Amada", "Biz"]:  # DEBUG específico
                self.logger.debug(f"Skill '{skill.name}' check_interval not ready: {time_since_last_use:.2f}s < {skill.check_interval}s")
            return False

        # Comprobación de maná
        if skill.mana_cost > self.game_state.get("mp", 0):
            if skill_name in ["Amada", "Biz"]:  # DEBUG específico
                self.logger.debug(f"Skill '{skill.name}' insufficient mana: {skill.mana_cost} > {self.game_state.get('mp', 0)}")
            return False

        # ✅ NUEVA LÓGICA DE COMPROBACIÓN VISUAL
        if skill.icon and skill.icon.strip():
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
                        if skill_name in ["Amada", "Biz"]:  # DEBUG específico
                            self.logger.debug(f"Skill '{skill.name}' en cooldown (visual) - icon analysis failed")
                        else:
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

        self.logger.debug(f"Skill '{skill.name}' passed all checks and is ready to use")
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

        # DEBUG para buffs específicamente
        if skill.skill_type == SkillType.BUFF:
            self.logger.info(f"🔍 ATTEMPTING to use {skill_name} - Type: {skill.skill_type.value}, Duration: {skill.duration}s, Icon: '{skill.icon}'")

        try:
            # Enviar la tecla
            success = self.input_controller.send_key(skill.key)
            if not success:
                self.logger.debug(f"Failed to send key for skill: {skill.name}")
                usage.failed_uses += 1
                return False

            # ✅ SIMPLIFICADO: Esperar y verificar - lógica straight-forward
            import time as time_module
            time_module.sleep(0.15)  # Esperar para que el juego procese
            
            # Verificación simple: si tiene icono, verificar que ya no esté disponible
            skill_confirmed = True
            if skill.icon and skill.icon.strip():
                slot_index = self.key_to_slot_map.get(skill.key.lower())
                if slot_index is not None:
                    skill_bar_config = self.config_manager.config_data.get("skill_bar", {})
                    slots = skill_bar_config.get("slots", [])
                    threshold = skill_bar_config.get("cooldown_similarity_threshold", 0.7)
                    
                    if slot_index < len(slots):
                        slot_region = tuple(slots[slot_index])
                        # Para buffs, asumimos que siempre se usan correctamente (no tienen cooldown visual)
                        if skill.skill_type == SkillType.BUFF:
                            skill_confirmed = True
                            self.logger.debug(f"Buff '{skill.name}' assumed successful (buffs don't have visual cooldown)")
                        else:
                            # Simple: si sigue disponible = no se usó
                            skill_confirmed = not self.pixel_analyzer.is_skill_ready(slot_region, skill.icon, threshold)

            # Log simple y directo
            if skill_confirmed:
                self.logger.info(f"🔥 Using skill: {skill.name}")
            else:
                # self.logger.debug(f"❌ Skill '{skill.name}' not confirmed - still available")
                pass

            # Actualizar estadísticas
            current_time = time.time()
            usage.last_used = current_time
            usage.total_uses += 1
            self.last_skill_used = current_time
            
            if skill_confirmed:
                usage.successful_uses += 1
                # Si es un buff, establecer cuándo expira
                if skill.skill_type == SkillType.BUFF and skill.duration > 0:
                    usage.buff_expires_at = current_time + skill.duration
                    self.logger.info(f"🛡️ Buff '{skill.name}' applied, expires at {usage.buff_expires_at:.1f} (duration: {skill.duration}s)")
                elif skill.skill_type == SkillType.BUFF:
                    self.logger.debug(f"Buff '{skill.name}' has no duration ({skill.duration}), not tracking expiration")
                return True
            else:
                usage.failed_uses += 1
                return False
        except Exception as e:
            usage.failed_uses += 1
            raise SkillError(f"Failed to execute skill '{skill_name}': {e}")

    def get_next_skill(self) -> Optional[str]:
        # Prioridad 1: Pociones de emergencia
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

        # Prioridad 2: Buffs automáticos (solo out of combat)
        if not self.game_state.get("in_combat", False):
            buff_to_cast = self._get_expired_buff()
            if buff_to_cast:
                return buff_to_cast

        # Prioridad 3: Usar rotación si está activa (solo in combat o si no hay buffs pendientes)
        if self.active_rotation and self.active_rotation in self.rotations:
            self.logger.debug(f"Using active rotation: {self.active_rotation}")
            rotation = self.rotations[self.active_rotation]
            if rotation.enabled and rotation.skills:
                # Intentar encontrar un skill de la rotación que esté listo
                for _ in range(len(rotation.skills)):
                    next_skill_name = rotation.get_next_skill()
                    if next_skill_name and self.can_use_skill(next_skill_name):
                        return next_skill_name
        else:
            # Si no hay rotación activa, usar sistema de prioridades
            self.logger.debug("No active rotation, using priority system")
            
            # DEBUG: Evaluar todos los skills ofensivos individualmente
            offensive_skills = [skill for skill in self.skills.values() 
                              if skill.enabled and skill.skill_type not in [SkillType.HP_POTION, SkillType.MP_POTION, SkillType.AUTO_ATTACK, SkillType.BUFF]]
            
            for skill in offensive_skills:
                can_use = self.can_use_skill(skill.name)
                self.logger.debug(f"Skill '{skill.name}' - Enabled: {skill.enabled}, Type: {skill.skill_type.value}, Can use: {can_use}")
            
            # Obtener skills habilitados ordenados por prioridad (mayor número = mayor prioridad)
            available_skills = [skill for skill in offensive_skills if self.can_use_skill(skill.name)]
            
            if available_skills:
                # Ordenar por prioridad descendente (mayor número = mayor prioridad)
                available_skills.sort(key=lambda s: s.priority, reverse=True)
                self.logger.debug(f"Available skills by priority: {[(s.name, s.priority) for s in available_skills]}")
                selected_skill = available_skills[0].name
                self.logger.debug(f"Selected skill by priority: {selected_skill} (priority: {available_skills[0].priority})")
                return selected_skill

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

    def _get_expired_buff(self) -> Optional[str]:
        """✅ CORREGIDO: Encuentra buffs que han expirado y necesitan ser relanzados."""
        current_time = time.time()
        buff_skills = [
            skill for skill in self.skills.values()
            if skill.skill_type == SkillType.BUFF and skill.enabled and skill.duration > 0
        ]
        
        # DEBUG: Log all available buffs
        if buff_skills:
            self.logger.debug(f"Available buff skills: {[s.name for s in buff_skills]}")
        
        for skill in buff_skills:
            usage = self.usage_stats[skill.name]
            
            # Si nunca se ha usado (buff_expires_at == 0.0) o si ha expirado
            if (usage.buff_expires_at == 0.0 or current_time >= usage.buff_expires_at):
                if self.can_use_skill(skill.name):
                    self.logger.debug(f"Buff '{skill.name}' needs to be cast: expires_at={usage.buff_expires_at}, current={current_time:.1f}")
                    return skill.name
                else:
                    self.logger.debug(f"Buff '{skill.name}' expired but can't use skill yet")
        
        return None

    def export_config(self) -> Dict[str, Any]:
        skills_data = {}
        for name, skill in self.skills.items():
            skills_data[name] = {
                "key": skill.key,
                "check_interval": skill.check_interval,
                "skill_type": skill.skill_type.value,
                "priority": skill.priority,
                "mana_cost": skill.mana_cost,
                "icon": skill.icon,
                "duration": skill.duration,
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
                    check_interval=skill_data.get("check_interval", skill_data.get("cooldown", 1.0)),  # Compatibilidad con ambos nombres
                    skill_type=SkillType(skill_data["skill_type"]),
                    priority=skill_data.get("priority", 1),
                    mana_cost=skill_data.get("mana_cost", 0),
                    icon=skill_data.get("icon"),
                    duration=skill_data.get("duration", 0.0),  # ✅ NUEVO
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
            f"Imported {len(self.skills)} skills and {len(self.rotations)} rotations. Active rotation: {self.active_rotation}"
        )

    def reset_usage_stats(self):
        self.usage_stats.clear()
        for name in self.skills:
            self.usage_stats[name] = SkillUsage()

    def reset_active_rotation(self):
        if self.active_rotation and self.active_rotation in self.rotations:
            self.rotations[self.active_rotation].reset()
