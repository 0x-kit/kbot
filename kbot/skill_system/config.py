# skill_system/config.py
"""
Configuration Management for Visual Skill System

Handles loading, saving, and managing configurations for the visual skill system.
Provides backward compatibility with the existing config system.
"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging

from .skill_types import SkillType, DetectionMethod


class VisualSkillConfig:
    """Configuration manager for the visual skill system"""
    
    # Default configuration template
    DEFAULT_CONFIG = {
        "version": "3.0",
        "current_class": "nakayuda",
        "skill_bar_regions": {
            "main_bar": [100, 500, 700, 550],
            "secondary_bar": [100, 550, 700, 600]
        },
        "detection_settings": {
            "template_threshold": 0.85,
            "cooldown_threshold": 0.7,
            "scan_interval": 0.1,
            "use_multi_scale": True,
            "scale_range": [0.8, 1.2],
            "detection_methods": ["template_match", "cooldown_overlay"]
        },
        "execution_settings": {
            "global_cooldown": 0.15,
            "visual_verification": True,
            "auto_retry": True,
            "max_retries": 3,
            "adaptive_timing": True
        },
        "classes": {
            "nakayuda": {
                "display_name": "Nakayuda",
                "skills": {
                    "Basic Attack": {
                        "icon": "ICON_SKILL_AO_TRIPLEORAPUNCH.BMP",
                        "type": "visual",
                        "key": "r",
                        "cooldown_duration": 1.0,
                        "has_visual_cooldown": True,
                        "cast_time": 0,
                        "priority": 1,
                        "range_check": True
                    },
                    "Power Strike": {
                        "icon": "ICON_SKILL_AO_SURIAFIRECRACK.BMP",
                        "type": "visual",
                        "key": "1",
                        "cooldown_duration": 3.0,
                        "has_visual_cooldown": True,
                        "cast_time": 0.5,
                        "priority": 5,
                        "mana_cost": 20
                    },
                    "Shield Buff": {
                        "icon": "ICON_SKILL_AV_ORASHIELD.BMP",
                        "type": "timed",
                        "key": "2",
                        "duration": 300,
                        "has_visual_cooldown": False,
                        "recast_prevention": True,
                        "priority": 8
                    }
                },
                "rotations": {
                    "basic_combo": ["Basic Attack", "Power Strike"],
                    "with_buffs": ["Shield Buff", "Power Strike", "Basic Attack"]
                }
            },
            "abikara": {
                "display_name": "Abikara",
                "skills": {
                    "Fireball": {
                        "icon": "ICON_SKILL_AO_AGNI.BMP",
                        "type": "visual",
                        "key": "1",
                        "cooldown_duration": 2.0,
                        "has_visual_cooldown": True,
                        "cast_time": 1.0,
                        "priority": 3,
                        "mana_cost": 30
                    },
                    "Frost Bolt": {
                        "icon": "ICON_SKILL_AO_HIMA.BMP",
                        "type": "visual",
                        "key": "2",
                        "cooldown_duration": 2.5,
                        "has_visual_cooldown": True,
                        "cast_time": 1.2,
                        "priority": 3,
                        "mana_cost": 35
                    },
                    "Teleport": {
                        "icon": "ICON_SKILL_AO_CHANDRAFORCE.BMP",
                        "type": "instant",
                        "key": "q",
                        "cooldown_duration": 10.0,
                        "has_visual_cooldown": True,
                        "cast_time": 0,
                        "priority": 7,
                        "mana_cost": 50
                    }
                },
                "rotations": {
                    "fire_combo": ["Fireball", "Fireball", "Frost Bolt"],
                    "balanced": ["Fireball", "Frost Bolt"]
                }
            },
            "banar": {
                "display_name": "Banar",
                "skills": {
                    "Heal": {
                        "icon": "ICON_SKILL_AO_NAUTI.BMP",
                        "type": "visual",
                        "key": "1",
                        "cooldown_duration": 3.0,
                        "has_visual_cooldown": True,
                        "cast_time": 2.0,
                        "priority": 9,
                        "mana_cost": 40,
                        "conditions": [{"type": "hp_below", "value": 70}]
                    },
                    "Buff": {
                        "icon": "ICON_SKILL_AV_SAVITRIFORCE.BMP",
                        "type": "timed",
                        "key": "2",
                        "duration": 600,
                        "has_visual_cooldown": False,
                        "recast_prevention": True,
                        "priority": 8,
                        "mana_cost": 60
                    },
                    "Resurrect": {
                        "icon": "ICON_SKILL_AV_MAYAT.BMP",
                        "type": "manual",
                        "key": "r",
                        "cooldown_duration": 30.0,
                        "has_visual_cooldown": False,
                        "cast_time": 3.0,
                        "priority": 10,
                        "mana_cost": 100
                    }
                },
                "rotations": {
                    "support": ["Buff", "Heal"],
                    "emergency": ["Heal", "Resurrect"]
                }
            }
        }
    }
    
    def __init__(self, config_file: str = "visual_skills_config.json", logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.config_file = Path(config_file)
        self.config_data = {}
        
        # Load or create configuration
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                # Validate and migrate if needed
                if self._validate_config(loaded_data):
                    self.config_data = loaded_data
                    self.logger.info(f"Configuration loaded from {self.config_file}")
                    return True
                else:
                    self.logger.warning("Invalid configuration file, creating default")
                    return self._create_default_config()
            else:
                self.logger.info("Configuration file not found, creating default")
                return self._create_default_config()
                
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {e}")
            return self._create_default_config()
    
    def save_config(self) -> bool:
        """Save current configuration to file"""
        try:
            # Create backup if file exists
            if self.config_file.exists():
                backup_file = self.config_file.with_suffix('.json.backup')
                self.config_file.rename(backup_file)
            
            # Save configuration
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {e}")
            return False
    
    def _create_default_config(self) -> bool:
        """Create default configuration"""
        try:
            self.config_data = self.DEFAULT_CONFIG.copy()
            return self.save_config()
        except Exception as e:
            self.logger.error(f"Failed to create default configuration: {e}")
            return False
    
    def _validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate configuration structure"""
        try:
            # Check required top-level keys
            required_keys = ["version", "current_class", "skill_bar_regions", 
                           "detection_settings", "execution_settings", "classes"]
            
            for key in required_keys:
                if key not in config:
                    self.logger.error(f"Missing required config key: {key}")
                    return False
            
            # Validate version
            version = config.get("version", "1.0")
            if version < "3.0":
                self.logger.info(f"Migrating configuration from version {version} to 3.0")
                return self._migrate_config(config)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration validation failed: {e}")
            return False
    
    def _migrate_config(self, old_config: Dict[str, Any]) -> bool:
        """Migrate old configuration to new format"""
        try:
            # Start with default configuration
            new_config = self.DEFAULT_CONFIG.copy()
            
            # Preserve existing settings where possible
            if "current_class" in old_config:
                new_config["current_class"] = old_config["current_class"]
            
            # Migrate skill bar regions
            if "skill_bar_regions" in old_config:
                new_config["skill_bar_regions"].update(old_config["skill_bar_regions"])
            
            # Migrate detection settings
            if "detection_settings" in old_config:
                new_config["detection_settings"].update(old_config["detection_settings"])
            
            # Migrate classes and skills
            if "classes" in old_config:
                for class_name, class_data in old_config["classes"].items():
                    if class_name not in new_config["classes"]:
                        new_config["classes"][class_name] = {
                            "display_name": class_name.title(),
                            "skills": {},
                            "rotations": {}
                        }
                    
                    # Migrate skills
                    if "skills" in class_data:
                        for skill_name, skill_data in class_data["skills"].items():
                            migrated_skill = self._migrate_skill_data(skill_data)
                            new_config["classes"][class_name]["skills"][skill_name] = migrated_skill
                    
                    # Migrate rotations
                    if "rotations" in class_data:
                        new_config["classes"][class_name]["rotations"] = class_data["rotations"]
            
            # Update version
            new_config["version"] = "3.0"
            
            self.config_data = new_config
            self.logger.info("Configuration migrated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration migration failed: {e}")
            return False
    
    def _migrate_skill_data(self, old_skill: Dict[str, Any]) -> Dict[str, Any]:
        """Migrate old skill data to new format"""
        new_skill = {
            "icon": old_skill.get("icon", ""),
            "type": old_skill.get("type", "visual"),
            "key": old_skill.get("key", "1"),
            "cooldown_duration": old_skill.get("cooldown", 2.0),
            "has_visual_cooldown": old_skill.get("has_visual_cooldown", True),
            "cast_time": old_skill.get("cast_time", 0.0),
            "priority": old_skill.get("priority", 3),
            "mana_cost": old_skill.get("mana_cost", 0),
            "conditions": old_skill.get("conditions", [])
        }
        
        # Handle special skill types
        if old_skill.get("type") == "timed":
            new_skill["duration"] = old_skill.get("duration", 300)
            new_skill["recast_prevention"] = old_skill.get("recast_prevention", True)
        
        return new_skill
    
    def get_class_config(self, class_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific class"""
        return self.config_data.get("classes", {}).get(class_name)
    
    def set_class_config(self, class_name: str, class_config: Dict[str, Any]) -> bool:
        """Set configuration for specific class"""
        try:
            if "classes" not in self.config_data:
                self.config_data["classes"] = {}
            
            self.config_data["classes"][class_name] = class_config
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set class config for {class_name}: {e}")
            return False
    
    def get_current_class(self) -> str:
        """Get current active class"""
        return self.config_data.get("current_class", "nakayuda")
    
    def set_current_class(self, class_name: str) -> bool:
        """Set current active class"""
        try:
            if class_name in self.config_data.get("classes", {}):
                self.config_data["current_class"] = class_name
                return True
            else:
                self.logger.error(f"Class not found in configuration: {class_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to set current class: {e}")
            return False
    
    def get_detection_settings(self) -> Dict[str, Any]:
        """Get detection settings"""
        return self.config_data.get("detection_settings", {})
    
    def set_detection_settings(self, settings: Dict[str, Any]) -> bool:
        """Set detection settings"""
        try:
            if "detection_settings" not in self.config_data:
                self.config_data["detection_settings"] = {}
            
            self.config_data["detection_settings"].update(settings)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set detection settings: {e}")
            return False
    
    def get_execution_settings(self) -> Dict[str, Any]:
        """Get execution settings"""
        return self.config_data.get("execution_settings", {})
    
    def set_execution_settings(self, settings: Dict[str, Any]) -> bool:
        """Set execution settings"""
        try:
            if "execution_settings" not in self.config_data:
                self.config_data["execution_settings"] = {}
            
            self.config_data["execution_settings"].update(settings)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set execution settings: {e}")
            return False
    
    def get_skill_bar_regions(self) -> Dict[str, List[int]]:
        """Get skill bar regions"""
        return self.config_data.get("skill_bar_regions", {})
    
    def set_skill_bar_regions(self, regions: Dict[str, List[int]]) -> bool:
        """Set skill bar regions"""
        try:
            self.config_data["skill_bar_regions"] = regions
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to set skill bar regions: {e}")
            return False
    
    def add_skill(self, class_name: str, skill_name: str, skill_data: Dict[str, Any]) -> bool:
        """Add skill to class configuration"""
        try:
            if class_name not in self.config_data.get("classes", {}):
                # Create class if it doesn't exist
                self.config_data.setdefault("classes", {})[class_name] = {
                    "display_name": class_name.title(),
                    "skills": {},
                    "rotations": {}
                }
            
            self.config_data["classes"][class_name]["skills"][skill_name] = skill_data
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add skill {skill_name} to {class_name}: {e}")
            return False
    
    def remove_skill(self, class_name: str, skill_name: str) -> bool:
        """Remove skill from class configuration"""
        try:
            class_config = self.config_data.get("classes", {}).get(class_name, {})
            if skill_name in class_config.get("skills", {}):
                del class_config["skills"][skill_name]
                
                # Remove from rotations that contain this skill
                for rotation_name, rotation_skills in class_config.get("rotations", {}).items():
                    if skill_name in rotation_skills:
                        rotation_skills.remove(skill_name)
                
                return True
            else:
                self.logger.warning(f"Skill {skill_name} not found in {class_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove skill {skill_name} from {class_name}: {e}")
            return False
    
    def add_rotation(self, class_name: str, rotation_name: str, skill_list: List[str]) -> bool:
        """Add rotation to class configuration"""
        try:
            if class_name not in self.config_data.get("classes", {}):
                return False
            
            class_config = self.config_data["classes"][class_name]
            if "rotations" not in class_config:
                class_config["rotations"] = {}
            
            class_config["rotations"][rotation_name] = skill_list
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add rotation {rotation_name} to {class_name}: {e}")
            return False
    
    def remove_rotation(self, class_name: str, rotation_name: str) -> bool:
        """Remove rotation from class configuration"""
        try:
            class_config = self.config_data.get("classes", {}).get(class_name, {})
            if rotation_name in class_config.get("rotations", {}):
                del class_config["rotations"][rotation_name]
                return True
            else:
                self.logger.warning(f"Rotation {rotation_name} not found in {class_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove rotation {rotation_name} from {class_name}: {e}")
            return False
    
    def get_available_classes(self) -> List[Tuple[str, str]]:
        """Get list of available classes as (class_name, display_name) tuples"""
        classes = []
        for class_name, class_data in self.config_data.get("classes", {}).items():
            display_name = class_data.get("display_name", class_name.title())
            classes.append((class_name, display_name))
        return classes
    
    def export_config(self, filename: str = None) -> str:
        """Export configuration to JSON string or file"""
        try:
            json_string = json.dumps(self.config_data, indent=2, ensure_ascii=False)
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(json_string)
                self.logger.info(f"Configuration exported to {filename}")
            
            return json_string
            
        except Exception as e:
            self.logger.error(f"Failed to export configuration: {e}")
            return ""
    
    def import_config(self, config_source: str) -> bool:
        """Import configuration from JSON string or file"""
        try:
            # Determine if it's a file path or JSON string
            if config_source.strip().startswith('{'):
                # JSON string
                imported_data = json.loads(config_source)
            else:
                # File path
                with open(config_source, 'r', encoding='utf-8') as f:
                    imported_data = json.load(f)
            
            # Validate imported configuration
            if self._validate_config(imported_data):
                self.config_data = imported_data
                self.logger.info("Configuration imported successfully")
                return True
            else:
                self.logger.error("Imported configuration is invalid")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to import configuration: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset configuration to defaults"""
        try:
            self.config_data = self.DEFAULT_CONFIG.copy()
            self.logger.info("Configuration reset to defaults")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to reset configuration: {e}")
            return False
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "version": self.config_data.get("version", "unknown"),
            "current_class": self.config_data.get("current_class", "none"),
            "total_classes": len(self.config_data.get("classes", {})),
            "classes": {
                name: {
                    "skills_count": len(data.get("skills", {})),
                    "rotations_count": len(data.get("rotations", {}))
                }
                for name, data in self.config_data.get("classes", {}).items()
            }
        }