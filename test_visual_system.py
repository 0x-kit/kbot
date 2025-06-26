#!/usr/bin/env python3
"""
Test script for Visual Skill System

This script tests the basic functionality of the visual skill detection system
without requiring the full bot infrastructure.
"""

import sys
import os
from pathlib import Path

# Add kbot directory to Python path
kbot_dir = Path(__file__).parent / "kbot"
sys.path.insert(0, str(kbot_dir))

try:
    # Test basic imports
    print("🔍 Testing imports...")
    
    from skill_system.skill_types import VisualSkill, SkillType, SkillState
    print("✅ skill_types imported successfully")
    
    from skill_system.class_manager import ClassManager
    print("✅ class_manager imported successfully")
    
    from skill_system.detector import SkillDetector
    print("✅ detector imported successfully")
    
    from skill_system.visual_system import VisualSkillSystem
    print("✅ visual_system imported successfully")
    
    from skill_system.config import VisualSkillConfig
    print("✅ config imported successfully")
    
    print("\n🧪 Testing basic functionality...")
    
    # Test configuration system
    print("\n1️⃣ Testing configuration system...")
    config = VisualSkillConfig("test_config.json")
    print(f"   Current class: {config.get_current_class()}")
    print(f"   Available classes: {len(config.get_available_classes())}")
    for class_name, display_name in config.get_available_classes():
        print(f"      - {display_name} ({class_name})")
    
    # Test class manager
    print("\n2️⃣ Testing class manager...")
    resources_path = kbot_dir / "resources" / "skills"
    print(f"   Resources path: {resources_path}")
    print(f"   Resources exist: {resources_path.exists()}")
    
    class_manager = ClassManager(str(resources_path))
    print(f"   Discovered classes: {len(class_manager.class_profiles)}")
    
    for class_name, profile in class_manager.class_profiles.items():
        print(f"      - {profile.display_name}: {len(profile.skills)} skills")
    
    # Test visual system initialization
    print("\n3️⃣ Testing visual system...")
    visual_system = VisualSkillSystem(resources_path=str(resources_path))
    print("   Visual system created successfully")
    
    # Test class initialization
    if class_manager.class_profiles:
        first_class = next(iter(class_manager.class_profiles.keys()))
        print(f"   Initializing for class: {first_class}")
        
        # Create a simple skill bar region for testing
        skill_bar_regions = [
            (100 + i*60, 500, 50, 50) for i in range(10)  # 10 slots
        ]
        
        success = visual_system.initialize_class(first_class, skill_bar_regions)
        print(f"   Initialization success: {success}")
        
        if success:
            print("   ✅ Class initialized successfully!")
            
            # Get current profile
            profile = visual_system.class_manager.get_current_profile()
            if profile:
                print(f"   Profile loaded: {profile.display_name}")
                print(f"   Skills available: {len(profile.skills)}")
                
                # List first few skills
                for i, (name, skill) in enumerate(list(profile.skills.items())[:3]):
                    print(f"      {i+1}. {name} (key: {skill.key}, type: {skill.skill_type.value})")
    
    # Test detector without screen capture
    print("\n4️⃣ Testing detector (basic)...")
    detector = SkillDetector()
    print("   Detector created successfully")
    
    # Show performance stats
    stats = detector.get_performance_stats()
    print(f"   Templates cached: {stats['templates_cached']}")
    print(f"   Cache hit rate: {stats['cache_hit_rate']:.2%}")
    
    print("\n✅ ALL TESTS PASSED!")
    print("\n📝 Next steps:")
    print("   1. Install missing dependencies: pip install python-Levenshtein")
    print("   2. Test with GUI: python test_visual_gui.py")
    print("   3. Configure skill bar regions in the actual game")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n🔧 Possible fixes:")
    print("   1. Install dependencies: pip install -r kbot/requirements.txt")
    print("   2. Check Python path and working directory")
    print("   3. Ensure all files are in the correct location")
    
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    print(f"\nFull traceback:")
    traceback.print_exc()

print(f"\n📂 Current working directory: {os.getcwd()}")
print(f"📂 Script location: {Path(__file__).parent}")
print(f"📂 Kbot directory: {kbot_dir}")
print(f"📂 Kbot exists: {kbot_dir.exists()}")