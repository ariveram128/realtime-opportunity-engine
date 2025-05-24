#!/usr/bin/env python3
"""
Comprehensive search functionality test script
"""

import requests
import json
from database_manager import DatabaseManager

def test_search_functionality():
    """Test all search features thoroughly"""
    base_url = "http://127.0.0.1:5000"
    
    print("🔍 COMPREHENSIVE SEARCH TESTING")
    print("=" * 50)
    
    # Initialize database for verification
    db = DatabaseManager()
    
    print("📊 Current Database Status:")
    stats = db.get_job_stats()
    print(f"   Total Jobs: {stats['total_jobs']}")
    print(f"   Companies: {len(stats.get('top_companies', {}))}")
    print(f"   Top Companies: {list(stats.get('top_companies', {}).keys())[:5]}")
    print()

    # Test 1: Basic Text Search
    print("🔍 TEST 1: Basic Text Search")
    test_searches = [
        "software engineer",
        "machine learning", 
        "python",
        "frontend",
        "data science",
        "cybersecurity",
        "remote"
    ]
    
    for search_term in test_searches:
        try:
            response = requests.get(f"{base_url}/api/search", params={
                'search_text': search_term,
                'page': 1
            })
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results_count = len(data['jobs'])
                    total = data['total']
                    print(f"   ✅ '{search_term}': {results_count} jobs on page 1 (Total: {total})")
                    
                    # Show first result for verification
                    if results_count > 0:
                        first_job = data['jobs'][0]
                        print(f"      📋 First result: {first_job['job_title']} at {first_job['company']}")
                else:
                    print(f"   ❌ '{search_term}': API returned error - {data.get('error')}")
            else:
                print(f"   ❌ '{search_term}': HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ '{search_term}': Exception - {e}")
    
    print()
    
    # Test 2: Company Filter
    print("🏢 TEST 2: Company Filter")
    test_companies = ["Google", "Microsoft", "Meta", "Apple", "OpenAI"]
    
    for company in test_companies:
        try:
            response = requests.get(f"{base_url}/api/search", params={
                'company': company,
                'page': 1
            })
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results = data['jobs']
                    print(f"   ✅ {company}: {len(results)} jobs")
                    if results:
                        for job in results:
                            print(f"      📋 {job['job_title']} - {job['location']}")
                else:
                    print(f"   ❌ {company}: {data.get('error')}")
        except Exception as e:
            print(f"   ❌ {company}: {e}")
    
    print()
    
    # Test 3: Location Filter  
    print("📍 TEST 3: Location Filter")
    test_locations = ["San Francisco", "Seattle", "Mountain View", "Remote", "CA"]
    
    for location in test_locations:
        try:
            response = requests.get(f"{base_url}/api/search", params={
                'location': location,
                'page': 1
            })
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results = data['jobs']
                    print(f"   ✅ {location}: {len(results)} jobs")
                    if results:
                        companies = [job['company'] for job in results]
                        print(f"      🏢 Companies: {', '.join(companies[:3])}")
                else:
                    print(f"   ❌ {location}: {data.get('error')}")
        except Exception as e:
            print(f"   ❌ {location}: {e}")
    
    print()
    
    # Test 4: Combined Search (Text + Company + Location)
    print("🔗 TEST 4: Combined Search")
    combined_tests = [
        {
            'search_text': 'engineer',
            'company': 'Google',
            'location': 'Mountain View'
        },
        {
            'search_text': 'data',
            'company': 'Microsoft',
            'location': 'Seattle'
        },
        {
            'search_text': 'intern',
            'location': 'CA'
        }
    ]
    
    for i, test_params in enumerate(combined_tests, 1):
        try:
            response = requests.get(f"{base_url}/api/search", params=test_params)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results = data['jobs']
                    print(f"   ✅ Combined Test {i}: {len(results)} jobs")
                    print(f"      Parameters: {test_params}")
                    if results:
                        for job in results:
                            print(f"      📋 {job['job_title']} at {job['company']} ({job['location']})")
                else:
                    print(f"   ❌ Combined Test {i}: {data.get('error')}")
        except Exception as e:
            print(f"   ❌ Combined Test {i}: {e}")
    
    print()
    
    # Test 5: Status Filter
    print("📊 TEST 5: Status Filter")
    all_statuses = ["new", "interested", "applied", "interview", "rejected"]
    
    for status in all_statuses:
        try:
            response = requests.get(f"{base_url}/api/search", params={
                'status': status,
                'page': 1
            })
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results = data['jobs']
                    print(f"   ✅ Status '{status}': {len(results)} jobs")
                else:
                    print(f"   ❌ Status '{status}': {data.get('error')}")
        except Exception as e:
            print(f"   ❌ Status '{status}': {e}")
    
    print()
    
    # Test 6: Pagination
    print("📄 TEST 6: Pagination")
    try:
        # Get all jobs first
        response = requests.get(f"{base_url}/api/search", params={'page': 1})
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                total_jobs = data['total']
                per_page = data['per_page']
                total_pages = (total_jobs + per_page - 1) // per_page
                
                print(f"   ✅ Total Jobs: {total_jobs}")
                print(f"   ✅ Per Page: {per_page}")
                print(f"   ✅ Total Pages: {total_pages}")
                
                # Test different pages
                for page in range(1, min(total_pages + 1, 4)):  # Test up to 3 pages
                    page_response = requests.get(f"{base_url}/api/search", params={'page': page})
                    if page_response.status_code == 200:
                        page_data = page_response.json()
                        if page_data['success']:
                            jobs_on_page = len(page_data['jobs'])
                            print(f"   ✅ Page {page}: {jobs_on_page} jobs")
                        else:
                            print(f"   ❌ Page {page}: {page_data.get('error')}")
    except Exception as e:
        print(f"   ❌ Pagination test: {e}")
    
    print()
    
    # Test 7: Empty Results
    print("🚫 TEST 7: Empty Results")
    empty_search_tests = [
        "nonexistent keyword xyz123",
        {"company": "FakeCompany"},
        {"location": "Mars"},
        {"search_text": "zzzzzz", "company": "Google"}
    ]
    
    for i, test in enumerate(empty_search_tests, 1):
        try:
            if isinstance(test, str):
                params = {'search_text': test}
            else:
                params = test
            
            response = requests.get(f"{base_url}/api/search", params=params)
            if response.status_code == 200:
                data = response.json()
                if data['success']:
                    results_count = len(data['jobs'])
                    if results_count == 0:
                        print(f"   ✅ Empty Test {i}: Correctly returned 0 results")
                    else:
                        print(f"   ⚠️  Empty Test {i}: Expected 0 but got {results_count} results")
                else:
                    print(f"   ❌ Empty Test {i}: {data.get('error')}")
        except Exception as e:
            print(f"   ❌ Empty Test {i}: {e}")
    
    print()
    print("🎉 SEARCH TESTING COMPLETE!")
    print("=" * 50)

if __name__ == '__main__':
    test_search_functionality() 