# config/config_manager.py
import configparser
import ast
import os
import json
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
            "whitelist": {"mobs": "Byokbo"},
            "options": {"auto_pots": True, "potion_threshold": 70},
            "regions": {
                "hp": (4, 20, 168, 36),
                "mp": (4, 36, 168, 51),
                "target": (4, 66, 168, 75),
                "target_name": (4, 55, 168, 70),
            },
            "timing": {
                "combat_check": 1.0,
                "attack": 1.5,
                "target_switch": 0.7,
                "potion": 0.5,
                "post_combat_delay": 1.0,
                "skill_interval": 1.3,
            },
            "skills": {
                "rotations": [],
                "priorities": {},
                "cooldowns": {},
                "conditions": {},
            },
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
            with open(self.config_file, "w") as configfile:
                self.config.write(configfile)
            print(f"ConfigManager: Saved config to {self.config_file}")  # Debug
        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    def get_whitelist(self) -> List[str]:
        """Get mob whitelist"""
        if self.config.has_section("Whitelist") and self.config.has_option(
            "Whitelist", "mobs"
        ):
            mobs = self.config["Whitelist"]["mobs"].split(",")
            return [mob.strip() for mob in mobs if mob.strip()]
        return [self._defaults["whitelist"]["mobs"]]

    def set_whitelist(self, mobs: List[str]) -> None:
        """Set mob whitelist"""
        if not self.config.has_section("Whitelist"):
            self.config.add_section("Whitelist")

        self.config["Whitelist"]["mobs"] = ",".join(mobs)

    def get_option(self, option: str, default: Any = None) -> Any:
        """Get a specific option value"""
        if self.config.has_section("Options") and self.config.has_option(
            "Options", option
        ):
            value = self.config["Options"][option]

            # Handle boolean values
            if isinstance(default, bool) or value.lower() in ("true", "false"):
                return value.lower() == "true"

            # Handle numeric values
            if isinstance(default, (int, float)):
                return type(default)(value)

            return value

        return default if default is not None else self._defaults["options"].get(option)

    def set_option(self, option: str, value: Any) -> None:
        """Set a specific option value"""
        if not self.config.has_section("Options"):
            self.config.add_section("Options")

        self.config["Options"][option] = str(value)

    def get_regions(self) -> Dict[str, Tuple[int, int, int, int]]:
        """Get region coordinates"""
        regions = {}

        # Default regions
        default_regions = {
            "hp": (4, 20, 168, 36),
            "mp": (4, 36, 168, 51),
            "target": (4, 66, 168, 75),
            "target_name": (4, 55, 168, 70),
        }

        if self.config.has_section("Regions"):
            for region in ["hp", "mp", "target", "target_name"]:
                if self.config.has_option("Regions", region):
                    try:
                        coords = ast.literal_eval(self.config["Regions"][region])
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
        if not self.config.has_section("Regions"):
            self.config.add_section("Regions")

        for region, coords in regions.items():
            self.config["Regions"][region] = str(coords)

        print(f"ConfigManager: Set regions to {regions}")  # Debug

    def get_timing(self) -> Dict[str, float]:
        """Get timing intervals, ensuring all defaults are present."""
        # Empezamos con una copia de los valores por defecto.
        timing = self._defaults["timing"].copy()

        # Si la sección existe, la recorremos y sobrescribimos los valores.
        if self.config.has_section("Timing"):
            for key, value in self.config.items("Timing"):
                try:
                    # Actualizamos la clave solo si existe en los defaults, para evitar claves basura.
                    if key in timing:
                        timing[key] = float(value)
                except ValueError:
                    # Si el valor no es un número, lo ignoramos y mantenemos el default.
                    self.logger.warning(
                        f"Invalid non-numeric value for timing key '{key}' in config file. Using default."
                    )
                    continue
        return timing

    def set_timing(self, timing: Dict[str, float]) -> None:
        """Set timing intervals"""
        if not self.config.has_section("Timing"):
            self.config.add_section("Timing")

        for key, value in timing.items():
            self.config["Timing"][key] = str(value)

    def get_skills(self) -> Dict[str, Any]:
        """
        Get skill configurations using robust JSON parsing for each key.
        """
        # Tu diccionario base está perfecto, lo mantenemos.
        skills = {
            "rotations": {},
            "skills": {},
            "active_rotation": None,
            "global_cooldown": 0.2,
        }

        if self.config.has_section("Skills"):
            # --- Lógica de carga con JSON ---

            # Cargar skills
            if self.config.has_option("Skills", "skills"):
                try:
                    skills_str = self.config.get("Skills", "skills")
                    skills["skills"] = json.loads(skills_str)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"DEBUG: Error parsing 'skills' with JSON: {e}")

            # Cargar rotations
            if self.config.has_option("Skills", "rotations"):
                try:
                    rotations_str = self.config.get("Skills", "rotations")
                    skills["rotations"] = json.loads(rotations_str)
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"DEBUG: Error parsing 'rotations' with JSON: {e}")

            # Cargar active_rotation (es un string simple, no necesita JSON)
            # Usamos .get() que devuelve None si no existe, es más limpio.
            active_rot = self.config.get("Skills", "active_rotation", fallback=None)
            if active_rot and active_rot != "None":
                skills["active_rotation"] = active_rot

            # Cargar global_cooldown (es un float, no necesita JSON)
            skills["global_cooldown"] = self.config.getfloat(
                "Skills", "global_cooldown", fallback=0.2
            )

        print(
            f"DEBUG: Final skills config loaded: {len(skills.get('skills', {}))} skills, {len(skills.get('rotations', {}))} rotations"
        )
        return skills

    def set_skills(self, skills_config: Dict[str, Any]) -> None:
        """
        Set skill configurations using robust JSON serialization for each key.
        """
        if not self.config.has_section("Skills"):
            self.config.add_section("Skills")

        # --- Lógica de guardado con JSON ---

        # Guardar skills (diccionario complejo)
        self.config.set("Skills", "skills", json.dumps(skills_config.get("skills", {})))

        # Guardar rotations (diccionario complejo)
        self.config.set(
            "Skills", "rotations", json.dumps(skills_config.get("rotations", {}))
        )

        # Guardar active_rotation (string simple)
        self.config.set(
            "Skills",
            "active_rotation",
            str(skills_config.get("active_rotation", "None")),
        )

        # Guardar global_cooldown (float simple)
        self.config.set(
            "Skills", "global_cooldown", str(skills_config.get("global_cooldown", 0.2))
        )

        print(
            f"ConfigManager: Saved skills config with {len(skills_config.get('skills', {}))} skills and {len(skills_config.get('rotations', {}))} rotations"
        )

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
        self.config.add_section("Whitelist")
        self.config["Whitelist"]["mobs"] = self._defaults["whitelist"]["mobs"]

        # Options section
        self.config.add_section("Options")
        for option, value in self._defaults["options"].items():
            self.config["Options"][option] = str(value)

        # Regions section
        self.config.add_section("Regions")
        for region, coords in self._defaults["regions"].items():
            self.config["Regions"][region] = str(coords)

        # Timing section
        self.config.add_section("Timing")
        for key, value in self._defaults["timing"].items():
            self.config["Timing"][key] = str(value)

        # Skills section
        self.config.add_section("Skills")
        for key, value in self._defaults["skills"].items():
            self.config["Skills"][key] = str(value)

        self.save_config()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values"""
        self.config.clear()
        self._create_default_config()

    def export_config(self, filename: str) -> None:
        """Export configuration to a different file"""
        with open(filename, "w") as configfile:
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
