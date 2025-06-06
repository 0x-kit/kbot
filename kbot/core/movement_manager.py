# core/movement_manager.py
import time
import random
from typing import Tuple, List, Optional
from core.input_controller import InputController
from core.window_manager import WindowManager
from utils.logger import BotLogger

class MovementManager:
    """Handles intelligent movement and pathfinding"""
    
    def __init__(self, input_controller: InputController, window_manager: WindowManager, logger: BotLogger):
        self.input_controller = input_controller
        self.window_manager = window_manager
        self.logger = logger
        
        # Movement patterns
        self.movement_patterns = [
            "random_walk",
            "circle_movement", 
            "click_movement",
            "directional_keys"
        ]
        
        # Movement state
        self.last_movement_time = 0
        self.current_pattern = "random_walk"
        self.stuck_detection_time = 0
        self.last_position_check = 0
        
        # Configuration
        self.movement_config = {
            'max_stuck_time': 5.0,  # Seconds before considering stuck
            'movement_interval': 3.0,  # Time between movements
            'click_radius': 100,  # Pixels around center for click movement
            'directional_duration': 2.0  # Seconds for directional movement
        }
    
    def execute_movement_strategy(self, strategy: str = None) -> bool:
        """Execute a specific movement strategy"""
        if strategy is None:
            strategy = self.current_pattern
        
        try:
            current_time = time.time()
            
            # Prevent too frequent movements
            if current_time - self.last_movement_time < 1.0:
                return False
            
            success = False
            
            if strategy == "click_movement":
                success = self._click_movement()
            elif strategy == "random_walk":
                success = self._random_walk()
            elif strategy == "circle_movement":
                success = self._circle_movement()
            elif strategy == "directional_keys":
                success = self._directional_keys()
            else:
                success = self._random_walk()  # Fallback
            
            if success:
                self.last_movement_time = current_time
                self.logger.info(f"Executed movement strategy: {strategy}")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Movement strategy failed: {e}")
            return False
    
    def _click_movement(self) -> bool:
        """Move by clicking on random positions around the character"""
        try:
            if not self.window_manager.target_window:
                return False
            
            # Get window center
            window_rect = self.window_manager.target_window.rect
            center_x = (window_rect[0] + window_rect[2]) // 2
            center_y = (window_rect[1] + window_rect[3]) // 2
            
            # Generate random click position around center
            radius = self.movement_config['click_radius']
            angle = random.uniform(0, 2 * 3.14159)  # Random angle
            distance = random.uniform(30, radius)  # Random distance
            
            click_x = center_x + int(distance * random.uniform(-1, 1))
            click_y = center_y + int(distance * random.uniform(-1, 1))
            
            # Ensure click is within window bounds
            click_x = max(window_rect[0] + 50, min(window_rect[2] - 50, click_x))
            click_y = max(window_rect[1] + 50, min(window_rect[3] - 50, click_y))
            
            # Click to move
            success = self.input_controller.click_at(click_x, click_y, 'left')
            
            if success:
                self.logger.debug(f"Click movement to ({click_x}, {click_y})")
                # Wait a bit for movement to start
                time.sleep(0.5)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Click movement failed: {e}")
            return False
    
    def _random_walk(self) -> bool:
        """Random directional movement - turn then walk"""
        try:
            # First turn to a random direction
            turn_direction = random.choice(['a', 'd'])  # Only turn left or right
            turn_duration = random.uniform(0.3, 1.0)  # Short turn
            
            self.logger.debug(f"Random walk: turning {turn_direction} for {turn_duration:.1f}s")
            self.input_controller.hold_key(turn_direction, turn_duration)
            
            # Small pause between turn and walk
            time.sleep(0.2)
            
            # Then walk forward
            walk_duration = random.uniform(1.5, 3.0)
            self.logger.debug(f"Random walk: walking forward for {walk_duration:.1f}s")
            return self.input_controller.hold_key('w', walk_duration)
            
        except Exception as e:
            self.logger.error(f"Random walk failed: {e}")
            return False
    
    def _circle_movement(self) -> bool:
        """Move in a circular pattern - turn and walk repeatedly"""
        try:
            # Sequence: turn right, walk, turn right, walk (creates circle)
            movements = [
                ('d', 0.4, 'turn'),    # Turn right
                ('w', 1.0, 'walk'),    # Walk forward
                ('d', 0.4, 'turn'),    # Turn right again
                ('w', 1.0, 'walk'),    # Walk forward
                ('d', 0.4, 'turn'),    # Turn right again
                ('w', 1.0, 'walk'),    # Walk forward
            ]
            
            for key, duration, action_type in movements:
                self.logger.debug(f"Circle movement: {action_type} {key} for {duration:.1f}s")
                if not self.input_controller.hold_key(key, duration):
                    return False
                time.sleep(0.1)  # Small pause between movements
            
            self.logger.debug("Executed circle movement")
            return True
            
        except Exception as e:
            self.logger.error(f"Circle movement failed: {e}")
            return False
    
    def _directional_keys(self) -> bool:
        """Try different directional combinations - turn then walk"""
        try:
            # Different turn patterns followed by walking
            patterns = [
                [('a', 0.5), ('w', 2.0)],  # Turn left, walk
                [('d', 0.5), ('w', 2.0)],  # Turn right, walk
                [('a', 1.0), ('w', 1.5)],  # Turn left more, walk
                [('d', 1.0), ('w', 1.5)],  # Turn right more, walk
                [('a', 0.3), ('w', 1.0), ('d', 0.3), ('w', 1.0)],  # Turn left, walk, turn right, walk
                [('d', 0.3), ('w', 1.0), ('a', 0.3), ('w', 1.0)],  # Turn right, walk, turn left, walk
                [('s', 1.5)],  # Just walk backwards (if S works for backward)
            ]
            
            pattern = random.choice(patterns)
            
            for key, duration in pattern:
                action = "walking" if key == 'w' else ("backing" if key == 's' else f"turning {key}")
                self.logger.debug(f"Directional movement: {action} for {duration:.1f}s")
                
                if not self.input_controller.hold_key(key, duration):
                    return False
                time.sleep(0.1)  # Small pause between actions
                
            return True
            
        except Exception as e:
            self.logger.error(f"Directional movement failed: {e}")
            return False
    
    def smart_approach_target(self, target_position: Optional[Tuple[int, int]] = None) -> bool:
        """Intelligently move towards target or unstuck"""
        try:
            # If we have target position, click near it
            if target_position:
                return self._click_near_target(target_position)
            
            # Otherwise, try to get unstuck
            return self.execute_anti_stuck_movement()
            
        except Exception as e:
            self.logger.error(f"Smart approach failed: {e}")
            return False
    
    def _click_near_target(self, target_pos: Tuple[int, int]) -> bool:
        """Click near target position to move closer"""
        try:
            target_x, target_y = target_pos
            
            # Click slightly offset from target to avoid clicking on target itself
            offset_x = random.randint(-30, 30)
            offset_y = random.randint(-30, 30)
            
            click_x = target_x + offset_x
            click_y = target_y + offset_y
            
            # Ensure click is within window bounds
            if self.window_manager.target_window:
                window_rect = self.window_manager.target_window.rect
                click_x = max(window_rect[0], min(window_rect[2], click_x))
                click_y = max(window_rect[1], min(window_rect[3], click_y))
            
            success = self.input_controller.click_at(click_x, click_y, 'left')
            
            if success:
                self.logger.debug(f"Clicked near target at ({click_x}, {click_y})")
                time.sleep(0.5)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Click near target failed: {e}")
            return False
    
    def execute_anti_stuck_movement(self) -> bool:
        """Execute movement specifically designed to get unstuck"""
        try:
            self.logger.info("Executing anti-stuck movement")
            
            # Try multiple strategies in sequence
            strategies = [
                "click_movement",   # Try clicking first (most reliable)
                "directional_keys", # Try key combinations
                "random_walk",      # Random movement
                "circle_movement"   # Circular pattern
            ]
            
            for strategy in strategies:
                if self.execute_movement_strategy(strategy):
                    time.sleep(1.0)  # Wait to see if we got unstuck
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Anti-stuck movement failed: {e}")
            return False
    
    def detect_stuck_situation(self) -> bool:
        """Detect if the character might be stuck"""
        # This is a simplified version - you could enhance with position tracking
        current_time = time.time()
        
        # If we haven't moved in a while, consider it stuck
        if current_time - self.last_movement_time > self.movement_config['max_stuck_time']:
            return True
        
        return False
    
    def set_movement_config(self, config: dict) -> None:
        """Update movement configuration"""
        self.movement_config.update(config)
        self.logger.info(f"Movement config updated: {config}")
    
    def get_movement_stats(self) -> dict:
        """Get movement statistics"""
        return {
            'last_movement_time': self.last_movement_time,
            'current_pattern': self.current_pattern,
            'time_since_last_movement': time.time() - self.last_movement_time
        }