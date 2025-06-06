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
    """Enhanced combat manager with full skills integration"""
    
    def __init__(self, pixel_analyzer: PixelAnalyzer, skill_manager: SkillManager, 
                    input_controller: InputController, logger: BotLogger, movement_manager=None):
            self.pixel_analyzer = pixel_analyzer
            self.skill_manager = skill_manager
            self.input_controller = input_controller
            self.logger = logger
            self.movement_manager = movement_manager

            self.is_running = False
            
            # Combat state
            self.state = CombatState.IDLE
            self.current_target = None
            self.last_target_attempt = 0
            self.last_movement = 0
            self.last_attack_time = 0
            self.last_skill_time = 0  # NEW: Track skill usage
            self.stuck_start_time = 0
            
            # Configuration
            self.mob_whitelist: List[str] = []
            self.potion_threshold = 70
            self.max_targeting_attempts = 10
            self.movement_duration = 3.0
            
            # Skills configuration
            self.use_skills = True  # NEW: Enable/disable skill usage
            self.use_basic_attack_fallback = True  # NEW: Use basic attack if no skills available
            self.skill_priority_mode = "rotation"  # NEW: "rotation" or "priority"
            
            # Combat timing
            self.timing = {
                'target_attempt_interval': 1.0,
                'movement_interval': 5.0,
                'attack_interval': 1.5,
                'skill_interval': 0.8,  # NEW: Minimum time between skills
                'stuck_detection_time': 10.0
            }
            
            # Statistics
            self.combat_stats = {
                'targets_acquired': 0,
                'targets_lost': 0,
                'targeting_attempts': 0,
                'movement_attempts': 0,
                'attacks_made': 0,
                'skills_used': 0,  # NEW: Track skill usage
                'skill_failures': 0,  # NEW: Track skill failures
                'stuck_situations': 0
            }
    
    def set_skill_usage(self, enabled: bool) -> None:
        """Enable or disable skill usage"""
        self.use_skills = enabled
        self.logger.info(f"Skill usage {'enabled' if enabled else 'disabled'}")
    
    def set_skill_priority_mode(self, mode: str) -> None:
        """Set skill priority mode: 'rotation' or 'priority'"""
        if mode in ['rotation', 'priority']:
            self.skill_priority_mode = mode
            self.logger.info(f"Skill priority mode set to: {mode}")
    
    def set_mob_whitelist(self, whitelist: List[str]) -> None:
        """Set the mob whitelist"""
        self.mob_whitelist = [mob.strip() for mob in whitelist if mob.strip()]
        self.logger.info(f"Mob whitelist updated: {self.mob_whitelist}")
    
    def set_potion_threshold(self, threshold: int) -> None:
        """Set potion usage threshold"""
        self.potion_threshold = max(1, min(100, threshold))
        self.logger.info(f"Potion threshold set to {self.potion_threshold}%")
    
    def process_combat(self) -> None:
            """Main combat processing method with skills integration"""
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
                    self.logger.debug(f"Mid-combat with {self.current_target} ({target_health}% HP) - continuing combat")
                    self._handle_combat_with_skills(current_time)  # ENHANCED: Use skills in combat
                    return
                
                # Only evaluate targets if we're not currently fighting or target is dead/lost
                valid_target = self._evaluate_target(target_exists, target_name)
                
                if valid_target:
                    # We have a valid target to attack
                    self.state = CombatState.FIGHTING
                    self._handle_combat_with_skills(current_time)  # ENHANCED: Use skills in combat
                else:
                    # No valid target - try to find one
                    self.state = CombatState.TARGETING
                    self._handle_no_target(current_time)
                    
            except Exception as e:
                self.logger.error(f"Error in combat loop: {e}")

    def _handle_combat_with_skills(self, current_time: float) -> None:
        """Enhanced combat handler that uses skills intelligently"""
        try:
            # Double-check we have a target before attacking
            if not self.current_target:
                self.logger.warning("_handle_combat_with_skills called but no current_target!")
                return
            
            # Get current target health for logging
            game_state = self.skill_manager.game_state
            target_health = game_state.get('target_hp', 0)
            target_exists = game_state.get('target_exists', False)
            
            # Final verification before attack
            if not target_exists:
                self.logger.info(f"Target {self.current_target} disappeared during combat")
                return
            
            # ENHANCED COMBAT LOGIC: Try to use skills first, then fallback to basic attack
            skill_used = False
            
            if self.use_skills:
                skill_used = self._try_use_skill(current_time, target_health)
            
            # If no skill was used and enough time has passed, use basic attack
            if not skill_used and (current_time - self.last_attack_time >= self.timing['attack_interval']):
                self._use_basic_attack(current_time, target_health)
                
        except Exception as e:
            self.logger.error(f"Combat error: {e}")

    def _try_use_skill(self, current_time: float, target_health: int) -> bool:
        """FIXED: Try to use the next appropriate skill with correct step logging"""
        try:
            # Check if enough time has passed since last skill
            if current_time - self.last_skill_time < self.timing['skill_interval']:
                return False
            
            # Get next skill to use based on priority mode
            next_skill = None
            
            if self.skill_priority_mode == "rotation":
                if self.skill_manager.active_rotation:
                    # Get rotation status BEFORE getting next skill
                    rotation = self.skill_manager.rotations[self.skill_manager.active_rotation]
                    current_step = rotation.current_index  # This is the step BEFORE advancement
                    total_steps = len(rotation.skills)
                    
                    next_skill = self.skill_manager.get_next_skill()
                    
                    if next_skill:
                        self.logger.debug(f"Rotation: Step {current_step}/{total_steps} -> Skill '{next_skill}'")
                else:
                    next_skill = self.skill_manager._get_priority_skill()
            else:
                next_skill = self.skill_manager._get_priority_skill()
            
            if next_skill:
                # Check if the skill can actually be used
                if self.skill_manager.can_use_skill(next_skill):
                    # Use the skill
                    if self.skill_manager.use_skill(next_skill):
                        self.last_skill_time = current_time
                        self.combat_stats['skills_used'] += 1
                        
                        # ENHANCED LOGGING: Show correct rotation context
                        rotation_context = ""
                        if (self.skill_manager.active_rotation and 
                            self.skill_priority_mode == "rotation"):
                            
                            rotation = self.skill_manager.rotations[self.skill_manager.active_rotation]
                            # Current step is now AFTER advancement
                            current_step_after = rotation.current_index
                            total_steps = len(rotation.skills)
                            
                            # Calculate what step we just executed (before advancement)
                            executed_step = (current_step_after - 1) % total_steps
                            
                            rotation_context = f" [Rotation: {self.skill_manager.active_rotation}, Step: {executed_step + 1}/{total_steps}]"
                        
                        self.logger.info(f"Used skill '{next_skill}' on {self.current_target} (HP: {target_health}%){rotation_context}")
                        
                        return True
                    else:
                        self.combat_stats['skill_failures'] += 1
                        self.logger.warning(f"Failed to execute skill '{next_skill}'")
                else:
                    skill_info = self.skill_manager.get_skill_info(next_skill)
                    cooldown_remaining = skill_info['cooldown_remaining']
                    
                    if cooldown_remaining > 0:
                        self.logger.debug(f"Skill '{next_skill}' on cooldown: {cooldown_remaining:.1f}s remaining")
                    else:
                        self.logger.debug(f"Skill '{next_skill}' conditions not met")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error trying to use skill: {e}")
            return False
    
    def _use_basic_attack(self, current_time: float, target_health: int) -> bool:
        """Use basic attack as fallback"""
        try:
            if not self.use_basic_attack_fallback:
                return False
            
            # Use basic attack
            if self.input_controller.send_key('r'):
                self.last_attack_time = current_time
                self.combat_stats['attacks_made'] += 1
                
                # Log basic attack
                self.logger.info(f"Basic attack on {self.current_target} (HP: {target_health}%)")
                
                # Health status logging
                if target_health > 0:
                    if target_health < 30:
                        self.logger.info(f"{self.current_target} is low health ({target_health}%)")
                    elif target_health < 50:
                        self.logger.debug(f"{self.current_target} at {target_health}% health")
                
                return True
            else:
                self.logger.warning("Failed to send basic attack command")
                return False
                
        except Exception as e:
            self.logger.error(f"Basic attack error: {e}")
            return False
    
    def _use_emergency_skills(self, current_time: float) -> bool:
        """Use emergency skills (potions, defensive skills) when needed"""
        try:
            emergency_used = False
            
            # Get current vitals
            game_state = self.skill_manager.game_state
            hp = game_state.get('hp', 100)
            mp = game_state.get('mp', 100)
            
            # Check for emergency potion usage
            if hp < self.potion_threshold:
                if self.skill_manager.can_use_skill('HP Potion'):
                    if self.skill_manager.use_skill('HP Potion', force=True):
                        self.logger.info(f"EMERGENCY: Used HP potion (HP: {hp}%)")
                        emergency_used = True
            
            if mp < self.potion_threshold:
                if self.skill_manager.can_use_skill('MP Potion'):
                    if self.skill_manager.use_skill('MP Potion', force=True):
                        self.logger.info(f"EMERGENCY: Used MP potion (MP: {mp}%)")
                        emergency_used = True
            
            # Try to use any defensive skills if health is very low
            if hp < 30:
                for skill_name, skill in self.skill_manager.skills.items():
                    if (skill.skill_type.value in ['defensive', 'buff'] and 
                        skill.enabled and 
                        self.skill_manager.can_use_skill(skill_name)):
                        
                        if self.skill_manager.use_skill(skill_name, force=True):
                            self.logger.info(f"EMERGENCY: Used defensive skill '{skill_name}' (HP: {hp}%)")
                            emergency_used = True
                            break
            
            return emergency_used
            
        except Exception as e:
            self.logger.error(f"Error using emergency skills: {e}")
            return False
    
    def _evaluate_target(self, target_exists: bool, target_name: str) -> bool:
        """Evaluate if we have a valid target to attack"""
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
        
        # We have a target with a name
        if target_name:
            self.logger.debug(f"Target detected with name: '{target_name}'")
            
            # CRITICAL CHECK: If we already have a target and it's valid, DON'T SWITCH
            if self.current_target and self._is_target_allowed(self.current_target):
                if target_name == self.current_target:
                    # Same target - all good, keep attacking
                    self.logger.debug(f"Same target confirmed: {target_name}")
                    return True
                else:
                    # DIFFERENT target detected
                    self.logger.warning(f"Different target detected: current='{self.current_target}' detected='{target_name}'")
                    
                    # Check if the current target is still valid
                    if self._is_target_allowed(self.current_target):
                        self.logger.info(f"KEEPING current target '{self.current_target}' - ignoring '{target_name}'")
                        return True
                    else:
                        self.logger.info(f"Current target '{self.current_target}' no longer valid, switching to '{target_name}'")
            
            # No current target OR current target is invalid
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
    
    def _turn_and_walk_pattern(self) -> None:
        """Turn to a new direction and walk"""
        turn_direction = random.choice(['a', 'd'])
        turn_duration = random.uniform(0.3, 1.2)
        
        self.logger.info(f"Turn and walk: turning {turn_direction} for {turn_duration:.1f}s")
        self.input_controller.hold_key(turn_direction, turn_duration)
        
        time.sleep(0.2)
        
        walk_duration = random.uniform(2.0, 3.5)
        self.logger.info(f"Turn and walk: walking forward for {walk_duration:.1f}s")
        self.input_controller.hold_key('w', walk_duration)

    def _backward_movement(self) -> None:
        """Move backwards if S key works for that"""
        duration = random.uniform(1.5, 2.5)
        self.logger.info(f"Backward movement for {duration:.1f}s")
        self.input_controller.hold_key('s', duration)

    def _zigzag_movement(self) -> None:
        """Create zigzag pattern"""
        first_turn = random.choice(['a', 'd'])
        opposite_turn = 'd' if first_turn == 'a' else 'a'
        
        movements = [
            (first_turn, 0.4),
            ('w', 1.5),
            (opposite_turn, 0.8),
            ('w', 1.5),
            (first_turn, 0.4),
            ('w', 1.0),
        ]
        
        self.logger.info(f"Zigzag movement: {first_turn} -> {opposite_turn} -> {first_turn}")
        
        for key, duration in movements:
            self.input_controller.hold_key(key, duration)
            time.sleep(0.1)

    def _simple_turn_walk(self) -> None:
        """Simple turn and walk"""
        turn_direction = random.choice(['a', 'd'])
        turn_duration = random.uniform(0.5, 1.0)
        walk_duration = random.uniform(1.5, 3.0)
        
        self.logger.info(f"Simple movement: turn {turn_direction} then walk")
        
        self.input_controller.hold_key(turn_direction, turn_duration)
        time.sleep(0.2)
        self.input_controller.hold_key('w', walk_duration)

    def _spiral_movement(self) -> None:
        """NEW: Spiral movement pattern for better area coverage"""
        try:
            self.logger.info("Executing spiral movement pattern")
            
            # Create expanding spiral: short turn + walk, longer turn + walk, etc.
            movements = [
                ('d', 0.3, 'w', 1.0),  # Short turn, short walk
                ('d', 0.5, 'w', 1.5),  # Medium turn, medium walk  
                ('d', 0.7, 'w', 2.0),  # Longer turn, longer walk
                ('d', 0.9, 'w', 2.5),  # Full turn, long walk
            ]
            
            for turn_key, turn_duration, walk_key, walk_duration in movements:
                self.input_controller.hold_key(turn_key, turn_duration)
                time.sleep(0.1)
                self.input_controller.hold_key(walk_key, walk_duration)
                time.sleep(0.2)
                
        except Exception as e:
            self.logger.error(f"Spiral movement failed: {e}")

    def _exploration_movement(self) -> None:
        """NEW: Exploration movement - longer distance in new directions"""
        try:
            import random
            
            self.logger.info("Executing exploration movement")
            
            # Big directional change + long walk to explore new areas
            turn_direction = random.choice(['a', 'd'])
            turn_duration = random.uniform(1.5, 3.0)  # Bigger turn
            walk_duration = random.uniform(4.0, 6.0)  # Longer walk
            
            self.logger.debug(f"Exploration: {turn_direction} turn {turn_duration:.1f}s, walk {walk_duration:.1f}s")
            
            self.input_controller.hold_key(turn_direction, turn_duration)
            time.sleep(0.3)
            self.input_controller.hold_key('w', walk_duration)
            
        except Exception as e:
            self.logger.error(f"Exploration movement failed: {e}")

    # ADD method to configure movement behavior
    def configure_movement_behavior(self, aggressive_search: bool = True) -> None:
        """Configure how aggressive the movement behavior should be"""
        if aggressive_search:
            # More aggressive settings
            self.timing['movement_interval'] = 3.0      # Move every 3 seconds
            self.timing['stuck_detection_time'] = 10.0  # Consider stuck after 10 seconds
            self.logger.info("Configured for aggressive movement (faster searching)")
        else:
            # Conservative settings  
            self.timing['movement_interval'] = 8.0      # Move every 8 seconds
            self.timing['stuck_detection_time'] = 20.0  # Consider stuck after 20 seconds
            self.logger.info("Configured for conservative movement (slower searching)")

    # ADD method to check movement effectiveness
    def get_movement_stats(self) -> Dict[str, Any]:
        """Get movement-related statistics"""
        current_time = time.time()
        
        return {
            'movement_attempts': self.combat_stats['movement_attempts'],
            'stuck_situations': self.combat_stats['stuck_situations'],
            'time_since_last_movement': current_time - self.last_movement,
            'movement_interval': self.timing['movement_interval'],
            'stuck_detection_time': self.timing['stuck_detection_time'],
            'has_movement_manager': self.movement_manager is not None,
            'current_state': self.state.value
        }

    def _enhanced_basic_movement(self) -> None:
        """IMPROVED: Enhanced movement without movement manager"""
        try:
            # More varied movement strategies
            strategies = [
                self._turn_and_walk_pattern,
                self._backward_movement,
                self._zigzag_movement,
                self._spiral_movement,     # NEW
                self._exploration_movement # NEW
            ]
            
            import random
            strategy = random.choice(strategies)
            
            self.logger.debug(f"Executing enhanced movement strategy: {strategy.__name__}")
            strategy()
            
        except Exception as e:
            self.logger.error(f"Enhanced movement failed: {e}")

    def _fallback_movement(self) -> None:
        """Fallback movement when all else fails"""
        try:
            self.logger.info("Using fallback movement - turning around")
            self.input_controller.hold_key('a', 1.5)
            time.sleep(0.2)
            self.input_controller.hold_key('w', 2.5)
        except Exception as e:
            self.logger.error(f"Fallback movement failed: {e}")

    def _execute_smart_movement(self) -> None:
        """FIXED: Execute intelligent movement when stuck"""
        try:
            self.state = CombatState.MOVING
            self.logger.info("Executing smart anti-stuck movement")
            
            movement_success = False
            
            # PRIORITY 1: Use movement manager if available
            if self.movement_manager:
                self.logger.debug("Using movement manager for anti-stuck movement")
                movement_success = self.movement_manager.execute_anti_stuck_movement()
                
                if movement_success:
                    self.logger.info("Movement manager executed anti-stuck movement successfully")
                else:
                    self.logger.warning("Movement manager failed, trying fallback movement")
            else:
                self.logger.debug("No movement manager available, using basic movement")
            
            # FALLBACK: Use basic movement if movement manager failed or unavailable
            if not movement_success:
                self.logger.debug("Executing enhanced basic movement")
                self._enhanced_basic_movement()
            
            self.state = CombatState.IDLE
            
        except Exception as e:
            self.logger.error(f"Smart movement failed: {e}")
            self.state = CombatState.IDLE
    
    def _handle_no_target(self, current_time: float) -> None:
        """FIXED: Handle situation when we have no valid target with better movement"""
        # Check if we might be stuck (no target for too long)
        if self.stuck_start_time == 0:
            self.stuck_start_time = current_time
            self.logger.debug("Started stuck timer - no target found")
        
        time_stuck = current_time - self.stuck_start_time
        
        # ENHANCED: More aggressive movement when no targets
        if time_stuck > self.timing['stuck_detection_time']:
            self.logger.warning(f"No target for {time_stuck:.1f}s - executing anti-stuck movement")
            self._execute_smart_movement()
            self.stuck_start_time = current_time  # Reset timer
            self.combat_stats['stuck_situations'] += 1
            return
        
        # Try targeting at regular intervals
        if (current_time - self.last_target_attempt > 
            self.timing['target_attempt_interval']):
            
            self.logger.debug("Attempting to find new target...")
            self._attempt_new_target()
            self.last_target_attempt = current_time
            return
        
        # IMPROVED: Move more frequently when no targets are found
        time_since_last_movement = current_time - self.last_movement
        
        # Move if we've been without target for a reasonable time
        if (self.state == CombatState.TARGETING and 
            time_stuck > 2.0 and  # Start moving after just 2 seconds without target
            time_since_last_movement > self.timing['movement_interval']):
            
            self.logger.info(f"No targets found for {time_stuck:.1f}s - moving to search for mobs")
            self._move_to_find_targets()
            self.last_movement = current_time
    
    def _attempt_new_target(self) -> bool:
        """Attempt to acquire a new target"""
        try:
            self.state = CombatState.TARGETING
            self.combat_stats['targeting_attempts'] += 1
            
            self.logger.debug("Attempting to target nearest mob")
            
            if self.input_controller.send_key('e'):
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error attempting to target: {e}")
            return False
        
    def _basic_search_movement(self) -> None:
        """Basic movement pattern for searching targets"""
        try:
            import random
            
            # Choose movement pattern
            patterns = ["turn_and_walk", "random_direction", "circle_pattern"]
            pattern = random.choice(patterns)
            
            self.logger.debug(f"Executing basic search pattern: {pattern}")
            
            if pattern == "turn_and_walk":
                # Turn in a random direction and walk
                turn_direction = random.choice(['a', 'd'])
                turn_duration = random.uniform(0.5, 1.5)
                walk_duration = random.uniform(2.0, 4.0)
                
                self.logger.debug(f"Turn {turn_direction} for {turn_duration:.1f}s, then walk {walk_duration:.1f}s")
                
                self.input_controller.hold_key(turn_direction, turn_duration)
                time.sleep(0.2)
                self.input_controller.hold_key('w', walk_duration)
                
            elif pattern == "random_direction":
                # Just turn and walk in a completely new direction
                turn_duration = random.uniform(1.0, 2.0)
                walk_duration = random.uniform(2.5, 4.0)
                
                self.logger.debug(f"Random turn for {turn_duration:.1f}s, then walk {walk_duration:.1f}s")
                
                self.input_controller.hold_key('d', turn_duration)  # Turn right
                time.sleep(0.2)
                self.input_controller.hold_key('w', walk_duration)
                
            elif pattern == "circle_pattern":
                # Move in a partial circle to cover more area
                self.logger.debug("Executing circle search pattern")
                
                # Multiple short movements in an arc
                for i in range(3):
                    self.input_controller.hold_key('d', 0.4)  # Turn right
                    time.sleep(0.1)
                    self.input_controller.hold_key('w', 1.5)  # Walk forward
                    time.sleep(0.2)
            
        except Exception as e:
            self.logger.error(f"Basic search movement failed: {e}")
    
    def _move_to_find_targets(self) -> None:
        """FIXED: Move around to find new targets with better logic"""
        try:
            self.state = CombatState.MOVING
            self.combat_stats['movement_attempts'] += 1
            
            self.logger.info("Searching for targets - executing movement pattern")
            
            movement_success = False
            
            # PRIORITY 1: Use movement manager if available
            if self.movement_manager:
                self.logger.debug("Using movement manager to search for targets")
                
                # Try different movement strategies
                strategies = ["random_walk", "click_movement", "circle_movement"]
                
                for strategy in strategies:
                    if self.movement_manager.execute_movement_strategy(strategy):
                        self.logger.info(f"Executed {strategy} movement to find targets")
                        movement_success = True
                        break
                    else:
                        self.logger.debug(f"Movement strategy {strategy} failed, trying next")
            
            # FALLBACK: Use basic movement if movement manager failed
            if not movement_success:
                self.logger.debug("Movement manager unavailable or failed, using basic movement")
                self._basic_search_movement()
            
            self.state = CombatState.IDLE
            
        except Exception as e:
            self.logger.error(f"Error during target search movement: {e}")
            self.state = CombatState.IDLE
    
    def get_combat_state(self) -> str:
        """Get current combat state"""
        return self.state.value
    
    def get_current_target(self) -> Optional[str]:
        """Get current target name"""
        return self.current_target
    
    def get_combat_stats(self) -> Dict[str, Any]:
        """Get enhanced combat statistics"""
        stats = self.combat_stats.copy()
        
        # Add skill usage statistics
        if self.skill_manager:
            skill_stats = {}
            for skill_name, usage in self.skill_manager.usage_stats.items():
                skill_stats[skill_name] = {
                    'total_uses': usage.total_uses,
                    'success_rate': usage.success_rate,
                    'last_used': usage.last_used
                }
            stats['skill_details'] = skill_stats
        
        return stats
    
    def reset_combat_stats(self) -> None:
        """Reset combat statistics"""
        self.combat_stats = {
            'targets_acquired': 0,
            'targets_lost': 0,
            'targeting_attempts': 0,
            'movement_attempts': 0,
            'attacks_made': 0,
            'skills_used': 0,
            'skill_failures': 0,
            'stuck_situations': 0
        }
        
        # Also reset skill manager stats
        if self.skill_manager:
            self.skill_manager.reset_usage_stats()
    
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
        self.last_skill_time = time.time()  # NEW: Initialize skill timer
        self.current_target = None
        self.state = CombatState.IDLE
        self.logger.info("Enhanced combat manager started with skills integration")

    def stop(self):
        self.is_running = False
        self.current_target = None
        self.state = CombatState.IDLE
        self.logger.info("Enhanced combat manager stopped")

    def pause(self):
        self.is_running = False
        self.logger.info("Enhanced combat manager paused")

    def resume(self):
        self.is_running = True
        self.logger.info("Enhanced combat manager resumed")
    
    def get_skill_usage_summary(self) -> Dict[str, Any]:
        """Get a summary of skill usage"""
        if not self.skill_manager:
            return {}
        
        summary = {
            'total_skills_registered': len(self.skill_manager.skills),
            'enabled_skills': len([s for s in self.skill_manager.skills.values() if s.enabled]),
            'active_rotation': self.skill_manager.active_rotation,
            'total_skill_uses': sum(usage.total_uses for usage in self.skill_manager.usage_stats.values()),
            'skill_success_rate': 0,
            'most_used_skill': None,
            'skills_on_cooldown': []
        }
        
        # Calculate overall success rate
        total_uses = summary['total_skill_uses']
        total_successes = sum(usage.successful_uses for usage in self.skill_manager.usage_stats.values())
        if total_uses > 0:
            summary['skill_success_rate'] = (total_successes / total_uses) * 100
        
        # Find most used skill
        if self.skill_manager.usage_stats:
            most_used = max(self.skill_manager.usage_stats.items(), 
                          key=lambda x: x[1].total_uses, default=(None, None))
            if most_used[0]:
                summary['most_used_skill'] = {
                    'name': most_used[0],
                    'uses': most_used[1].total_uses
                }
        
        # Find skills on cooldown
        current_time = time.time()
        for skill_name, skill in self.skill_manager.skills.items():
            if skill.enabled:
                usage = self.skill_manager.usage_stats.get(skill_name)
                if usage and current_time - usage.last_used < skill.cooldown:
                    remaining = skill.cooldown - (current_time - usage.last_used)
                    summary['skills_on_cooldown'].append({
                        'name': skill_name,
                        'remaining': remaining
                    })
        
        return summary