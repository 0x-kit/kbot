# config/config_manager.py
import configparser
import ast
import os
from typing import Dict, Any, Tuple, List
from utils.exceptions import ConfigError

class ConfigManager:
    """Manages all bot configuration settings"""
    
    def __init__(self, config_file: str = "bot_config.ini"):
        self.config_file = config_file
        self.config = configparser.ConfigParser()
        self._defaults = self._get_default_config()
        self.load_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Define default configuration values"""
        return {
            'whitelist': {
                'mobs': 'Byokbo'
            },
            'options': {
                'auto_pots': True,
                'potion_threshold': 70
            },
            'regions': {
                'hp': (4, 20, 168, 36),
                'mp': (4, 36, 168, 51),
                'target': (4, 66, 168, 75),
                'target_name': (4, 55, 168, 70)
            },
            'timing': {
                'combat_check': 1.0,
                'attack': 1.5,
                'target_switch': 0.7,
                'potion': 0.5,
                'post_combat_delay': 1.0
            },
            'skills': {
                'rotations': [],
                'priorities': {},
                'cooldowns': {},
                'conditions': {}
            }
        }
    
    def load_config(self) -> None:
        """Load configuration from file or create with defaults"""
        try:
            if os.path.exists(self.config_file):
                self.config.read(self.config_file)
                self._validate_config()
            else:
                self._create_default_config()
        except Exception as e:
            raise ConfigError(f"Failed to load configuration: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as configfile:
                self.config.write(configfile)
            print(f"ConfigManager: Saved config to {self.config_file}")  # Debug
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")
    
    
    def get_whitelist(self) -> List[str]:
        """Get mob whitelist"""
        if (self.config.has_section('Whitelist') and 
            self.config.has_option('Whitelist', 'mobs')):
            mobs = self.config['Whitelist']['mobs'].split(',')
            return [mob.strip() for mob in mobs if mob.strip()]
        return [self._defaults['whitelist']['mobs']]
    
    def set_whitelist(self, mobs: List[str]) -> None:
        """Set mob whitelist"""
        if not self.config.has_section('Whitelist'):
            self.config.add_section('Whitelist')
        
        self.config['Whitelist']['mobs'] = ','.join(mobs)
    
    def get_option(self, option: str, default: Any = None) -> Any:
        """Get a specific option value"""
        if (self.config.has_section('Options') and 
            self.config.has_option('Options', option)):
            value = self.config['Options'][option]
            
            # Handle boolean values
            if isinstance(default, bool) or value.lower() in ('true', 'false'):
                return value.lower() == 'true'
            
            # Handle numeric values
            if isinstance(default, (int, float)):
                return type(default)(value)
            
            return value
        
        return default if default is not None else self._defaults['options'].get(option)
    
    def set_option(self, option: str, value: Any) -> None:
        """Set a specific option value"""
        if not self.config.has_section('Options'):
            self.config.add_section('Options')
        
        self.config['Options'][option] = str(value)
    
    def get_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get region coordinates"""
        regions = {}
        
        # Default regions
        default_regions = {
            'hp': (4, 20, 168, 36),
            'mp': (4, 36, 168, 51),
            'target': (4, 66, 168, 75),
            'target_name': (4, 55, 168, 70)
        }
        
        if self.config.has_section('Regions'):
            for region in ['hp', 'mp', 'target', 'target_name']:
                if self.config.has_option('Regions', region):
                    try:
                        coords = ast.literal_eval(self.config['Regions'][region])
                        if isinstance(coords, tuple) and len(coords) == 4:
                            regions[region] = coords
                            continue
                    except (ValueError, SyntaxError) as e:
                        print(f"Error parsing region {region}: {e}")
                
                # Use default if parsing failed or option doesn't exist
                regions[region] = default_regions[region]
        else:
            # No Regions section, use all defaults
            regions = default_regions.copy()
        
        print(f"ConfigManager: Got regions {regions}")  # Debug
        return regions

    
    def set_regions(self, regions: Dict[str, Tuple[int, int, int, int]]) -> None:
        """Set region coordinates"""
        if not self.config.has_section('Regions'):
            self.config.add_section('Regions')
        
        for region, coords in regions.items():
            self.config['Regions'][region] = str(coords)
        
        print(f"ConfigManager: Set regions to {regions}")  # Debug
    
    def get_timing(self) -> Dict[str, float]:
        """Get timing intervals"""
        timing = {}
        
        if self.config.has_section('Timing'):
            for key in ['combat_check', 'attack', 'target_switch', 'potion', 'post_combat_delay']:
                timing[key] = self.config.getfloat('Timing', key, 
                                                 fallback=self._defaults['timing'][key])
        else:
            timing = self._defaults['timing'].copy()
        
        return timing
    
    def set_timing(self, timing: Dict[str, float]) -> None:
        """Set timing intervals"""
        if not self.config.has_section('Timing'):
            self.config.add_section('Timing')
        
        for key, value in timing.items():
            self.config['Timing'][key] = str(value)
    

    def get_skills(self) -> Dict[str, Any]:
        """FIXED: Get skill configurations with better parsing"""
        skills = {
            'rotations': {},
            'priorities': {},
            'cooldowns': {},
            'conditions': {},
            'skills': {},
            'active_rotation': None,
            'global_cooldown': 0.5
        }
        
        if self.config.has_section('Skills'):
            print("DEBUG: Skills section found in config")
            
            # Load skills data with better error handling
            if self.config.has_option('Skills', 'skills'):
                try:
                    skills_str = self.config['Skills']['skills']
                    print(f"DEBUG: Raw skills string: {skills_str[:200]}...")  # Show first 200 chars
                    
                    skills_data = ast.literal_eval(skills_str)
                    if isinstance(skills_data, dict):
                        skills['skills'] = skills_data
                        print(f"DEBUG: Parsed {len(skills_data)} skills from config")
                        
                        # Debug: Show which skills were loaded
                        for skill_name, skill_data in skills_data.items():
                            enabled = skill_data.get('enabled', False)
                            key = skill_data.get('key', '')
                            print(f"DEBUG: Skill {skill_name}: enabled={enabled}, key={key}")
                    else:
                        print("DEBUG: Skills data is not a dict")
                except (ValueError, SyntaxError) as e:
                    print(f"DEBUG: Error parsing skills: {e}")
            else:
                print("DEBUG: No 'skills' option found in Skills section")
            
            # Load rotations with better error handling
            if self.config.has_option('Skills', 'rotations'):
                try:
                    rotations_str = self.config['Skills']['rotations']
                    print(f"DEBUG: Raw rotations string: {rotations_str[:200]}...")
                    
                    rotations_data = ast.literal_eval(rotations_str)
                    if isinstance(rotations_data, dict):
                        skills['rotations'] = rotations_data
                        print(f"DEBUG: Parsed {len(rotations_data)} rotations from config")
                        
                        # Debug: Show which rotations were loaded
                        for rot_name, rot_data in rotations_data.items():
                            rot_skills = rot_data.get('skills', [])
                            print(f"DEBUG: Rotation {rot_name}: skills={rot_skills}")
                    else:
                        print("DEBUG: Rotations data is not a dict")
                except (ValueError, SyntaxError) as e:
                    print(f"DEBUG: Error parsing rotations: {e}")
            else:
                print("DEBUG: No 'rotations' option found in Skills section")
            
            # Load active rotation
            if self.config.has_option('Skills', 'active_rotation'):
                active_rot = self.config['Skills']['active_rotation']
                if active_rot and active_rot != 'None':
                    skills['active_rotation'] = active_rot
                    print(f"DEBUG: Active rotation: {active_rot}")
                else:
                    print("DEBUG: No active rotation set")
            
            # Load global cooldown
            if self.config.has_option('Skills', 'global_cooldown'):
                try:
                    skills['global_cooldown'] = float(self.config['Skills']['global_cooldown'])
                except ValueError:
                    pass
        else:
            print("DEBUG: No Skills section found in config")
        
        print(f"DEBUG: Final skills config: {len(skills['skills'])} skills, {len(skills['rotations'])} rotations")
        return skills
    
    def set_skills(self, skills: Dict[str, Any]) -> None:
        """Set skill configurations"""
        if not self.config.has_section('Skills'):
            self.config.add_section('Skills')
        
        # Save each component
        self.config['Skills']['skills'] = str(skills.get('skills', {}))
        self.config['Skills']['rotations'] = str(skills.get('rotations', {}))
        self.config['Skills']['active_rotation'] = str(skills.get('active_rotation', None))
        self.config['Skills']['global_cooldown'] = str(skills.get('global_cooldown', 0.5))
        
        print(f"ConfigManager: Saved skills config with {len(skills.get('skills', {}))} skills and {len(skills.get('rotations', {}))} rotations")
    
    def _validate_config(self) -> None:
        """Validate loaded configuration"""
        # Validate regions
        regions = self.get_regions()
        for region, coords in regions.items():
            if not all(isinstance(c, int) and c >= 0 for c in coords):
                raise ConfigError(f"Invalid coordinates for region {region}")
        
        # Validate timing
        timing = self.get_timing()
        for key, value in timing.items():
            if not isinstance(value, (int, float)) or value <= 0:
                raise ConfigError(f"Invalid timing value for {key}")
    
    def _create_default_config(self) -> None:
        """Create configuration file with default values"""
        
        # Whitelist section
        self.config.add_section('Whitelist')
        self.config['Whitelist']['mobs'] = self._defaults['whitelist']['mobs']
        
        # Options section
        self.config.add_section('Options')
        for option, value in self._defaults['options'].items():
            self.config['Options'][option] = str(value)
        
        # Regions section
        self.config.add_section('Regions')
        for region, coords in self._defaults['regions'].items():
            self.config['Regions'][region] = str(coords)
        
        # Timing section
        self.config.add_section('Timing')
        for key, value in self._defaults['timing'].items():
            self.config['Timing'][key] = str(value)
        
        # Skills section
        self.config.add_section('Skills')
        for key, value in self._defaults['skills'].items():
            self.config['Skills'][key] = str(value)
        
        self.save_config()
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config.clear()
        self._create_default_config()
    
    def export_config(self, filename: str) -> None:
        """Export configuration to a different file"""
        with open(filename, 'w') as configfile:
            self.config.write(configfile)
    
    def import_config(self, filename: str) -> None:
        """Import configuration from a file"""
        if not os.path.exists(filename):
            raise ConfigError(f"Configuration file {filename} not found")
        
        temp_config = configparser.ConfigParser()
        temp_config.read(filename)
        
        # Validate imported config before applying
        old_config = self.config
        self.config = temp_config
        
        try:
            self._validate_config()
        except ConfigError:
            self.config = old_config
            raise
        
        self.save_config()