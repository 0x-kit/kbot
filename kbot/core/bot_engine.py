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
    """Enhanced bot engine with full skills integration"""
    
    # Signals for UI updates
    state_changed = pyqtSignal(str)
    vitals_updated = pyqtSignal(dict)
    target_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Initialize core components
        self.logger = BotLogger("BotEngine")
        self.config_manager = ConfigManager()
        self.pixel_analyzer = PixelAnalyzer()
        self.window_manager = WindowManager(self.logger)
        self.input_controller = InputController(self.logger)
        self.timer_manager = TimerManager()

        # NUEVO: Crear movement manager
        from core.movement_manager import MovementManager
        self.movement_manager = MovementManager(
            self.input_controller,
            self.window_manager,
            self.logger
        )
        
        # Initialize skill system
        self.skill_manager = SkillManager(self.input_controller, self.logger)
        self.combat_manager = CombatManager(
            self.pixel_analyzer,
            self.skill_manager,
            self.input_controller,
            self.logger,
            self.movement_manager
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
            
            # Setup skills with enhanced configuration
            self._setup_enhanced_skills()
            
            # Load whitelist for combat manager
            whitelist = self.config_manager.get_whitelist()
            self.combat_manager.set_mob_whitelist(whitelist)
            
            # Set potion threshold
            threshold = self.config_manager.get_option('potion_threshold', 70)
            self.combat_manager.set_potion_threshold(threshold)
            
            # Configure combat manager skills settings
            self.combat_manager.set_skill_usage(True)  # Enable skills by default
            self.combat_manager.set_skill_priority_mode("rotation")  # Use rotation mode

            # Configure movement manager
            movement_config = {
                'movement_interval': 4.0,        # Move every 4 seconds when searching
                'max_stuck_time': 12.0,          # Consider stuck after 12 seconds
                'click_radius': 150,             # Larger click radius for more movement
                'directional_duration': 3.0      # Longer directional movements
            }
            self.movement_manager.set_movement_config(movement_config)

            # Configure combat manager for more aggressive searching
            self.combat_manager.configure_movement_behavior(aggressive_search=True)

            self.logger.info("Movement manager configured for active mob searching")
            
            # Update combat timing to include skills
            enhanced_timing = timing.copy()
            enhanced_timing['skill_interval'] = 0.8  # Add skill interval
            self.combat_manager.set_timing(enhanced_timing)
            
            self.logger.info("Bot configured successfully with enhanced skills integration")
            
        except Exception as e:
            self.logger.error(f"Failed to setup from config: {e}")
            raise BotError(f"Configuration setup failed: {e}")
        
    def _create_basic_skills_fallback(self) -> None:
        """Create basic skills as fallback"""
        try:
            # Create comprehensive Tantra skills
            basic_skills = TantraSkillTemplates.create_basic_skills()
            
            # Register all basic skills
            for skill in basic_skills:
                self.skill_manager.register_skill(skill)
            
            # Create a simple default rotation
            self.skill_manager.create_rotation("Default", ["Skill 1", "Skill 2"], repeat=True)
            self.skill_manager.set_active_rotation("Default")
            
            self.logger.info("Created basic skills fallback configuration")
            
        except Exception as e:
            self.logger.error(f"Failed to create basic skills fallback: {e}")
    
    def _setup_enhanced_skills(self) -> None:
        """FIXED: Enhanced skill setup with proper config loading"""
        try:
            # Clear existing skills first
            self.skill_manager.skills.clear()
            self.skill_manager.usage_stats.clear()
            self.skill_manager.rotations.clear()
            
            # Load custom configuration FIRST from config file
            skill_config = self.config_manager.get_skills()
            
            self.logger.info(f"Loading skills config: {len(skill_config.get('skills', {}))} skills found in config")
            
            # If we have a complete custom skills configuration, use it
            if skill_config and skill_config.get('skills'):
                self.logger.info("Loading skills from saved configuration")
                
                # Import the complete configuration from file
                try:
                    self.skill_manager.import_config(skill_config)
                    self.logger.info(f"Imported {len(self.skill_manager.skills)} skills from config")
                    
                    # Log which skills were loaded
                    for skill_name, skill in self.skill_manager.skills.items():
                        self.logger.debug(f"Loaded skill: {skill_name} (Key: {skill.key}, Enabled: {skill.enabled})")
                    
                except Exception as e:
                    self.logger.error(f"Failed to import skills config: {e}")
                    # Fall back to creating basic skills
                    self._create_basic_skills_fallback()
            else:
                # No saved config, create basic skills
                self.logger.info("No saved skills config found, creating basic skills")
                self._create_basic_skills_fallback()
            
            # Update skill keybinds and cooldowns from slots configuration
            slots = self.config_manager.get_slots()
            self._update_skill_keybinds(slots)
            
            # ENSURE ACTIVE ROTATION IS SET
            if skill_config.get('active_rotation') and skill_config['active_rotation'] in self.skill_manager.rotations:
                self.skill_manager.set_active_rotation(skill_config['active_rotation'])
                self.logger.info(f"Set active rotation from config: {skill_config['active_rotation']}")
            elif self.skill_manager.rotations:
                # If no active rotation set but rotations exist, set the first one
                first_rotation = list(self.skill_manager.rotations.keys())[0]
                self.skill_manager.set_active_rotation(first_rotation)
                self.logger.info(f"Auto-set active rotation: {first_rotation}")
            
            # Log final skill setup
            enabled_skills = [name for name, skill in self.skill_manager.skills.items() if skill.enabled]
            self.logger.info(f"Skills setup completed: {len(self.skill_manager.skills)} total, {len(enabled_skills)} enabled")
            self.logger.info(f"Active skills: {enabled_skills}")
            
            if self.skill_manager.rotations:
                self.logger.info(f"Available rotations: {list(self.skill_manager.rotations.keys())}")
                if self.skill_manager.active_rotation:
                    rotation = self.skill_manager.rotations[self.skill_manager.active_rotation]
                    self.logger.info(f"Active rotation: {self.skill_manager.active_rotation} -> Skills: {rotation.skills}")
                else:
                    self.logger.warning("No active rotation set!")
            else:
                self.logger.warning("No rotations configured!")
            
        except Exception as e:
            self.logger.error(f"Failed to setup enhanced skills: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
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
                        self.logger.debug(f"Updated {skill_name} cooldown to {cooldown}s")
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
                        self.logger.debug(f"Updated {skill_name} cooldown to {cooldown}s")
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
        
        # Combat timer with skills
        self.timer_manager.create_timer(
            'combat_loop',
            timing.get('combat_check', 0.5),
            self._combat_loop
        )
        
        # Stats update timer
        self.timer_manager.create_timer(
            'stats_update',
            5.0,  # Update stats every 5 seconds
            self._update_stats
        )
        
        # Skills maintenance timer (check cooldowns, etc.)
        self.timer_manager.create_timer(
            'skills_maintenance',
            2.0,  # Every 2 seconds
            self._maintain_skills
        )
    
    def start(self) -> bool:
        """Start the bot with enhanced logging"""
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
            
            # Start combat manager
            self.combat_manager.start()
            
            # Start timers
            self.timer_manager.start_all_timers()
            
            self._set_state(BotState.RUNNING)
            
            # Log startup summary
            skill_summary = self.combat_manager.get_skill_usage_summary()
            self.logger.info(f"Bot started successfully!")
            self.logger.info(f"Skills: {skill_summary.get('enabled_skills', 0)}/{skill_summary.get('total_skills_registered', 0)} enabled")
            if skill_summary.get('active_rotation'):
                self.logger.info(f"Active rotation: {skill_summary['active_rotation']}")
            
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
            
            # Stop combat manager
            self.combat_manager.stop()
            
            # Emergency stop input controller
            self.input_controller.emergency_stop()
            
            # Update final stats
            if self.stats['start_time'] > 0:
                self.stats['total_runtime'] += time.time() - self.stats['start_time']
            
            # Log final statistics
            combat_stats = self.combat_manager.get_combat_stats()
            skill_summary = self.combat_manager.get_skill_usage_summary()
            
            self.logger.info("Bot stopped successfully")
            self.logger.info(f"Session summary:")
            self.logger.info(f"  Targets killed: {combat_stats.get('targets_acquired', 0)}")
            self.logger.info(f"  Skills used: {combat_stats.get('skills_used', 0)}")
            self.logger.info(f"  Basic attacks: {combat_stats.get('attacks_made', 0)}")
            self.logger.info(f"  Total skill uses: {skill_summary.get('total_skill_uses', 0)}")
            
            self._set_state(BotState.STOPPED)
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
            self.combat_manager.pause()
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
            self.combat_manager.resume()
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
        
        # Check if we have at least some enabled skills
        enabled_skills = [s for s in self.skill_manager.skills.values() if s.enabled]
        if not enabled_skills:
            self.logger.warning("No skills are enabled - bot will only use basic attack")
        
        return True
    
    def _is_likely_ocr_noise(self, new_name: str, current_name: str) -> bool:
        """Check if the new name is likely OCR noise"""
        # Very different length
        if abs(len(new_name) - len(current_name)) > 3:
            return True
        
        # Contains obvious OCR garbage
        if any(char in new_name.lower() for char in ['1', '0', 'l', 'i']) and len(new_name) > 6:
            return True
        
        # Very short and not similar
        if len(new_name) <= 2:
            return True
        
        # Check similarity (simple check)
        if len(current_name) > 0:
            common_chars = sum(1 for c in new_name.lower() if c in current_name.lower())
            similarity = common_chars / max(len(new_name), len(current_name))
            
            # If less than 30% similarity, likely noise
            if similarity < 0.3:
                return True
        
        return False
    
    def _check_vitals(self) -> None:
        """Enhanced vitals checking with better skill state tracking"""
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
            
            # Update skill manager game state with comprehensive information
            self.skill_manager.update_game_state({
                'hp': vitals['hp'],
                'mp': vitals['mp'],
                'target_exists': vitals['target_exists'],
                'target_hp': vitals['target_health'],
                'target_name': vitals.get('target_name', ''),
                'in_combat': vitals['target_exists'] and vitals['target_health'] > 0
            })
            
            # Check for SIGNIFICANT target changes (filter OCR noise)
            detected_name = vitals['target_name']
            
            # Smart target change detection
            should_log_change = False
            
            if detected_name != self.current_target:
                if not self.current_target and detected_name:
                    # No previous target -> new target
                    should_log_change = True
                elif self.current_target and not detected_name:
                    # Had target -> no target (target died/lost)
                    should_log_change = True
                elif self.current_target and detected_name:
                    # Target name changed - check if it's significant
                    if (len(detected_name) >= 3 and 
                        detected_name.isalpha() and
                        not self._is_likely_ocr_noise(detected_name, self.current_target)):
                        should_log_change = True
                    else:
                        # Likely OCR noise - don't update current_target
                        self.logger.debug(f"Filtering OCR noise: '{detected_name}' (keeping '{self.current_target}')")
                        detected_name = self.current_target
            
            # Only update and log if it's a significant change
            if should_log_change:
                old_target = self.current_target
                self.current_target = detected_name
                
                if old_target and not self.current_target:
                    self.stats['targets_killed'] += 1
                    self.logger.info(f"Target defeated: {old_target}")
                
                if self.current_target and self.current_target != old_target:
                    self.logger.info(f"New target: {self.current_target}")
                
                self.target_changed.emit(self.current_target or "")
            
            # Enhanced potion usage with skill manager integration
            auto_pots = self.config_manager.get_option('auto_pots', True)
            if auto_pots:
                threshold = self.config_manager.get_option('potion_threshold', 70)
                
                # Try to use potions through skill manager first (for better tracking)
                if vitals['hp'] < threshold:
                    if self.skill_manager.can_use_skill('HP Potion'):
                        if self.skill_manager.use_skill('HP Potion'):
                            self.stats['potions_used'] += 1
                            self.logger.info(f"Used HP potion via skill system (HP: {vitals['hp']}%)")
                    else:
                        # Fallback to direct input if skill system fails
                        if self.input_controller.send_key('0'):
                            self.stats['potions_used'] += 1
                            self.logger.info(f"Used HP potion directly (HP: {vitals['hp']}%)")
                
                if vitals['mp'] < threshold:
                    if self.skill_manager.can_use_skill('MP Potion'):
                        if self.skill_manager.use_skill('MP Potion'):
                            self.stats['potions_used'] += 1
                            self.logger.info(f"Used MP potion via skill system (MP: {vitals['mp']}%)")
                    else:
                        # Fallback to direct input if skill system fails
                        if self.input_controller.send_key('9'):
                            self.stats['potions_used'] += 1
                            self.logger.info(f"Used MP potion directly (MP: {vitals['mp']}%)")
            
            # Store vitals and emit signal
            self.last_vitals = vitals
            self.vitals_updated.emit(vitals)
            
        except Exception as e:
            self.logger.error(f"Error checking vitals: {e}")
            self.stats['errors_occurred'] += 1
    
    def _combat_loop(self) -> None:
        """Main combat loop with enhanced logging"""
        if self.state != BotState.RUNNING:
            return
        
        try:
            self.combat_manager.process_combat()
            
        except Exception as e:
            self.logger.error(f"Error in combat loop: {e}")
            self.stats['errors_occurred'] += 1
    
    def _maintain_skills(self) -> None:
        """Maintain skills system (check cooldowns, update stats, etc.)"""
        if self.state != BotState.RUNNING:
            return
        
        try:
            # Update skill usage stats for main stats
            total_skill_uses = sum(usage.total_uses for usage in self.skill_manager.usage_stats.values())
            self.stats['skills_used'] = total_skill_uses
            
            # Log skill cooldown status periodically (every 30 seconds)
            current_time = time.time()
            if not hasattr(self, '_last_skill_log') or current_time - self._last_skill_log > 30:
                self._last_skill_log = current_time
                
                skills_on_cooldown = []
                for skill_name, skill in self.skill_manager.skills.items():
                    if skill.enabled:
                        usage = self.skill_manager.usage_stats.get(skill_name)
                        if usage and current_time - usage.last_used < skill.cooldown:
                            remaining = skill.cooldown - (current_time - usage.last_used)
                            if remaining > 1:  # Only log if more than 1 second remaining
                                skills_on_cooldown.append(f"{skill_name}({remaining:.0f}s)")
                
                if skills_on_cooldown:
                    self.logger.debug(f"Skills on cooldown: {', '.join(skills_on_cooldown)}")
            
        except Exception as e:
            self.logger.error(f"Error maintaining skills: {e}")
    
    def _update_stats(self) -> None:
        """Update runtime statistics with skills information"""
        if self.state == BotState.RUNNING and self.stats['start_time'] > 0:
            current_runtime = time.time() - self.stats['start_time']
            
            # Update skill usage stats from skill manager
            total_skill_uses = sum(usage.total_uses for usage in self.skill_manager.usage_stats.values())
            self.stats['skills_used'] = total_skill_uses
    
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
    
    # Enhanced public API methods
    
    def get_state(self) -> str:
        """Get current bot state"""
        return self.state.value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get enhanced bot statistics including skills"""
        current_stats = self.stats.copy()
        
        if self.state == BotState.RUNNING and self.stats['start_time'] > 0:
            current_stats['current_runtime'] = time.time() - self.stats['start_time']
        else:
            current_stats['current_runtime'] = 0
        
        # Add input controller stats
        input_stats = self.input_controller.get_input_stats()
        current_stats.update(input_stats)
        
        # Add combat stats
        combat_stats = self.combat_manager.get_combat_stats()
        current_stats.update(combat_stats)
        
        # Add skill usage summary
        skill_summary = self.combat_manager.get_skill_usage_summary()
        current_stats['skill_summary'] = skill_summary
        
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
            # Update skill configuration from skill manager
            skill_config = self.skill_manager.export_config()
            self.config_manager.set_skills(skill_config)
            
            # Save to file
            self.config_manager.save_config()
            self.logger.info("Configuration saved successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    # New methods for skills management
    
    def get_skill_manager(self) -> SkillManager:
        """Get the skill manager instance"""
        return self.skill_manager
    
    def get_combat_manager(self) -> CombatManager:
        """Get the combat manager instance"""
        return self.combat_manager
    
    def toggle_skill_usage(self) -> bool:
        """Toggle skill usage on/off"""
        current_state = self.combat_manager.use_skills
        new_state = not current_state
        self.combat_manager.set_skill_usage(new_state)
        self.logger.info(f"Skill usage {'enabled' if new_state else 'disabled'}")
        return new_state
    
    def set_active_rotation(self, rotation_name: Optional[str]) -> bool:
        """Set the active skill rotation"""
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
        """Get comprehensive skills status"""
        return {
            'skill_usage_enabled': self.combat_manager.use_skills,
            'priority_mode': self.combat_manager.skill_priority_mode,
            'active_rotation': self.skill_manager.active_rotation,
            'total_skills': len(self.skill_manager.skills),
            'enabled_skills': len([s for s in self.skill_manager.skills.values() if s.enabled]),
            'available_rotations': list(self.skill_manager.rotations.keys()),
            'skill_usage_summary': self.combat_manager.get_skill_usage_summary()
        }