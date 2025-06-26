#!/usr/bin/env python3
"""
Test script for the improved Visual Skill System UI

This script tests the new simplified and improved user interface.
"""

import sys
import os
from pathlib import Path

# Add kbot directory to Python path
kbot_dir = Path(__file__).parent / "kbot"
sys.path.insert(0, str(kbot_dir))

def test_improved_ui():
    """Test the improved UI"""
    try:
        print("🚀 Testing Improved Visual Skill System UI")
        print("=" * 60)
        
        # Import PyQt5 first
        from PyQt5.QtWidgets import QApplication, QMessageBox
        print("✅ PyQt5 imported successfully")
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("Visual Skill System - Improved UI Test")
        print("✅ QApplication created")
        
        # Import improved UI components
        from ui.dialogs.simple_visual_config import SimpleVisualConfigDialog
        print("✅ Simplified UI imported")
        
        from ui.dialogs.visual_region_selector import VisualRegionSelector
        print("✅ Visual region selector imported")
        
        # Test basic functionality first
        print("\n🧪 Testing basic functionality...")
        from skill_system import VisualSkillSystem, ClassManager
        
        resources_path = kbot_dir / "resources" / "skills"
        if resources_path.exists():
            class_manager = ClassManager(str(resources_path))
            print(f"✅ Found {len(class_manager.class_profiles)} character classes")
            
            for class_name, profile in class_manager.class_profiles.items():
                print(f"   - {profile.display_name}: {len(profile.skills)} skills")
        else:
            print(f"⚠️ Resources not found at: {resources_path}")
        
        # Create and show simplified dialog
        print("\n🖥️ Opening Simplified Visual Skill Configuration...")
        
        # Mock bot engine for testing (if you have the real one available, pass it here)
        try:
            # Try to create a minimal mock bot engine
            class MockBotEngine:
                def __init__(self):
                    from core.window_manager import WindowManager
                    self.window_manager = WindowManager()
                    self.window_manager.target_window = None  # No window selected initially
            
            mock_bot_engine = MockBotEngine()
            print("✅ Mock bot engine created")
        except:
            mock_bot_engine = None
            print("⚠️ Bot engine not available - some features will be limited")
        
        dialog = SimpleVisualConfigDialog(bot_engine=mock_bot_engine)
        
        # Show welcome message
        welcome_msg = """
        🎮 Welcome to the Improved Visual Skill System!
        
        ✨ New Features:
        • Step-by-step setup process
        • Visual skill bar region selection
        • Real-time skill state monitoring
        • Much simpler and intuitive interface
        
        📋 How to use:
        1. Select your character class
        2. Configure skill bar region (visually!)
        3. Test auto-detection
        4. Start real-time monitoring
        
        💡 Tips:
        • Use quick presets for common resolutions
        • The visual selector shows live preview
        • Green = ready, Yellow = cooldown, Red = unavailable
        """
        
        QMessageBox.information(dialog, "Visual Skill System - Improved UI", welcome_msg)
        
        print("✅ Simplified dialog created and shown!")
        
        # Show the dialog
        dialog.show()
        
        # Add some status information
        print("\n📊 UI Features Available:")
        print("   ✅ Step-by-step class selection")
        print("   ✅ Visual region configuration")
        print("   ✅ Quick resolution presets")
        print("   ✅ Auto-detection testing")
        print("   ✅ Real-time skill monitoring")
        print("   ✅ Integrated help system")
        
        print("\n🎯 To test fully:")
        print("   1. Select a character class from dropdown")
        print("   2. Click 'Configure Skill Bar' for visual selection")
        print("   3. Try quick presets (1080p/1440p) if you prefer")
        print("   4. Click 'Auto-Detect Skills' to test")
        print("   5. Start monitoring to see real-time states")
        
        # Run the application
        return app.exec_()
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Please install missing dependencies:")
        print("   python install_dependencies.py")
        return 1
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def main():
    """Main function"""
    try:
        print("🔍 Checking prerequisites...")
        
        # Check if kbot directory exists
        kbot_dir = Path(__file__).parent / "kbot"
        if not kbot_dir.exists():
            print(f"❌ Kbot directory not found: {kbot_dir}")
            return 1
        
        print(f"✅ Kbot directory found: {kbot_dir}")
        
        # Check if resources exist
        resources_dir = kbot_dir / "resources" / "skills"
        if resources_dir.exists():
            print(f"✅ Skill resources found: {resources_dir}")
        else:
            print(f"⚠️ Skill resources not found: {resources_dir}")
            print("   Some features may be limited")
        
        # Check if UI files exist
        ui_files = [
            kbot_dir / "ui" / "dialogs" / "simple_visual_config.py",
            kbot_dir / "ui" / "dialogs" / "visual_region_selector.py"
        ]
        
        missing_files = []
        for ui_file in ui_files:
            if ui_file.exists():
                print(f"✅ UI file found: {ui_file.name}")
            else:
                missing_files.append(ui_file)
        
        if missing_files:
            print("❌ Missing UI files:")
            for file in missing_files:
                print(f"   - {file}")
            return 1
        
        # Start the test
        return test_improved_ui()
        
    except KeyboardInterrupt:
        print("\n\n⏹️ Test cancelled by user")
        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())