# kbot/core/bot_engine.py

import time
import traceback
from typing import Dict, Any, Optional, Callable
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from config.unified_config_manager import UnifiedConfigManager
from core.pixel_analyzer import PixelAnalyzer
from core.window_manager import WindowManager
from core.input_controller import InputController
from combat.combat_manager import CombatManager, CombatState
from combat.skill_manager import SkillManager, Skill, SkillType
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
    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = BotLogger("BotEngine")
        self.config_manager = UnifiedConfigManager()

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
        if self.state == BotState.STOPPED:
            self.start()

    def set_target_window(self, hwnd: int) -> bool:
        try:
            if self.window_manager.set_target_window(hwnd):
                self.pixel_analyzer.set_target_window(hwnd)
                self.logger.info(f"PixelAnalyzer is now targeting window 0x{hwnd:X}.")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to set target window: {e}")
            return False

    def start(self) -> bool:
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
        try:
            self.logger.info("Setting up bot components from unified configuration...")
            self.update_components_from_config()
            self._setup_skills_from_config()
            self.logger.info("Bot configured successfully with unified config system.")
        except Exception as e:
            self.logger.error(f"Failed to setup from unified config: {e}")
            raise BotError(f"Unified configuration setup failed: {e}")

    def _setup_skills_from_config(self) -> None:
        try:
            skills_config = self.config_manager.get_skills_config()
            if skills_config and skills_config.get("definitions"):
                self.logger.info("Loading skills from unified configuration.")
                self.skill_manager.import_config(skills_config)
                self.logger.info(f"Imported {len(self.skill_manager.skills)} skills.")
            else:
                self.logger.warning(
                    "No skills found in config, creating fallback skills."
                )
                self._create_basic_skills_fallback()

        except Exception as e:
            self.logger.error(f"Failed to setup skills: {e}", exc_info=True)

    def _create_basic_skills_fallback(self) -> None:
        """✅ CORREGIDO: Crea skills básicos directamente sin usar TantraSkillTemplates."""
        try:
            self.logger.info("Creating default essential skills (Attack & Potions)...")

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
                    key="8",
                    cooldown=1.0,
                    skill_type=SkillType.HP_POTION,
                    priority=10,
                    enabled=True,
                    icon="resources/skills/samabat/ICON_SKILL_AO_DESTI.bmp",
                ),
                Skill(
                    name="MP Potion",
                    key="9",
                    cooldown=1.0,
                    skill_type=SkillType.MP_POTION,
                    priority=10,
                    enabled=True,
                    icon="resources/skills/samabat/ICON_SKILL_AO_DADATI.bmp",
                ),
                Skill(
                    name="Assist",
                    key="q",
                    cooldown=1.0,
                    skill_type=SkillType.ASSIST,
                    priority=1,
                    enabled=True,
                ),
            ]

            for skill in essential_skills:
                if not self.skill_manager.find_skill_by_type(skill.skill_type):
                    self.skill_manager.register_skill(skill)
                    self.logger.info(
                        f"Created default skill '{skill.name}' (Type: {skill.skill_type.value})"
                    )

            # Guardar esta configuración básica para que el usuario pueda empezar
            self.save_config()

        except Exception as e:
            self.logger.error(
                f"Failed to create basic skills fallback: {e}", exc_info=True
            )

    def _setup_timers(self) -> None:
        timing = self.config_manager.get_combat_timing()
        vitals_interval = timing.get("vitals_check_interval", 0.5)
        self.timer_manager.create_timer(
            "main_loop", vitals_interval, self._optimized_main_loop
        )
        stats_interval = timing.get("stats_update_interval", 5.0)
        self.timer_manager.create_timer(
            "stats_update", stats_interval, self._update_stats
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
            self._set_state(BotState.STOPPED)
            return True
        except Exception as e:
            self.logger.error(f"Error while stopping bot: {e}")
            self._set_state(BotState.ERROR)
            return False

    def pause(self) -> bool:
        if self.state != BotState.RUNNING:
            return False
        self._set_state(BotState.PAUSING)
        self.timer_manager.stop_all_timers()
        self.combat_manager.pause()
        self._set_state(BotState.PAUSED)
        self.logger.info("Bot paused")
        return True

    def resume(self) -> bool:
        if self.state != BotState.PAUSED:
            return False
        self.combat_manager.resume()
        self.timer_manager.start_all_timers()
        self._set_state(BotState.RUNNING)
        self.logger.info("Bot resumed")
        return True

    def _validate_setup(self) -> bool:
        if not self.window_manager.target_window:
            self.logger.error("No target window selected")
            return False
        if not all(self.config_manager.get_regions().values()):
            self.logger.error("Not all regions are configured")
            return False
        return True

    def _check_vitals(self) -> None:
        if self.state != BotState.RUNNING:
            return
        try:
            self.window_manager.update_target_window_rect()
            regions = self.config_manager.get_regions()
            vitals = self.pixel_analyzer.analyze_vitals(regions)

            game_state = {
                "hp": vitals.get("hp", 100),
                "mp": vitals.get("mp", 100),
                "target_exists": vitals.get("target_exists", False),
                "target_hp": vitals.get("target_health", 0),
                "target_name": vitals.get("target_name", ""),
                "in_combat": self.combat_manager.state == CombatState.FIGHTING,
            }
            self.skill_manager.update_game_state(game_state)
            self.vitals_updated.emit(vitals)
        except Exception as e:
            self.logger.error(f"Error checking vitals: {e}", exc_info=True)

    def _optimized_main_loop(self) -> None:
        if self.state != BotState.RUNNING:
            return
        try:
            self._check_vitals()
            self.combat_manager.process_combat()
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}", exc_info=True)

    def _update_stats(self) -> None:
        if self.state == BotState.RUNNING and self.stats["start_time"] > 0:
            self.stats["skills_used"] = sum(
                usage.total_uses for usage in self.skill_manager.usage_stats.values()
            )

    def _set_state(self, new_state: BotState) -> None:
        if self.state != new_state:
            self.state = new_state
            self.state_changed.emit(new_state.value)

    def get_state(self) -> str:
        return self.state.value

    def get_stats(self) -> Dict[str, Any]:
        return self.stats.copy()

    def get_vitals(self) -> Dict[str, Any]:
        return self.last_vitals.copy()
    
    def get_skills_status(self) -> list:
        """Get current skills status for UI display - only offensive and buff skills"""
        if not self.skill_manager:
            return []
        
        from combat.skill_manager import SkillType
        
        skills_data = []
        skills = self.skill_manager.get_all_skills()
        current_time = time.time()
        
        for skill in skills:
            # Solo mostrar skills ofensivos y buffs
            if skill.skill_type not in [SkillType.OFFENSIVE, SkillType.BUFF]:
                continue
                
            skill_usage = self.skill_manager.usage_stats.get(skill.name, None)
            
            if skill.skill_type == SkillType.OFFENSIVE:
                # Para skills ofensivos: verificar cooldown visual
                try:
                    is_ready = self.skill_manager.can_use_skill(skill.name) if skill_usage else False
                except Exception:
                    is_ready = False
                status_info = {
                    'name': skill.name,
                    'key': skill.key,
                    'enabled': skill.enabled,
                    'type': 'offensive',
                    'visual_cooldown': not is_ready,  # True si está en cooldown visual
                    'is_ready': is_ready,
                    'icon': skill.icon or ''
                }
            
            elif skill.skill_type == SkillType.BUFF:
                # Para buffs: mostrar duración restante
                buff_remaining = 0
                if skill_usage and skill_usage.buff_expires_at > 0:
                    buff_remaining = max(0, skill_usage.buff_expires_at - current_time)
                
                status_info = {
                    'name': skill.name,
                    'key': skill.key,
                    'enabled': skill.enabled,
                    'type': 'buff',
                    'buff_remaining': buff_remaining,
                    'buff_duration': skill.duration,
                    'icon': skill.icon or ''
                }
            
            skills_data.append(status_info)
        
        # Ordenar por key (tecla asignada)
        skills_data.sort(key=lambda x: x['key'])
        return skills_data

    def update_components_from_config(self):
        try:
            behavior = self.config_manager.get_combat_behavior()
            timing = self.config_manager.get_combat_timing()
            whitelist = self.config_manager.get_whitelist()
            self.combat_manager.set_mob_whitelist(whitelist)
            self.combat_manager.set_potion_threshold(
                behavior.get("potion_threshold", 70)
            )
            self.combat_manager.set_ocr_tolerance(behavior.get("ocr_tolerance", 85))
            self.combat_manager.set_looting_enabled(
                behavior.get("enable_looting", True)
            )
            self.combat_manager.set_loot_attempts(behavior.get("loot_attempts", 1))
            self.combat_manager.set_assist_mode(behavior.get("assist_mode", False))
            self.combat_manager.set_use_skills(behavior.get("use_skills", True))
            
            # ✅ SIMPLIFICADO: Incluir loot_duration de behavior en timing
            complete_timing = timing.copy()
            if "loot_duration" in behavior:
                complete_timing["loot_duration"] = behavior["loot_duration"]
            
            self.combat_manager.set_timing(complete_timing)
        except Exception as e:
            self.logger.error(
                f"Failed to update components from config: {e}", exc_info=True
            )

    def save_config(self) -> bool:
        try:
            skill_config_export = self.skill_manager.export_config()
            self.config_manager.set_skills_config(skill_config_export)
            self.config_manager.save_config()
            return True
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}", exc_info=True)
            return False


