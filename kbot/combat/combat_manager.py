# kbot/combat/combat_manager.py

import time
from typing import Optional, List, Dict, Any
from enum import Enum
import random

from core.pixel_analyzer import PixelAnalyzer
from combat.skill_manager import SkillManager
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger
from utils.exceptions import BotError

class CombatState(Enum):
    IDLE = "idle"
    TARGETING = "targeting"
    FIGHTING = "fighting"
    MOVING = "moving"
    LOOTING = "looting" # <-- NUEVO

class CombatManager:
    """Combat manager with a simplified and robust self-contained movement logic."""
    
    def __init__(self, pixel_analyzer: PixelAnalyzer, skill_manager: SkillManager, 
                 input_controller: InputController, logger: BotLogger):
        self.pixel_analyzer = pixel_analyzer
        self.skill_manager = skill_manager
        self.input_controller = input_controller
        self.logger = logger
        self.window_manager: WindowManager = self.input_controller.window_manager

        self.is_running = False
        self.state = CombatState.IDLE
        self.current_target = None
        self.last_target_attempt = 0
        self.last_movement = 0
        self.last_attack_time = 0
        self.last_skill_time = 0
        
        self.stuck_detector = {
            "last_target_hp": 100,
            "hp_unchanged_since": 0,
            "stuck_in_combat_timeout": 8.0,
            "last_unstuck_attempt": 0,
            "unstuck_cooldown": 5.0
        }
        self.stuck_search_timer = 0

        self.last_kill_time = 0 
        
        
        self.mob_whitelist: List[str] = []
        self.potion_threshold = 70
        self.use_skills = True
        self.use_basic_attack_fallback = True
        self.skill_priority_mode = "rotation"
        
        self.timing = {
            'target_attempt_interval': 1.0,
            'movement_interval_searching': 4.0,
            'stuck_detection_searching': 10.0,
            'attack_interval': 1.5,
            'skill_interval': 0.8,
            'post_combat_delay': 2.0  # Valor por defecto, se sobrescribirá desde config
        }
        
        self.combat_stats = {
            'targets_acquired': 0, 'targets_lost': 0, 'skills_used': 0,
            'attacks_made': 0, 'stuck_in_combat': 0, 'stuck_searching': 0
        }
        
        # --- NUEVA CONFIGURACIÓN PARA EL LOOTEO ---
        self.looting_state = {
            "start_time": 0,
            "duration": 2.5,          # Duración total del estado de looteo (segundos)
            "initial_delay": 0.75,    # Esperar este tiempo antes del primer intento
            "loot_attempts": 2,       # Cuántas veces presionar la tecla de loot
            "attempt_interval": 0.5,  # Tiempo entre cada intento de loot
            "loot_key": "f"
        }

    def process_combat(self) -> None:
        if not self.is_running: return
        
        try:
            current_time = time.time()
            game_state = self.skill_manager.game_state
            target_exists = game_state.get('target_exists', False)
            target_name = game_state.get('target_name', '')
            target_hp = game_state.get('target_hp', 0)

            if self.state == CombatState.FIGHTING:
                    target_exists = game_state.get('target_exists', False)
                    target_hp = game_state.get('target_hp', 0)
                    if not self.current_target or not target_exists or target_hp <= 0:
                        # El objetivo murió, ¡a lootear!
                        self._transition_to_looting(current_time)
                    else:
                        self._check_stuck_in_combat(current_time, target_hp)
                        self._handle_fighting(current_time)

            elif self.state == CombatState.LOOTING:
                self._handle_looting(current_time)

            else: # Estamos en IDLE o TARGETING
                target_exists = game_state.get('target_exists', False)
                target_name = game_state.get('target_name', '')
                is_valid_new_target = self._evaluate_and_acquire_target(target_exists, target_name)
                if is_valid_new_target:
                    self.state = CombatState.FIGHTING
                else:
                    self._handle_searching(current_time)

        except Exception as e:
            self.logger.error(f"Error in combat loop: {e}")

    def _evaluate_and_acquire_target(self, target_exists: bool, target_name: str) -> bool:
        if self.current_target and not target_exists:
            self.logger.info(f"Target '{self.current_target}' defeated or lost.")
            self.combat_stats['targets_lost'] += 1
            self.current_target = None
            self.stuck_search_timer = 0

            self.last_kill_time = time.time()
        
        if target_exists and self._is_target_allowed(target_name):
            if self.current_target != target_name:
                self.logger.info(f"Acquired valid target: {target_name}")
                self.current_target = target_name
                self.stuck_detector["hp_unchanged_since"] = time.time()
                self.stuck_detector["last_target_hp"] = 100
                self.combat_stats['targets_acquired'] += 1
            return True
            
        return False

    def _handle_fighting(self, current_time: float):
        try:
            skill_used = False
            if self.use_skills and (current_time - self.last_skill_time >= self.timing['skill_interval']):
                next_skill = self.skill_manager.get_next_skill()
                if next_skill and self.skill_manager.can_use_skill(next_skill):
                    if self.skill_manager.use_skill(next_skill):
                        self.last_skill_time = current_time
                        self.combat_stats['skills_used'] += 1
                        self.logger.info(f"Used skill '{next_skill}' on {self.current_target}")
                        skill_used = True
            
            if not skill_used and (current_time - self.last_attack_time >= self.timing['attack_interval']):
                if self.use_basic_attack_fallback and self.input_controller.send_key('r'):
                    self.last_attack_time = current_time
                    self.combat_stats['attacks_made'] += 1
                    self.logger.info(f"Basic attack on {self.current_target}")
        except Exception as e:
            self.logger.error(f"Error during skill/attack execution: {e}")

    def _handle_searching(self, current_time: float):
        time_since_last_kill = current_time - self.last_kill_time
        if self.last_kill_time > 0 and time_since_last_kill < self.timing['post_combat_delay']:
            self.logger.debug(f"Post-combat delay. Waiting {self.timing['post_combat_delay'] - time_since_last_kill:.1f}s more...")
            return # No hacemos nada más hasta que pase el retraso
        if self.stuck_search_timer == 0:
            self.stuck_search_timer = current_time

        if current_time - self.last_target_attempt > self.timing['target_attempt_interval']:
            self.last_target_attempt = current_time
            self.logger.debug("Searching... attempting to target.")
            self.input_controller.send_key('e')

        if current_time - self.stuck_search_timer > self.timing['stuck_detection_searching']:
            self.logger.warning("No targets found for a while. Executing search movement.")
            self._simple_unstuck_movement("Searching for mobs")
            self.stuck_search_timer = current_time
            self.combat_stats['stuck_searching'] += 1

    def _check_stuck_in_combat(self, current_time: float, target_hp: int):
        if target_hp < self.stuck_detector["last_target_hp"]:
            self.stuck_detector["last_target_hp"] = target_hp
            self.stuck_detector["hp_unchanged_since"] = current_time
            return

        time_stuck = current_time - self.stuck_detector["hp_unchanged_since"]
        if time_stuck > self.stuck_detector["stuck_in_combat_timeout"]:
            if current_time - self.stuck_detector["last_unstuck_attempt"] > self.stuck_detector["unstuck_cooldown"]:
                self.logger.warning(f"STUCK IN COMBAT! Target HP unchanged for {time_stuck:.1f}s. Attempting to reposition.")
                self._simple_unstuck_movement("Stuck in combat")
                self.stuck_detector["last_unstuck_attempt"] = current_time
                self.stuck_detector["hp_unchanged_since"] = current_time
                self.combat_stats['stuck_in_combat'] += 1

    def _simple_unstuck_movement(self, reason: str):
        self.logger.info(f"Executing simple movement: {reason}")
        if not self.window_manager.target_window: return

        try:
            window_rect = self.window_manager.target_window.rect
            center_x = (window_rect[0] + window_rect[2]) // 2
            center_y = (window_rect[1] + window_rect[3]) // 2
            
            for i in range(2):
                radius = 100 
                rand_x = center_x + random.randint(-radius, radius)
                rand_y = center_y + random.randint(-radius, radius)
                self.logger.debug(f"Unstuck click #{i+1} at ({rand_x}, {rand_y})")
                self.input_controller.click_at(rand_x, rand_y, 'left')
                time.sleep(random.uniform(0.2, 0.4))
        except Exception as e:
            self.logger.error(f"Simple unstuck movement failed: {e}")

    def _is_target_allowed(self, target_name: str) -> bool:
        if not self.mob_whitelist: return True
        if not target_name: return False
        target_lower = target_name.lower().strip()
        for allowed in self.mob_whitelist:
            if allowed.lower().strip() in target_lower:
                return True
        return False
        
    def _reset_combat_state(self):
        self.current_target = None
        self.state = CombatState.IDLE
        self.stuck_search_timer = 0
        self.combat_stats['targets_lost'] += 1

    # ================================================================= #
    # === MÉTODOS DE CONTROL RESTAURADOS PARA COMPATIBILIDAD CON BOTENGINE ===
    # ================================================================= #

    def start(self):
        self.is_running = True
        self.logger.info("Combat Manager started.")
        self._reset_combat_state()

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
        """Devuelve una copia de las estadísticas de combate."""
        return self.combat_stats.copy()

    def reset_combat_stats(self) -> None:
        """Resetea las estadísticas de combate a cero."""
        for key in self.combat_stats:
            self.combat_stats[key] = 0
        self.logger.info("Combat stats have been reset.")
        if self.skill_manager:
            self.skill_manager.reset_usage_stats()

    # ================================================================= #
    # === RESTO DE MÉTODOS DE CONFIGURACIÓN (SIN CAMBIOS) ===
    # ================================================================= #

    def set_skill_usage(self, enabled: bool): self.use_skills = enabled
    def set_mob_whitelist(self, whitelist: List[str]): self.mob_whitelist = whitelist
    def set_potion_threshold(self, threshold: int): self.potion_threshold = threshold
    def set_skill_priority_mode(self, mode: str): self.skill_priority_mode = mode

    def _transition_to_looting(self, current_time: float):
        """Prepara e inicia el estado de looteo."""
        self.logger.info(f"Target '{self.current_target}' defeated. Transitioning to LOOTING.")
        self.combat_stats['targets_lost'] += 1
        self.current_target = None
        self.state = CombatState.LOOTING
        self.looting_state["start_time"] = current_time
        # Reiniciar los intentos de looteo para este ciclo
        self.looting_state["_attempts_made"] = 0 
        self.last_kill_time = current_time # Para el delay post-combate que ya tenías

    def _handle_looting(self, current_time: float):
        """Lógica que se ejecuta mientras se está en el estado LOOTING."""
        time_in_state = current_time - self.looting_state["start_time"]

        # 1. Si el tiempo total de looteo ha pasado, volvemos a buscar enemigos.
        if time_in_state > self.looting_state["duration"]:
            self.logger.info("Looting phase finished. Resuming search.")
            self.state = CombatState.TARGETING
            return

        # 2. Esperar el delay inicial antes de hacer el primer intento.
        if time_in_state < self.looting_state["initial_delay"]:
            return # Aún no es hora de lootear

        # 3. Hacer los intentos de looteo
        attempts_made = self.looting_state.get("_attempts_made", 0)
        if attempts_made < self.looting_state["loot_attempts"]:
            # Calculamos si ya es hora del siguiente intento
            next_attempt_time = self.looting_state["initial_delay"] + (attempts_made * self.looting_state["attempt_interval"])
            if time_in_state >= next_attempt_time:
                self.logger.debug(f"Looting attempt #{attempts_made + 1}")
                self.input_controller.send_key(self.looting_state["loot_key"])
                self.looting_state["_attempts_made"] = attempts_made + 1