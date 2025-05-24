#!/usr/bin/env python3
"""
Simple test for Access Phase with Web Unlocker zone
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_simple_access():
    """Test accessing a single URL with minimal parameters"""
    
    # Configuration
    api_key = os.getenv('BRIGHT_DATA_API_KEY')
    web_unlocker_zone = os.getenv('BRIGHT_DATA_WEB_UNLOCKER_ZONE')
    web_zone = os.getenv('BRIGHT_DATA_WEB_ZONE') 
    serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
    
    # Try to use Web Unlocker first, then Web Zone, then SERP as fallback
    zone_to_use = web_unlocker_zone or web_zone or serp_zone
    zone_type = "Web Unlocker" if web_unlocker_zone else ("Web Zone" if web_zone else "SERP Zone")
    
    api_endpoint = "https://api.brightdata.com/request"
    
    if not api_key or not zone_to_use:
        print("❌ Missing API credentials")
        print(f"   API Key: {'✅' if api_key else '❌'}")
        print(f"   Web Unlocker Zone: {'✅' if web_unlocker_zone else '❌'}")
        print(f"   Web Zone: {'✅' if web_zone else '❌'}")
        print(f"   SERP Zone: {'✅' if serp_zone else '❌'}")
        print(f"\n💡 For Access Phase, you need a Web Unlocker zone.")
        print(f"   Add BRIGHT_DATA_WEB_UNLOCKER_ZONE to your .env file")
        return False
    
    print(f"🔧 Using {zone_type}: {zone_to_use}")
    
    # Test URL
    test_url = "https://www.indeed.com/viewjob?jk=9699bc02fa538e70"
    
    # Minimal payload - only supported parameters
    payload = {
        "zone": zone_to_use,
        "url": test_url,
        "format": "raw",
        "country": "us"
    }
    
    # Headers
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"🌐 Testing access to: {test_url}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(
            api_endpoint,
            json=payload,
            headers=headers,
            timeout=45
        )
        
        print(f"📊 Response status: {response.status_code}")
        print(f"📄 Response length: {len(response.text)} characters")
        
        if response.status_code == 200:
            content = response.text
            
            # Check for common error messages
            if "isn't supported with SERP API" in content:
                print("❌ SERP zone can't access job URLs - need Web Unlocker zone")
                print("💡 Please add BRIGHT_DATA_WEB_UNLOCKER_ZONE to your .env file")
                return False
            elif '<html' in content.lower() or '<!doctype' in content.lower():
                print("🎉 SUCCESS! Received HTML content - Access Phase working!")
                
                # Save sample for inspection
                with open('sample_access_result.html', 'w', encoding='utf-8') as f:
                    f.write(content)
                print("💾 Sample saved to sample_access_result.html")
                
                return True
            else:
                print("⚠️  Received non-HTML content")
                print(f"📄 First 200 chars: {content[:200]}")
                return False
        else:
            print(f"❌ Request failed: {response.status_code}")
            print(f"📄 Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Simple Access Phase Test")
    print("Testing with Web Unlocker zone for job URL access")
    print("=" * 50)
    
    success = test_simple_access()
    
    if success:
        print("\n✨ Test successful! Access Phase is working with proper zone.")
        print("💡 Next steps:")
        print("   • Update brightdata_handler.py to use Web Unlocker zone")
        print("   • Test with multiple URLs")
        print("   • Implement content extraction")
    else:
        print("\n❌ Test failed.")
        print("💡 Make sure you have a Web Unlocker zone configured in Bright Data dashboard")
        print("   and add BRIGHT_DATA_WEB_UNLOCKER_ZONE to your .env file") 