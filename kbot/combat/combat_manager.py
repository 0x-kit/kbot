# kbot/combat/combat_manager.py

import time
from typing import Optional, List, Dict, Any
from enum import Enum
import random
from fuzzywuzzy import fuzz
from core.pixel_analyzer import PixelAnalyzer
from combat.skill_manager import SkillManager
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger
from utils.exceptions import BotError
class CombatState(Enum):
    IDLE = "idle"; TARGETING = "targeting"; FIGHTING = "fighting"; MOVING = "moving"; LOOTING = "looting"; POST_COMBAT = "post_combat"

class CombatManager:
    # ... (__init__ no cambia)
    def __init__(self, pixel_analyzer: PixelAnalyzer, skill_manager: SkillManager, 
                 input_controller: InputController, logger: BotLogger):
        self.pixel_analyzer = pixel_analyzer; self.skill_manager = skill_manager; self.input_controller = input_controller; self.logger = logger
        self.window_manager: WindowManager = self.input_controller.window_manager
        self.is_running = False; self.state = CombatState.IDLE; self.current_target = None; self.last_target_attempt = 0; self.last_attack_time = 0; self.last_skill_time = 0; self.stuck_search_timer = 0
        self.stuck_detector = {"last_target_hp": 100, "hp_unchanged_since": 0, "stuck_in_combat_timeout": 8.0, "last_unstuck_attempt": 0, "unstuck_cooldown": 5.0}
        self.looting_config = {"enabled": True, "duration": 1, "initial_delay": 0.2, "loot_attempts": 2, "attempt_interval": 0.3, "loot_key": "f"}
        self.looting_state_tracker = {"start_time": 0, "_attempts_made": 0}
        self.last_kill_time = 0; self.mob_whitelist: List[str] = []; self.potion_threshold = 70; self.use_skills = True;  self.use_basic_attack_fallback = True; self.skill_priority_mode = "rotation"
        self.timing = {'combat_log_interval': 2.0,'target_attempt_interval': 1.0, 'movement_interval_searching': 4.0, 'stuck_detection_searching': 10.0, 'attack_interval': 0.5, 'skill_interval': 2.25, 'post_combat_delay': 3.0}
        self.combat_stats = {'targets_acquired': 0, 'targets_lost': 0, 'skills_used': 0, 'attacks_made': 0, 'stuck_in_combat': 0, 'stuck_searching': 0}
        self.ocr_tolerance_threshold = 80
        self.last_combat_log_time = 0

    def process_combat(self) -> None:
        if not self.is_running: return
        try:
            current_time = time.time(); game_state = self.skill_manager.game_state
            if self.state == CombatState.FIGHTING: self._handle_fighting_state(current_time, game_state)
            elif self.state == CombatState.LOOTING: self._handle_looting_state(current_time)
            elif self.state == CombatState.POST_COMBAT: self._handle_post_combat_state(current_time)
            else: self._handle_searching_state(current_time, game_state)
        except Exception as e: self.logger.error(f"Error in main combat loop: {e}")

    # --- MÉTODO _handle_searching_state() REESCRITO ---
    def _handle_searching_state(self, current_time: float, game_state: dict):
        """
        Lógica unificada para cuando no estamos en combate. Gestiona la búsqueda,
        el re-targeteo de objetivos inválidos y el movimiento por atasco.
        """
        # 1. Comprobar si hemos encontrado un objetivo válido
        target_exists = game_state.get('target_exists', False)
        target_name = game_state.get('target_name', '')
        
        if target_exists and self._is_target_allowed(target_name):
            # ¡Éxito! Hemos encontrado algo que atacar.
            self.logger.info(f"Acquired valid target: {target_name}")
            self.current_target = target_name
            self.state = CombatState.FIGHTING

            # Justo después de adquirir un nuevo objetivo, reseteamos la rotación.
            self.skill_manager.reset_active_rotation()

            self._reset_stuck_detectors(current_time)
            self.combat_stats['targets_acquired'] += 1
            return # Salimos de la función de búsqueda

        # 2. Si llegamos aquí, no tenemos un objetivo válido. Iniciamos el temporizador de atasco.
        if self.stuck_search_timer == 0:
            self.stuck_search_timer = current_time

        # 3. Comprobar si el temporizador de atasco ha expirado.
        if current_time - self.stuck_search_timer > self.timing['stuck_detection_searching']:
            self.logger.warning(f"No valid target found for {self.timing['stuck_detection_searching']}s. Forcing movement.")
            self._simple_unstuck_movement("Searching for mobs")
            self.stuck_search_timer = current_time # Reiniciar temporizador
            return

        # 4. Si el temporizador no ha expirado, intentamos buscar un objetivo.
        if current_time - self.last_target_attempt > self.timing['target_attempt_interval']:
            self.last_target_attempt = current_time
            if target_exists:
                self.logger.debug(f"Invalid target '{target_name}'. Retrying target selection.")
            else:
                self.logger.debug("No target. Attempting to find one...")
            self.input_controller.send_key('e')
            time.sleep(0.1)

    # El resto del archivo no cambia. Lo pego para asegurar la integridad.
    def _handle_fighting_state(self, current_time: float, game_state: dict):
            """Lógica para cuando el bot está en combate."""
            target_exists = game_state.get('target_exists', False)
            target_hp = game_state.get('target_hp', 0)

            if not target_exists or target_hp <= 0 and self.looting_config['enabled']:
                self._transition_to_looting(current_time)
                return

            # --- NUEVA LÓGICA DE LOG DE PROGRESO ---
            if current_time - self.last_combat_log_time > self.timing['combat_log_interval']:
                self.logger.info(f"Fighting {self.current_target} (HP: {target_hp}%)")
                self.last_combat_log_time = current_time
            # --- FIN DE LA NUEVA LÓGICA ---

            self._check_stuck_in_combat(current_time, target_hp)
            self._perform_attack_routine(current_time)

    def _handle_looting_state(self, current_time: float):
            """
            Lógica que se ejecuta mientras se está en el estado LOOTING.
            Al finalizar, desactiva el modo caminar.
            """
            time_in_state = current_time - self.looting_state_tracker["start_time"]

            # Si el tiempo total de looteo ha pasado...
            if time_in_state > self.looting_config["duration"]:
                self.logger.info("Looting phase finished.")
                
                # --- NUEVA LÓGICA ---
                # 2. Desactivamos el modo caminar para volver a correr.
                self.logger.debug("Switching back to run mode.")
                # self.input_controller.send_key('z')
                # --------------------
                
                # Transicionamos al estado de espera post-combate.
                self.state = CombatState.POST_COMBAT
                self.last_kill_time = current_time # Guardamos el tiempo para el delay
                return

            # El resto de la lógica de looteo permanece igual.
            if time_in_state < self.looting_config["initial_delay"]: return
            
            attempts_made = self.looting_state_tracker.get("_attempts_made", 0)
            if attempts_made < self.looting_config["loot_attempts"]:
                next_attempt_time = self.looting_config["initial_delay"] + (attempts_made * self.looting_config["attempt_interval"])
                if time_in_state >= next_attempt_time:
                    self.logger.debug(f"Looting attempt #{attempts_made + 1}")
                    self.input_controller.send_key(self.looting_config["loot_key"])
                    self.looting_state_tracker["_attempts_made"] = attempts_made + 1

    def _handle_post_combat_state(self, current_time: float):
        """
        NUEVO MÉTODO: Simplemente espera a que pase el 'post_combat_delay'.
        """
        time_since_last_kill = current_time - self.last_kill_time

        #elf._simple_unstuck_movement("Cancel potential not owed loot")

        
        # Comprobamos si el tiempo de espera ha terminado.
        if time_since_last_kill >= self.timing['post_combat_delay']:
            self.logger.info("Post-combat delay finished. Resuming search.")
            self.state = CombatState.IDLE # Volvemos a buscar
        else:
            # Si no, logueamos cuánto falta.
            remaining = self.timing['post_combat_delay'] - time_since_last_kill
            self.logger.debug(f"Post-combat delay... {remaining:.1f}s remaining.")
            # Es importante añadir una pequeña pausa aquí para no consumir CPU en un bucle vacío.
            time.sleep(0.1)

    def _perform_attack_routine(self, current_time: float):
        """
        Ejecuta la rutina de ataque con lógica de "confirmación de daño".
        """
        # Obtenemos la vida actual del objetivo desde el game_state
        target_hp = self.skill_manager.game_state.get('target_hp', 100)

        # Si la vida del objetivo está al 100%, solo usamos el ataque básico para acercarnos/iniciar.
        if target_hp >= 100:
            if current_time - self.last_attack_time >= self.timing['attack_interval']:
                self.logger.debug(f"Target at 100% HP. Using basic attack to engage...")
                if self.input_controller.send_key('r'):
                    self.last_attack_time = current_time
                    self.combat_stats['attacks_made'] += 1
        
        # Si la vida del objetivo ya ha bajado, ¡desatamos la rotación de skills!
        else:
            skill_used = False
            if self.use_skills and (current_time - self.last_skill_time >= self.timing['skill_interval']):
                next_skill = self.skill_manager.get_next_skill()
                if next_skill and self.skill_manager.can_use_skill(next_skill):
                    if self.skill_manager.use_skill(next_skill):
                        self.last_skill_time = current_time
                        self.combat_stats['skills_used'] += 1
                        self.logger.info(f"Used skill '{next_skill}' on {self.current_target}")
                        skill_used = True
                        time.sleep(0.35)
                        
            
            # Si no se usó un skill, usamos el ataque básico como relleno.
            if not skill_used and (current_time - self.last_attack_time >= self.timing['attack_interval']):
                if self.use_basic_attack_fallback and self.input_controller.send_key('r'):
                    self.last_attack_time = current_time
                    self.combat_stats['attacks_made'] += 1
                    self.logger.info(f"Basic attack on {self.current_target}")
    def _is_target_allowed(self, target_name: str) -> bool:
        if not self.mob_whitelist: return True
        if not target_name: return False
        for allowed_mob in self.mob_whitelist:
            similarity_score = fuzz.partial_ratio(target_name.lower(), allowed_mob.lower())
            status = "Accepted" if  similarity_score >= self.ocr_tolerance_threshold else "Rejected"
            self.logger.debug(f"Fuzzy Match: '{target_name}' vs '{allowed_mob}' -> Score: {similarity_score}%. {status}")
            if  similarity_score >= self.ocr_tolerance_threshold: 
                return True
        return False
    def _transition_to_looting(self, current_time: float):
        """
        Prepara e inicia el estado de looteo, activando el modo caminar.
        """
        self.logger.info(f"Target '{self.current_target}' defeated. Transitioning to LOOTING.")
        self.combat_stats['targets_lost'] += 1
        self.current_target = None
        
        # --- NUEVA LÓGICA ---
        # 1. Activamos el modo caminar ANTES de empezar a lootear.
        # self.logger.debug("Switching to walk mode for safe looting.")
        # self.input_controller.send_key('z')
        # --------------------
        
        self.state = CombatState.LOOTING
        self.looting_state_tracker["start_time"] = current_time
        self.looting_state_tracker["_attempts_made"] = 0

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
        se mueve Y ABANDONA el objetivo actual para buscar uno nuevo.
        """
        # Si estamos haciendo daño, todo va bien. Reiniciamos el timer.
        if target_hp < self.stuck_detector["last_target_hp"]:
            self.stuck_detector["last_target_hp"] = target_hp
            self.stuck_detector["hp_unchanged_since"] = current_time
            return

        # Si no hemos hecho daño, comprobamos cuánto tiempo ha pasado.
        time_stuck = current_time - self.stuck_detector["hp_unchanged_since"]

        # Si superamos el tiempo límite...
        if time_stuck > self.stuck_detector["stuck_in_combat_timeout"]:
            # Y no hemos intentado desatascarnos recientemente...
            if current_time - self.stuck_detector["last_unstuck_attempt"] > self.stuck_detector["unstuck_cooldown"]:
                self.logger.warning(
                    f"STUCK IN COMBAT! Target HP unchanged for {time_stuck:.1f}s. "
                    f"Abandoning target '{self.current_target}' and repositioning."
                )
                
                # 1. Ejecutamos el movimiento de desatasco.
                self._simple_unstuck_movement("Stuck in combat")
                
                # --- 2. LÓGICA CLAVE AÑADIDA ---
                # "Nos rendimos" del objetivo actual y forzamos la vuelta al estado de búsqueda.
                self.current_target = None
                self.state = CombatState.IDLE # IDLE forzará una nueva búsqueda en el siguiente ciclo
                self.stuck_search_timer = 0 # Reiniciamos también el timer de búsqueda

                self.skill_manager.reset_active_rotation()
                
                # Actualizamos las estadísticas y el cooldown de desatasco
                self.combat_stats['stuck_in_combat'] += 1
                self.stuck_detector["last_unstuck_attempt"] = current_time
                return # Salimos para que el próximo ciclo empiece desde el estado IDLE
    def _simple_unstuck_movement(self, reason: str):
        self.logger.info(f"Executing simple movement: {reason}");
        if not self.window_manager.target_window: return
        try:
            window_rect = self.window_manager.target_window.rect; center_x = (window_rect[0] + window_rect[2]) // 2; center_y = (window_rect[1] + window_rect[3]) // 2
            for i in range(2):
                radius = 220; rand_x = center_x + random.randint(-radius, radius); rand_y = center_y + random.randint(-radius, radius)
                self.logger.debug(f"Unstuck click #{i+1} at ({rand_x}, {rand_y})"); self.input_controller.click_at(rand_x, rand_y, 'left'); time.sleep(random.uniform(0.2, 0.4))
        except Exception as e: self.logger.error(f"Simple unstuck movement failed: {e}")
    def start(self): self.is_running = True; self.logger.info("Combat Manager started."); self.state = CombatState.IDLE
    def stop(self): self.is_running = False; self.logger.info("Combat Manager stopped.")
    def pause(self): self.is_running = False; self.logger.info("Combat Manager paused.")
    def resume(self): self.is_running = True; self.logger.info("Combat Manager resumed.")
    def get_combat_stats(self) -> Dict[str, Any]: return self.combat_stats.copy()
    def reset_combat_stats(self):
        for key in self.combat_stats: self.combat_stats[key] = 0
        self.logger.info("Combat stats have been reset.")
        if self.skill_manager: self.skill_manager.reset_usage_stats()
    def set_skill_usage(self, enabled: bool): self.use_skills = enabled
    def set_mob_whitelist(self, whitelist: List[str]): self.mob_whitelist = whitelist
    def set_potion_threshold(self, threshold: int): self.potion_threshold = threshold
    def set_skill_priority_mode(self, mode: str): self.skill_priority_mode = mode
    def set_timing(self, timing_config: Dict[str, float]): self.timing.update(timing_config); self.logger.info(f"Combat timings updated: {self.timing}")
    def set_ocr_tolerance(self, tolerance: int):
        """Permite al BotEngine configurar la tolerancia."""
        # Asegurarse de que el valor está en un rango razonable
        self.ocr_tolerance_threshold = max(50, min(100, tolerance))
        self.logger.info(f"OCR match tolerance set to {self.ocr_tolerance_threshold}%.")
    def set_looting_enabled(self, enabled: bool):
        """NUEVO MÉTODO: Permite al BotEngine activar/desactivar el looteo."""
        self.looting_config['enabled'] = enabled
        self.logger.info(f"Looting after combat set to: {enabled}")
