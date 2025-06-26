#!/usr/bin/env python3
"""
Dependency installer for Visual Skill System

This script installs all required dependencies for the visual skill system.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and print the result"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed:")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    version = sys.version_info
    print(f"🐍 Python version: {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ is required for the visual skill system")
        return False
    
    print("✅ Python version is compatible")
    return True

def install_dependencies():
    """Install all required dependencies"""
    
    if not check_python_version():
        return False
    
    # Find requirements file
    kbot_dir = Path(__file__).parent / "kbot"
    requirements_file = kbot_dir / "requirements.txt"
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    print(f"📋 Requirements file found: {requirements_file}")
    
    # Upgrade pip first
    if not run_command(f'"{sys.executable}" -m pip install --upgrade pip', "Upgrading pip"):
        print("⚠️ Failed to upgrade pip, continuing anyway...")
    
    # Install requirements
    install_cmd = f'"{sys.executable}" -m pip install -r "{requirements_file}"'
    if not run_command(install_cmd, "Installing requirements"):
        return False
    
    # Install additional performance dependencies
    additional_deps = [
        "python-Levenshtein>=0.21.0",  # For fast fuzzy matching
        "psutil>=5.9.0",               # For system monitoring
    ]
    
    for dep in additional_deps:
        install_cmd = f'"{sys.executable}" -m pip install "{dep}"'
        run_command(install_cmd, f"Installing {dep}")
    
    return True

def verify_installation():
    """Verify that all dependencies are installed correctly"""
    print("\n🔍 Verifying installation...")
    
    required_packages = [
        "PyQt5",
        "opencv-python", 
        "numpy",
        "pillow",
        "fuzzywuzzy",
        "python-Levenshtein"
    ]
    
    failed_packages = []
    
    for package in required_packages:
        try:
            if package == "opencv-python":
                import cv2
                print(f"✅ OpenCV version: {cv2.__version__}")
            elif package == "PyQt5":
                from PyQt5 import QtCore
                print(f"✅ PyQt5 version: {QtCore.QT_VERSION_STR}")
            elif package == "pillow":
                from PIL import Image
                print(f"✅ Pillow imported successfully")
            elif package == "numpy":
                import numpy as np
                print(f"✅ NumPy version: {np.__version__}")
            elif package == "fuzzywuzzy":
                from fuzzywuzzy import fuzz
                print(f"✅ FuzzyWuzzy imported successfully")
            elif package == "python-Levenshtein":
                import Levenshtein
                print(f"✅ Levenshtein imported successfully")
                
        except ImportError as e:
            print(f"❌ {package} not available: {e}")
            failed_packages.append(package)
    
    if failed_packages:
        print(f"\n❌ Installation verification failed for: {', '.join(failed_packages)}")
        return False
    else:
        print(f"\n✅ All dependencies verified successfully!")
        return True

def main():
    """Main installation process"""
    print("🚀 Visual Skill System - Dependency Installer")
    print("=" * 60)
    
    try:
        # Install dependencies
        if install_dependencies():
            print("\n📦 Dependencies installed successfully!")
            
            # Verify installation
            if verify_installation():
                print("\n🎉 Installation completed successfully!")
                print("\n📝 Next steps:")
                print("   1. Test basic functionality: python test_visual_system.py")
                print("   2. Test GUI interface: python test_visual_gui.py")
                print("   3. Configure skill bar regions in the game")
                print("   4. Start using the visual skill system!")
                return True
            else:
                print("\n⚠️ Installation completed but verification failed")
                print("   Some packages may not be working correctly")
                return False
        else:
            print("\n❌ Dependency installation failed")
            return False
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Installation cancelled by user")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error during installation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)