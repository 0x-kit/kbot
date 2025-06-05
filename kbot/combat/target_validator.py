# combat/target_validator.py
import re
from typing import List, Dict, Any, Optional
from utils.logger import BotLogger

class TargetValidator:
    """Validates targets against whitelist and other criteria"""
    
    def __init__(self, logger: Optional[BotLogger] = None):
        self.logger = logger or BotLogger("TargetValidator")
        self.whitelist: List[str] = []
        self.blacklist: List[str] = []
        self.validation_rules: Dict[str, Any] = {}
        
        # Default validation rules
        self.default_rules = {
            'min_name_length': 2,
            'max_name_length': 50,
            'allow_special_chars': False,
            'case_sensitive': False
        }
        self.validation_rules.update(self.default_rules)
    
    def set_whitelist(self, whitelist: List[str]) -> None:
        """Set the mob whitelist"""
        self.whitelist = [name.strip() for name in whitelist if name.strip()]
        self.logger.info(f"Whitelist updated with {len(self.whitelist)} entries")
    
    def set_blacklist(self, blacklist: List[str]) -> None:
        """Set the mob blacklist"""
        self.blacklist = [name.strip() for name in blacklist if name.strip()]
        self.logger.info(f"Blacklist updated with {len(self.blacklist)} entries")
    
    def add_to_whitelist(self, name: str) -> None:
        """Add a name to whitelist"""
        name = name.strip()
        if name and name not in self.whitelist:
            self.whitelist.append(name)
            self.logger.info(f"Added '{name}' to whitelist")
    
    def remove_from_whitelist(self, name: str) -> None:
        """Remove a name from whitelist"""
        if name in self.whitelist:
            self.whitelist.remove(name)
            self.logger.info(f"Removed '{name}' from whitelist")
    
    def add_to_blacklist(self, name: str) -> None:
        """Add a name to blacklist"""
        name = name.strip()
        if name and name not in self.blacklist:
            self.blacklist.append(name)
            self.logger.info(f"Added '{name}' to blacklist")
    
    def remove_from_blacklist(self, name: str) -> None:
        """Remove a name from blacklist"""
        if name in self.blacklist:
            self.blacklist.remove(name)
            self.logger.info(f"Removed '{name}' from blacklist")
    
    def is_valid_target(self, target_name: str) -> bool:
        """Check if target is valid according to all rules"""
        if not target_name:
            return False
        
        # Basic validation
        if not self._basic_validation(target_name):
            return False
        
        # Blacklist check (takes priority)
        if self._is_blacklisted(target_name):
            self.logger.debug(f"Target '{target_name}' is blacklisted")
            return False
        
        # Whitelist check
        if self.whitelist and not self._is_whitelisted(target_name):
            self.logger.debug(f"Target '{target_name}' not in whitelist")
            return False
        
        return True
    
    def _basic_validation(self, target_name: str) -> bool:
        """Perform basic validation checks"""
        # Length check
        if (len(target_name) < self.validation_rules['min_name_length'] or
            len(target_name) > self.validation_rules['max_name_length']):
            return False
        
        # Special characters check
        if not self.validation_rules['allow_special_chars']:
            if not re.match(r'^[a-zA-Z0-9\s]+$', target_name):
                return False
        
        return True
    
    def _is_whitelisted(self, target_name: str) -> bool:
        """Check if target is in whitelist"""
        if not self.whitelist:
            return True  # Empty whitelist means all targets allowed
        
        case_sensitive = self.validation_rules['case_sensitive']
        
        for allowed_name in self.whitelist:
            if case_sensitive:
                if allowed_name in target_name:
                    return True
            else:
                if allowed_name.lower() in target_name.lower():
                    return True
        
        return False
    
    def _is_blacklisted(self, target_name: str) -> bool:
        """Check if target is in blacklist"""
        if not self.blacklist:
            return False  # Empty blacklist means no targets forbidden
        
        case_sensitive = self.validation_rules['case_sensitive']
        
        for forbidden_name in self.blacklist:
            if case_sensitive:
                if forbidden_name in target_name:
                    return True
            else:
                if forbidden_name.lower() in target_name.lower():
                    return True
        
        return False
    
    def get_match_score(self, target_name: str) -> float:
        """Get a score indicating how well the target matches criteria"""
        if not self.is_valid_target(target_name):
            return 0.0
        
        score = 1.0
        
        # Bonus for exact whitelist matches
        case_sensitive = self.validation_rules['case_sensitive']
        for allowed_name in self.whitelist:
            if case_sensitive:
                if target_name == allowed_name:
                    score += 0.5
                elif allowed_name in target_name:
                    score += 0.2
            else:
                if target_name.lower() == allowed_name.lower():
                    score += 0.5
                elif allowed_name.lower() in target_name.lower():
                    score += 0.2
        
        return min(2.0, score)  # Cap at 2.0
    
    def set_validation_rule(self, rule_name: str, value: Any) -> None:
        """Set a validation rule"""
        self.validation_rules[rule_name] = value
        self.logger.debug(f"Validation rule '{rule_name}' set to {value}")
    
    def get_validation_rules(self) -> Dict[str, Any]:
        """Get current validation rules"""
        return self.validation_rules.copy()
    
    def reset_to_defaults(self) -> None:
        """Reset validation rules to defaults"""
        self.validation_rules.clear()
        self.validation_rules.update(self.default_rules)
        self.logger.info("Validation rules reset to defaults")
    
    def export_config(self) -> Dict[str, Any]:
        """Export validator configuration"""
        return {
            'whitelist': self.whitelist.copy(),
            'blacklist': self.blacklist.copy(),
            'validation_rules': self.validation_rules.copy()
        }
    
    def import_config(self, config: Dict[str, Any]) -> None:
        """Import validator configuration"""
        if 'whitelist' in config:
            self.set_whitelist(config['whitelist'])
        
        if 'blacklist' in config:
            self.set_blacklist(config['blacklist'])
        
        if 'validation_rules' in config:
            self.validation_rules.update(config['validation_rules'])
        
        self.logger.info("Validator configuration imported")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get validator statistics"""
        return {
            'whitelist_entries': len(self.whitelist),
            'blacklist_entries': len(self.blacklist),
            'validation_rules': len(self.validation_rules),
            'whitelist': self.whitelist.copy(),
            'blacklist': self.blacklist.copy()
        }