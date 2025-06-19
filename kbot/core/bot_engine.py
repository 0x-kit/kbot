# kbot/core/bot_engine.py

import time
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from config.unified_config_manager import UnifiedConfigManager as ConfigManager
from core.pixel_analyzer import PixelAnalyzer
from core.window_manager import WindowManager
from core.input_controller import InputController
from combat.combat_manager import CombatManager, CombatState
from combat.skill_manager import SkillManager, TantraSkillTemplates, SkillType, Skill
from core.movement_manager import MovementManager
from utils.logger import BotLogger
from utils.timer_manager import TimerManager
from utils.exceptions import BotError


class BotState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSING = "pausing"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


class BotEngine(QObject):
    state_changed = pyqtSignal(str)
    vitals_updated = pyqtSignal(dict)
    # target_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):  # <-- Acepta un parent
        super().__init__(parent)  # <-- Pásalo al super

        # --- Componentes SIN estado de hilo (se pueden crear en cualquier sitio) ---
        self.logger = BotLogger("BotEngine")
        self.config_manager = ConfigManager()

        # --- Componentes que SÍ tienen estado de hilo (QObject) ---
        # Serán creados por el Worker para asegurar que están en el hilo correcto.
        self.timer_manager: Optional[TimerManager] = None
        self.window_manager: Optional[WindowManager] = None
        self.pixel_analyzer: Optional[PixelAnalyzer] = None
        self.input_controller: Optional[InputController] = None
        self.movement_manager: Optional[MovementManager] = None
        self.skill_manager: Optional[SkillManager] = None
        self.combat_manager: Optional[CombatManager] = None

        self.state = BotState.STOPPED
        self.last_vitals = {}
        self.current_target = None
        self.stats = {
            "start_time": 0,
            "total_runtime": 0,
            "targets_killed": 0,
            "potions_used": 0,
            "skills_used": 0,
            "errors_occurred": 0,
        }

    @pyqtSlot()
    def run(self):
        """Inicia el bot. Este slot será llamado por una señal desde el hilo principal."""
        if self.state == BotState.STOPPED:
            self.start()

    def set_target_window(self, hwnd: int) -> bool:
        """Set target window AND inform the pixel analyzer."""
        try:
            if self.window_manager.set_target_window(hwnd):
                # Este enlace es crucial. Informa al PixelAnalyzer de qué ventana capturar.
                self.pixel_analyzer.set_target_window(hwnd)
                self.logger.info(f"PixelAnalyzer is now targeting window 0x{hwnd:X}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set target window: {e}")
            return False

    def start(self) -> bool:
        """
        Prepara el bot para ejecutarse, validando la configuración.
        NO inicia los timers, eso lo hará el Worker.
        """
        if self.state != BotState.STOPPED:
            self.logger.warning("Bot is already running or in transition")
            return False

        try:
            self._set_state(BotState.STARTING)

            if self.window_manager.target_window:
                self.pixel_analyzer.set_target_window(
                    self.window_manager.target_window.hwnd
                )
            else:
                raise BotError("Cannot start bot: No target window selected.")

            if not self._validate_setup():
                raise BotError("Bot setup validation failed")

            # Opcional: Si quieres que la ventana se ponga al frente al iniciar.
            # self.window_manager.bring_to_foreground()

            self.stats["start_time"] = time.time()
            self.combat_manager.start()

            self._set_state(BotState.RUNNING)
            self.logger.info("Bot engine prepared and state set to RUNNING.")
            return True

        except Exception as e:
            self._set_state(BotState.ERROR)
            self.logger.error(f"Failed to start bot engine: {e}")
            self.error_occurred.emit(str(e))
            return False

    def _setup_from_config(self) -> None:
        """
        ✅ VERSIÓN ACTUALIZADA - Configura los componentes usando el sistema unificado
        """
        try:
            self.logger.info("Setting up bot components from unified configuration...")

            # Aplicar configuración usando métodos especializados
            self.update_components_from_config()

            # Configurar skills desde la nueva estructura
            self._setup_enhanced_skills_unified()

            self.logger.info("Bot configured successfully with unified config system.")

        except Exception as e:
            self.logger.error(f"Failed to setup from unified config: {e}")
            raise BotError(f"Unified configuration setup failed: {e}")

    def _setup_enhanced_skills_unified(self) -> None:
        """✅ NUEVO - Setup skills usando configuración unificada"""
        try:
            # Limpiar skills existentes
            self.skill_manager.skills.clear()
            self.skill_manager.usage_stats.clear()
            self.skill_manager.rotations.clear()

            # Obtener configuración de skills del sistema unificado
            skills_config = self.config_manager.get_skills_config()

            self.logger.info(
                f"Loading skills config: {len(skills_config.get('definitions', {}))} skills found"
            )

            if skills_config and skills_config.get("definitions"):
                self.logger.info("Loading skills from unified configuration")
                try:
                    # Preparar configuración en formato esperado por SkillManager
                    unified_skill_config = {
                        "skills": skills_config.get("definitions", {}),
                        "rotations": skills_config.get("rotations", {}),
                        "active_rotation": skills_config.get("active_rotation"),
                        "global_cooldown": skills_config.get("global_cooldown", 0.15),
                    }

                    self.skill_manager.import_config(unified_skill_config)
                    self.logger.info(
                        f"Imported {len(self.skill_manager.skills)} skills from unified config"
                    )

                except Exception as e:
                    self.logger.error(f"Failed to import unified skills config: {e}")
                    self._create_basic_skills_fallback()
            else:
                self.logger.info("No saved skills config found, creating basic skills")
                self._create_basic_skills_fallback()

            # Configurar rotación activa si existe
            if (
                skills_config.get("active_rotation")
                and skills_config["active_rotation"] in self.skill_manager.rotations
            ):
                self.skill_manager.set_active_rotation(skills_config["active_rotation"])
                self.logger.info(
                    f"Set active rotation from unified config: {skills_config['active_rotation']}"
                )

        except Exception as e:
            self.logger.error(f"Failed to setup unified skills: {e}")
            import traceback

            self.logger.error(traceback.format_exc())

    def _create_basic_skills_fallback(self) -> None:
        try:
            self.logger.info("Creating default essential skills (Attack & Potions)...")

            # Definimos los skills esenciales que el bot NECESITA para funcionar
            essential_skills = [
                Skill(
                    name="Basic Attack",
                    key="r",
                    cooldown=1.0,
                    skill_type=SkillType.AUTO_ATTACK,
                    priority=1,
                    enabled=True,
                ),
                Skill(
                    name="HP Potion",
                    key="0",
                    cooldown=0.5,
                    skill_type=SkillType.HP_POTION,
                    priority=10,
                    enabled=True,
                ),
                Skill(
                    name="MP Potion",
                    key="9",
                    cooldown=0.5,
                    skill_type=SkillType.MP_POTION,
                    priority=10,
                    enabled=True,
                ),
            ]

            for skill in essential_skills:
                # Solo lo registra si no existe un skill de ese tipo
                if not self.skill_manager.find_skill_by_type(skill.skill_type):
                    self.skill_manager.register_skill(skill)
                    self.logger.info(
                        f"Created default skill '{skill.name}' (Type: {skill.skill_type.value})"
                    )

            # Opcional: Crear una rotación por defecto si no hay ninguna
            if not self.skill_manager.rotations:
                # Creamos skills de ejemplo para la rotación
                demo_skill_1 = Skill(
                    name="Demo Skill 1",
                    key="1",
                    cooldown=1.0,
                    skill_type=SkillType.OFFENSIVE,
                    priority=2,
                )
                demo_skill_2 = Skill(
                    name="Demo Skill 2",
                    key="2",
                    cooldown=1.0,
                    skill_type=SkillType.OFFENSIVE,
                    priority=2,
                )
                self.skill_manager.register_skill(demo_skill_1)
                self.skill_manager.register_skill(demo_skill_2)
                self.skill_manager.create_rotation(
                    "DefaultRotation", ["Demo Skill 1", "Demo Skill 2"], repeat=True
                )
                self.skill_manager.set_active_rotation("DefaultRotation")
                self.logger.info("Created a default skill rotation for demonstration.")

        except Exception as e:
            self.logger.error(f"Failed to create basic skills fallback: {e}")

    def _setup_enhanced_skills(self) -> None:
        try:
            self.skill_manager.skills.clear()
            self.skill_manager.usage_stats.clear()
            self.skill_manager.rotations.clear()
            skill_config = self.config_manager.get_skills()
            self.logger.info(
                f"Loading skills config: {len(skill_config.get('skills', {}))} skills found in config"
            )
            if skill_config and skill_config.get("skills"):
                self.logger.info("Loading skills from saved configuration")
                try:
                    self.skill_manager.import_config(skill_config)
                    self.logger.info(
                        f"Imported {len(self.skill_manager.skills)} skills from config"
                    )
                    for skill_name, skill in self.skill_manager.skills.items():
                        self.logger.debug(
                            f"Loaded skill: {skill_name} (Key: {skill.key}, Enabled: {skill.enabled})"
                        )
                except Exception as e:
                    self.logger.error(f"Failed to import skills config: {e}")
                    self._create_basic_skills_fallback()
            else:
                self.logger.info("No saved skills config found, creating basic skills")
                self._create_basic_skills_fallback()
            # slots = self.config_manager.get_slots()
            # self._update_skill_keybinds(slots)
            if (
                skill_config.get("active_rotation")
                and skill_config["active_rotation"] in self.skill_manager.rotations
            ):
                self.skill_manager.set_active_rotation(skill_config["active_rotation"])
                self.logger.info(
                    f"Set active rotation from config: {skill_config['active_rotation']}"
                )
            elif self.skill_manager.rotations:
                first_rotation = list(self.skill_manager.rotations.keys())[0]
                self.skill_manager.set_active_rotation(first_rotation)
                self.logger.info(f"Auto-set active rotation: {first_rotation}")
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced skills: {e}")
            import traceback

            self.logger.error(traceback.format_exc())

    def _update_skill_keybinds(self, slots: Dict[str, str]) -> None:
        for i in range(1, 9):
            skill_name = f"Skill {i}"
            slot_key = f"slot{i}"
            if skill_name in self.skill_manager.skills and slot_key in slots:
                try:
                    self.skill_manager.skills[skill_name].cooldown = float(
                        slots[slot_key]
                    )
                except ValueError:
                    self.logger.warning(
                        f"Invalid cooldown value for {skill_name}: {slots[slot_key]}"
                    )
        for i in range(1, 11):
            skill_name = f"Skill F{i}"
            slot_key = f"slotF{i}"
            if skill_name in self.skill_manager.skills and slot_key in slots:
                try:
                    self.skill_manager.skills[skill_name].cooldown = float(
                        slots[slot_key]
                    )
                except ValueError:
                    self.logger.warning(
                        f"Invalid cooldown value for {skill_name}: {slots[slot_key]}"
                    )

    def _setup_timers(self) -> None:
        timing = self.config_manager.get_timing()
        self.timer_manager.create_timer(
            "vitals_check", timing.get("potion", 0.5), self._check_vitals
        )
        self.timer_manager.create_timer(
            "combat_loop", timing.get("combat_check", 0.5), self._combat_loop
        )
        self.timer_manager.create_timer("stats_update", 5.0, self._update_stats)
        self.timer_manager.create_timer(
            "skills_maintenance", 2.0, self._maintain_skills
        )
        self.timer_manager.create_timer(
            "buffs_maintenance", 5.0, self._maintain_skills_and_buffs
        )

    def stop(self) -> bool:
        if self.state == BotState.STOPPED:
            return True
        try:
            self._set_state(BotState.STOPPING)
            self.timer_manager.stop_all_timers()
            self.combat_manager.stop()
            self.input_controller.emergency_stop()
            if self.stats["start_time"] > 0:
                self.stats["total_runtime"] += time.time() - self.stats["start_time"]
            combat_stats = self.combat_manager.get_combat_stats()
            self.logger.info("Bot stopped successfully")
            self.logger.info(f"Session summary:")
            self.logger.info(
                f"  Targets killed: {combat_stats.get('targets_acquired', 0)}"
            )
            self._set_state(BotState.STOPPED)
            return True
        except Exception as e:
            self.logger.error(f"Error while stopping bot: {e}")
            self._set_state(BotState.ERROR)
            return False

    def pause(self) -> bool:
        if self.state != BotState.RUNNING:
            return False
        try:
            self._set_state(BotState.PAUSING)
            self.timer_manager.stop_all_timers()
            self.combat_manager.pause()
            self._set_state(BotState.PAUSED)
            self.logger.info("Bot paused")
            return True
        except Exception as e:
            self.logger.error(f"Error while pausing bot: {e}")
            return False

    def resume(self) -> bool:
        if self.state != BotState.PAUSED:
            return False
        try:
            self.combat_manager.resume()
            self.timer_manager.start_all_timers()
            self._set_state(BotState.RUNNING)
            self.logger.info("Bot resumed")
            return True
        except Exception as e:
            self.logger.error(f"Error while resuming bot: {e}")
            return False

    def toggle(self) -> bool:
        if self.state == BotState.RUNNING:
            return self.stop()
        if self.state == BotState.STOPPED:
            return self.start()
        if self.state == BotState.PAUSED:
            return self.resume()
        return False

    def _validate_setup(self) -> bool:
        if not self.window_manager.target_window:
            self.logger.error("No target window selected")
            return False
        if not self.window_manager.is_window_valid():
            self.logger.error("Target window is not valid")
            return False
        if not all(self.config_manager.get_regions().values()):
            self.logger.error("Not all regions are configured")
            return False
        return True

    def _is_likely_ocr_noise(self, new_name: str, current_name: str) -> bool:
        if not current_name or not new_name:
            return False
        if abs(len(new_name) - len(current_name)) > 3:
            return True
        common_chars = sum(1 for c in new_name.lower() if c in current_name.lower())
        similarity = common_chars / max(len(new_name), len(current_name), 1)
        return similarity < 0.3

    def _check_vitals(self) -> None:
        if self.state != BotState.RUNNING:
            return
        try:
            self.window_manager.update_target_window_rect()
            regions = self.config_manager.get_regions()
            vitals = self.pixel_analyzer.analyze_vitals(regions)

            self.skill_manager.update_game_state(
                {
                    "hp": vitals["hp"],
                    "mp": vitals["mp"],
                    "target_exists": vitals["target_exists"],
                    "target_hp": vitals["target_health"],
                    "target_name": vitals.get("target_name", ""),
                    "in_combat": vitals["target_exists"]
                    and vitals["target_health"] > 0,
                }
            )

            game_state_for_skills = {
                "hp": vitals.get("hp"),
                "mp": vitals.get("mp"),
                "target_exists": vitals.get("target_exists"),
                "target_hp": vitals.get("target_health"),
                "in_combat": self.combat_manager.state == CombatState.FIGHTING,
            }

            self.skill_manager.update_game_state(game_state_for_skills)

            detected_name = vitals.get("target_name", "")
            if detected_name != self.current_target:
                if (
                    (not self.current_target and detected_name)
                    or (self.current_target and not detected_name)
                    or (
                        self.current_target
                        and detected_name
                        and not self._is_likely_ocr_noise(
                            detected_name, self.current_target
                        )
                    )
                ):
                    old_target = self.current_target
                    self.current_target = detected_name
                    if old_target and not self.current_target:
                        self.stats["targets_killed"] += 1
                        self.logger.info(f"Target defeated: {old_target}")
                    if self.current_target and self.current_target != old_target:
                        self.logger.info(f"New target: {self.current_target}")
                #  self.target_changed.emit(self.current_target or "")
            auto_pots = self.config_manager.get_option("auto_pots", True)
            if auto_pots:
                threshold = self.config_manager.get_option("potion_threshold", 70)

                # --- LÓGICA DE HP POTION MEJORADA ---
                if vitals["hp"] < threshold:
                    hp_potion_skill = self.skill_manager.find_skill_by_type(
                        SkillType.HP_POTION
                    )
                    if hp_potion_skill and self.skill_manager.can_use_skill(
                        hp_potion_skill.name
                    ):
                        if self.skill_manager.use_skill(hp_potion_skill.name):
                            self.logger.debug(
                                f"Used HP Potion skill: '{hp_potion_skill.name}'"
                            )
                            self.stats["potions_used"] += 1

                # --- LÓGICA DE MP POTION MEJORADA ---
                if vitals["mp"] < threshold:
                    mp_potion_skill = self.skill_manager.find_skill_by_type(
                        SkillType.MP_POTION
                    )
                    if mp_potion_skill and self.skill_manager.can_use_skill(
                        mp_potion_skill.name
                    ):
                        if self.skill_manager.use_skill(mp_potion_skill.name):
                            self.logger.debug(
                                f"Used MP Potion skill: '{mp_potion_skill.name}'"
                            )
                            self.stats["potions_used"] += 1

            self.last_vitals = vitals
            self.vitals_updated.emit(vitals)
        except Exception as e:
            self.logger.error(f"Error checking vitals: {e}")
            self.stats["errors_occurred"] += 1

    def _combat_loop(self) -> None:
        if self.state == BotState.RUNNING:
            try:
                self.combat_manager.process_combat()
            except Exception as e:
                self.logger.error(f"Error in combat loop: {e}")
                self.stats["errors_occurred"] += 1

    def _maintain_skills(self) -> None:
        if self.state == BotState.RUNNING:
            try:
                self.stats["skills_used"] = sum(
                    usage.total_uses
                    for usage in self.skill_manager.usage_stats.values()
                )
                current_time = time.time()
                if (
                    not hasattr(self, "_last_skill_log")
                    or current_time - self._last_skill_log > 30
                ):
                    self._last_skill_log = current_time
                    skills_on_cooldown = []
                    for skill_name, skill in self.skill_manager.skills.items():
                        if skill.enabled:
                            usage = self.skill_manager.usage_stats.get(skill_name)
                            if (
                                usage
                                and current_time - usage.last_used < skill.cooldown
                            ):
                                remaining = skill.cooldown - (
                                    current_time - usage.last_used
                                )
                                if remaining > 1:
                                    skills_on_cooldown.append(
                                        f"{skill_name}({remaining:.0f}s)"
                                    )
                    if skills_on_cooldown:
                        self.logger.debug(
                            f"Skills on cooldown: {', '.join(skills_on_cooldown)}"
                        )
            except Exception as e:
                self.logger.error(f"Error maintaining skills: {e}")

    def _maintain_skills_and_buffs(self) -> None:
        """
        MÉTODO MEJORADO: Mantiene el sistema de habilidades, actualiza estadísticas
        Y se encarga de mantener los buffs activos fuera de combate.
        """
        if self.state != BotState.RUNNING:
            return

        try:
            # 1. Lógica de Buffs (LA NUEVA PARTE)
            # No queremos usar buffs si estamos en medio de una pelea, para no interrumpir el DPS.
            # Comprobamos el estado del CombatManager.
            if self.combat_manager.state != CombatState.FIGHTING:
                buffs_to_cast = self.skill_manager.get_buffs_to_refresh()

                if buffs_to_cast:
                    self.logger.info(f"Refrescando buffs: {', '.join(buffs_to_cast)}")
                    for buff_name in buffs_to_cast:
                        # Usamos la habilidad y añadimos un pequeño delay para no lanzarlos todos de golpe
                        if self.skill_manager.use_skill(buff_name):
                            self.logger.debug(f"Buff '{buff_name}' casteado con éxito.")
                            time.sleep(
                                1.2
                            )  # Pausa de 1.2 segundos entre cada buff para evitar fallos.
                        else:
                            self.logger.warning(
                                f"Intento de refrescar buff '{buff_name}' falló."
                            )

            # 2. Lógica de Estadísticas (la que ya tenías)
            total_skill_uses = sum(
                usage.total_uses for usage in self.skill_manager.usage_stats.values()
            )
            self.stats["skills_used"] = total_skill_uses

        except Exception as e:
            self.logger.error(f"Error en el mantenimiento de skills y buffs: {e}")
            self.stats["errors_occurred"] += 1

    def _update_stats(self) -> None:
        if self.state == BotState.RUNNING and self.stats["start_time"] > 0:
            self.stats["skills_used"] = sum(
                usage.total_uses for usage in self.skill_manager.usage_stats.values()
            )

    def _set_state(self, new_state: BotState) -> None:
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.state_changed.emit(new_state.value)
            self.logger.debug(f"State changed: {old_state.value} -> {new_state.value}")

    def _on_log_message(self, message: str) -> None:
        pass

    def get_state(self) -> str:
        return self.state.value

    def get_stats(self) -> Dict[str, Any]:
        current_stats = self.stats.copy()
        if self.state == BotState.RUNNING and self.stats["start_time"] > 0:
            current_stats["current_runtime"] = time.time() - self.stats["start_time"]
        else:
            current_stats["current_runtime"] = 0
        current_stats.update(self.input_controller.get_input_stats())
        current_stats.update(self.combat_manager.get_combat_stats())
        return current_stats

    def get_vitals(self) -> Dict[str, Any]:
        return self.last_vitals.copy()

    def update_config(self) -> None:
        """
        Recarga la configuración DESDE EL DISCO y actualiza los componentes.
        Se usa al inicio o si se carga un perfil.
        """
        try:
            self.config_manager.load_config()
            self.update_components_from_config()  # Reutilizamos la lógica
            self.logger.info("Configuration reloaded from file and components updated.")
        except Exception as e:
            self.logger.error(f"Failed to update configuration from file: {e}")

    def update_components_from_config(self):
        """
        ✅ VERSIÓN ACTUALIZADA - Usa métodos especializados del sistema unificado
        """
        try:
            # Obtener configuraciones usando métodos especializados
            behavior = self.config_manager.get_combat_behavior()
            timing = self.config_manager.get_combat_timing()
            whitelist = self.config_manager.get_whitelist()

            # Aplicar configuración de comportamiento
            self.combat_manager.set_mob_whitelist(whitelist)
            self.combat_manager.set_potion_threshold(
                behavior.get("potion_threshold", 70)
            )
            self.combat_manager.set_ocr_tolerance(behavior.get("ocr_tolerance", 85))
            self.combat_manager.set_looting_enabled(
                behavior.get("enable_looting", True)
            )
            self.combat_manager.set_assist_mode(behavior.get("assist_mode", False))
            self.combat_manager.set_skill_usage(behavior.get("use_skills", True))

            # Aplicar configuración de timing
            self.combat_manager.set_timing(timing)

            # Actualizar configuración de looteo
            loot_config = {
                "duration": behavior.get("loot_duration", 0.8),
                "initial_delay": behavior.get("loot_initial_delay", 0.1),
                "loot_attempts": behavior.get("loot_attempts", 2),
                "attempt_interval": behavior.get("loot_attempt_interval", 0.2),
                "loot_key": behavior.get("loot_key", "f"),
            }

            # Aplicar configuración de looteo al CombatManager
            if hasattr(self.combat_manager, "looting_config"):
                self.combat_manager.looting_config.update(loot_config)

            self.logger.info("Bot components updated from unified configuration.")

        except Exception as e:
            self.logger.error(f"Failed to update components from unified config: {e}")

    def save_config(self) -> bool:
        """
        ✅ VERSIÓN ACTUALIZADA - Guarda usando sistema unificado
        """
        try:
            # Exportar configuración de skills
            skill_config = self.skill_manager.export_config()

            # Guardar configuración de skills en el sistema unificado
            unified_skills_config = {
                "global_cooldown": skill_config.get("global_cooldown", 0.15),
                "active_rotation": skill_config.get("active_rotation"),
                "definitions": skill_config.get("skills", {}),
                "rotations": skill_config.get("rotations", {}),
            }

            self.config_manager.set_skills_config(unified_skills_config)

            # Guardar archivo
            self.config_manager.save_config()

            return True

        except Exception as e:
            self.logger.error(f"Failed to save unified configuration: {e}")
            return False

    def get_skill_manager(self) -> SkillManager:
        return self.skill_manager

    def get_combat_manager(self) -> CombatManager:
        return self.combat_manager

    def toggle_skill_usage(self) -> bool:
        new_state = not self.combat_manager.use_skills
        self.combat_manager.set_skill_usage(new_state)
        self.logger.info(f"Skill usage {'enabled' if new_state else 'disabled'}")
        return new_state

    def set_active_rotation(self, rotation_name: Optional[str]) -> bool:
        try:
            self.skill_manager.set_active_rotation(rotation_name)
            if rotation_name:
                self.logger.info(f"Active rotation set to: {rotation_name}")
            else:
                self.logger.info("Active rotation disabled (using priority mode)")
            return True
        except Exception as e:
            self.logger.error(f"Failed to set active rotation: {e}")
            return False

    def get_skills_status(self) -> Dict[str, Any]:
        return {
            "skill_usage_enabled": self.combat_manager.use_skills,
            "priority_mode": self.combat_manager.skill_priority_mode,
            "active_rotation": self.skill_manager.active_rotation,
            "total_skills": len(self.skill_manager.skills),
            "enabled_skills": len(
                [s for s in self.skill_manager.skills.values() if s.enabled]
            ),
            "available_rotations": list(self.skill_manager.rotations.keys()),
        }


