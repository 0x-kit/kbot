# kbot/combat/combat_manager.py - VERSIÓN OPTIMIZADA

import time
from typing import Optional, List, Dict, Any
from enum import Enum
import random
from fuzzywuzzy import fuzz
from core.pixel_analyzer import PixelAnalyzer
from combat.skill_manager import SkillManager, SkillType
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger
from utils.exceptions import BotError
from core.movement_manager import MovementManager


class CombatState(Enum):
    IDLE = "idle"
    TARGETING = "targeting"
    FIGHTING = "fighting"
    MOVING = "moving"
    LOOTING = "looting"
    POST_COMBAT = "post_combat"
    ASSISTING = "assisting"


class CombatManager:
    """VERSIÓN OPTIMIZADA - Combat Manager más fluido y eficiente"""

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
        self.window_manager: WindowManager = self.input_controller.window_manager

        # Estado del bot
        self.is_running = False
        self.state = CombatState.IDLE
        self.current_target = None

        # Timestamps para control de timing
        self.last_target_attempt = 0
        self.last_attack_time = 0
        self.last_skill_time = 0
        self.last_assist_attempt = 0
        self.last_kill_time = 0
        self.last_combat_log_time = 0

        # Sistema anti-stuck mejorado
        self.stuck_search_timer = 0
        self.stuck_detector = {
            "last_target_hp": 100,
            "hp_unchanged_since": 0,
            "stuck_in_combat_timeout": 8.0,  # ✅ Reducido de 12s
            "last_unstuck_attempt": 0,
            "unstuck_cooldown": 3.0,  # ✅ Reducido de 5s
        }

        # Configuración de looteo
        self.looting_config = {
            "enabled": True,
            "duration": 0.8,  # ✅ Reducido de 1s
            "initial_delay": 0.1,  # ✅ Reducido de 0.2s
            "loot_attempts": 2,
            "attempt_interval": 0.2,  # ✅ Reducido de 0.3s
            "loot_key": "f",
        }
        self.looting_state_tracker = {"start_time": 0, "_attempts_made": 0}

        # Configuración de combate
        self.mob_whitelist: List[str] = []
        self.potion_threshold = 70
        self.use_skills = True
        self.use_basic_attack_fallback = True
        self.skill_priority_mode = "rotation"
        self.assist_mode_enabled = False

        # ✅ TIMINGS OPTIMIZADOS PARA FLUIDEZ
        self.timing = {
            "combat_log_interval": 5.0,  # ✅ Menos spam de logs
            "target_attempt_interval": 0.3,  # ✅ Búsqueda más rápida (era 1.0s)
            "stuck_detection_searching": 6.0,  # ✅ Detección más rápida (era 10s)
            "attack_interval": 1.2,  # ✅ MUCHO más rápido (era 10s!)
            "skill_interval": 1.0,  # ✅ Skills más fluidos (era 2.25s)
            "post_combat_delay": 1.5,  # ✅ Menos espera (era 3s)
            "assist_interval": 0.8,  # ✅ Assist más responsivo (era 1.5s)
            "engage_timeout": 3.0,  # ✅ NUEVO: Timeout para fase de engage
        }

        # Estadísticas
        self.combat_stats = {
            "targets_acquired": 0,
            "targets_lost": 0,
            "skills_used": 0,
            "attacks_made": 0,
            "stuck_in_combat": 0,
            "stuck_searching": 0,
            "unstuck_maneuvers": 0,
        }

        self.ocr_tolerance_threshold = 80

    def process_combat(self) -> None:
        """BUCLE PRINCIPAL OPTIMIZADO"""
        if not self.is_running:
            return

        try:
            current_time = time.time()
            game_state = self.skill_manager.game_state

            # ✅ LÓGICA DE DECISIÓN SIMPLIFICADA Y MÁS RÁPIDA
            target_exists = game_state.get("target_exists", False)

            # Si tenemos target, vamos directo a combate
            if target_exists:
                if self.state != CombatState.FIGHTING:
                    target_name = game_state.get("target_name", "")
                    if self._is_target_allowed(target_name):
                        self._start_combat(target_name, current_time)
                else:
                    self._handle_fighting_state(current_time, game_state)
            else:
                # Sin target: manejar estados post-combate o búsqueda
                if self.state == CombatState.FIGHTING:
                    # Target perdido durante combate
                    self._transition_to_looting(current_time)
                elif self.state == CombatState.LOOTING:
                    self._handle_looting_state(current_time)
                elif self.state == CombatState.POST_COMBAT:
                    self._handle_post_combat_state(current_time)
                else:
                    # Búsqueda o assist
                    if self.assist_mode_enabled:
                        self._handle_assisting_state(current_time)
                    else:
                        self._handle_searching_state(current_time, game_state)

        except Exception as e:
            self.logger.error(f"Error in combat loop: {e}")

    def _start_combat(self, target_name: str, current_time: float):
        """✅ NUEVO: Inicio de combate optimizado"""
        self.logger.info(f"🎯 Target acquired: {target_name}")
        self.current_target = target_name
        self.state = CombatState.FIGHTING
        self.skill_manager.reset_active_rotation()
        self._reset_stuck_detectors(current_time)
        self.combat_stats["targets_acquired"] += 1

    def _handle_fighting_state(self, current_time: float, game_state: dict):
        """✅ LÓGICA DE COMBATE OPTIMIZADA"""
        target_hp = game_state.get("target_hp", 0)

        # Target muerto o perdido
        if target_hp <= 0:
            if self.looting_config["enabled"]:
                self._transition_to_looting(current_time)
            else:
                self.logger.info(f"✅ {self.current_target} defeated!")
                self.state = CombatState.POST_COMBAT
                self.last_kill_time = current_time
            return

        # Log de progreso (menos frecuente)
        if (
            current_time - self.last_combat_log_time
            > self.timing["combat_log_interval"]
        ):
            self.logger.info(f"⚔️ Fighting {self.current_target} ({target_hp}% HP)")
            self.last_combat_log_time = current_time

        # Detección de stuck
        self._check_stuck_in_combat(current_time, target_hp)

        # ✅ SISTEMA DE COMBATE NUEVO Y MÁS FLUIDO
        self._execute_optimized_combat(current_time, target_hp)

    def _execute_optimized_combat(self, current_time: float, target_hp: int):
        """✅ NUEVO: Sistema de combate unificado y más fluido"""

        # Intentar usar skill primero (prioridad)
        skill_used = False
        if self.use_skills:
            time_since_last_skill = current_time - self.last_skill_time
            if time_since_last_skill >= self.timing["skill_interval"]:
                next_skill = self.skill_manager.get_next_skill()
                if next_skill and self.skill_manager.can_use_skill(next_skill):
                    self.logger.debug(f"🔥 Using skill: {next_skill}")
                    if self.skill_manager.use_skill(next_skill):
                        self.last_skill_time = current_time
                        self.combat_stats["skills_used"] += 1
                        skill_used = True

        # Si no se pudo usar skill, usar ataque básico como fallback
        if not skill_used and self.use_basic_attack_fallback:
            time_since_last_attack = current_time - self.last_attack_time
            if time_since_last_attack >= self.timing["attack_interval"]:
                auto_attack = self.skill_manager.find_skill_by_type(
                    SkillType.AUTO_ATTACK
                )
                if auto_attack:
                    self.logger.debug(f"⚔️ Basic attack on {self.current_target}")
                    if self.skill_manager.use_skill(auto_attack.name):
                        self.last_attack_time = current_time
                        self.combat_stats["attacks_made"] += 1

    def _handle_searching_state(self, current_time: float, game_state: dict):
        """✅ BÚSQUEDA OPTIMIZADA"""

        # ✅ Búsqueda más frecuente de targets
        if (
            current_time - self.last_target_attempt
            > self.timing["target_attempt_interval"]
        ):
            self.last_target_attempt = current_time
            self.input_controller.send_key("e")

            # Reset search timer si estamos buscando activamente
            if self.stuck_search_timer == 0:
                self.stuck_search_timer = current_time

        # Detección de stuck en búsqueda (más rápida)
        if (
            current_time - self.stuck_search_timer
            > self.timing["stuck_detection_searching"]
        ):
            self.logger.warning(
                f"🔄 No target found in {self.timing['stuck_detection_searching']:.1f}s. Anti-stuck maneuver."
            )

            if self.movement_manager.execute_anti_stuck_maneuver("Stuck searching"):
                self.combat_stats["unstuck_maneuvers"] += 1

            self.stuck_search_timer = current_time
            self.combat_stats["stuck_searching"] += 1

    def _handle_looting_state(self, current_time: float):
        """✅ LOOTEO OPTIMIZADO"""
        time_in_state = current_time - self.looting_state_tracker["start_time"]

        if time_in_state > self.looting_config["duration"]:
            self.logger.debug("📦 Looting finished")
            self.state = CombatState.POST_COMBAT
            self.last_kill_time = current_time
            return

        # Ejecutar intentos de looteo
        if time_in_state >= self.looting_config["initial_delay"]:
            attempts_made = self.looting_state_tracker.get("_attempts_made", 0)
            if attempts_made < self.looting_config["loot_attempts"]:
                next_attempt_time = self.looting_config["initial_delay"] + (
                    attempts_made * self.looting_config["attempt_interval"]
                )
                if time_in_state >= next_attempt_time:
                    self.input_controller.send_key(self.looting_config["loot_key"])
                    self.looting_state_tracker["_attempts_made"] = attempts_made + 1

    def _handle_post_combat_state(self, current_time: float):
        """✅ POST-COMBATE OPTIMIZADO"""
        time_since_kill = current_time - self.last_kill_time

        if time_since_kill >= self.timing["post_combat_delay"]:
            self.state = CombatState.IDLE
            self.stuck_search_timer = 0  # Reset para nueva búsqueda

    def _handle_assisting_state(self, current_time: float):
        """✅ MODO ASSIST OPTIMIZADO"""
        # Verificar si ya tenemos target
        target_exists = self.skill_manager.game_state.get("target_exists", False)
        if target_exists:
            self.state = CombatState.IDLE  # Volverá a fighting en el siguiente ciclo
            return

        # Usar skill de assist más frecuentemente
        if current_time - self.last_assist_attempt > self.timing["assist_interval"]:
            self.last_assist_attempt = current_time
            assist_skill = self.skill_manager.find_skill_by_type(SkillType.ASSIST)

            if assist_skill:
                self.logger.debug("🤝 Using assist skill...")
                self.skill_manager.use_skill(assist_skill.name)
            else:
                self.logger.warning("⚠️ Assist mode ON but no assist skill configured!")
                self.last_assist_attempt = (
                    current_time + 3
                )  # Esperar más si no hay skill

    def _transition_to_looting(self, current_time: float):
        """✅ TRANSICIÓN A LOOTEO OPTIMIZADA"""
        self.logger.debug(f"✅ {self.current_target} defeated. Starting loot phase.")
        self.combat_stats["targets_lost"] += 1
        self.current_target = None
        self.state = CombatState.LOOTING
        self.looting_state_tracker["start_time"] = current_time
        self.looting_state_tracker["_attempts_made"] = 0

    def _check_stuck_in_combat(self, current_time: float, target_hp: int):
        """✅ DETECCIÓN DE STUCK OPTIMIZADA"""
        if target_hp < self.stuck_detector["last_target_hp"]:
            # HP bajó, no estamos stuck
            self.stuck_detector["last_target_hp"] = target_hp
            self.stuck_detector["hp_unchanged_since"] = current_time
            return

        time_stuck = current_time - self.stuck_detector["hp_unchanged_since"]

        if time_stuck > self.stuck_detector["stuck_in_combat_timeout"]:
            if (
                current_time - self.stuck_detector["last_unstuck_attempt"]
                > self.stuck_detector["unstuck_cooldown"]
            ):

                self.logger.warning(
                    f"🔄 STUCK! HP unchanged for {time_stuck:.1f}s. Abandoning target."
                )

                if self.movement_manager.execute_anti_stuck_maneuver("Stuck in combat"):
                    self.combat_stats["unstuck_maneuvers"] += 1

                self.current_target = None
                self.state = CombatState.IDLE
                self.stuck_search_timer = 0
                self.skill_manager.reset_active_rotation()
                self.combat_stats["stuck_in_combat"] += 1
                self.stuck_detector["last_unstuck_attempt"] = current_time

    def _is_target_allowed(self, target_name: str) -> bool:
        self.logger.info(
            f"TESTING: Validating target '{target_name}' against whitelist {self.mob_whitelist}"
        )

        """✅ VALIDACIÓN DE TARGET OPTIMIZADA"""
        if not self.mob_whitelist or not target_name:
            return bool(target_name)  # Si no hay whitelist, cualquier target vale

        # ✅ Caché simple para evitar recalcular fuzzy matching
        if not hasattr(self, "_target_cache"):
            self._target_cache = {}

        if target_name in self._target_cache:
            return self._target_cache[target_name]

        # Fuzzy matching optimizado
        for allowed_mob in self.mob_whitelist:
            similarity = fuzz.partial_ratio(target_name.lower(), allowed_mob.lower())
            if similarity >= self.ocr_tolerance_threshold:
                self._target_cache[target_name] = True
                return True

        self._target_cache[target_name] = False
        return False

    def _reset_stuck_detectors(self, current_time: float):
        """✅ RESET DE DETECTORES OPTIMIZADO"""
        self.stuck_detector["hp_unchanged_since"] = current_time
        self.stuck_detector["last_target_hp"] = 100
        self.stuck_search_timer = 0
        self.last_combat_log_time = 0

        # Limpiar caché de targets cuando empezamos nuevo combate
        if hasattr(self, "_target_cache"):
            self._target_cache.clear()

    # ✅ MÉTODOS DE CONFIGURACIÓN SIMPLIFICADOS
    def start(self):
        self.is_running = True
        self.state = CombatState.IDLE
        self.logger.info("🚀 Combat Manager started with optimized settings")

    def stop(self):
        self.is_running = False
        self.logger.info("⏹️ Combat Manager stopped")

    def set_timing(self, timing_config: Dict[str, float]):
        """✅ Actualizar timings dinámicamente"""
        old_timings = self.timing.copy()
        self.timing.update(timing_config)

        # Log solo cambios significativos
        changed = {k: v for k, v in timing_config.items() if old_timings.get(k) != v}
        if changed:
            self.logger.info(f"⚙️ Updated timings: {changed}")

    def set_assist_mode(self, enabled: bool):
        self.assist_mode_enabled = enabled
        mode_text = "ENABLED" if enabled else "DISABLED"
        self.logger.info(f"🤝 Assist Mode: {mode_text}")

    def set_mob_whitelist(self, whitelist: List[str]):
        self.mob_whitelist = whitelist
        # Limpiar caché cuando cambia whitelist
        if hasattr(self, "_target_cache"):
            self._target_cache.clear()

    def set_looting_enabled(self, enabled: bool):
        self.looting_config["enabled"] = enabled

    def set_ocr_tolerance(self, tolerance: int):
        self.ocr_tolerance_threshold = max(50, min(100, tolerance))
        # Limpiar caché cuando cambia tolerancia
        if hasattr(self, "_target_cache"):
            self._target_cache.clear()

    def get_combat_stats(self) -> Dict[str, Any]:
        return self.combat_stats.copy()

    def reset_combat_stats(self):
        for key in self.combat_stats:
            self.combat_stats[key] = 0
        if self.skill_manager:
            self.skill_manager.reset_usage_stats()
        self.logger.info("📊 Combat stats reset")

    def set_potion_threshold(self, threshold: int):
        """Set potion threshold - MÉTODO FALTANTE"""
        self.potion_threshold = threshold
        self.logger.debug(f"Potion threshold set to {threshold}%")

    def set_skill_usage(self, enabled: bool):
        """Enable/disable skill usage - MÉTODO FALTANTE"""
        self.use_skills = enabled
        status = "enabled" if enabled else "disabled"
        self.logger.info(f"Skill usage {status}")

    def set_skill_priority_mode(self, mode: str):
        """Set skill priority mode - MÉTODO FALTANTE"""
        self.skill_priority_mode = mode
        self.logger.debug(f"Skill priority mode set to: {mode}")

    def pause(self):
        """Pause combat manager - MÉTODO FALTANTE"""
        self.is_running = False
        self.logger.info("Combat Manager paused")

    def resume(self):
        """Resume combat manager - MÉTODO FALTANTE"""
        self.is_running = True
        self.logger.info("Combat Manager resumed")
