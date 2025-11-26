#!/usr/bin/env python3
"""
Setup script for Document Classification Agent
"""

import os
import sys
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("Error: Python 3.7 or higher is required")
        sys.exit(1)
    print(f"✓ Python {sys.version.split()[0]} detected")


def create_directories():
    """Create necessary directories"""
    directories = [
        "input_documents",
        "classified_documents", 
        "backup",
        "logs",
        "templates"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✓ Created directory: {directory}")


def install_dependencies():
    """Install required dependencies"""
    import subprocess
    
    print("Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✓ Dependencies installed successfully")
    except subprocess.CalledProcessError:
        print("✗ Error installing dependencies")
        print("Please install manually: pip install -r requirements.txt")


def setup_config():
    """Check if config file exists"""
    if Path("config.json").exists():
        print("✓ Configuration file exists")
    else:
        print("✗ Configuration file not found")
        print("Please ensure config.json exists")


def main():
    """Main setup function"""
    print("Document Classification Agent Setup")
    print("=" * 40)
    
    check_python_version()
    create_directories()
    setup_config()
    
    # Optional dependency installation
    install_deps = input("\nInstall dependencies automatically? (y/n): ").lower()
    if install_deps == 'y':
        install_dependencies()
    
    print("\n" + "=" * 40)
    print("Setup completed!")
    print("\nNext steps:")
    print("1. Place documents in input_documents/ folder")
    print("2. Run: python main.py")
    print("3. Check results in classified_documents/ folder")
    print("\nFor a demo, run: python demo.py")


if __name__ == "__main__":
    main()