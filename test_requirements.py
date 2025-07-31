#!/usr/bin/env python3
"""
Test script to verify all dependencies are properly installed
"""

import sys
import importlib

def test_import(module_name, package_name=None):
    """Test if a module can be imported"""
    try:
        if package_name:
            importlib.import_module(package_name)
        else:
            importlib.import_module(module_name)
        print(f"✅ {module_name}")
        return True
    except ImportError as e:
        print(f"❌ {module_name}: {e}")
        return False

def main():
    """Test all required dependencies"""
    print("🔍 Testing Vietnamese AI Voice Chat System Dependencies")
    print("=" * 60)
    
    # Core dependencies
    dependencies = [
        # Web framework
        ("Flask", "flask"),
        ("Flask-CORS", "flask_cors"),
        
        # OpenAI
        ("OpenAI", "openai"),
        
        # Environment
        ("python-dotenv", "dotenv"),
        
        # Audio processing
        ("SoundFile", "soundfile"),
        ("SoundDevice", "sounddevice"),
        ("NumPy", "numpy"),
        ("PyDub", "pydub"),
        ("Librosa", "librosa"),
        
        # Text-to-Speech
        ("gTTS", "gtts"),
        
        # Vietnamese TTS models
        ("HuggingFace Hub", "huggingface_hub"),
        ("Cached Path", "cached_path"),
        
        # Machine Learning
        ("PyTorch", "torch"),
        ("Transformers", "transformers"),
        
        # Utilities
        ("Requests", "requests"),
        ("urllib3", "urllib3"),
    ]
    
    # Optional dependencies
    optional_deps = [
        ("WebRTC VAD", "webrtcvad"),
    ]
    
    print("\n📦 Required Dependencies:")
    print("-" * 30)
    
    failed_imports = []
    for name, module in dependencies:
        if not test_import(name, module):
            failed_imports.append(name)
    
    print("\n🔧 Optional Dependencies:")
    print("-" * 30)
    
    for name, module in optional_deps:
        test_import(name, module)
    
    print("\n" + "=" * 60)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        print("\n💡 To install missing dependencies:")
        print("pip install -r requirements.txt")
        return False
    else:
        print("✅ All required dependencies are installed!")
        print("\n🚀 You can now run the Vietnamese AI Voice Chat System:")
        print("   python main.py      # CLI mode")
        print("   python app.py       # Web mode")
        print("   python demo.py      # Demo mode")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 