# combat/combat_manager.py
import time
from typing import Optional, List, Dict, Any
from enum import Enum

from core.pixel_analyzer import PixelAnalyzer
from combat.skill_manager import SkillManager
from core.input_controller import InputController
from utils.logger import BotLogger
from utils.exceptions import BotError

class CombatState(Enum):
    IDLE = "idle"
    TARGETING = "targeting"
    FIGHTING = "fighting"
    MOVING = "moving"

class CombatManager:
    """Manages combat logic and target selection"""
    
    def __init__(self, pixel_analyzer: PixelAnalyzer, skill_manager: SkillManager, 
                 input_controller: InputController, logger: BotLogger):
        self.pixel_analyzer = pixel_analyzer
        self.skill_manager = skill_manager
        self.input_controller = input_controller
        self.logger = logger
        
        # Combat state
        self.state = CombatState.IDLE
        self.current_target = None
        self.last_target_attempt = 0
        self.last_movement = 0
        
        # Configuration
        self.mob_whitelist: List[str] = []
        self.potion_threshold = 70
        self.max_targeting_attempts = 10
        self.movement_duration = 3.0  # Seconds to move when no targets
        
        # Combat timing
        self.timing = {
            'target_attempt_interval': 0.7,
            'movement_interval': 5.0,
            'attack_interval': 1.5
        }
        
        # Statistics
        self.combat_stats = {
            'targets_acquired': 0,
            'targets_lost': 0,
            'targeting_attempts': 0,
            'movement_attempts': 0
        }
    
    def set_mob_whitelist(self, whitelist: List[str]) -> None:
        """Set the mob whitelist"""
        self.mob_whitelist = [mob.strip() for mob in whitelist if mob.strip()]
        self.logger.info(f"Mob whitelist updated: {self.mob_whitelist}")
    
    def set_potion_threshold(self, threshold: int) -> None:
        """Set potion usage threshold"""
        self.potion_threshold = max(1, min(100, threshold))
        self.logger.info(f"Potion threshold set to {self.potion_threshold}%")
    
    def process_combat(self) -> None:
        """Main combat processing method"""
        current_time = time.time()
        
        # Check if we have a valid target
        has_target = self._check_current_target()
        
        if has_target:
            self._handle_combat()
        else:
            self._handle_no_target(current_time)
    
    def _check_current_target(self) -> bool:
        """Check if current target is valid"""
        try:
            # This would be called from the main vitals check
            # We assume the game state is already updated in skill_manager
            game_state = self.skill_manager.game_state
            
            if not game_state.get('target_exists', False):
                if self.current_target:
                    self.logger.info(f"Lost target: {self.current_target}")
                    self.current_target = None
                    self.combat_stats['targets_lost'] += 1
                    self.state = CombatState.IDLE
                return False
            
            # Target exists, check if it's a valid target
            target_name = game_state.get('target_name', '')
            
            if target_name and target_name != self.current_target:
                # New target detected
                if self._is_target_allowed(target_name):
                    self.current_target = target_name
                    self.combat_stats['targets_acquired'] += 1
                    self.logger.info(f"Target acquired: {target_name}")
                    self.state = CombatState.FIGHTING
                    return True
                else:
                    # Invalid target, try to find a new one
                    self.logger.info(f"Skipping forbidden target: {target_name}")
                    self._attempt_new_target()
                    return False
            
            if self.current_target:
                self.state = CombatState.FIGHTING
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking target: {e}")
            return False
    
    def _is_target_allowed(self, target_name: str) -> bool:
        """Check if target is in whitelist"""
        if not self.mob_whitelist:
            return True  # If no whitelist, allow all targets
        
        target_lower = target_name.lower()
        return any(allowed.lower() in target_lower for allowed in self.mob_whitelist)
    
    def _handle_combat(self) -> None:
        """Handle combat when we have a target"""
        try:
            # Get next skill to use
            next_skill = self.skill_manager.get_next_skill()
            
            if next_skill:
                if self.skill_manager.use_skill(next_skill):
                    self.logger.debug(f"Used skill: {next_skill}")
                else:
                    # If we can't use any skills, fall back to basic attack
                    if self.skill_manager.use_skill('Basic Attack', force=True):
                        self.logger.debug("Used basic attack (fallback)")
            else:
                # No skills available, use basic attack
                if self.skill_manager.use_skill('Basic Attack', force=True):
                    self.logger.debug("Used basic attack (no skills available)")
                    
        except Exception as e:
            self.logger.error(f"Error in combat handling: {e}")
    
    def _handle_no_target(self, current_time: float) -> None:
        """Handle situation when we have no target"""
        # Try to acquire a new target
        if (current_time - self.last_target_attempt > 
            self.timing['target_attempt_interval']):
            self._attempt_new_target()
            self.last_target_attempt = current_time
        
        # If we still don't have a target after multiple attempts, move around
        if (self.state == CombatState.IDLE and 
            current_time - self.last_movement > self.timing['movement_interval']):
            self._move_to_find_targets()
            self.last_movement = current_time
    
    def _attempt_new_target(self) -> bool:
        """Attempt to acquire a new target"""
        try:
            self.state = CombatState.TARGETING
            self.combat_stats['targeting_attempts'] += 1
            
            # Press 'E' to target nearest mob
            if self.input_controller.send_key('e'):
                self.logger.debug("Attempting to target nearest mob")
                
                # Give some time for targeting to complete
                time.sleep(0.5)
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error attempting to target: {e}")
            return False
    
    def _move_to_find_targets(self) -> None:
        """Move around to find new targets"""
        try:
            self.state = CombatState.MOVING
            self.combat_stats['movement_attempts'] += 1
            
            self.logger.info("Moving to find targets")
            
            # Move forward for a short time
            self.input_controller.hold_key('w', self.movement_duration)
            
            self.state = CombatState.IDLE
            
        except Exception as e:
            self.logger.error(f"Error during movement: {e}")
            self.state = CombatState.IDLE
    
    def get_combat_state(self) -> str:
        """Get current combat state"""
        return self.state.value
    
    def get_current_target(self) -> Optional[str]:
        """Get current target name"""
        return self.current_target
    
    def get_combat_stats(self) -> Dict[str, Any]:
        """Get combat statistics"""
        return self.combat_stats.copy()
    
    def reset_combat_stats(self) -> None:
        """Reset combat statistics"""
        self.combat_stats = {
            'targets_acquired': 0,
            'targets_lost': 0,
            'targeting_attempts': 0,
            'movement_attempts': 0
        }
    
    def set_timing(self, timing_config: Dict[str, float]) -> None:
        """Update combat timing configuration"""
        self.timing.update(timing_config)
        self.logger.info(f"Combat timing updated: {self.timing}")
    
    def emergency_stop(self) -> None:
        """Emergency stop all combat actions"""
        self.state = CombatState.IDLE
        self.current_target = None
        self.input_controller.emergency_stop()
        self.logger.info("Combat emergency stop executed")