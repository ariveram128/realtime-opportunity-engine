#!/usr/bin/env python3
"""
Setup Test Script for AI Internship Opportunity Finder
This script verifies that all dependencies and configuration are properly set up.
"""

import sys
import os
import importlib

def test_python_version():
    """Test if Python version is compatible"""
    print("🐍 Testing Python version...")
    version = sys.version_info
    if version.major >= 3 and version.minor >= 7:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} - Requires Python 3.7+")
        return False

def test_dependencies():
    """Test if all required dependencies are installed"""
    print("\n📦 Testing dependencies...")
    required_packages = [
        'requests',
        'dotenv',
        'json',
        'os',
        'sys'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            if package == 'dotenv':
                importlib.import_module('dotenv')
            else:
                importlib.import_module(package)
            print(f"✅ {package} - Available")
        except ImportError:
            print(f"❌ {package} - Missing")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Run: pip install -r requirements.txt")
        return False
    
    return True

def test_project_structure():
    """Test if all required project files exist"""
    print("\n📁 Testing project structure...")
    required_files = [
        'main.py',
        'brightdata_handler.py',
        'config.py',
        'requirements.txt',
        '.gitignore',
        'README.md'
    ]
    
    missing_files = []
    
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file} - Found")
        else:
            print(f"❌ {file} - Missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️  Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def test_env_file():
    """Test if .env file exists and has required variables"""
    print("\n🔧 Testing environment configuration...")
    
    if not os.path.exists('.env'):
        print("❌ .env file not found")
        print("📝 Create a .env file with the following structure:")
        print("""
BRIGHT_DATA_API_KEY=your_bright_data_api_key_here
BRIGHT_DATA_SERP_ZONE=your_serp_zone_name_here
REQUEST_TIMEOUT=30
MAX_RESULTS_PER_SEARCH=20
""")
        return False
    
    print("✅ .env file found")
    
    # Try to load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv('BRIGHT_DATA_API_KEY')
        serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
        
        if api_key and api_key != 'your_bright_data_api_key_here':
            print("✅ BRIGHT_DATA_API_KEY - Set")
        else:
            print("❌ BRIGHT_DATA_API_KEY - Missing or placeholder")
            
        if serp_zone and serp_zone != 'your_serp_zone_name_here':
            print("✅ BRIGHT_DATA_SERP_ZONE - Set")
        else:
            print("❌ BRIGHT_DATA_SERP_ZONE - Missing or placeholder")
            
        # Check optional variables
        timeout = os.getenv('REQUEST_TIMEOUT', '30')
        max_results = os.getenv('MAX_RESULTS_PER_SEARCH', '20')
        
        print(f"ℹ️  REQUEST_TIMEOUT: {timeout}")
        print(f"ℹ️  MAX_RESULTS_PER_SEARCH: {max_results}")
        
        if (api_key and api_key != 'your_bright_data_api_key_here' and 
            serp_zone and serp_zone != 'your_serp_zone_name_here'):
            return True
        else:
            return False
            
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False

def test_import_modules():
    """Test if project modules can be imported"""
    print("\n🔧 Testing project modules...")
    
    modules_to_test = [
        ('config', 'config.py'),
        ('brightdata_handler', 'brightdata_handler.py')
    ]
    
    all_imported = True
    
    for module_name, file_name in modules_to_test:
        try:
            importlib.import_module(module_name)
            print(f"✅ {file_name} - Imports successfully")
        except Exception as e:
            print(f"❌ {file_name} - Import error: {e}")
            all_imported = False
    
    return all_imported

def main():
    """Run all tests"""
    print("🧪 AI Internship Opportunity Finder - Setup Test")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Project Structure", test_project_structure),
        ("Environment Configuration", test_env_file),
        ("Module Imports", test_import_modules)
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
        except Exception as e:
            print(f"❌ {test_name} - Error: {e}")
    
    print("\n" + "=" * 60)
    print(f"🎯 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Your setup is ready.")
        print("\nNext steps:")
        print("1. Make sure your .env file has valid Bright Data credentials")
        print("2. Run: python main.py --demo")
        return 0
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Run: pip install -r requirements.txt")
        print("- Create .env file with your Bright Data credentials")
        print("- Check that all project files are present")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code) 