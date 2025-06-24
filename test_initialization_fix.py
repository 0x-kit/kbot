#!/usr/bin/env python3
"""
Test script to verify the bot initialization fix.
This script tests the initialization flow without requiring PyQt5 installation.
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'kbot'))

def test_imports():
    """Test that all modules can be imported without errors"""
    try:
        print("Testing imports...")
        
        # Test core modules
        from core.bot_engine import BotEngine, BotWorker, ComponentFactory
        print("✓ Core bot engine imports successful")
        
        # Test configuration system
        from config.unified_config_manager import UnifiedConfigManager
        print("✓ Unified config manager import successful")
        
        # Test that old config manager is removed
        try:
            from config.config_manager import ConfigManager
            print("✗ ERROR: Old ConfigManager still exists!")
            return False
        except ImportError:
            print("✓ Old ConfigManager successfully removed")
        
        return True
        
    except Exception as e:
        print(f"✗ Import test failed: {e}")
        return False

def test_bot_engine_basic():
    """Test basic BotEngine instantiation"""
    try:
        print("\nTesting BotEngine instantiation...")
        
        # Test basic BotEngine creation
        engine = BotEngine()
        print("✓ BotEngine instance created successfully")
        
        # Verify initial state
        if engine.state.value == "stopped":
            print("✓ BotEngine initial state is correct")
        else:
            print(f"✗ Unexpected initial state: {engine.state.value}")
            return False
            
        # Test that components are None initially (will be set by worker)
        if engine.timer_manager is None:
            print("✓ Components are properly uninitialized")
        else:
            print("✗ Components should be None initially")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ BotEngine test failed: {e}")
        return False

def test_bot_worker_basic():
    """Test basic BotWorker instantiation"""
    try:
        print("\nTesting BotWorker instantiation...")
        
        # Test BotWorker creation
        worker = BotWorker()
        print("✓ BotWorker instance created successfully")
        
        # Verify it has a bot_engine
        if worker.bot_engine is not None:
            print("✓ BotWorker has bot_engine instance")
        else:
            print("✗ BotWorker should have bot_engine")
            return False
            
        # Verify initial state
        if not worker._initialized:
            print("✓ BotWorker is properly uninitialized")
        else:
            print("✗ BotWorker should start uninitialized")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ BotWorker test failed: {e}")
        return False

def test_config_cleanup():
    """Test configuration system cleanup"""
    try:
        print("\nTesting configuration cleanup...")
        
        # Test unified config manager
        from config.unified_config_manager import UnifiedConfigManager
        config = UnifiedConfigManager()
        print("✓ UnifiedConfigManager instantiated successfully")
        
        # Test loading default config (it's loaded automatically in __init__)
        print("✓ Configuration loaded successfully")
        
        # Test that old compatibility methods are removed
        if not hasattr(config, 'get_option'):
            print("✓ Old compatibility methods removed")
        else:
            print("✗ Old compatibility methods still exist")
            return False
            
        return True
        
    except Exception as e:
        print(f"✗ Config cleanup test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("Testing Bot Initialization Fix")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_bot_engine_basic,
        test_bot_worker_basic,
        test_config_cleanup
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Initialization fix is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())