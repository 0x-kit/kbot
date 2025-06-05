# core/bot_engine.py
import time
from typing import Dict, Any, Optional, Callable
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal

from config.config_manager import ConfigManager
from core.pixel_analyzer import PixelAnalyzer
from core.window_manager import WindowManager
from core.input_controller import InputController
from combat.combat_manager import CombatManager
from combat.skill_manager import SkillManager, TantraSkillTemplates
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
    """Main bot engine that coordinates all subsystems"""
    
    # Signals for UI updates
    state_changed = pyqtSignal(str)  # Bot state changes
    vitals_updated = pyqtSignal(dict)  # Health/mana updates
    target_changed = pyqtSignal(str)  # Target changes
    error_occurred = pyqtSignal(str)  # Error messages
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.logger = BotLogger("BotEngine")
        self.config_manager = ConfigManager()
        self.pixel_analyzer = PixelAnalyzer()
        self.window_manager = WindowManager(self.logger)
        self.input_controller = InputController(self.logger)
        self.timer_manager = TimerManager()
        
        # Initialize combat system
        self.skill_manager = SkillManager(self.input_controller)
        self.combat_manager = CombatManager(
            self.pixel_analyzer,
            self.skill_manager,
            self.input_controller,
            self.logger
        )
        
        # Bot state
        self.state = BotState.STOPPED
        self.last_vitals = {}
        self.current_target = None
        
        # Performance tracking
        self.stats = {
            'start_time': 0,
            'total_runtime': 0,
            'targets_killed': 0,
            'potions_used': 0,
            'skills_used': 0,
            'errors_occurred': 0
        }
        
        # Setup initial configuration
        self._setup_from_config()
        self._setup_timers()
        
        # Connect signals
        self.logger.log_message.connect(self._on_log_message)
    
    def _setup_from_config(self) -> None:
        """Initialize bot components from configuration"""
        try:
            # Load regions for pixel analyzer
            regions = self.config_manager.get_regions()
            
            # Load timing intervals
            timing = self.config_manager.get_timing()
            
            # Setup skills
            self._setup_skills()
            
            # Load whitelist for combat manager
            whitelist = self.config_manager.get_whitelist()
            self.combat_manager.set_mob_whitelist(whitelist)
            
            # Set potion threshold
            threshold = self.config_manager.get_option('potion_threshold', 70)
            self.combat_manager.set_potion_threshold(threshold)
            
            self.logger.info("Bot configured successfully from config file")
            
        except Exception as e:
            self.logger.error(f"Failed to setup from config: {e}")
            raise BotError(f"Configuration setup failed: {e}")
    
    def _setup_skills(self) -> None:
        """Setup skills from configuration"""
        try:
            # Create basic Tantra skills
            basic_skills = TantraSkillTemplates.create_basic_skills()
            for skill in basic_skills:
                self.skill_manager.register_skill(skill)
            
            # Load custom skill configuration
            skill_config = self.config_manager.get_skills()
            if skill_config and any(skill_config.values()):
                self.skill_manager.import_config(skill_config)
            
            # Update skill keybinds from slots configuration
            slots = self.config_manager.get_slots()
            self._update_skill_keybinds(slots)
            
        except Exception as e:
            self.logger.error(f"Failed to setup skills: {e}")
    
    def _update_skill_keybinds(self, slots: Dict[str, str]) -> None:
        """Update skill keybinds and cooldowns from slot configuration"""
        # Update number key skills (1-8)
        for i in range(1, 9):
            skill_name = f"Skill {i}"
            if skill_name in self.skill_manager.skills:
                slot_key = f"slot{i}"
                if slot_key in slots:
                    try:
                        cooldown = float(slots[slot_key])
                        self.skill_manager.skills[skill_name].cooldown = cooldown
                    except ValueError:
                        self.logger.warning(f"Invalid cooldown value for {skill_name}: {slots[slot_key]}")
        
        # Update F-key skills (F1-F10)
        for i in range(1, 11):
            skill_name = f"Skill F{i}"
            if skill_name in self.skill_manager.skills:
                slot_key = f"slotF{i}"
                if slot_key in slots:
                    try:
                        cooldown = float(slots[slot_key])
                        self.skill_manager.skills[skill_name].cooldown = cooldown
                    except ValueError:
                        self.logger.warning(f"Invalid cooldown value for {skill_name}: {slots[slot_key]}")
    
    def _setup_timers(self) -> None:
        """Setup all bot timers"""
        timing = self.config_manager.get_timing()
        
        # Main vitals monitoring timer
        self.timer_manager.create_timer(
            'vitals_check',
            timing.get('potion', 0.5),
            self._check_vitals
        )
        
        # Combat timer
        self.timer_manager.create_timer(
            'combat_loop',
            timing.get('combat_check', 1.0),
            self._combat_loop
        )
        
        # Stats update timer
        self.timer_manager.create_timer(
            'stats_update',
            5.0,  # Update stats every 5 seconds
            self._update_stats
        )
    
    def start(self) -> bool:
        """Start the bot"""
        if self.state != BotState.STOPPED:
            self.logger.warning("Bot is already running or in transition")
            return False
        
        try:
            self._set_state(BotState.STARTING)
            
            # Validate setup
            if not self._validate_setup():
                raise BotError("Bot setup validation failed")
            
            # Bring game window to foreground
            if self.window_manager.target_window:
                self.window_manager.bring_to_foreground()
            
            # Reset stats
            self.stats['start_time'] = time.time()
            
            # Start timers
            self.timer_manager.start_all_timers()
            
            self._set_state(BotState.RUNNING)
            self.logger.info("Bot started successfully")
            return True
            
        except Exception as e:
            self._set_state(BotState.ERROR)
            self.logger.error(f"Failed to start bot: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def stop(self) -> bool:
        """Stop the bot"""
        if self.state == BotState.STOPPED:
            return True
        
        try:
            self._set_state(BotState.STOPPING)
            
            # Stop all timers
            self.timer_manager.stop_all_timers()
            
            # Emergency stop input controller
            self.input_controller.emergency_stop()
            
            # Update final stats
            if self.stats['start_time'] > 0:
                self.stats['total_runtime'] += time.time() - self.stats['start_time']
            
            self._set_state(BotState.STOPPED)
            self.logger.info("Bot stopped successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error while stopping bot: {e}")
            self._set_state(BotState.ERROR)
            return False
    
    def pause(self) -> bool:
        """Pause the bot"""
        if self.state != BotState.RUNNING:
            return False
        
        try:
            self._set_state(BotState.PAUSING)
            self.timer_manager.stop_all_timers()
            self._set_state(BotState.PAUSED)
            self.logger.info("Bot paused")
            return True
        except Exception as e:
            self.logger.error(f"Error while pausing bot: {e}")
            return False
    
    def resume(self) -> bool:
        """Resume the bot from paused state"""
        if self.state != BotState.PAUSED:
            return False
        
        try:
            self.timer_manager.start_all_timers()
            self._set_state(BotState.RUNNING)
            self.logger.info("Bot resumed")
            return True
        except Exception as e:
            self.logger.error(f"Error while resuming bot: {e}")
            return False
    
    def toggle(self) -> bool:
        """Toggle bot between running and stopped"""
        if self.state == BotState.RUNNING:
            return self.stop()
        elif self.state == BotState.STOPPED:
            return self.start()
        elif self.state == BotState.PAUSED:
            return self.resume()
        else:
            return False
    
    def _validate_setup(self) -> bool:
        """Validate that bot is properly configured"""
        # Check if target window is set and valid
        if not self.window_manager.target_window:
            self.logger.error("No target window selected")
            return False
        
        if not self.window_manager.is_window_valid():
            self.logger.error("Target window is not valid")
            return False
        
        # Check if regions are configured
        regions = self.config_manager.get_regions()
        if not all(regions.values()):
            self.logger.error("Not all regions are configured")
            return False
        
        return True
    
    def _check_vitals(self) -> None:
        """Check health/mana and use potions if needed"""
        if self.state != BotState.RUNNING:
            return
        
        try:
            # Update window rectangle in case it moved
            self.window_manager.update_target_window_rect()
            
            # Set monitor rect for pixel analyzer
            if self.window_manager.target_window:
                self.pixel_analyzer.set_monitor_rect(self.window_manager.target_window.rect)
            
            # Get current vitals
            regions = self.config_manager.get_regions()
            vitals = self.pixel_analyzer.analyze_vitals(regions)
            
            # Update skill manager game state
            self.skill_manager.update_game_state({
                'hp': vitals['hp'],
                'mp': vitals['mp'],
                'target_exists': vitals['target_exists'],
                'target_hp': vitals['target_health'],
                'in_combat': vitals['target_exists']
            })
            
            # Check for target changes
            if vitals['target_name'] != self.current_target:
                old_target = self.current_target
                self.current_target = vitals['target_name']
                
                if old_target and not self.current_target:
                    self.stats['targets_killed'] += 1
                    self.logger.info(f"Target defeated: {old_target}")
                
                if self.current_target:
                    self.logger.info(f"New target: {self.current_target}")
                
                self.target_changed.emit(self.current_target or "")
            
            # Use potions if needed
            auto_pots = self.config_manager.get_option('auto_pots', True)
            if auto_pots:
                threshold = self.config_manager.get_option('potion_threshold', 70)
                
                if vitals['hp'] < threshold:
                    if self.skill_manager.use_skill('HP Potion'):
                        self.stats['potions_used'] += 1
                        self.logger.info(f"Used HP potion (HP: {vitals['hp']}%)")
                
                if vitals['mp'] < threshold:
                    if self.skill_manager.use_skill('MP Potion'):
                        self.stats['potions_used'] += 1
                        self.logger.info(f"Used MP potion (MP: {vitals['mp']}%)")
            
            # Store vitals and emit signal
            self.last_vitals = vitals
            self.vitals_updated.emit(vitals)
            
        except Exception as e:
            self.logger.error(f"Error checking vitals: {e}")
            self.stats['errors_occurred'] += 1
    
    def _combat_loop(self) -> None:
        """Main combat loop"""
        if self.state != BotState.RUNNING:
            return
        
        try:
            self.combat_manager.process_combat()
            
        except Exception as e:
            self.logger.error(f"Error in combat loop: {e}")
            self.stats['errors_occurred'] += 1
    
    def _update_stats(self) -> None:
        """Update runtime statistics"""
        if self.state == BotState.RUNNING and self.stats['start_time'] > 0:
            current_runtime = time.time() - self.stats['start_time']
            
            # Update skill usage stats
            self.stats['skills_used'] = sum(
                usage.total_uses for usage in self.skill_manager.usage_stats.values()
            )
    
    def _set_state(self, new_state: BotState) -> None:
        """Set bot state and emit signal"""
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            self.state_changed.emit(new_state.value)
            self.logger.debug(f"State changed: {old_state.value} -> {new_state.value}")
    
    def _on_log_message(self, message: str) -> None:
        """Handle log messages (can be connected to UI)"""
        pass  # This can be connected to UI log display
    
    # Public API methods
    
    def get_state(self) -> str:
        """Get current bot state"""
        return self.state.value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get bot statistics"""
        current_stats = self.stats.copy()
        
        if self.state == BotState.RUNNING and self.stats['start_time'] > 0:
            current_stats['current_runtime'] = time.time() - self.stats['start_time']
        else:
            current_stats['current_runtime'] = 0
        
        # Add input controller stats
        input_stats = self.input_controller.get_input_stats()
        current_stats.update(input_stats)
        
        return current_stats
    
    def get_vitals(self) -> Dict[str, Any]:
        """Get last vitals reading"""
        return self.last_vitals.copy()
    
    def set_target_window(self, hwnd: int) -> bool:
        """Set target window"""
        try:
            return self.window_manager.set_target_window(hwnd)
        except Exception as e:
            self.logger.error(f"Failed to set target window: {e}")
            return False
    
    def update_config(self) -> None:
        """Reload configuration and update components"""
        try:
            self.config_manager.load_config()
            self._setup_from_config()
            self.logger.info("Configuration updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update configuration: {e}")
    
    def save_config(self) -> bool:
        """Save current configuration"""
        try:
            # Update skill configuration
            skill_config = self.skill_manager.export_config()
            self.config_manager.set_skills(skill_config)
            
            # Save to file
            self.config_manager.save_config()
            self.logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False