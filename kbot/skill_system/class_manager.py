# skill_system/class_manager.py
"""
Class and Resource Management System

Handles loading and managing skill resources, class profiles, and character configurations.
Provides automatic resource discovery and profile management.
"""

import os
import json
import glob
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import logging

from .skill_types import (
    VisualSkill, SkillType, ClassProfile, VisualRotation,
    SkillBarMapping, DetectionConfig, SkillPosition
)


class ClassManager:
    """Manages character classes, skills, and resources"""
    
    # Class mapping based on existing resource structure
    CLASS_MAPPING = {
        "nakayuda": {"display_name": "Nakayuda", "type": "warrior"},
        "abikara": {"display_name": "Abikara", "type": "mage"}, 
        "banar": {"display_name": "Banar", "type": "priest"},
        "druka": {"display_name": "Druka", "type": "rogue"},
        "karya": {"display_name": "Karya", "type": "archer"},
        "samabat": {"display_name": "Samabat", "type": "summoner"},
        "satya": {"display_name": "Satya", "type": "priest"},
        "vidya": {"display_name": "Vidya", "type": "monk"}
    }
    
    def __init__(self, resources_path: str = None, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        
        # Set resources path
        if resources_path is None:
            current_dir = Path(__file__).parent
            self.resources_path = current_dir.parent / "resources" / "skills"
        else:
            self.resources_path = Path(resources_path)
            
        # Storage
        self.class_profiles: Dict[str, ClassProfile] = {}
        self.current_class: Optional[str] = None
        
        # Resource cache
        self._resource_cache: Dict[str, List[str]] = {}
        self._skill_cache: Dict[str, Dict[str, Any]] = {}
        
        # Auto-discovery settings
        self.auto_discovery_enabled = True
        self.icon_extensions = ['.bmp', '.png', '.jpg', '.jpeg']
        
        self.logger.info(f"ClassManager initialized with resources path: {self.resources_path}")
        
        # Load existing classes
        self._discover_classes()
    
    def _discover_classes(self):
        """Auto-discover available classes from resources directory"""
        try:
            if not self.resources_path.exists():
                self.logger.warning(f"Resources path does not exist: {self.resources_path}")
                return
            
            for class_dir in self.resources_path.iterdir():
                if class_dir.is_dir() and class_dir.name in self.CLASS_MAPPING:
                    self._load_class_profile(class_dir.name)
            
            self.logger.info(f"Discovered {len(self.class_profiles)} classes")
            
        except Exception as e:
            self.logger.error(f"Class discovery failed: {e}")
    
    def _load_class_profile(self, class_name: str) -> Optional[ClassProfile]:
        """Load or create class profile"""
        try:
            if class_name in self.class_profiles:
                return self.class_profiles[class_name]
            
            # Get class info
            class_info = self.CLASS_MAPPING.get(class_name, {})
            display_name = class_info.get("display_name", class_name.title())
            
            # Create resource path
            resource_path = str(self.resources_path / class_name)
            
            # Create profile
            profile = ClassProfile(
                class_name=class_name,
                display_name=display_name,
                resource_path=resource_path,
                detection_settings=DetectionConfig()
            )
            
            # Auto-discover skills for this class
            self._discover_skills_for_class(profile)
            
            # Create default rotations
            self._create_default_rotations(profile)
            
            self.class_profiles[class_name] = profile
            self.logger.info(f"Loaded class profile: {display_name} ({len(profile.skills)} skills)")
            
            return profile
            
        except Exception as e:
            self.logger.error(f"Failed to load class profile {class_name}: {e}")
            return None
    
    def _discover_skills_for_class(self, profile: ClassProfile):
        """Auto-discover skills from class resource directory"""
        try:
            resource_dir = Path(profile.resource_path)
            if not resource_dir.exists():
                self.logger.warning(f"Resource directory not found: {resource_dir}")
                return
            
            # Find all skill icon files
            skill_files = []
            for ext in self.icon_extensions:
                pattern = f"*{ext}"
                skill_files.extend(resource_dir.glob(pattern))
            
            self.logger.debug(f"Found {len(skill_files)} potential skill icons for {profile.class_name}")
            
            # Create skills from icons
            for skill_file in skill_files:
                skill_name = self._parse_skill_name(skill_file.name)
                if skill_name:
                    skill = self._create_skill_from_icon(skill_name, str(skill_file), profile)
                    if skill:
                        profile.skills[skill_name] = skill
            
            self.logger.info(f"Created {len(profile.skills)} skills for {profile.display_name}")
            
        except Exception as e:
            self.logger.error(f"Skill discovery failed for {profile.class_name}: {e}")
    
    def _parse_skill_name(self, filename: str) -> Optional[str]:
        """Parse skill name from icon filename"""
        try:
            # Remove extension
            name = os.path.splitext(filename)[0]
            
            # Skip if not a skill icon
            if not name.upper().startswith('ICON_SKILL'):
                return None
            
            # Remove common prefixes
            prefixes_to_remove = [
                'ICON_SKILL_', 'ICON_SKILL_AO_', 'ICON_SKILL_AV_',
                'ICON_SKILL_P_', 'Icon_skill_', 'Icon_skill_ao_',
                'Icon_skill_av_'
            ]
            
            for prefix in prefixes_to_remove:
                if name.upper().startswith(prefix.upper()):
                    name = name[len(prefix):]
                    break
            
            # Clean up the name
            name = name.replace('_', ' ').title()
            
            # Handle special cases
            name_mappings = {
                '100lv 01': 'Level 100 Skill',
                '100lv 02': 'Level 100 Skill 2',
                '100lv 03': 'Level 100 Skill 3',
                # Add more mappings as needed
            }
            
            return name_mappings.get(name, name)
            
        except Exception as e:
            self.logger.error(f"Failed to parse skill name from {filename}: {e}")
            return None
    
    def _create_skill_from_icon(self, skill_name: str, icon_path: str, 
                              profile: ClassProfile) -> Optional[VisualSkill]:
        """Create VisualSkill from icon file"""
        try:
            # Determine skill type based on name patterns
            skill_type = self._determine_skill_type(skill_name, icon_path)
            
            # Generate default hotkey
            hotkey = self._generate_default_hotkey(skill_name, profile)
            
            # Create skill
            skill = VisualSkill(
                name=skill_name,
                key=hotkey,
                skill_type=skill_type,
                icon_path=icon_path,
                cooldown_duration=self._estimate_cooldown(skill_name, skill_type),
                priority=self._estimate_priority(skill_name, skill_type),
                enabled=True,
                description=f"Auto-discovered skill: {skill_name}",
                detection_config=profile.detection_settings
            )
            
            return skill
            
        except Exception as e:
            self.logger.error(f"Failed to create skill {skill_name}: {e}")
            return None
    
    def _determine_skill_type(self, skill_name: str, icon_path: str) -> SkillType:
        """Determine skill type from name and path"""
        name_lower = skill_name.lower()
        path_lower = icon_path.lower()
        
        # Buff skills (AV_ prefix typically indicates buffs)
        if 'av_' in path_lower or any(word in name_lower for word in ['buff', 'shield', 'mantra', 'force']):
            return SkillType.TIMED
        
        # Level skills are usually powerful attacks
        if 'level' in name_lower or '100lv' in path_lower:
            return SkillType.VISUAL
        
        # Default to visual for most skills
        return SkillType.VISUAL
    
    def _generate_default_hotkey(self, skill_name: str, profile: ClassProfile) -> str:
        """Generate default hotkey for skill"""
        # Get already assigned keys
        assigned_keys = {skill.key.lower() for skill in profile.skills.values()}
        
        # Common key preferences
        preferred_keys = ['1', '2', '3', '4', '5', '6', '7', '8', 'q', 'w', 'e', 't', 'y']
        
        # Find first available key
        for key in preferred_keys:
            if key not in assigned_keys:
                return key
        
        # Fallback to letters
        for i in range(26):
            key = chr(ord('a') + i)
            if key not in assigned_keys:
                return key
        
        return 'x'  # Ultimate fallback
    
    def _estimate_cooldown(self, skill_name: str, skill_type: SkillType) -> float:
        """Estimate skill cooldown based on type and name"""
        name_lower = skill_name.lower()
        
        # Buff skills typically have longer cooldowns
        if skill_type == SkillType.TIMED:
            if 'mantra' in name_lower or 'shield' in name_lower:
                return 30.0
            return 15.0
        
        # Level skills are powerful with longer cooldowns
        if 'level' in name_lower:
            return 10.0
        
        # Regular skills
        return 2.0
    
    def _estimate_priority(self, skill_name: str, skill_type: SkillType) -> int:
        """Estimate skill priority"""
        name_lower = skill_name.lower()
        
        # High priority for buffs
        if skill_type == SkillType.TIMED:
            return 8
        
        # High priority for powerful skills
        if 'level' in name_lower or 'ultimate' in name_lower:
            return 7
        
        # Medium priority for most combat skills
        return 3
    
    def _create_default_rotations(self, profile: ClassProfile):
        """Create default rotations for the class"""
        if not profile.skills:
            return
        
        # Get offensive skills
        offensive_skills = [
            name for name, skill in profile.skills.items()
            if skill.skill_type == SkillType.VISUAL and skill.priority < 6
        ]
        
        if offensive_skills:
            # Create basic rotation
            basic_rotation = VisualRotation(
                name="Basic Combo",
                skill_names=offensive_skills[:4],  # Limit to first 4 skills
                repeat=True,
                adaptive=True
            )
            profile.rotations["Basic Combo"] = basic_rotation
        
        # Get buff skills
        buff_skills = [
            name for name, skill in profile.skills.items()
            if skill.skill_type == SkillType.TIMED
        ]
        
        if buff_skills:
            # Create buff rotation
            buff_rotation = VisualRotation(
                name="Buffs",
                skill_names=buff_skills,
                repeat=False,
                adaptive=True
            )
            profile.rotations["Buffs"] = buff_rotation
    
    def get_class_profile(self, class_name: str) -> Optional[ClassProfile]:
        """Get class profile by name"""
        return self.class_profiles.get(class_name)
    
    def get_available_classes(self) -> List[Tuple[str, str]]:
        """Get list of available classes as (class_name, display_name) tuples"""
        return [
            (name, profile.display_name)
            for name, profile in self.class_profiles.items()
        ]
    
    def set_current_class(self, class_name: str) -> bool:
        """Set current active class"""
        if class_name not in self.class_profiles:
            self.logger.error(f"Class not found: {class_name}")
            return False
        
        self.current_class = class_name
        self.logger.info(f"Set current class to: {self.class_profiles[class_name].display_name}")
        return True
    
    def get_current_profile(self) -> Optional[ClassProfile]:
        """Get current class profile"""
        if self.current_class:
            return self.class_profiles.get(self.current_class)
        return None
    
    def create_custom_skill(self, class_name: str, skill_data: Dict[str, Any]) -> bool:
        """Create custom skill for a class"""
        try:
            profile = self.get_class_profile(class_name)
            if not profile:
                return False
            
            skill = VisualSkill(
                name=skill_data['name'],
                key=skill_data['key'],
                skill_type=SkillType(skill_data.get('type', 'visual')),
                icon_path=skill_data.get('icon_path'),
                cooldown_duration=skill_data.get('cooldown', 2.0),
                priority=skill_data.get('priority', 3),
                mana_cost=skill_data.get('mana_cost', 0),
                enabled=skill_data.get('enabled', True),
                description=skill_data.get('description', ''),
                detection_config=profile.detection_settings
            )
            
            profile.skills[skill.name] = skill
            self.logger.info(f"Created custom skill {skill.name} for {profile.display_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create custom skill: {e}")
            return False
    
    def create_custom_rotation(self, class_name: str, rotation_data: Dict[str, Any]) -> bool:
        """Create custom rotation for a class"""
        try:
            profile = self.get_class_profile(class_name)
            if not profile:
                return False
            
            # Validate skill names
            skill_names = rotation_data['skills']
            for skill_name in skill_names:
                if skill_name not in profile.skills:
                    self.logger.error(f"Skill not found: {skill_name}")
                    return False
            
            rotation = VisualRotation(
                name=rotation_data['name'],
                skill_names=skill_names,
                repeat=rotation_data.get('repeat', True),
                adaptive=rotation_data.get('adaptive', True)
            )
            
            profile.rotations[rotation.name] = rotation
            self.logger.info(f"Created custom rotation {rotation.name} for {profile.display_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create custom rotation: {e}")
            return False
    
    def export_class_config(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Export class configuration to dictionary"""
        try:
            profile = self.get_class_profile(class_name)
            if not profile:
                return None
            
            # Export skills
            skills_data = {}
            for name, skill in profile.skills.items():
                skills_data[name] = {
                    'name': skill.name,
                    'key': skill.key,
                    'type': skill.skill_type.value,
                    'icon_path': skill.icon_path,
                    'cooldown': skill.cooldown_duration,
                    'cast_time': skill.cast_time,
                    'mana_cost': skill.mana_cost,
                    'priority': skill.priority,
                    'enabled': skill.enabled,
                    'description': skill.description,
                    'has_visual_cooldown': skill.has_visual_cooldown,
                    'conditions': skill.conditions,
                    'buff_duration': skill.buff_duration,
                    'recast_prevention': skill.recast_prevention
                }
            
            # Export rotations
            rotations_data = {}
            for name, rotation in profile.rotations.items():
                rotations_data[name] = {
                    'name': rotation.name,
                    'skills': rotation.skill_names,
                    'repeat': rotation.repeat,
                    'adaptive': rotation.adaptive,
                    'enabled': rotation.enabled
                }
            
            return {
                'version': '3.0',
                'class_name': profile.class_name,
                'display_name': profile.display_name,
                'resource_path': profile.resource_path,
                'active_rotation': profile.active_rotation,
                'detection_settings': {
                    'template_threshold': profile.detection_settings.template_threshold,
                    'cooldown_threshold': profile.detection_settings.cooldown_threshold,
                    'scan_interval': profile.detection_settings.scan_interval,
                    'use_multi_scale': profile.detection_settings.use_multi_scale
                },
                'skills': skills_data,
                'rotations': rotations_data
            }
            
        except Exception as e:
            self.logger.error(f"Failed to export class config for {class_name}: {e}")
            return None
    
    def import_class_config(self, config_data: Dict[str, Any]) -> bool:
        """Import class configuration from dictionary"""
        try:
            class_name = config_data['class_name']
            
            # Create or get profile
            if class_name in self.class_profiles:
                profile = self.class_profiles[class_name]
            else:
                profile = ClassProfile(
                    class_name=class_name,
                    display_name=config_data.get('display_name', class_name.title()),
                    resource_path=config_data.get('resource_path', '')
                )
                self.class_profiles[class_name] = profile
            
            # Import detection settings
            if 'detection_settings' in config_data:
                ds = config_data['detection_settings']
                profile.detection_settings = DetectionConfig(
                    template_threshold=ds.get('template_threshold', 0.85),
                    cooldown_threshold=ds.get('cooldown_threshold', 0.7),
                    scan_interval=ds.get('scan_interval', 0.1),
                    use_multi_scale=ds.get('use_multi_scale', True)
                )
            
            # Import skills
            profile.skills.clear()
            for skill_name, skill_data in config_data.get('skills', {}).items():
                skill = VisualSkill(
                    name=skill_data['name'],
                    key=skill_data['key'],
                    skill_type=SkillType(skill_data['type']),
                    icon_path=skill_data.get('icon_path'),
                    cooldown_duration=skill_data.get('cooldown', 2.0),
                    cast_time=skill_data.get('cast_time', 0.0),
                    mana_cost=skill_data.get('mana_cost', 0),
                    priority=skill_data.get('priority', 3),
                    enabled=skill_data.get('enabled', True),
                    description=skill_data.get('description', ''),
                    has_visual_cooldown=skill_data.get('has_visual_cooldown', True),
                    conditions=skill_data.get('conditions', []),
                    buff_duration=skill_data.get('buff_duration', 0.0),
                    recast_prevention=skill_data.get('recast_prevention', False),
                    detection_config=profile.detection_settings
                )
                profile.skills[skill_name] = skill
            
            # Import rotations
            profile.rotations.clear()
            for rotation_name, rotation_data in config_data.get('rotations', {}).items():
                rotation = VisualRotation(
                    name=rotation_data['name'],
                    skill_names=rotation_data['skills'],
                    repeat=rotation_data.get('repeat', True),
                    adaptive=rotation_data.get('adaptive', True),
                    enabled=rotation_data.get('enabled', True)
                )
                profile.rotations[rotation_name] = rotation
            
            # Set active rotation
            profile.active_rotation = config_data.get('active_rotation')
            
            self.logger.info(f"Imported configuration for {profile.display_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to import class config: {e}")
            return False
    
    def reload_class_resources(self, class_name: str) -> bool:
        """Reload resources for a specific class"""
        try:
            if class_name in self.class_profiles:
                del self.class_profiles[class_name]
            
            profile = self._load_class_profile(class_name)
            return profile is not None
            
        except Exception as e:
            self.logger.error(f"Failed to reload resources for {class_name}: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get class manager statistics"""
        stats = {
            'total_classes': len(self.class_profiles),
            'current_class': self.current_class,
            'classes': {}
        }
        
        for name, profile in self.class_profiles.items():
            stats['classes'][name] = {
                'display_name': profile.display_name,
                'skills_count': len(profile.skills),
                'rotations_count': len(profile.rotations),
                'active_rotation': profile.active_rotation
            }
        
        return stats