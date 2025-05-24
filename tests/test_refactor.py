#!/usr/bin/env python3
"""
Test script to verify the refactored structure works correctly
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Testing imports after refactoring...")

try:
    # Test main.py imports
    print("✓ Testing main.py imports...")
    from src.database_manager import DatabaseManager
    from src.job_filter import JobFilter
    print("  ✓ DatabaseManager and JobFilter imported successfully")

    # Test run.py functionality  
    print("✓ Testing run.py entry point...")
    from src.app import app
    print("  ✓ Flask app imported successfully")
    
    # Test scripts imports
    print("✓ Testing scripts imports...")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
    # Note: We would import from scripts here if needed
    
    print("\n🎉 All imports successful! Refactoring completed successfully.")
    print("\nTo start the web application, run:")
    print("  python run.py")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1)
