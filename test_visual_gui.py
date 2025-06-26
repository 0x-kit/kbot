#!/usr/bin/env python3
"""
Test script for Visual Skill System GUI

This script tests the PyQt5 interface for the visual skill system.
"""

import sys
import os
from pathlib import Path

# Add kbot directory to Python path
kbot_dir = Path(__file__).parent / "kbot"
sys.path.insert(0, str(kbot_dir))

def test_gui():
    """Test the GUI components"""
    try:
        # Import PyQt5 first
        from PyQt5.QtWidgets import QApplication, QMessageBox
        from PyQt5.QtCore import Qt
        
        print("✅ PyQt5 imported successfully")
        
        # Create QApplication first (this fixes the QWidget error)
        app = QApplication(sys.argv)
        app.setApplicationName("Visual Skill System Test")
        
        print("✅ QApplication created")
        
        # Now import our GUI components
        from ui.dialogs.visual_skill_config import VisualSkillConfigDialog, SkillMonitorWidget
        print("✅ GUI components imported successfully")
        
        # Create and show the main dialog
        print("🖥️ Creating Visual Skill Configuration Dialog...")
        dialog = VisualSkillConfigDialog()
        
        # Show welcome message
        QMessageBox.information(
            dialog, 
            "Visual Skill System Test",
            "Visual Skill System GUI test started successfully!\n\n"
            "This is the new visual skill configuration interface.\n"
            "You can now configure skills, rotations, and detection settings.\n\n"
            "Note: For full functionality, configure skill bar regions in the Detection tab."
        )
        
        print("✅ Dialog created successfully!")
        print("🎯 Opening configuration dialog...")
        
        # Show the dialog
        dialog.show()
        
        # Run the application
        return app.exec_()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Possible fixes:")
        print("   1. Install PyQt5: pip install PyQt5")
        print("   2. Install all dependencies: pip install -r kbot/requirements.txt")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_basic_functionality():
    """Test basic functionality without GUI"""
    try:
        print("🧪 Testing basic components...")
        
        # Test core imports
        from skill_system import VisualSkillSystem, SkillDetector, ClassManager
        print("✅ Core components imported")
        
        # Test configuration
        from skill_system.config import VisualSkillConfig
        config = VisualSkillConfig("test_config.json")
        print(f"✅ Configuration loaded - Current class: {config.get_current_class()}")
        
        # Test class manager with resources
        resources_path = kbot_dir / "resources" / "skills"
        if resources_path.exists():
            class_manager = ClassManager(str(resources_path))
            print(f"✅ Class manager loaded - Found {len(class_manager.class_profiles)} classes")
        else:
            print(f"⚠️ Resources path not found: {resources_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Visual Skill System GUI Test")
    print("=" * 50)
    
    # First test basic functionality
    if test_basic_functionality():
        print("\n✅ Basic functionality test passed!")
        print("🖥️ Starting GUI test...")
        
        # Then test GUI
        result = test_gui()
        
        if result == 0:
            print("✅ GUI test completed successfully!")
        else:
            print("❌ GUI test failed")
            
        sys.exit(result)
    else:
        print("❌ Basic functionality test failed - skipping GUI test")
        sys.exit(1)