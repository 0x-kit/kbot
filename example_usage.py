#!/usr/bin/env python3
"""
Example usage of the Visual Skill System

This script demonstrates how to use the visual skill system in your bot.
"""

import sys
import time
from pathlib import Path

# Add kbot directory to Python path
kbot_dir = Path(__file__).parent / "kbot"
sys.path.insert(0, str(kbot_dir))

def example_basic_usage():
    """Example of basic visual skill system usage"""
    print("📖 Basic Usage Example")
    print("-" * 30)
    
    try:
        from skill_system import VisualSkillSystem
        from skill_system.skill_types import SkillType
        
        # 1. Create visual skill system
        print("1️⃣ Creating visual skill system...")
        visual_system = VisualSkillSystem()
        
        # 2. Initialize for a specific class
        print("2️⃣ Initializing for nakayuda class...")
        class_name = "nakayuda"
        
        # Define skill bar regions (you'll need to configure these for your game)
        skill_bar_regions = [
            (100 + i*60, 500, 50, 50) for i in range(10)  # 10 slots, 60px apart
        ]
        
        success = visual_system.initialize_class(class_name, skill_bar_regions)
        if not success:
            print("❌ Failed to initialize class")
            return False
        
        print("✅ Class initialized successfully!")
        
        # 3. Get current profile information
        profile = visual_system.class_manager.get_current_profile()
        if profile:
            print(f"   Class: {profile.display_name}")
            print(f"   Skills: {len(profile.skills)}")
            print(f"   Rotations: {len(profile.rotations)}")
        
        # 4. Auto-detect skills (requires game to be running)
        print("3️⃣ Auto-detecting skills...")
        print("   ⚠️ Note: This requires the game to be running with skill bar visible")
        
        # In real usage, you would call:
        # results = visual_system.auto_detect_skills()
        # print(f"   Detected {len(results)} skills")
        
        # 5. Start monitoring (for real-time skill state detection)
        print("4️⃣ Starting skill monitoring...")
        print("   ⚠️ Note: This requires auto-detection to be completed first")
        
        # In real usage, you would call:
        # visual_system.start_monitoring()
        
        # 6. Execute skills
        print("5️⃣ Skill execution example...")
        
        if profile and profile.skills:
            # Get first skill as example
            first_skill = next(iter(profile.skills.values()))
            print(f"   Example skill: {first_skill.name} (key: {first_skill.key})")
            
            # In real usage with input controller:
            # success = visual_system.execute_skill(first_skill, verify_execution=True)
            # print(f"   Execution result: {success}")
        
        # 7. Use rotations
        print("6️⃣ Rotation usage example...")
        
        if profile and profile.rotations:
            rotation_name = next(iter(profile.rotations.keys()))
            print(f"   Setting active rotation: {rotation_name}")
            
            visual_system.set_active_rotation(rotation_name)
            
            # Get next skill from rotation
            next_skill = visual_system.get_next_skill()
            if next_skill:
                print(f"   Next skill in rotation: {next_skill.name}")
        
        print("✅ Basic usage example completed!")
        return True
        
    except Exception as e:
        print(f"❌ Example failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def example_configuration():
    """Example of configuration management"""
    print("\n📖 Configuration Example")
    print("-" * 30)
    
    try:
        from skill_system.config import VisualSkillConfig
        
        # 1. Create configuration manager
        config = VisualSkillConfig("example_config.json")
        
        # 2. Get current settings
        print("1️⃣ Current configuration:")
        print(f"   Current class: {config.get_current_class()}")
        print(f"   Available classes: {len(config.get_available_classes())}")
        
        # 3. Modify detection settings
        print("2️⃣ Updating detection settings...")
        detection_settings = {
            'template_threshold': 0.9,  # Higher threshold for more accuracy
            'cooldown_threshold': 0.8,
            'scan_interval': 0.05,      # Faster scanning
            'use_multi_scale': True
        }
        config.set_detection_settings(detection_settings)
        
        # 4. Modify execution settings
        print("3️⃣ Updating execution settings...")
        execution_settings = {
            'global_cooldown': 0.1,     # Faster execution
            'visual_verification': True,
            'auto_retry': True,
            'max_retries': 2
        }
        config.set_execution_settings(execution_settings)
        
        # 5. Add custom skill
        print("4️⃣ Adding custom skill...")
        custom_skill = {
            'icon': 'custom_skill.bmp',
            'type': 'visual',
            'key': 'x',
            'cooldown_duration': 5.0,
            'priority': 7,
            'mana_cost': 50,
            'enabled': True
        }
        config.add_skill('nakayuda', 'Custom Skill', custom_skill)
        
        # 6. Add custom rotation
        print("5️⃣ Adding custom rotation...")
        config.add_rotation('nakayuda', 'Custom Combo', ['Basic Attack', 'Custom Skill'])
        
        # 7. Save configuration
        print("6️⃣ Saving configuration...")
        if config.save_config():
            print("✅ Configuration saved successfully!")
        
        # 8. Export configuration
        print("7️⃣ Exporting configuration...")
        exported = config.export_config("exported_config.json")
        if exported:
            print("✅ Configuration exported!")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration example failed: {e}")
        return False

def example_advanced_usage():
    """Example of advanced features"""
    print("\n📖 Advanced Usage Example")
    print("-" * 30)
    
    try:
        from skill_system import VisualSkillSystem
        from skill_system.execution import ExecutionEngine, ExecutionMode, QueuePriority
        
        # 1. Create system with custom settings
        visual_system = VisualSkillSystem()
        
        # 2. Add callbacks for events
        def on_skill_detected(slot_index, result):
            print(f"🔍 Skill detected in slot {slot_index}: {result.detected_skill.name}")
        
        def on_skill_state_changed(skill, old_state, new_state):
            print(f"🔄 {skill.name} state changed: {old_state.value} → {new_state.value}")
        
        visual_system.add_callback('skill_detected', on_skill_detected)
        visual_system.add_callback('skill_state_changed', on_skill_state_changed)
        
        # 3. Performance optimization
        print("1️⃣ Optimizing performance...")
        visual_system.optimize_performance()
        
        # 4. Get system statistics
        print("2️⃣ System statistics:")
        stats = visual_system.get_system_stats()
        print(f"   Skills detected: {stats.get('skills_detected', 0)}")
        print(f"   Skills executed: {stats.get('skills_executed', 0)}")
        print(f"   Detection errors: {stats.get('detection_errors', 0)}")
        
        # 5. Export full system configuration
        print("3️⃣ Exporting system configuration...")
        full_config = visual_system.export_config()
        if full_config:
            print("✅ System configuration exported!")
        
        return True
        
    except Exception as e:
        print(f"❌ Advanced example failed: {e}")
        return False

def main():
    """Run all examples"""
    print("🚀 Visual Skill System - Usage Examples")
    print("=" * 50)
    
    # Check if basic imports work
    try:
        from skill_system import VisualSkillSystem
        print("✅ Visual skill system imports working")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("\n🔧 Please run: python install_dependencies.py")
        return False
    
    success = True
    
    # Run examples
    if not example_basic_usage():
        success = False
    
    if not example_configuration():
        success = False
    
    if not example_advanced_usage():
        success = False
    
    if success:
        print("\n🎉 All examples completed successfully!")
        print("\n📝 Integration tips:")
        print("   1. Configure skill bar regions for your game resolution")
        print("   2. Test auto-detection with the actual game running")
        print("   3. Customize detection thresholds for optimal accuracy")
        print("   4. Create class-specific skill configurations")
        print("   5. Use callbacks to integrate with your bot's combat system")
    else:
        print("\n⚠️ Some examples failed - check error messages above")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)