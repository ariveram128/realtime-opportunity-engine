#!/usr/bin/env python3
"""
Test script to verify the company name fix works correctly.
This simulates the exact data flow that happens during LinkedIn searches.
"""

import sys
import os
import json
from datetime import datetime

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.linkedin_scraper_handler import LinkedInScraperHandler
from src.database_manager import DatabaseManager

def test_company_name_fix():
    """Test that company names are correctly converted and stored"""
    
    print("🧪 Testing Company Name Fix")
    print("=" * 50)
    
    # Initialize components
    linkedin_scraper = LinkedInScraperHandler()
    db = DatabaseManager()
    
    # Sample LinkedIn API response data (this is what the real API returns)
    sample_linkedin_jobs = [
        {
            "job_title": "Software Engineering Internship",
            "company_name": "Google Inc.",  # LinkedIn API uses 'company_name'
            "location": "Mountain View, CA",
            "url": "https://linkedin.com/jobs/test-1",
            "description": "Join our engineering team for an exciting internship opportunity.",
            "posted_date": "2025-05-25",
            "job_type": "Internship",
            "experience_level": "Entry Level"
        },
        {
            "job_title": "Data Science Intern",
            "company_name": "Meta Platforms",  # LinkedIn API uses 'company_name'
            "location": "Menlo Park, CA", 
            "url": "https://linkedin.com/jobs/test-2",
            "description": "Work with cutting-edge ML technologies.",
            "posted_date": "2025-05-24",
            "job_type": "Internship",
            "experience_level": "Entry Level"
        },
        {
            "job_title": "Product Management Intern",
            "company_name": "Apple Inc.",  # LinkedIn API uses 'company_name'
            "location": "Cupertino, CA",
            "url": "https://linkedin.com/jobs/test-3", 
            "description": "Shape the future of consumer technology.",
            "posted_date": "2025-05-23",
            "job_type": "Internship",
            "experience_level": "Entry Level"
        }
    ]
    
    print(f"📥 Testing with {len(sample_linkedin_jobs)} sample LinkedIn jobs")
    
    # Test 1: Verify raw LinkedIn data format
    print("\n1️⃣ Testing raw LinkedIn data format...")
    for i, job in enumerate(sample_linkedin_jobs):
        print(f"   Job {i+1}: company_name = '{job['company_name']}'")
      # Test 2: Test conversion function
    print("\n2️⃣ Testing convert_to_standard_format()...")
    
    try:
        # Call convert_to_standard_format with the LIST of jobs (not individual jobs)
        converted_jobs = linkedin_scraper.convert_to_standard_format(sample_linkedin_jobs)
        
        print(f"   ✅ Converted {len(converted_jobs)} jobs successfully")
        
        # Verify each conversion
        for i, (raw_job, converted_job) in enumerate(zip(sample_linkedin_jobs, converted_jobs)):
            print(f"   Job {i+1} conversion:")
            print(f"      Before: company_name = '{raw_job['company_name']}'")
            print(f"      After:  company = '{converted_job.get('company', 'MISSING!')}'")
            print(f"      Source: '{converted_job.get('source', 'MISSING!')}'")
            
            # Verify the conversion worked
            if converted_job.get('company') == raw_job['company_name']:
                print(f"      ✅ Conversion SUCCESS")
            else:
                print(f"      ❌ Conversion FAILED!")
                return False
                
    except Exception as e:
        print(f"      ❌ Conversion ERROR: {e}")
        return False
      # Test 3: Test database storage (simulate the exact app.py workflow)
    print("\n3️⃣ Testing database storage workflow...")
    stored_count = 0
    
    # This simulates the EXACT same logic from app.py after our fix
    if sample_linkedin_jobs: # Ensure there are jobs to store
        try:
            print(f"   Converting {len(sample_linkedin_jobs)} jobs from LinkedIn API format...")
            converted_jobs = linkedin_scraper.convert_to_standard_format(sample_linkedin_jobs)
            print(f"   ✅ Successfully converted {len(converted_jobs)} jobs")
            
            # Store each converted job
            for i, converted_job in enumerate(converted_jobs):
                if isinstance(converted_job, dict):
                    # Add a unique identifier to avoid duplicates
                    converted_job['url'] = f"{converted_job['url']}-test-{datetime.now().timestamp()}-{i}"
                    
                    if db.insert_job(converted_job):
                        stored_count += 1
                        print(f"      ✅ Job {i+1} stored: '{converted_job.get('company')}'")
                    else:
                        print(f"      ⚠️ Job {i+1} not stored (possibly duplicate)")
                else:
                    print(f"      ❌ Job {i+1} is not a dict: {type(converted_job)}")
                        
        except Exception as e:
            print(f"      ❌ Error during job conversion: {e}")
            return False
    
    print(f"\n   📊 Storage Summary: {stored_count}/{len(sample_linkedin_jobs)} jobs stored")
    
    # Test 4: Verify database contains correct data
    print("\n4️⃣ Verifying stored data in database...")
    
    # Get the most recent jobs
    recent_jobs = db.get_jobs(limit=10)
    
    # Find our test jobs
    test_companies = ["Google Inc.", "Meta Platforms", "Apple Inc."]
    found_jobs = []
    
    for job in recent_jobs:
        if job.get('company') in test_companies:
            found_jobs.append(job)
    
    print(f"   Found {len(found_jobs)} test jobs in database:")
    
    success = True
    for job in found_jobs:
        company = job.get('company')
        source = job.get('source', '')
        
        print(f"      Job: {job.get('job_title', 'Unknown Title')}")
        print(f"        Company: '{company}' (should NOT be None/Unknown)")
        print(f"        Source: '{source}' (should be 'LinkedIn')")
        
        if company and company != 'Unknown' and company in test_companies:
            print(f"        ✅ Company name correct!")
        else:
            print(f"        ❌ Company name WRONG! Got: '{company}'")
            success = False
            
        if source == 'LinkedIn':
            print(f"        ✅ Source correct!")
        else:
            print(f"        ❌ Source WRONG! Got: '{source}'")
            success = False
    
    # Final result
    print("\n" + "=" * 50)
    if success and len(found_jobs) >= len(test_companies):
        print("🎉 TEST PASSED! Company name fix is working correctly!")
        print("✅ LinkedIn API data is properly converted before database storage")
        print("✅ Company names are correctly stored in the database")
        print("✅ The bug has been fixed!")
    else:
        print("❌ TEST FAILED! The fix is not working properly.")
        if len(found_jobs) < len(test_companies):
            print(f"   Only found {len(found_jobs)}/{len(test_companies)} test jobs in database")
        print("   The company name issue persists.")
    
    return success

if __name__ == "__main__":
    test_company_name_fix()
