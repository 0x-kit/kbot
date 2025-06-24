# config/unified_config_manager.py - NUEVO SISTEMA UNIFICADO

import json
import os
from typing import Dict, Any, List, Tuple
try:
    from utils.exceptions import ConfigError
    from utils.logger import BotLogger
except ImportError:
    # Define basic exceptions and logger if not available
    class ConfigError(Exception):
        pass
    
    class BotLogger:
        def __init__(self, name):
            self.name = name
        
        def info(self, msg):
            print(f"[INFO] {self.name}: {msg}")
        
        def debug(self, msg):
            print(f"[DEBUG] {self.name}: {msg}")
        
        def error(self, msg):
            print(f"[ERROR] {self.name}: {msg}")
        
        def warning(self, msg):
            print(f"[WARNING] {self.name}: {msg}")


class UnifiedConfigManager:
    """
    ✅ NUEVO - Sistema de configuración unificado en JSON
    Reemplaza el ConfigManager basado en INI fragmentado
    """

    def __init__(self, config_file: str = "bot_config.json"):
        self.config_file = config_file
        self.logger = BotLogger("UnifiedConfig")
        self.config_data = {}
        self._load_or_create_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """✅ Configuración por defecto completamente definida"""
        return {
            "version": "2.0",
            "combat": {
                "timing": {
                    # Timing principal del combate
                    "skill_interval": 1.0,  # Intervalo entre skills
                    "attack_interval": 1.2,  # Intervalo entre ataques básicos
                    "target_attempt_interval": 0.3,  # Frecuencia de búsqueda de targets
                    "post_combat_delay": 1.5,  # Espera después de matar
                    "assist_interval": 0.8,  # Frecuencia de assist
                    # Detección de problemas
                    "stuck_detection_searching": 6.0,  # Timeout búsqueda
                    "stuck_in_combat_timeout": 8.0,  # Timeout combate
                    "unstuck_cooldown": 3.0,  # Cooldown anti-stuck
                    # Logging y monitoreo
                    "combat_log_interval": 5.0,  # Frecuencia logs combate
                    "vitals_check_interval": 0.5,  # Frecuencia check HP/MP
                    "stats_update_interval": 5.0,  # Frecuencia stats
                },
                "behavior": {
                    # Comportamiento general
                    "auto_potions": True,
                    "potion_threshold": 70,
                    "enable_looting": True,
                    "assist_mode": False,
                    "use_skills": True,
                    # OCR y targeting
                    "ocr_tolerance": 85,
                    "fuzzy_match_threshold": 80,
                    # Looteo
                    "loot_duration": 0.8,
                    "loot_initial_delay": 0.1,
                    "loot_attempts": 2,
                    "loot_attempt_interval": 0.2,
                    "loot_key": "f",
                },
                "whitelist": ["Byokbo"],
            },
            "regions": {
                "hp": [4, 20, 168, 36],
                "mp": [4, 36, 168, 51],
                "target": [4, 66, 168, 75],
                "target_name": [4, 55, 168, 70],
            },
            "skills": {
                "global_cooldown": 0.15,
                "active_rotation": None,
                "definitions": {
                    # Skills básicos por defecto
                    "Basic Attack": {
                        "key": "r",
                        "cooldown": 1.0,
                        "type": "auto_attack",
                        "priority": 1,
                        "mana_cost": 0,
                        "enabled": True,
                        "description": "Basic attack skill",
                    },
                    "HP Potion": {
                        "key": "0",
                        "cooldown": 0.3,
                        "type": "hp_potion",
                        "priority": 10,
                        "mana_cost": 0,
                        "enabled": True,
                        "description": "Emergency HP potion",
                        "conditions": [{"type": "hp_below", "value": 70}],
                    },
                    "MP Potion": {
                        "key": "9",
                        "cooldown": 0.3,
                        "type": "mp_potion",
                        "priority": 10,
                        "mana_cost": 0,
                        "enabled": True,
                        "description": "Emergency MP potion",
                        "conditions": [{"type": "mp_below", "value": 70}],
                    },
                    "Assist": {
                        "key": "q",
                        "cooldown": 0.5,
                        "type": "assist",
                        "priority": 1,
                        "mana_cost": 0,
                        "enabled": True,
                        "description": "Assist party leader",
                    },
                },
                "rotations": {},
            },
            "ui": {
                "refresh_interval": 1000,  # ms
                "log_max_lines": 1000,
                "auto_scroll_logs": True,
                "window_size": [1200, 800],
                "window_position": [100, 100],
            },
            "debug": {
                "log_level": "INFO",
                "save_screenshots": False,
                "performance_monitoring": True,
                "verbose_combat_logs": False,
            },
        }

    def _load_or_create_config(self):
        """✅ Carga configuración o crea una nueva"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded_config = json.load(f)

                # Verificar versión y migrar si es necesario
                self._migrate_if_needed(loaded_config)
                self.config_data = loaded_config
                self.logger.info(f"Configuration loaded from {self.config_file}")

            except Exception as e:
                self.logger.error(f"Failed to load config: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        """✅ Crear configuración por defecto"""
        self.config_data = self._get_default_config()
        self.save_config()
        self.logger.info("Created default configuration")

    def _migrate_if_needed(self, config: Dict[str, Any]):
        """✅ Migración automática de versiones anteriores"""
        config_version = config.get("version", "1.0")

        if config_version < "2.0":
            self.logger.info("Migrating configuration from v1.0 to v2.0...")
            # Migrar INI antiguo a JSON nuevo
            default_config = self._get_default_config()

            # Preservar valores existentes donde sea posible
            if "combat" in config and "timing" in config["combat"]:
                # Merge timing values
                default_config["combat"]["timing"].update(config["combat"]["timing"])

            # Actualizar versión
            config["version"] = "2.0"

            # Merge con defaults para campos faltantes
            self._deep_merge(default_config, config)

    def _deep_merge(self, default: Dict, override: Dict) -> Dict:
        """✅ Merge profundo de diccionarios"""
        for key, value in override.items():
            if (
                key in default
                and isinstance(default[key], dict)
                and isinstance(value, dict)
            ):
                self._deep_merge(default[key], value)
            else:
                default[key] = value
        return default

    def save_config(self):
        """✅ Guardar configuración en JSON"""
        try:
            # Crear backup antes de guardar
            if os.path.exists(self.config_file):
                backup_file = f"{self.config_file}.backup"
                with open(self.config_file, "r") as original:
                    with open(backup_file, "w") as backup:
                        backup.write(original.read())

            # Guardar nueva configuración
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)

            self.logger.debug(f"Configuration saved to {self.config_file}")

        except Exception as e:
            raise ConfigError(f"Failed to save configuration: {e}")

    # ✅ GETTERS ESPECIALIZADOS POR CATEGORÍA

    def get_combat_timing(self) -> Dict[str, float]:
        """Get all combat timing parameters"""
        return self.config_data.get("combat", {}).get("timing", {})

    def get_combat_behavior(self) -> Dict[str, Any]:
        """Get combat behavior parameters"""
        return self.config_data.get("combat", {}).get("behavior", {})

    def get_whitelist(self) -> List[str]:
        """Get mob whitelist"""
        return self.config_data.get("combat", {}).get("whitelist", [])

    def get_regions(self) -> Dict[str, List[int]]:
        """Get screen regions"""
        return self.config_data.get("regions", {})

    def get_skills_config(self) -> Dict[str, Any]:
        """Get complete skills configuration"""
        return self.config_data.get("skills", {})

    def get_ui_config(self) -> Dict[str, Any]:
        """Get UI configuration"""
        return self.config_data.get("ui", {})

    # ✅ SETTERS ESPECIALIZADOS

    def set_combat_timing(self, timing: Dict[str, float]):
        """Update combat timing parameters"""
        if "combat" not in self.config_data:
            self.config_data["combat"] = {}
        if "timing" not in self.config_data["combat"]:
            self.config_data["combat"]["timing"] = {}

        self.config_data["combat"]["timing"].update(timing)
        self.logger.debug(f"Updated combat timing: {timing}")

    def set_combat_behavior(self, behavior: Dict[str, Any]):
        """Update combat behavior parameters"""
        if "combat" not in self.config_data:
            self.config_data["combat"] = {}
        if "behavior" not in self.config_data["combat"]:
            self.config_data["combat"]["behavior"] = {}

        self.config_data["combat"]["behavior"].update(behavior)
        self.logger.debug(f"Updated combat behavior: {behavior}")

    def set_whitelist(self, whitelist: List[str]):
        """Update mob whitelist"""
        if "combat" not in self.config_data:
            self.config_data["combat"] = {}

        self.config_data["combat"]["whitelist"] = whitelist
        self.logger.info(f"Updated whitelist: {whitelist}")

    def set_regions(self, regions: Dict[str, List[int]]):
        """Update screen regions"""
        self.config_data["regions"] = regions
        self.logger.debug(f"Updated regions: {regions}")

    def set_skills_config(self, skills_config: Dict[str, Any]):
        """Update complete skills configuration"""
        self.config_data["skills"] = skills_config
        self.logger.info(f"Updated skills configuration")


    # ✅ UTILIDADES

    def export_config(self, filename: str):
        """Export configuration to a different file"""
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.config_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Configuration exported to {filename}")
        except Exception as e:
            raise ConfigError(f"Failed to export configuration: {e}")

    def import_config(self, filename: str):
        """Import configuration from a file"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                imported_config = json.load(f)

            self._migrate_if_needed(imported_config)
            self.config_data = imported_config
            self.save_config()

            self.logger.info(f"Configuration imported from {filename}")
        except Exception as e:
            raise ConfigError(f"Failed to import configuration: {e}")

    def reset_to_defaults(self):
        """Reset configuration to defaults"""
        self.config_data = self._get_default_config()
        self.save_config()
        self.logger.info("Configuration reset to defaults")

    def get_all_config(self) -> Dict[str, Any]:
        """Get complete configuration"""
        return self.config_data.copy()

    def validate_config(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validar timing values
        timing = self.get_combat_timing()
        for key, value in timing.items():
            if not isinstance(value, (int, float)) or value <= 0:
                issues.append(f"Invalid timing value for {key}: {value}")

        # Validar regions
        regions = self.get_regions()
        for region_name, coords in regions.items():
            if not isinstance(coords, list) or len(coords) != 4:
                issues.append(f"Invalid region coordinates for {region_name}")
            elif not all(isinstance(c, int) and c >= 0 for c in coords):
                issues.append(f"Invalid coordinate values for {region_name}")

        return issues

    def get_summary(self) -> Dict[str, Any]:
        """Get configuration summary for debugging"""
        return {
            "version": self.config_data.get("version"),
            "skills_count": len(self.get_skills_config().get("definitions", {})),
            "rotations_count": len(self.get_skills_config().get("rotations", {})),
            "whitelist_count": len(self.get_whitelist()),
            "active_rotation": self.get_skills_config().get("active_rotation"),
            "auto_potions": self.get_combat_behavior().get("auto_potions"),
            "assist_mode": self.get_combat_behavior().get("assist_mode"),
        }

