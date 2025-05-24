#!/usr/bin/env python3
"""
Simple test script to debug Bright Data SERP API connection
"""

import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_basic_connection():
    """Test basic connection to Bright Data API"""
    
    api_key = os.getenv('BRIGHT_DATA_API_KEY')
    serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
    
    print("🔧 Testing Bright Data SERP API Connection")
    print("=" * 50)
    print(f"API Key: {'*' * 20}{api_key[-4:] if api_key and len(api_key) > 4 else '****'}")
    print(f"SERP Zone: {serp_zone}")
    print()
    
    if not api_key or not serp_zone:
        print("❌ Missing API credentials!")
        return False
    
    # Test 1: Simple Google search using Direct API
    print("📡 Test 1: Direct API method")
    
    url = "https://api.brightdata.com/request"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Simple test search
    payload = {
        "zone": serp_zone,
        "url": "https://www.google.com/search?q=test&gl=us&hl=en&num=10",
        "format": "json"
    }
    
    try:
        print(f"Making request to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        print(f"Headers: {json.dumps({k: v for k, v in headers.items()}, indent=2)}")
        print()
        
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Length: {len(response.text)} characters")
        
        if response.status_code == 200:
            print("✅ Direct API test successful!")
            print(f"Response preview: {response.text[:200]}...")
            return True
        else:
            print(f"❌ Direct API test failed!")
            print(f"Error response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Direct API test error: {str(e)}")
        return False

def test_zone_configuration():
    """Test if the zone is properly configured"""
    
    api_key = os.getenv('BRIGHT_DATA_API_KEY')
    serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
    
    print("\n🔧 Test 2: Zone Configuration Check")
    
    # This is a hypothetical endpoint to check zone status
    # (Bright Data might have different endpoints for this)
    
    url = f"https://api.brightdata.com/zones/{serp_zone}/status"
    headers = {
        'Authorization': f'Bearer {api_key}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        print(f"Zone status check: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Zone appears to be active")
        else:
            print(f"⚠️  Zone status: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"ℹ️  Zone status check not available: {str(e)}")

def test_alternative_format():
    """Test with different format options"""
    
    api_key = os.getenv('BRIGHT_DATA_API_KEY')
    serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
    
    print("\n🔧 Test 3: Alternative Format Test")
    
    url = "https://api.brightdata.com/request"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }
    
    # Try with 'raw' format instead of 'json'
    payload = {
        "zone": serp_zone,
        "url": "https://www.google.com/search?q=test&gl=us&hl=en&num=5",
        "format": "raw"
    }
    
    try:
        print("Trying with 'raw' format...")
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        print(f"Raw format response: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Raw format works!")
            print(f"Response length: {len(response.text)}")
        else:
            print(f"❌ Raw format failed: {response.text}")
            
    except Exception as e:
        print(f"❌ Raw format error: {str(e)}")

def main():
    """Run all tests"""
    
    print("🧪 Bright Data SERP API Debug Tests")
    print("=" * 60)
    
    success = test_basic_connection()
    test_zone_configuration()
    test_alternative_format()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 At least one test succeeded! Your credentials appear to be working.")
    else:
        print("⚠️  All tests failed. Please check:")
        print("1. Your API key is correct")
        print("2. Your SERP zone name is correct")
        print("3. Your Bright Data account has SERP API access")
        print("4. Your zone is properly configured in the Bright Data dashboard")

if __name__ == "__main__":
    main() 