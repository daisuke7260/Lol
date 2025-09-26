#!/usr/bin/env python3
"""
LOL Auto BAN Tool V4 - Production Test
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Import test"""
    try:
        from lol_auto_ban_v4_integrated import LOLAutoBanV4System
        print("✅ LOLAutoBanV4System import successful")
        
        from lol_auto_ban_v4_gui import LOLV4GUI
        print("✅ LOLV4GUI import successful")
        
        return True
    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_initialization():
    """Initialization test"""
    try:
        from lol_auto_ban_v4_integrated import LOLAutoBanV4System
        
        config = {"v4_settings": {"monitoring_interval": 3}}
        system = LOLAutoBanV4System(config)
        print("✅ V4 System initialization successful")
        
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

if __name__ == "__main__":
    print("LOL Auto BAN Tool V4 - Production Test")
    print("=" * 40)
    
    success = True
    success &= test_imports()
    success &= test_initialization()
    
    if success:
        print("\n🎉 All tests passed! System is ready.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
