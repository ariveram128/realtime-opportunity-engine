#!/usr/bin/env python3
"""
Debug script to examine LinkedIn data structure
"""

import json
import requests
import logging
from linkedin_scraper_handler import LinkedInScraperHandler

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_linkedin_data():
    """Debug LinkedIn data structure"""
    try:
        print("🔍 Starting LinkedIn data structure debugging...")
        
        scraper = LinkedInScraperHandler()
        
        # Test with minimal search
        test_keyword = "test internship"
        print(f"\n📡 Testing with keyword: '{test_keyword}'")
        
        result = scraper.discover_jobs_by_keyword(test_keyword, max_results=3)
        
        print(f"\n📊 Raw Result Structure:")
        print(f"   Type: {type(result)}")
        print(f"   Keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        if 'job_data' in result:
            job_data = result['job_data']
            print(f"\n📊 Job Data Structure:")
            print(f"   Type: {type(job_data)}")
            print(f"   Length: {len(job_data) if hasattr(job_data, '__len__') else 'No length'}")
            
            if isinstance(job_data, list) and len(job_data) > 0:
                print(f"\n📊 Examining individual job items:")
                
                for i, job in enumerate(job_data[:3]):  # Only check first 3
                    print(f"\n   Job {i+1}:")
                    print(f"     Type: {type(job)}")
                    print(f"     Content: {str(job)[:300]}...")
                    
                    if isinstance(job, dict):
                        print(f"     Keys: {list(job.keys())}")
                    elif isinstance(job, list):
                        print(f"     List length: {len(job)}")
                        if len(job) > 0:
                            print(f"     First item type: {type(job[0])}")
                            print(f"     First item: {str(job[0])[:200]}...")
        
        # Test conversion
        if 'job_data' in result and result['job_data']:
            print(f"\n🔄 Testing conversion...")
            try:
                converted = scraper.convert_to_standard_format(result['job_data'])
                print(f"✅ Conversion successful: {len(converted)} jobs converted")
                
                if converted:
                    print(f"📋 First converted job keys: {list(converted[0].keys())}")
                    
            except Exception as conv_error:
                print(f"❌ Conversion failed: {conv_error}")
                logger.exception("Conversion error details:")
        
        scraper.close()
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        logger.exception("Debug error details:")

if __name__ == "__main__":
    debug_linkedin_data()
