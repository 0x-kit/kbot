# skill_system/visual_system.py
"""
Main Visual Skill System

This is the primary interface for the visual skill detection system.
It coordinates between the detector, class manager, and execution engine.
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging

from .skill_types import (
    VisualSkill, SkillState, ClassProfile, VisualRotation,
    SkillBarMapping, DetectionConfig, SkillPosition, DetectionResult
)
from .detector import SkillDetector
from .class_manager import ClassManager


class SystemState(Enum):
    """Visual skill system states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"


class VisualSkillSystem:
    """Main visual skill detection and management system"""
    
    def __init__(self, input_controller=None, logger=None, resources_path: str = None):
        self.logger = logger or logging.getLogger(__name__)
        self.input_controller = input_controller
        
        # Core components
        self.detector = SkillDetector(logger=self.logger)
        self.class_manager = ClassManager(resources_path=resources_path, logger=self.logger)
        
        # System state
        self.state = SystemState.STOPPED
        self.current_class: Optional[str] = None
        self.skill_bar_mapping: Optional[SkillBarMapping] = None
        
        # Monitoring thread
        self._monitoring_thread: Optional[threading.Thread] = None
        self._monitoring_enabled = False
        self._monitoring_interval = 0.1
        
        # Callbacks for events
        self.callbacks: Dict[str, List[Callable]] = {
            'skill_detected': [],
            'skill_state_changed': [],
            'rotation_changed': [],
            'class_changed': [],
            'error_occurred': []
        }
        
        # Performance tracking
        self.stats = {
            'skills_detected': 0,
            'skills_executed': 0,
            'detection_errors': 0,
            'last_scan_time': 0.0,
            'scan_count': 0
        }
        
        # Configuration cache
        self._config_cache: Dict[str, Any] = {}
        
        self.logger.info("VisualSkillSystem initialized")
    
    def initialize_class(self, class_name: str, skill_bar_regions: List[tuple] = None) -> bool:
        """Initialize system for a specific class"""
        try:
            self.logger.info(f"Initializing visual skill system for class: {class_name}")
            
            # Set current class in class manager
            if not self.class_manager.set_current_class(class_name):
                self.logger.error(f"Failed to set class: {class_name}")
                return False
            
            self.current_class = class_name
            profile = self.class_manager.get_current_profile()
            
            if not profile:
                self.logger.error(f"No profile found for class: {class_name}")
                return False
            
            # Load skill templates
            loaded_count = 0
            for skill in profile.skills.values():
                if self.detector.load_skill_template(skill):
                    loaded_count += 1
            
            self.logger.info(f"Loaded {loaded_count}/{len(profile.skills)} skill templates")
            
            # Set up skill bar mapping if regions provided
            if skill_bar_regions:
                self.skill_bar_mapping = SkillBarMapping(
                    bar_region=(0, 0, 0, 0),  # Will be set by auto-detection
                    slot_regions=skill_bar_regions
                )
            
            # Trigger callback
            self._trigger_callback('class_changed', class_name, profile)
            
            self.logger.info(f"Class {profile.display_name} initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize class {class_name}: {e}")
            self._trigger_callback('error_occurred', f"Class initialization failed: {e}")
            return False
    
    def auto_detect_skills(self, skill_bar_region: tuple = None) -> Dict[int, DetectionResult]:
        """Auto-detect skills in the skill bar"""
        try:
            if not self.current_class:
                self.logger.error("No class initialized for auto-detection")
                return {}
            
            profile = self.class_manager.get_current_profile()
            if not profile:
                return {}
            
            # Use provided region or default
            if skill_bar_region:
                # Create slot regions based on skill bar region
                x, y, w, h = skill_bar_region
                slot_width = w // 10  # Assume 10 slots
                slot_regions = []
                
                for i in range(10):
                    slot_x = x + (i * slot_width)
                    slot_regions.append((slot_x, y, slot_width, h))
                
                self.skill_bar_mapping = SkillBarMapping(
                    bar_region=skill_bar_region,
                    slot_regions=slot_regions
                )
            elif not self.skill_bar_mapping:
                self.logger.error("No skill bar mapping available for auto-detection")
                return {}
            
            # Perform skill detection
            skills_to_detect = list(profile.skills.values())
            results = self.detector.scan_skill_bar(
                self.skill_bar_mapping,
                skills_to_detect,
                profile.detection_settings
            )
            
            # Update statistics
            self.stats['skills_detected'] += len(results)
            self.stats['last_scan_time'] = time.time()
            self.stats['scan_count'] += 1
            
            # Trigger callbacks for detected skills
            for slot_index, result in results.items():
                if result.detected_skill:
                    self._trigger_callback('skill_detected', slot_index, result)
            
            self.logger.info(f"Auto-detection completed. Found {len(results)} skills.")
            return results
            
        except Exception as e:
            self.logger.error(f"Auto-detection failed: {e}")
            self._trigger_callback('error_occurred', f"Auto-detection failed: {e}")
            self.stats['detection_errors'] += 1
            return {}
    
    def get_next_skill(self, rotation_name: str = None) -> Optional[VisualSkill]:
        """Get next skill from active rotation considering visual states"""
        try:
            profile = self.class_manager.get_current_profile()
            if not profile:
                return None
            
            # Use specified rotation or active one
            rotation_name = rotation_name or profile.active_rotation
            if not rotation_name or rotation_name not in profile.rotations:
                # Fallback to first available rotation
                if profile.rotations:
                    rotation_name = next(iter(profile.rotations.keys()))
                else:
                    return None
            
            rotation = profile.rotations[rotation_name]
            if not rotation.enabled:
                return None
            
            # Get next skill from rotation
            next_skill_name = rotation.get_next_skill(profile.skills)
            if not next_skill_name:
                return None
            
            skill = profile.skills.get(next_skill_name)
            if skill and skill.is_ready():
                return skill
            
            return None
            
        except Exception as e:
            self.logger.error(f"Failed to get next skill: {e}")
            return None
    
    def execute_skill(self, skill: VisualSkill, verify_execution: bool = True) -> bool:
        """Execute skill with optional visual verification"""
        try:
            if not self.input_controller:
                self.logger.error("No input controller available for skill execution")
                return False
            
            if not skill.is_ready():
                self.logger.debug(f"Skill {skill.name} is not ready")
                return False
            
            # Execute the skill
            self.logger.debug(f"Executing skill: {skill.name} (key: {skill.key})")
            success = self.input_controller.send_key(skill.key)
            
            if success:
                # Mark skill as executed
                skill.execute()
                self.stats['skills_executed'] += 1
                
                # Optional: Verify execution visually
                if verify_execution and skill.position:
                    # Small delay to allow visual change
                    time.sleep(0.1)
                    
                    # Check if skill state changed to cooldown
                    result = self.detector.detect_skill_in_region(
                        skill, skill.position.region, skill.detection_config
                    )
                    
                    if result.state == SkillState.COOLDOWN:
                        self.logger.debug(f"Skill execution verified: {skill.name}")
                    else:
                        self.logger.warning(f"Skill execution not verified: {skill.name}")
                
                self.logger.info(f"Skill executed successfully: {skill.name}")
                return True
            else:
                self.logger.error(f"Failed to send key for skill: {skill.name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Skill execution failed for {skill.name}: {e}")
            self._trigger_callback('error_occurred', f"Skill execution failed: {e}")
            return False
    
    def start_monitoring(self) -> bool:
        """Start background monitoring of skill states"""
        try:
            if self._monitoring_enabled:
                self.logger.warning("Monitoring already running")
                return True
            
            if not self.current_class:
                self.logger.error("No class initialized for monitoring")
                return False
            
            self._monitoring_enabled = True
            self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
            self._monitoring_thread.start()
            
            self.state = SystemState.RUNNING
            self.logger.info("Visual skill monitoring started")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            self.state = SystemState.ERROR
            return False
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self._monitoring_enabled = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=1.0)
        
        self.state = SystemState.STOPPED
        self.logger.info("Visual skill monitoring stopped")
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        self.logger.debug("Monitoring loop started")
        
        while self._monitoring_enabled:
            try:
                if self.current_class:
                    profile = self.class_manager.get_current_profile()
                    if profile:
                        # Monitor skill states
                        states = self.detector.monitor_skill_states(
                            profile.skills, profile.detection_settings
                        )
                        
                        # Trigger callbacks for state changes
                        for skill_name, state in states.items():
                            skill = profile.skills.get(skill_name)
                            if skill and skill.current_state != state:
                                old_state = skill.current_state
                                skill.update_state(state)
                                self._trigger_callback('skill_state_changed', skill, old_state, state)
                
                time.sleep(self._monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Monitoring loop error: {e}")
                self.stats['detection_errors'] += 1
                time.sleep(1.0)  # Longer sleep on error
        
        self.logger.debug("Monitoring loop ended")
    
    def set_active_rotation(self, rotation_name: str) -> bool:
        """Set active rotation for current class"""
        try:
            profile = self.class_manager.get_current_profile()
            if not profile:
                return False
            
            if rotation_name not in profile.rotations:
                self.logger.error(f"Rotation not found: {rotation_name}")
                return False
            
            old_rotation = profile.active_rotation
            profile.active_rotation = rotation_name
            
            # Reset the rotation
            rotation = profile.rotations[rotation_name]
            rotation.reset()
            
            self._trigger_callback('rotation_changed', old_rotation, rotation_name)
            self.logger.info(f"Active rotation set to: {rotation_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set active rotation: {e}")
            return False
    
    def create_skill_bar_mapping(self, bar_region: tuple, slot_count: int = 10) -> SkillBarMapping:
        """Create skill bar mapping with uniform slot distribution"""
        x, y, w, h = bar_region
        slot_width = w // slot_count
        
        slot_regions = []
        for i in range(slot_count):
            slot_x = x + (i * slot_width)
            slot_regions.append((slot_x, y, slot_width, h))
        
        return SkillBarMapping(
            bar_region=bar_region,
            slot_regions=slot_regions
        )
    
    def add_callback(self, event_type: str, callback: Callable):
        """Add event callback"""
        if event_type in self.callbacks:
            self.callbacks[event_type].append(callback)
    
    def remove_callback(self, event_type: str, callback: Callable):
        """Remove event callback"""
        if event_type in self.callbacks and callback in self.callbacks[event_type]:
            self.callbacks[event_type].remove(callback)
    
    def _trigger_callback(self, event_type: str, *args):
        """Trigger callbacks for event"""
        for callback in self.callbacks.get(event_type, []):
            try:
                callback(*args)
            except Exception as e:
                self.logger.error(f"Callback error for {event_type}: {e}")
    
    def get_skill_info(self, skill_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a skill"""
        profile = self.class_manager.get_current_profile()
        if not profile:
            return None
        
        skill = profile.skills.get(skill_name)
        if not skill:
            return None
        
        return {
            'name': skill.name,
            'key': skill.key,
            'type': skill.skill_type.value,
            'state': skill.current_state.value,
            'cooldown_remaining': skill.get_cooldown_remaining(),
            'is_ready': skill.is_ready(),
            'confidence': skill.detection_confidence,
            'last_detection': skill.last_detection_time,
            'position': skill.position.region if skill.position else None,
            'enabled': skill.enabled,
            'priority': skill.priority
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get system performance statistics"""
        base_stats = self.stats.copy()
        
        # Add detector stats
        detector_stats = self.detector.get_performance_stats()
        base_stats.update({
            'detector_stats': detector_stats,
            'class_manager_stats': self.class_manager.get_stats(),
            'current_class': self.current_class,
            'monitoring_enabled': self._monitoring_enabled,
            'system_state': self.state.value
        })
        
        return base_stats
    
    def export_config(self) -> Optional[Dict[str, Any]]:
        """Export current configuration"""
        if not self.current_class:
            return None
        
        profile = self.class_manager.get_current_profile()
        if not profile:
            return None
        
        class_config = self.class_manager.export_class_config(self.current_class)
        if not class_config:
            return None
        
        # Add system-specific settings
        system_config = {
            'version': '3.0',
            'current_class': self.current_class,
            'monitoring_interval': self._monitoring_interval,
            'skill_bar_mapping': None
        }
        
        # Add skill bar mapping if available
        if self.skill_bar_mapping:
            system_config['skill_bar_mapping'] = {
                'bar_region': self.skill_bar_mapping.bar_region,
                'slot_regions': self.skill_bar_mapping.slot_regions
            }
        
        return {
            'system': system_config,
            'class_config': class_config
        }
    
    def import_config(self, config_data: Dict[str, Any]) -> bool:
        """Import configuration"""
        try:
            # Import class configuration
            class_config = config_data.get('class_config')
            if class_config:
                if not self.class_manager.import_class_config(class_config):
                    return False
            
            # Import system configuration
            system_config = config_data.get('system', {})
            current_class = system_config.get('current_class')
            
            if current_class:
                if not self.initialize_class(current_class):
                    return False
            
            # Import skill bar mapping
            mapping_data = system_config.get('skill_bar_mapping')
            if mapping_data:
                self.skill_bar_mapping = SkillBarMapping(
                    bar_region=tuple(mapping_data['bar_region']),
                    slot_regions=[tuple(region) for region in mapping_data['slot_regions']]
                )
            
            # Set monitoring interval
            self._monitoring_interval = system_config.get('monitoring_interval', 0.1)
            
            self.logger.info("Configuration imported successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def optimize_performance(self):
        """Optimize system performance based on current usage"""
        try:
            # Optimize detector settings
            if hasattr(self, '_recent_results'):
                optimized_config = self.detector.optimize_detection_settings(self._recent_results)
                
                # Apply to current profile
                profile = self.class_manager.get_current_profile()
                if profile:
                    profile.detection_settings = optimized_config
                    self.logger.info("Detection settings optimized")
            
            # Adjust monitoring interval based on performance
            avg_detection_time = self.detector.get_performance_stats().get('avg_detection_time_ms', 0)
            if avg_detection_time > 50:  # If detection is slow
                self._monitoring_interval = min(0.5, self._monitoring_interval * 1.2)
                self.logger.info(f"Monitoring interval increased to {self._monitoring_interval:.2f}s")
            
        except Exception as e:
            self.logger.error(f"Performance optimization failed: {e}")
    
    def reset_system(self):
        """Reset system to initial state"""
        try:
            # Stop monitoring
            self.stop_monitoring()
            
            # Clear caches
            self.detector.clear_cache()
            self._config_cache.clear()
            
            # Reset state
            self.current_class = None
            self.skill_bar_mapping = None
            self.state = SystemState.STOPPED
            
            # Reset statistics
            self.stats = {
                'skills_detected': 0,
                'skills_executed': 0,
                'detection_errors': 0,
                'last_scan_time': 0.0,
                'scan_count': 0
            }
            
            self.logger.info("Visual skill system reset")
            
        except Exception as e:
            self.logger.error(f"System reset failed: {e}")
    
    def __del__(self):
        """Cleanup on destruction"""
        try:
            self.stop_monitoring()
        except:
            pass  # Ignore errors during cleanup