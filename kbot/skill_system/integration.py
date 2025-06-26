# skill_system/integration.py
"""
Integration layer between the traditional skill system and the new visual skill system.

This allows seamless switching between systems and provides compatibility
with existing bot components.
"""

from typing import Optional, Dict, Any, List
from utils.logger import BotLogger
from combat.skill_manager import SkillManager, SkillType
from skill_system.visual_system import VisualSkillSystem
from skill_system.skill_types import SkillState, ExecutionMode, QueuePriority


class SkillSystemIntegrator:
    """
    Integration layer that provides a unified interface for both skill systems.
    
    This allows the combat manager to use either system transparently.
    """
    
    def __init__(self, 
                 traditional_skill_manager: SkillManager,
                 visual_skill_system: Optional[VisualSkillSystem] = None,
                 logger: Optional[BotLogger] = None):
        self.traditional_skill_manager = traditional_skill_manager
        self.visual_skill_system = visual_skill_system
        self.logger = logger or BotLogger("SkillIntegrator")
        
        # Configuration
        self.use_visual_system = False
        self.fallback_to_traditional = True
        
        # Check if visual system is ready
        if self.visual_skill_system:
            self.check_visual_system_status()
    
    def check_visual_system_status(self) -> bool:
        """Check if the visual skill system is configured and ready to use"""
        if not self.visual_skill_system:
            return False
        
        try:
            current_class = self.visual_skill_system.class_manager.current_class
            if not current_class:
                return False
                
            profile = self.visual_skill_system.class_manager.get_current_profile()
            if not profile:
                return False
                
            # Check if any skills have positions (been detected)
            positioned_skills = sum(1 for skill in profile.skills.values() if skill.position)
            
            if positioned_skills > 0:
                self.logger.info(f"Visual skill system ready: {positioned_skills} skills configured")
                return True
                
        except Exception as e:
            self.logger.warning(f"Visual skill system check failed: {e}")
            
        return False
    
    def set_use_visual_system(self, enabled: bool):
        """Enable or disable the visual skill system"""
        if enabled and not self.visual_skill_system:
            self.logger.warning("Cannot enable visual system - not available")
            return False
            
        if enabled and not self.check_visual_system_status():
            self.logger.warning("Cannot enable visual system - not configured properly")
            return False
            
        self.use_visual_system = enabled
        self.logger.info(f"Skill system mode: {'Visual' if enabled else 'Traditional'}")
        return True
    
    def execute_skill(self, skill_name: str, skill_type: Optional[SkillType] = None) -> bool:
        """
        Execute a skill using the appropriate system.
        
        Args:
            skill_name: Name of the skill to execute
            skill_type: Type of skill (for traditional system)
            
        Returns:
            True if skill was executed successfully
        """
        # Try visual system first if enabled
        if self.use_visual_system and self.visual_skill_system:
            try:
                # Get current profile
                profile = self.visual_skill_system.class_manager.get_current_profile()
                if profile and skill_name in profile.skills:
                    visual_skill = profile.skills[skill_name]
                    
                    # Check if skill is ready
                    if visual_skill.current_state == SkillState.READY:
                        success = self.visual_skill_system.execution_engine.execute_skill(
                            visual_skill,
                            mode=ExecutionMode.IMMEDIATE,
                            verify=True
                        )
                        
                        if success:
                            self.logger.info(f"Visual system executed skill: {skill_name}")
                            return True
                        else:
                            self.logger.warning(f"Visual system failed to execute: {skill_name}")
                    else:
                        self.logger.debug(f"Visual skill not ready: {skill_name} ({visual_skill.current_state})")
                        
            except Exception as e:
                self.logger.error(f"Visual skill execution error: {e}")
        
        # Fallback to traditional system
        if self.fallback_to_traditional:
            try:
                if skill_type:
                    success = self.traditional_skill_manager.execute_skill(skill_type)
                else:
                    # Try to map skill name to skill type
                    skill_type_mapped = self._map_skill_name_to_type(skill_name)
                    if skill_type_mapped:
                        success = self.traditional_skill_manager.execute_skill(skill_type_mapped)
                    else:
                        self.logger.warning(f"Could not map skill name to type: {skill_name}")
                        return False
                
                if success:
                    self.logger.info(f"Traditional system executed skill: {skill_name}")
                    return True
                    
            except Exception as e:
                self.logger.error(f"Traditional skill execution error: {e}")
        
        return False
    
    def _map_skill_name_to_type(self, skill_name: str) -> Optional[SkillType]:
        """Map skill name to SkillType for traditional system compatibility"""
        # Basic mapping - extend as needed
        skill_mapping = {
            'heal': SkillType.HEAL,
            'mana': SkillType.MANA,
            'attack': SkillType.ATTACK,
            'buff': SkillType.BUFF,
            'debuff': SkillType.DEBUFF,
            # Add more mappings as needed
        }
        
        skill_name_lower = skill_name.lower()
        return skill_mapping.get(skill_name_lower)
    
    def get_skill_status(self, skill_name: str) -> Dict[str, Any]:
        """Get status information for a skill from the active system"""
        status = {
            'available': False,
            'cooldown_remaining': 0,
            'system': 'none'
        }
        
        # Check visual system first if enabled
        if self.use_visual_system and self.visual_skill_system:
            try:
                profile = self.visual_skill_system.class_manager.get_current_profile()
                if profile and skill_name in profile.skills:
                    visual_skill = profile.skills[skill_name]
                    status.update({
                        'available': visual_skill.current_state == SkillState.READY,
                        'cooldown_remaining': visual_skill.get_cooldown_remaining(),
                        'system': 'visual',
                        'state': visual_skill.current_state.value,
                        'position': visual_skill.position
                    })
                    return status
            except Exception as e:
                self.logger.error(f"Error getting visual skill status: {e}")
        
        # Fallback to traditional system
        try:
            skill_type = self._map_skill_name_to_type(skill_name)
            if skill_type:
                is_ready = self.traditional_skill_manager.is_skill_ready(skill_type)
                status.update({
                    'available': is_ready,
                    'system': 'traditional',
                    'skill_type': skill_type.name
                })
        except Exception as e:
            self.logger.error(f"Error getting traditional skill status: {e}")
        
        return status
    
    def get_all_available_skills(self) -> List[str]:
        """Get list of all available skills from the active system"""
        skills = []
        
        if self.use_visual_system and self.visual_skill_system:
            try:
                profile = self.visual_skill_system.class_manager.get_current_profile()
                if profile:
                    # Only include skills that have been positioned
                    skills.extend([
                        name for name, skill in profile.skills.items()
                        if skill.position and skill.current_state == SkillState.READY
                    ])
            except Exception as e:
                self.logger.error(f"Error getting visual skills: {e}")
        
        if self.fallback_to_traditional:
            try:
                # Get available skills from traditional system
                for skill_type in SkillType:
                    if self.traditional_skill_manager.is_skill_ready(skill_type):
                        skills.append(skill_type.name.lower())
            except Exception as e:
                self.logger.error(f"Error getting traditional skills: {e}")
        
        return list(set(skills))  # Remove duplicates
    
    def start_monitoring(self) -> bool:
        """Start skill monitoring for the visual system"""
        if self.visual_skill_system:
            try:
                return self.visual_skill_system.start_monitoring()
            except Exception as e:
                self.logger.error(f"Failed to start visual skill monitoring: {e}")
        return False
    
    def stop_monitoring(self):
        """Stop skill monitoring for the visual system"""
        if self.visual_skill_system:
            try:
                self.visual_skill_system.stop_monitoring()
            except Exception as e:
                self.logger.error(f"Error stopping visual skill monitoring: {e}")
    
    def get_system_info(self) -> Dict[str, Any]:
        """Get information about both skill systems"""
        info = {
            'visual_system': {
                'available': self.visual_skill_system is not None,
                'enabled': self.use_visual_system,
                'configured': False,
                'skills_detected': 0
            },
            'traditional_system': {
                'available': self.traditional_skill_manager is not None,
                'enabled': not self.use_visual_system or self.fallback_to_traditional
            }
        }
        
        if self.visual_skill_system:
            try:
                profile = self.visual_skill_system.class_manager.get_current_profile()
                if profile:
                    positioned_skills = sum(1 for skill in profile.skills.values() if skill.position)
                    info['visual_system'].update({
                        'configured': positioned_skills > 0,
                        'skills_detected': positioned_skills,
                        'current_class': profile.display_name
                    })
            except Exception as e:
                self.logger.error(f"Error getting visual system info: {e}")
        
        return info