class ComponentFactory:
    """✅ CORREGIDO: Fábrica de componentes que pasa todas las dependencias necesarias."""

    @staticmethod
    def create_components(
        logger: BotLogger, config_manager: UnifiedConfigManager
    ) -> Dict[str, Any]:
        components = {}

        components["timer_manager"] = TimerManager()
        components["window_manager"] = WindowManager(logger=logger)
        components["pixel_analyzer"] = PixelAnalyzer(logger=logger)
        components["input_controller"] = InputController(
            window_manager=components["window_manager"], logger=logger
        )
        components["movement_manager"] = MovementManager(
            input_controller=components["input_controller"],
            window_manager=components["window_manager"],
            logger=logger,
        )

        # ✅ SkillManager ahora recibe pixel_analyzer y config_manager
        components["skill_manager"] = SkillManager(
            input_controller=components["input_controller"],
            pixel_analyzer=components["pixel_analyzer"],
            config_manager=config_manager,
            logger=logger,
        )

        components["combat_manager"] = CombatManager(
            pixel_analyzer=components["pixel_analyzer"],
            skill_manager=components["skill_manager"],
            input_controller=components["input_controller"],
            movement_manager=components["movement_manager"],
            logger=logger,
        )

        return components


class BotWorker(QObject):
    initialization_complete = pyqtSignal()
    initialization_failed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.bot_engine = BotEngine()
        self._initialized = False

    @pyqtSlot()
    def initialize_in_thread(self):
        if self._initialized:
            return
        try:
            self.bot_engine.logger.info(
                "Initializing bot components in worker thread..."
            )

            # ✅ Pasamos el config_manager a la fábrica
            components = ComponentFactory.create_components(
                logger=self.bot_engine.logger,
                config_manager=self.bot_engine.config_manager,
            )

            for name, component in components.items():
                setattr(self.bot_engine, name, component)

            self.bot_engine._setup_from_config()
            self.bot_engine._setup_timers()

            self._initialized = True
            self.initialization_complete.emit()
        except Exception as e:
            error_msg = (
                f"Failed to initialize bot components: {e}\n{traceback.format_exc()}"
            )
            self.bot_engine.logger.critical(error_msg)
            self.initialization_failed.emit(error_msg)

    @pyqtSlot()
    def start_bot(self):
        if not self._initialized:
            return
        if self.bot_engine.start():
            self.bot_engine.timer_manager.start_all_timers()

    @pyqtSlot()
    def stop_bot(self):
        if not self._initialized:
            return
        self.bot_engine.timer_manager.stop_all_timers()
        self.bot_engine.stop()

    @pyqtSlot()
    def pause_resume_bot(self):
        if not self._initialized:
            return
        state = self.bot_engine.get_state()
        if state == "running":
            self.bot_engine.pause()
        elif state == "paused":
            self.bot_engine.resume()
