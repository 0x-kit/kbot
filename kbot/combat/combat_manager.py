# kbot/combat/combat_manager.py

import time
from typing import Optional, List, Dict, Any
from enum import Enum
import random

try:
    from fuzzywuzzy import fuzz

    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False

from core.pixel_analyzer import PixelAnalyzer
from combat.skill_manager import SkillManager, SkillType
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger
from core.movement_manager import MovementManager


class CombatState(Enum):
    IDLE = "Idle"
    SEARCHING = "Searching for target"
    ENGAGING = "Engaging target"
    FIGHTING = "Fighting"
    LOOTING = "Looting"
    ASSISTING = "Assisting leader"


class CombatManager:
    def __init__(
        self,
        pixel_analyzer: PixelAnalyzer,
        skill_manager: SkillManager,
        input_controller: InputController,
        movement_manager: MovementManager,
        logger: BotLogger,
    ):
        self.pixel_analyzer = pixel_analyzer
        self.skill_manager = skill_manager
        self.input_controller = input_controller
        self.movement_manager = movement_manager
        self.logger = logger

        self.is_running = False
        self.state = CombatState.IDLE
        self.current_target_name: Optional[str] = None
        self.last_target_hp: int = 100

        self.last_action_time = 0
        self.last_target_search_time = 0
        self.last_assist_time = 0

        self.stuck_detector = {
            "search_start_time": 0,
            "combat_start_time": 0,
            "last_hp_change_time": 0,
        }

        # --- Configuración con valores por defecto ---
        # ✅ CORREGIDO: Renombrada la variable a 'whitelist' para consistencia.
        self.whitelist: List[str] = []
        self.assist_mode = False
        self.use_skills = True
        self.looting_enabled = True
        self.potion_threshold = 50
        self.ocr_tolerance = 80
        self.fuzzy_match_threshold = 80
        self.timing = {
            "target_search_interval": 0.3,
            "skill_use_interval": 0.6,
            "stuck_search_timeout": 8.0,
            "stuck_combat_timeout": 10.0,
            "loot_duration": 1.5,
        }
        self.loot_key = "f"

        self._target_validation_cache = {}

    def process_combat(self):
        if not self.is_running:
            return
        game_state = self.skill_manager.game_state
        has_target = (
            game_state.get("target_exists", False)
            and game_state.get("target_hp", 0) > 0
        )
        if has_target:
            self.handle_fighting_state(game_state)
        else:
            self.handle_no_target_state()

    def handle_fighting_state(self, game_state: Dict):
        target_name = game_state.get("target_name", "").strip()
        target_hp = game_state.get("target_hp", 100)

        if self.state != CombatState.FIGHTING:
            if self._is_target_allowed(target_name):
                self._start_combat(target_name or "Unknown Target")
            else:
                self.logger.info(
                    f"Target '{target_name}' is not in whitelist. Finding new target."
                )
                self.input_controller.send_key("e")
                self.state = CombatState.SEARCHING
                return

        if target_hp < self.last_target_hp:
            self.last_target_hp = target_hp
            self.stuck_detector["last_hp_change_time"] = time.time()

        if (
            time.time() - self.stuck_detector["last_hp_change_time"]
            > self.timing["stuck_combat_timeout"]
        ):
            self.logger.warning(
                f"Stuck in combat with {self.current_target_name} for too long. Abandoning."
            )
            self.movement_manager.execute_anti_stuck_maneuver("Stuck in combat")
            self._reset_combat_state()
            return

        if time.time() - self.last_action_time > self.timing["skill_use_interval"]:
            self.execute_combat_action()

    def execute_combat_action(self):
        """Lógica de decisión de skills con logging mejorado."""
        if self.use_skills:
            # ✅ CORREGIDO: Usar get_next_skill() que maneja rotaciones Y prioridades
            next_skill_name = self.skill_manager.get_next_skill()
            if next_skill_name:
                if self.skill_manager.use_skill(next_skill_name):
                    self.last_action_time = time.time()
                    return
            else:
                self.logger.debug("No usable skills found, falling back to basic attack.")

        # Fallback: usar ataque básico si no hay skills disponibles
        basic_attack = self.skill_manager.find_skill_by_type(SkillType.AUTO_ATTACK)
        if basic_attack:
            if self.skill_manager.use_skill(basic_attack.name):
                self.last_action_time = time.time()

    def handle_no_target_state(self):
        if self.state == CombatState.FIGHTING:
            self.logger.info(f"✅ Target {self.current_target_name} defeated.")
            self.current_target_name = None
            if self.looting_enabled:
                self.state = CombatState.LOOTING
                self.looting_start_time = time.time()
            else:
                self._reset_combat_state()

        if self.state == CombatState.LOOTING:
            if (
                time.time() - getattr(self, "looting_start_time", 0)
                > self.timing["loot_duration"]
            ):
                self._reset_combat_state()
            else:
                self.input_controller.send_key(self.loot_key)
            return

        if self.assist_mode:
            if time.time() - self.last_assist_time > self.timing["skill_use_interval"]:
                self.logger.debug("Attempting to assist party leader...")
                assist_skill = self.skill_manager.find_skill_by_type(SkillType.ASSIST)
                if assist_skill:
                    self.skill_manager.use_skill(assist_skill.name)
                self.last_assist_time = time.time()
        else:
            if self.state != CombatState.SEARCHING:
                self.logger.info("No target found. Starting search...")
                self.state = CombatState.SEARCHING
                self.stuck_detector["search_start_time"] = time.time()

            if (
                time.time() - self.last_target_search_time
                > self.timing["target_search_interval"]
            ):
                self.input_controller.send_key("e")
                self.last_target_search_time = time.time()

            if (
                time.time() - self.stuck_detector["search_start_time"]
                > self.timing["stuck_search_timeout"]
            ):
                self.logger.warning(
                    f"No target found for {self.timing['stuck_search_timeout']}s. Performing anti-stuck maneuver."
                )
                self.movement_manager.execute_anti_stuck_maneuver("Searching timeout")
                self.stuck_detector["search_start_time"] = time.time()

    def _start_combat(self, target_name: str):
        self.logger.info(f"🎯 Engaging target: {target_name}")
        self.state = CombatState.FIGHTING
        self.current_target_name = target_name
        self.last_target_hp = 100
        self.stuck_detector["last_hp_change_time"] = time.time()
        self.skill_manager.reset_active_rotation()

    def _reset_combat_state(self):
        self.state = CombatState.IDLE
        self.current_target_name = None

    def _is_target_allowed(self, target_name: str) -> bool:
        if not target_name:
            self.logger.debug("Target name is empty, assuming it's a valid mob.")
            return True
        # ✅ CORREGIDO: Usa self.whitelist
        if "*" in self.whitelist or not self.whitelist:
            return True

        target_lower = target_name.lower()
        if target_lower in self._target_validation_cache:
            return self._target_validation_cache[target_lower]

        best_match_score = (
            max(fuzz.ratio(target_lower, mob) for mob in self.whitelist)
            if FUZZYWUZZY_AVAILABLE
            else 0
        )
        is_allowed = best_match_score >= self.fuzzy_match_threshold

        if is_allowed:
            self.logger.info(
                f"Target '{target_name}' validated against whitelist (Score: {best_match_score}%)"
            )

        self._target_validation_cache[target_lower] = is_allowed
        return is_allowed

    def start(self):
        self.is_running = True
        self.logger.info("🚀 Combat Manager started.")

    def stop(self):
        self.is_running = False
        self.logger.info("⏹️ Combat Manager stopped.")

    def pause(self):
        self.is_running = False
        self.logger.info("Combat Manager paused.")

    def resume(self):
        self.is_running = True
        self.logger.info("Combat Manager resumed.")

    # --- Setters para configuración desde BotEngine ---
    def set_mob_whitelist(self, whitelist: List[str]):
        """✅ CORREGIDO: Nuevo nombre del método para consistencia."""
        self.whitelist = [mob.lower() for mob in whitelist]
        self._target_validation_cache.clear()
        self.logger.info(f"Whitelist updated: {self.whitelist}")

    def set_assist_mode(self, enabled: bool):
        self.assist_mode = enabled
        self.logger.info(f"🤝 Assist Mode: {'ENABLED' if enabled else 'DISABLED'}")

    def set_looting_enabled(self, enabled: bool):
        self.looting_enabled = enabled

    def set_potion_threshold(self, threshold: int):
        self.potion_threshold = threshold

    def set_ocr_tolerance(self, tolerance: int):
        self.ocr_tolerance = tolerance
        self.fuzzy_match_threshold = tolerance

    def set_use_skills(self, enabled: bool):
        self.use_skills = enabled
        self.logger.info(f"Skill usage {'enabled' if enabled else 'disabled'}")

    def set_timing(self, timing_config: Dict[str, float]):
        self.timing.update(timing_config)