class BotWorker(QObject):
    """
    Encapsula el BotEngine y gestiona su ciclo de vida y timers en un hilo separado.
    CRUCIAL: Ahora es responsable de INSTANCIAR los componentes en el hilo correcto.
    """

    def __init__(self):
        super().__init__()
        # El engine se crea vacío
        self.bot_engine = BotEngine()

    @pyqtSlot()
    def initialize_in_thread(self):
        """
        Este es el nuevo método clave. Se llama UNA VEZ que el worker
        ya ha sido movido al nuevo hilo. Aquí creamos todos los objetos
        que dependen de un hilo.
        """
        self.bot_engine.logger.info(
            "Initializing bot components inside the worker thread..."
        )

        # Ahora creamos el TimerManager DENTRO del nuevo hilo.
        self.bot_engine.timer_manager = TimerManager()

        # Y el resto de componentes.
        self.bot_engine.window_manager = WindowManager(logger=self.bot_engine.logger)
        self.bot_engine.pixel_analyzer = PixelAnalyzer(logger=self.bot_engine.logger)
        self.bot_engine.input_controller = InputController(
            window_manager=self.bot_engine.window_manager, logger=self.bot_engine.logger
        )
        self.bot_engine.movement_manager = MovementManager(
            input_controller=self.bot_engine.input_controller,
            window_manager=self.bot_engine.window_manager,
            logger=self.bot_engine.logger,
        )
        self.bot_engine.skill_manager = SkillManager(
            input_controller=self.bot_engine.input_controller,
            logger=self.bot_engine.logger,
        )
        self.bot_engine.combat_manager = CombatManager(
            pixel_analyzer=self.bot_engine.pixel_analyzer,
            skill_manager=self.bot_engine.skill_manager,
            input_controller=self.bot_engine.input_controller,
            movement_manager=self.bot_engine.movement_manager,
            logger=self.bot_engine.logger,
        )

        # Ahora que todo existe, configuramos el bot desde el config y creamos los timers.
        self.bot_engine._setup_from_config()
        self.bot_engine._setup_timers()
        self.bot_engine.logger.info(
            "Bot components initialized successfully in thread."
        )

        # Conectamos las señales del logger a nuestro slot interno
        self.bot_engine.logger.log_message.connect(self.bot_engine._on_log_message)

    # Los métodos start/stop/pause no cambian y funcionarán correctamente ahora.
    @pyqtSlot()
    def start_bot(self):
        if self.bot_engine.start():
            self.bot_engine.logger.info("Starting bot timers in worker thread...")
            self.bot_engine.timer_manager.start_all_timers()
        else:
            self.bot_engine.logger.error(
                "Bot engine failed to prepare, timers not started."
            )

    @pyqtSlot()
    def stop_bot(self):
        self.bot_engine.logger.info("Stopping bot timers in worker thread...")
        self.bot_engine.timer_manager.stop_all_timers()
        self.bot_engine.stop()

    @pyqtSlot()
    def pause_resume_bot(self):
        state = self.bot_engine.get_state()
        if state == "running":
            self.bot_engine.logger.info("Pausing timers...")
            self.bot_engine.timer_manager.stop_all_timers()
            self.bot_engine.pause()
        elif state == "paused":
            self.bot_engine.logger.info("Resuming timers...")
            self.bot_engine.timer_manager.start_all_timers()
            self.bot_engine.resume()
