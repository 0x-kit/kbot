# utils/exceptions.py
class BotError(Exception):
    """Base exception for bot-related errors"""
    pass

class ConfigError(BotError):
    """Configuration-related errors"""
    pass

class AnalysisError(BotError):
    """Pixel analysis and OCR errors"""
    pass

class SkillError(BotError):
    """Skill management errors"""
    pass

class WindowError(BotError):
    """Window management errors"""
    pass

class InputError(BotError):
    """Input/control errors"""
    pass
