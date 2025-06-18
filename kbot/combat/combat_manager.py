# kbot/combat/combat_manager.py

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
    # ... (__init__ no cambia)
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
        self.is_running = False
        self.state = CombatState.IDLE
        self.current_target = None
        self.last_target_attempt = 0
        self.last_attack_time = 0
        self.last_skill_time = 0
        self.stuck_search_timer = 0
        self.stuck_detector = {
            "last_target_hp": 100,
            "hp_unchanged_since": 0,
            "stuck_in_combat_timeout": 12.0,
            "last_unstuck_attempt": 0,
            "unstuck_cooldown": 5.0,
        }
        self.looting_config = {
            "enabled": True,
            "duration": 1,
            "initial_delay": 0.0,
            "loot_attempts": 2,
            "attempt_interval": 0.05,
            "loot_key": "f",
            "cancel_movement": True,  # Activar/desactivar la cancelación
            "cancel_delay": 0.1,  # Cuánto esperar DESPUÉS de pulsar loot antes de cancelar (tiempo para recoger)
            "cancel_key": "d",  # Tecla para cancelar el movimiento (un pequeño giro)
            "cancel_hold_duration": 5.0,  # Duración en segundos para mantener presionada la tecla de cancelación.
        }
        self.looting_state_tracker = {"start_time": 0, "_attempts_made": 0}
        self.last_kill_time = 0
        self.mob_whitelist: List[str] = []
        self.potion_threshold = 70
        self.use_skills = True
        self.use_basic_attack_fallback = True
        self.assist_mode_enabled = False
        self.last_assist_attempt = 0
        self.skill_priority_mode = "rotation"
        self.timing = {
            "combat_log_interval": 2.0,
            "target_attempt_interval": 1.0,
            "stuck_detection_searching": 10.0,
            "attack_interval": 10.0,
            "skill_interval": 2.25,
            "post_combat_delay": 3.0,
            "assist_interval": 1.5,
        }
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
        self.last_combat_log_time = 0

    def process_combat(self) -> None:
        if not self.is_running:
            return
        try:
            current_time = time.time()
            game_state = self.skill_manager.game_state

            # --- LÓGICA DE DECISIÓN PRINCIPAL MODIFICADA ---
            # Si no estamos en medio de una pelea, looteo o post-combate...
            if self.state not in [
                CombatState.FIGHTING,
                CombatState.LOOTING,
                CombatState.POST_COMBAT,
            ]:
                # ...y no tenemos objetivo...
                if not game_state.get("target_exists", False):
                    # ...y el modo asistir está activado...
                    if self.assist_mode_enabled:
                        # ...entonces nuestro estado debe ser ASISTIR.
                        self.state = CombatState.ASSISTING
                    else:
                        # ...si no, nuestro estado es buscar (IDLE).
                        self.state = CombatState.IDLE
            # --- FIN DE LA LÓGICA DE DECISIÓN ---

            if self.state == CombatState.FIGHTING:
                self._handle_fighting_state(current_time, game_state)
            elif self.state == CombatState.LOOTING:
                self._handle_looting_state(current_time)
            elif self.state == CombatState.POST_COMBAT:
                self._handle_post_combat_state(current_time)
            elif self.state == CombatState.ASSISTING:  # <-- NUEVO CASO
                self._handle_assisting_state(current_time)
            else:  # IDLE (Búsqueda normal)
                self._handle_searching_state(current_time, game_state)
        except Exception as e:
            self.logger.error(f"Error in main combat loop: {e}")

    def _handle_searching_state(self, current_time: float, game_state: dict):
        """Lógica unificada y mejorada para buscar objetivos."""
        target_exists = game_state.get("target_exists", False)
        target_name = game_state.get("target_name", "")

        if target_exists and self._is_target_allowed(target_name):
            # ... (lógica de adquisición de objetivo sin cambios) ...
            self.logger.info(f"¡Blanco adquirido! Atacando a: {target_name}")
            self.current_target = target_name
            self.state = CombatState.FIGHTING
            self.skill_manager.reset_active_rotation()
            self._reset_stuck_detectors(current_time)
            self.combat_stats["targets_acquired"] += 1
            return

        if self.stuck_search_timer == 0:
            self.stuck_search_timer = current_time

        if (
            current_time - self.stuck_search_timer
            > self.timing["stuck_detection_searching"]
        ):
            self.logger.warning(
                f"No se encontró un objetivo válido en {self.timing['stuck_detection_searching']:.1f}s. Iniciando maniobra anti-atasco."
            )

            # --- LLAMADA A LA NUEVA LÓGICA ---
            if self.movement_manager.execute_anti_stuck_maneuver("Stuck searching"):
                self.combat_stats["unstuck_maneuvers"] += 1
            # --- FIN DE LA LLAMADA ---

            self.stuck_search_timer = current_time
            self.combat_stats["stuck_searching"] += 1
            return

        if (
            current_time - self.last_target_attempt
            > self.timing["target_attempt_interval"]
        ):
            self.last_target_attempt = current_time
            if target_exists:
                self.logger.debug(
                    f"Objetivo inválido '{target_name}'. Buscando otro..."
                )
            else:
                self.logger.debug("Sin objetivo. Intentando buscar uno...")

            self.input_controller.send_key("e")
            time.sleep(0.15)

    # El resto del archivo no cambia. Lo pego para asegurar la integridad.
    def _handle_fighting_state(self, current_time: float, game_state: dict):
        """Lógica para cuando el bot está en combate."""
        target_exists = game_state.get("target_exists", False)
        target_hp = game_state.get("target_hp", 0)

        # Si el objetivo ya no existe o está muerto, pasamos a lootear.
        if not target_exists or target_hp <= 0:
            # Solo pasamos a lootear si la opción está habilitada.
            if self.looting_config["enabled"]:
                self._transition_to_looting(current_time)
            else:
                # Si no hay looteo, vamos directo a la fase post-combate.
                self.logger.info(
                    f"Target '{self.current_target}' defeated. Skipping loot phase."
                )
                self.state = CombatState.POST_COMBAT
                self.last_kill_time = current_time
            return

        # Logueamos el progreso del combate periódicamente.
        if (
            current_time - self.last_combat_log_time
            > self.timing["combat_log_interval"]
        ):
            self.logger.info(f"Fighting {self.current_target} (HP: {target_hp}%)")
            self.last_combat_log_time = current_time

        # Comprobamos si estamos atascados.
        self._check_stuck_in_combat(current_time, target_hp)

        # --- CAMBIO CLAVE: Pasamos la vida del objetivo a la rutina de ataque ---
        self._perform_attack_routine(current_time, target_hp)

    def _handle_looting_state(self, current_time: float):
        """
        Lógica de looteo MEJORADA que incluye una cancelación de movimiento
        para evitar que el personaje se aleje de la zona.
        """
        time_in_state = current_time - self.looting_state_tracker["start_time"]

        # Si la fase de looteo ha terminado, pasamos a la siguiente etapa.
        if time_in_state > self.looting_config["duration"]:
            self.logger.info("Looting phase finished.")
            self.state = CombatState.POST_COMBAT
            self.last_kill_time = current_time
            return

        # Esperamos el delay inicial antes de hacer nada.
        if time_in_state < self.looting_config["initial_delay"]:
            return

        attempts_made = self.looting_state_tracker.get("_attempts_made", 0)

        # Comprobamos si todavía nos quedan intentos de looteo por hacer.
        if attempts_made < self.looting_config["loot_attempts"]:
            # Calculamos cuándo debe ocurrir el próximo intento.
            next_attempt_time = self.looting_config["initial_delay"] + (
                attempts_made * self.looting_config["attempt_interval"]
            )

            # Si ya es hora del siguiente intento...
            if time_in_state >= next_attempt_time:
                self.logger.debug(f"Looting attempt #{attempts_made + 1}...")

                # 1. Pulsamos la tecla de loot.
                self.input_controller.send_key(self.looting_config["loot_key"])

                if self.looting_config["cancel_movement"]:
                    # 3. Esperamos el 'cancel_delay'.
                    time.sleep(self.looting_config["cancel_delay"])

                    # 4. Enviamos la tecla de cancelación para interrumpir el movimiento.
                    cancel_key = self.looting_config["cancel_key"]
                    hold_duration = self.looting_config["cancel_hold_duration"]

                    self.logger.debug(
                        f"Holding '{cancel_key}' for {hold_duration}s to cancel loot movement."
                    )

                    # --- LÍNEA MODIFICADA ---
                    # Usamos hold_key en lugar de send_key para una cancelación más fiable.
                    self.input_controller.hold_key(cancel_key, hold_duration)
                    # --- FIN DE LA MODIFICACIÓN ---

                # 5. Incrementamos el contador de intentos.
                self.looting_state_tracker["_attempts_made"] = attempts_made + 1

    def _handle_post_combat_state(self, current_time: float):
        """
        NUEVO MÉTODO: Simplemente espera a que pase el 'post_combat_delay'.
        """
        time_since_last_kill = current_time - self.last_kill_time

        # elf._simple_unstuck_movement("Cancel potential not owed loot")

        # Comprobamos si el tiempo de espera ha terminado.
        if time_since_last_kill >= self.timing["post_combat_delay"]:
            self.logger.info("Post-combat delay finished. Resuming search.")
            self.state = CombatState.IDLE  # Volvemos a buscar
        else:
            # Si no, logueamos cuánto falta.
            remaining = self.timing["post_combat_delay"] - time_since_last_kill
            self.logger.debug(f"Post-combat delay... {remaining:.1f}s remaining.")
            # Es importante añadir una pequeña pausa aquí para no consumir CPU en un bucle vacío.
            time.sleep(0.1)

    def _handle_assisting_state(self, current_time: float):
        """
        Estado especial para el modo asistir. Simplemente pulsa la tecla de asistir
        periódicamente hasta que el juego asigne un objetivo.
        """
        # Comprobamos si ya tenemos un objetivo (el líder mató al mob o se nos asignó uno).
        target_exists = self.skill_manager.game_state.get("target_exists", False)
        if target_exists:
            self.logger.info("Target acquired via assist. Engaging!")
            self.state = (
                CombatState.IDLE
            )  # Volvemos a IDLE, que en el siguiente ciclo nos pasará a FIGHTING.
            return

        # Si no hay objetivo, pulsamos la tecla de asistir.
        if current_time - self.last_assist_attempt > self.timing["assist_interval"]:
            self.last_assist_attempt = current_time
            assist_skill = self.skill_manager.find_skill_by_type(SkillType.ASSIST)

            if assist_skill:
                self.logger.debug(
                    f"No target, using '{assist_skill.name}' skill to assist party leader..."
                )
                self.skill_manager.use_skill(assist_skill.name)
            else:
                self.logger.warning(
                    "Assist mode is ON, but no skill with type 'assist' is configured!"
                )
                # Para evitar un bucle de spam de warnings, esperamos más tiempo.
                self.last_assist_attempt = current_time + 5

    def _perform_attack_routine(self, current_time: float, target_hp: int):
        """
        VERSIÓN MEJORADA: Rutina de ataque en dos fases.
        1. ENGAGE: Si el objetivo tiene 100% de vida, solo usa ataque básico para acercarse.
        2. FULL COMBAT: Si la vida es < 100%, desata la rotación completa de skills.
        """
        auto_attack_skill = self.skill_manager.find_skill_by_type(SkillType.AUTO_ATTACK)

        # --- FASE 1: ENGAGE (Tu lógica original, ¡la clave del éxito!) ---
        if target_hp >= 100:
            if current_time - self.last_attack_time >= self.timing["attack_interval"]:
                self.logger.debug(
                    f"Target {self.current_target} at 100% HP. Using basic attack to engage..."
                )
                if self.skill_manager.use_skill(auto_attack_skill.name):
                    self.last_attack_time = current_time
                    self.combat_stats["attacks_made"] += 1
            # Es importante salir aquí para no pasar a la fase de skills.
            return

        # --- FASE 2: COMBATE COMPLETO (La rotación agresiva) ---
        # Si llegamos aquí, es porque target_hp < 100, ¡estamos en rango!
        skill_used = False
        if self.use_skills and (
            current_time - self.last_skill_time >= self.timing["skill_interval"]
        ):
            next_skill = self.skill_manager.get_next_skill()
            if next_skill and self.skill_manager.can_use_skill(next_skill):
                self.logger.info(
                    f"Using skill '{next_skill}' on {self.current_target} ({target_hp}% HP)"
                )
                if self.skill_manager.use_skill(next_skill):
                    self.last_skill_time = current_time
                    self.combat_stats["skills_used"] += 1
                    skill_used = True
                    # Pequeña pausa después de un skill para que el juego lo procese
                    time.sleep(0.35)

        # Si no se pudo usar un skill (en CD, sin maná, etc.), usamos el ataque básico como relleno.
        if not skill_used and self.use_basic_attack_fallback:
            if current_time - self.last_attack_time >= self.timing["attack_interval"]:
                self.logger.debug(
                    f"Basic attack filler on {self.current_target} ({target_hp}% HP)"
                )
                if self.skill_manager.use_skill(auto_attack_skill.name):
                    self.last_attack_time = current_time
                    self.combat_stats["attacks_made"] += 1

    def _transition_to_looting(self, current_time: float):
        """
        Prepara e inicia el estado de looteo, activando el modo caminar.
        """
        self.logger.info(
            f"Target '{self.current_target}' defeated. Transitioning to LOOTING."
        )
        self.combat_stats["targets_lost"] += 1
        self.current_target = None

        # --- NUEVA LÓGICA ---
        # 1. Activamos el modo caminar ANTES de empezar a lootear.
        # self.logger.debug("Switching to walk mode for safe looting.")
        # self.input_controller.send_key('z')
        # --------------------

        self.state = CombatState.LOOTING
        self.looting_state_tracker["start_time"] = current_time
        self.looting_state_tracker["_attempts_made"] = 0

    def _is_target_allowed(self, target_name: str) -> bool:
        if not self.mob_whitelist:
            return True
        if not target_name:
            return False
        for allowed_mob in self.mob_whitelist:
            similarity_score = fuzz.partial_ratio(
                target_name.lower(), allowed_mob.lower()
            )
            status = (
                "Accepted"
                if similarity_score >= self.ocr_tolerance_threshold
                else "Rejected"
            )
            self.logger.debug(
                f"Fuzzy Match: '{target_name}' vs '{allowed_mob}' -> Score: {similarity_score}%. {status}"
            )
            if similarity_score >= self.ocr_tolerance_threshold:
                return True
        return False

    def _reset_stuck_detectors(self, current_time: float):
        """Reinicia los contadores de atasco Y el log de combate para un nuevo objetivo."""
        self.stuck_detector["hp_unchanged_since"] = current_time
        self.stuck_detector["last_target_hp"] = 100
        self.stuck_search_timer = 0
        # Reiniciamos también el log para que el primer mensaje de combate salga rápido
        self.last_combat_log_time = 0

    def _check_stuck_in_combat(self, current_time: float, target_hp: int):
        """
        Comprueba si estamos atascados. Si la vida del objetivo no baja,
        ejecuta una secuencia de desatasco y abandona el objetivo.
        """
        if target_hp < self.stuck_detector["last_target_hp"]:
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
                    f"STUCK IN COMBAT! Target HP sin cambios por {time_stuck:.1f}s. "
                    f"Abandonando a '{self.current_target}' e iniciando maniobra."
                )

                # --- LLAMADA A LA NUEVA LÓGICA ---
                if self.movement_manager.execute_anti_stuck_maneuver("Stuck in combat"):
                    self.combat_stats["unstuck_maneuvers"] += 1
                # --- FIN DE LA LLAMADA ---

                self.current_target = None
                self.state = CombatState.IDLE
                self.stuck_search_timer = 0
                self.skill_manager.reset_active_rotation()

                self.combat_stats["stuck_in_combat"] += 1
                self.stuck_detector["last_unstuck_attempt"] = current_time
                return

    def _simple_unstuck_movement(self, reason: str):
        self.logger.info(f"Executing simple movement: {reason}")
        if not self.window_manager.target_window:
            return
        try:
            window_rect = self.window_manager.target_window.rect
            center_x = (window_rect[0] + window_rect[2]) // 2
            center_y = (window_rect[1] + window_rect[3]) // 2
            for i in range(2):
                radius = 220
                rand_x = center_x + random.randint(-radius, radius)
                rand_y = center_y + random.randint(-radius, radius)
                self.logger.debug(f"Unstuck click #{i+1} at ({rand_x}, {rand_y})")
                self.input_controller.click_at(rand_x, rand_y, "left")
                time.sleep(random.uniform(0.2, 0.4))
        except Exception as e:
            self.logger.error(f"Simple unstuck movement failed: {e}")

    def start(self):
        self.is_running = True
        self.logger.info("Combat Manager started.")
        self.state = CombatState.IDLE

    def stop(self):
        self.is_running = False
        self.logger.info("Combat Manager stopped.")

    def pause(self):
        self.is_running = False
        self.logger.info("Combat Manager paused.")

    def resume(self):
        self.is_running = True
        self.logger.info("Combat Manager resumed.")

    def get_combat_stats(self) -> Dict[str, Any]:
        return self.combat_stats.copy()

    def reset_combat_stats(self):
        for key in self.combat_stats:
            self.combat_stats[key] = 0
        self.logger.info("Combat stats have been reset.")
        if self.skill_manager:
            self.skill_manager.reset_usage_stats()

    def set_skill_usage(self, enabled: bool):
        self.use_skills = enabled

    def set_mob_whitelist(self, whitelist: List[str]):
        self.mob_whitelist = whitelist

    def set_potion_threshold(self, threshold: int):
        self.potion_threshold = threshold

    def set_skill_priority_mode(self, mode: str):
        self.skill_priority_mode = mode

    def set_timing(self, timing_config: Dict[str, float]):
        """Actualiza los timings y loguea el cambio para depuración."""

        self.timing.update(timing_config)
        # --- DEBUGGING PRINT ---
        self.logger.info(f"CombatManager timings updated: {self.timing}")

    def set_ocr_tolerance(self, tolerance: int):
        """Permite al BotEngine configurar la tolerancia."""
        # Asegurarse de que el valor está en un rango razonable
        self.ocr_tolerance_threshold = max(50, min(100, tolerance))
        self.logger.info(f"OCR match tolerance set to {self.ocr_tolerance_threshold}%.")

    def set_looting_enabled(self, enabled: bool):
        """NUEVO MÉTODO: Permite al BotEngine activar/desactivar el looteo."""
        self.looting_config["enabled"] = enabled
        self.logger.info(f"Looting after combat set to: {enabled}")

    def set_assist_mode(self, enabled: bool):
        """Activa o desactiva el modo Asistir."""
        self.assist_mode_enabled = enabled
        if enabled:
            self.logger.info(
                "Assist Mode has been ENABLED. Target search is now disabled."
            )
        else:
            self.logger.info(
                "Assist Mode has been DISABLED. Target search is now enabled."
            )
