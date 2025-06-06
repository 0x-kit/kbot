# combat/combat_manager.py
import time
from typing import Optional, List, Dict, Any
from enum import Enum
import random

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
                    input_controller: InputController, logger: BotLogger, movement_manager=None):
            self.pixel_analyzer = pixel_analyzer
            self.skill_manager = skill_manager
            self.input_controller = input_controller
            self.logger = logger
            self.movement_manager = movement_manager  # Add movement manager

            self.is_running = False
            
            # Combat state
            self.state = CombatState.IDLE
            self.current_target = None
            self.last_target_attempt = 0
            self.last_movement = 0
            self.last_attack_time = 0
            self.stuck_start_time = 0  # Track when we might be stuck
            
            # Configuration
            self.mob_whitelist: List[str] = []
            self.potion_threshold = 70
            self.max_targeting_attempts = 10
            self.movement_duration = 3.0
            
            # Combat timing
            self.timing = {
                'target_attempt_interval': 1.0,  # Try targeting every 1 second
                'movement_interval': 8.0,        # Only move every 8 seconds if targeting fails
                'attack_interval': 1.5,
                'stuck_detection_time': 20.0     # Consider stuck after 12 seconds
            }

            
            # Statistics
            self.combat_stats = {
                'targets_acquired': 0,
                'targets_lost': 0,
                'targeting_attempts': 0,
                'movement_attempts': 0,
                'attacks_made': 0,
                'stuck_situations': 0
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
            if not self.is_running:
                return
                
            try:
                current_time = time.time()
                
                # Get current game state
                game_state = self.skill_manager.game_state
                target_exists = game_state.get('target_exists', False)
                target_name = game_state.get('target_name', '')
                target_health = game_state.get('target_hp', 0)
                
                # Enhanced logging for debugging
                self.logger.debug(f"Combat loop: exists={target_exists}, name='{target_name}', hp={target_health}%, current='{self.current_target}', state={self.state.value}")
                
                # CRITICAL: Don't evaluate targets if we're currently fighting and target still exists
                if (self.state == CombatState.FIGHTING and 
                    self.current_target and 
                    target_exists and 
                    target_health > 0):
                    
                    # We're in combat with a living target - DON'T re-evaluate, just keep fighting
                    self.logger.debug(f"Mid-combat with {self.current_target} ({target_health}% HP) - continuing attack")
                    self._handle_combat(current_time)
                    return
                
                # Only evaluate targets if:
                # 1. We're not currently fighting, OR
                # 2. Current target is dead/lost, OR  
                # 3. No target exists
                valid_target = self._evaluate_target(target_exists, target_name)
                
                if valid_target:
                    # We have a valid target to attack
                    self.state = CombatState.FIGHTING
                    self._handle_combat(current_time)
                else:
                    # No valid target - try to find one
                    self.state = CombatState.TARGETING
                    self._handle_no_target(current_time)
                    
            except Exception as e:
                self.logger.error(f"Error in combat loop: {e}")

    def _evaluate_target(self, target_exists: bool, target_name: str) -> bool:
            """Evaluate if we have a valid target to attack - NEVER switch mid-combat"""
            # Reset stuck timer when we have a target
            if target_exists:
                self.stuck_start_time = 0
            
            self.logger.debug(f"Target evaluation: exists={target_exists}, name='{target_name}', current='{self.current_target}'")
            
            # No target at all
            if not target_exists:
                if self.current_target:
                    self.logger.info(f"Lost target: {self.current_target}")
                    self.current_target = None
                    self.combat_stats['targets_lost'] += 1
                return False
            
            # We have a target, but no name detected (OCR issue or lag)
            if target_exists and not target_name:
                self.logger.debug("Target exists but no name detected")
                
                # CRITICAL: If we had a valid target before, KEEP ATTACKING IT
                if self.current_target and self._is_target_allowed(self.current_target):
                    self.logger.debug(f"Continuing attack on {self.current_target} (OCR temporary failure)")
                    return True
                
                # If no previous target, can't validate without name
                self.logger.debug("No previous target and no name - cannot validate")
                return False
            
            # We have a target with a name - this is where the logic needs to be VERY careful
            if target_name:
                self.logger.debug(f"Target detected with name: '{target_name}'")
                
                # CRITICAL CHECK: If we already have a target and it's valid, DON'T SWITCH
                if self.current_target and self._is_target_allowed(self.current_target):
                    # We have a valid current target
                    
                    if target_name == self.current_target:
                        # Same target - all good, keep attacking
                        self.logger.debug(f"Same target confirmed: {target_name}")
                        return True
                    else:
                        # DIFFERENT target detected - THIS IS THE CRITICAL DECISION
                        self.logger.warning(f"Different target detected: current='{self.current_target}' detected='{target_name}'")
                        
                        # Check if the current target is still in whitelist and alive
                        if self._is_target_allowed(self.current_target):
                            self.logger.info(f"KEEPING current target '{self.current_target}' - ignoring '{target_name}'")
                            # DON'T SWITCH - keep current target
                            return True
                        else:
                            self.logger.info(f"Current target '{self.current_target}' no longer valid, switching to '{target_name}'")
                
                # No current target OR current target is invalid
                # Check if the new target is allowed
                if self._is_target_allowed(target_name):
                    # Valid new target
                    if target_name != self.current_target:
                        if self.current_target:
                            self.logger.info(f"Target changed: {self.current_target} -> {target_name}")
                        else:
                            self.logger.info(f"Target acquired: {target_name}")
                        self.current_target = target_name
                        self.combat_stats['targets_acquired'] += 1
                    return True
                else:
                    # Invalid target - need to switch
                    if target_name != self.current_target:
                        self.logger.info(f"Detected forbidden target: {target_name} (skipping)")
                    self.current_target = None
                    return False
            
            return False
    
    def _is_target_allowed(self, target_name: str) -> bool:
        """Check if target is in whitelist"""
        if not self.mob_whitelist:
            return True  # If no whitelist, allow all targets
        
        if not target_name:
            return False
        
        target_lower = target_name.lower().strip()
        
        for allowed in self.mob_whitelist:
            allowed_lower = allowed.lower().strip()
            if allowed_lower in target_lower or target_lower in allowed_lower:
                self.logger.debug(f"Target '{target_name}' matches whitelist entry '{allowed}'")
                return True
        
        self.logger.debug(f"Target '{target_name}' not in whitelist {self.mob_whitelist}")
        return False
    
    def _handle_combat(self, current_time: float) -> None:
            """Handle combat when we have a valid target"""
            try:
                # Double-check we have a target before attacking
                if not self.current_target:
                    self.logger.warning("_handle_combat called but no current_target!")
                    return
                
                # Check if enough time has passed since last attack
                if current_time - self.last_attack_time < self.timing['attack_interval']:
                    return  # Not ready to attack yet
                
                # Get current target health for logging
                game_state = self.skill_manager.game_state
                target_health = game_state.get('target_hp', 0)
                target_exists = game_state.get('target_exists', False)
                
                # Final verification before attack
                if not target_exists:
                    self.logger.info(f"Target {self.current_target} disappeared during combat")
                    return
                
                # ATTACK THE TARGET!
                self.logger.info(f"Attacking {self.current_target} (HP: {target_health}%)")
                
                if self.input_controller.send_key('r'):
                    self.last_attack_time = current_time
                    self.combat_stats['attacks_made'] += 1
                    
                    # Log target health status
                    if target_health > 0:
                        if target_health < 30:
                            self.logger.info(f"{self.current_target} is low health ({target_health}%)")
                        elif target_health < 50:
                            self.logger.debug(f"{self.current_target} at {target_health}% health")
                else:
                    self.logger.warning("Failed to send attack command")
                    
            except Exception as e:
                self.logger.error(f"Attack error: {e}")

    def _turn_and_walk_pattern(self) -> None:
            """Turn to a new direction and walk"""
            
            # Turn left or right
            turn_direction = random.choice(['a', 'd'])
            turn_duration = random.uniform(0.3, 1.2)
            
            self.logger.info(f"Turn and walk: turning {turn_direction} for {turn_duration:.1f}s")
            self.input_controller.hold_key(turn_direction, turn_duration)
            
            # Brief pause
            time.sleep(0.2)
            
            # Walk forward
            walk_duration = random.uniform(2.0, 3.5)
            self.logger.info(f"Turn and walk: walking forward for {walk_duration:.1f}s")
            self.input_controller.hold_key('w', walk_duration)

    def _backward_movement(self) -> None:
        """Move backwards if S key works for that"""
        duration = random.uniform(1.5, 2.5)
        
        self.logger.info(f"Backward movement for {duration:.1f}s")
        self.input_controller.hold_key('s', duration)

    def _zigzag_movement(self) -> None:
        """Create zigzag pattern: turn, walk, turn opposite, walk"""
        import random
        
        # First direction
        first_turn = random.choice(['a', 'd'])
        opposite_turn = 'd' if first_turn == 'a' else 'a'
        
        movements = [
            (first_turn, 0.4),    # Turn first direction
            ('w', 1.5),           # Walk
            (opposite_turn, 0.8), # Turn opposite direction  
            ('w', 1.5),           # Walk
            (first_turn, 0.4),    # Turn back to first direction
            ('w', 1.0),           # Walk
        ]
        
        self.logger.info(f"Zigzag movement: {first_turn} -> {opposite_turn} -> {first_turn}")
        
        for key, duration in movements:
            self.input_controller.hold_key(key, duration)
            time.sleep(0.1)

    def _simple_turn_walk(self) -> None:
        """Simple turn and walk"""
        import random
        
        turn_direction = random.choice(['a', 'd'])
        turn_duration = random.uniform(0.5, 1.0)
        walk_duration = random.uniform(1.5, 3.0)
        
        self.logger.info(f"Simple movement: turn {turn_direction} then walk")
        
        # Turn
        self.input_controller.hold_key(turn_direction, turn_duration)
        time.sleep(0.2)
        
        # Walk
        self.input_controller.hold_key('w', walk_duration)

    def _enhanced_basic_movement(self) -> None:
            """Enhanced movement without movement manager"""
            try:
                # Try multiple movement strategies - turn then walk
                strategies = [
                    # Strategy 1: Turn and walk patterns
                    lambda: self._turn_and_walk_pattern(),
                    # Strategy 2: Backwards movement (if available)
                    lambda: self._backward_movement(),
                    # Strategy 3: Multiple direction changes
                    lambda: self._zigzag_movement(),
                    # Strategy 4: Simple random turn and walk
                    lambda: self._simple_turn_walk()
                ]
                
                import random
                strategy = random.choice(strategies)
                strategy()
                
            except Exception as e:
                self.logger.error(f"Enhanced movement failed: {e}")

    def _fallback_movement(self) -> None:
            """Fallback movement when all else fails"""
            try:
                # Simple fallback: turn around and walk
                self.logger.info("Using fallback movement - turning around")
                
                # Turn around (180 degrees approximately)
                self.input_controller.hold_key('a', 1.5)  # Turn left for ~180°
                time.sleep(0.2)
                
                # Walk forward in new direction
                self.input_controller.hold_key('w', 2.5)
                
            except Exception as e:
                self.logger.error(f"Fallback movement failed: {e}")

    def _execute_smart_movement(self) -> None:
            """Execute intelligent movement when stuck"""
            try:
                self.state = CombatState.MOVING
                self.logger.info("Executing smart anti-stuck movement")
                
                if self.movement_manager:
                    # Use the movement manager for intelligent movement
                    success = self.movement_manager.execute_anti_stuck_movement()
                    if not success:
                        # Fallback to basic movement if movement manager fails
                        self._fallback_movement()
                else:
                    # No movement manager, use enhanced basic movement
                    self._enhanced_basic_movement()
                
                self.state = CombatState.IDLE
                
            except Exception as e:
                self.logger.error(f"Smart movement failed: {e}")
                self.state = CombatState.IDLE
    
    def _handle_no_target(self, current_time: float) -> None:
            """Handle situation when we have no valid target"""
            # Check if we might be stuck (no target for too long)
            if self.stuck_start_time == 0:
                self.stuck_start_time = current_time
            
            time_stuck = current_time - self.stuck_start_time
            
            # If we've been without target for too long, use smart movement
            if time_stuck > self.timing['stuck_detection_time']:
                self.logger.warning(f"No target for {time_stuck:.1f}s - using smart movement")
                self._execute_smart_movement()
                self.stuck_start_time = current_time  # Reset timer
                self.combat_stats['stuck_situations'] += 1
                return
            
            # FIXED LOGIC: Try targeting first, only move if targeting fails consistently
            if (current_time - self.last_target_attempt > 
                self.timing['target_attempt_interval']):
                
                # Attempt to target
                self._attempt_new_target()
                self.last_target_attempt = current_time
                
                # DON'T move immediately - give targeting a chance to work
                return
            
            # Only move if we've been trying to target for a while without success
            # AND enough time has passed since last movement
            if (self.state == CombatState.TARGETING and 
                time_stuck > 3.0 and  # Give targeting 3 seconds to work
                current_time - self.last_movement > self.timing['movement_interval']):
                
                self.logger.info("Targeting attempts failed - moving to find targets")
                self._move_to_find_targets()
                self.last_movement = current_time
    
    def _attempt_new_target(self) -> bool:
            """Attempt to acquire a new target"""
            try:
                self.state = CombatState.TARGETING
                self.combat_stats['targeting_attempts'] += 1
                
                self.logger.debug("Attempting to target nearest mob")
                
                # Press 'E' to target nearest mob
                if self.input_controller.send_key('e'):
                    # Give targeting time to work - DON'T move immediately
                    # The next combat loop will check if we got a target
                    return True
                
                return False
                
            except Exception as e:
                self.logger.error(f"Error attempting to target: {e}")
                return False
    

    def _move_to_find_targets(self) -> None:
            """Move around to find new targets - corrected for turn+walk mechanics"""
            try:
                self.state = CombatState.MOVING
                self.combat_stats['movement_attempts'] += 1
                
                self.logger.info("Moving to find targets")
                
                # Turn to a random direction first
                import random
                turn_direction = random.choice(['a', 'd'])
                turn_duration = random.uniform(0.3, 1.0)
                
                self.logger.debug(f"Turning {turn_direction} for {turn_duration:.1f}s")
                self.input_controller.hold_key(turn_direction, turn_duration)
                
                # Brief pause
                time.sleep(0.2)
                
                # Then walk forward
                self.logger.debug(f"Walking forward for {self.movement_duration:.1f}s")
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
            'movement_attempts': 0,
            'attacks_made': 0
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
    
    def start(self):
        self.is_running = True
        self.last_attack_time = time.time()
        self.current_target = None
        self.state = CombatState.IDLE
        self.logger.info("Combat manager started")

    def stop(self):
        self.is_running = False
        self.current_target = None
        self.state = CombatState.IDLE
        self.logger.info("Combat manager stopped")

    def pause(self):
        self.is_running = False
        self.logger.info("Combat manager paused")

    def resume(self):
        self.is_running = True
        self.logger.info("Combat manager resumed")