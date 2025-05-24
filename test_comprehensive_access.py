#!/usr/bin/env python3
"""
Comprehensive Access Phase Test - Using Actual Discovered URLs
Tests BrightDataAccessHandler with real job URLs from our pipeline
"""

import json
import sys
import os
from datetime import datetime
import sqlite3

# Import our handlers
from brightdata_handler import BrightDataAccessHandler

def get_urls_from_database(max_urls: int = 5) -> list:
    """
    Get recent job URLs from our database
    
    Args:
        max_urls: Maximum number of URLs to retrieve
        
    Returns:
        List of job URLs
    """
    db_path = "internship_opportunities.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return []
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get recent URLs from database
        cursor.execute("""
            SELECT job_url, job_title, company, source 
            FROM internship_opportunities 
            WHERE job_url IS NOT NULL 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (max_urls,))
        
        rows = cursor.fetchall()
        conn.close()
        
        urls = []
        for row in rows:
            url, title, company, source = row
            urls.append({
                'url': url,
                'title': title,
                'company': company,
                'source': source
            })
        
        print(f"📊 Retrieved {len(urls)} URLs from database")
        return urls
        
    except Exception as e:
        print(f"❌ Error accessing database: {e}")
        return []

def get_sample_urls() -> list:
    """
    Get sample URLs for testing if database is empty
    
    Returns:
        List of sample job URLs
    """
    return [
        {
            'url': 'https://www.linkedin.com/jobs/view/machine-learning-intern-at-tracera-4141191205',
            'title': 'Machine Learning Intern',
            'company': 'Tracera',
            'source': 'LinkedIn'
        },
        {
            'url': 'https://www.linkedin.com/jobs/view/software-engineering-intern-summer-2025-at-acorns-4096785875',
            'title': 'Software Engineering Intern',
            'company': 'Acorns',
            'source': 'LinkedIn'
        },
        {
            'url': 'https://www.indeed.com/viewjob?jk=988880aa94260f68',
            'title': 'Data Science Intern',
            'company': 'Unknown',
            'source': 'Indeed'
        }
    ]

def test_comprehensive_access():
    """
    Run comprehensive Access Phase test
    """
    print("🚀 Comprehensive Access Phase Test")
    print("=" * 70)
    print("Testing BrightDataAccessHandler with real job URLs")
    print("Features: Navigation, Content Extraction, Rate Limiting")
    print("=" * 70)
    
    try:
        # Initialize Access Handler
        print("\n🔧 Initializing BrightDataAccessHandler...")
        access_handler = BrightDataAccessHandler()
        
        print("✅ BrightDataAccessHandler initialized successfully")
        print(f"📊 Configuration:")
        print(f"   - Zone: {access_handler.web_zone}")
        print(f"   - Timeout: {access_handler.timeout}s")
        print(f"   - Rate Limit: {access_handler.rate_limit_delay}s")
        
        # Get URLs to test
        print("\n📂 Getting URLs for testing...")
        test_urls = get_urls_from_database(max_urls=5)
        
        if not test_urls:
            print("⚠️  No URLs in database, using sample URLs")
            test_urls = get_sample_urls()
        
        print(f"🎯 Testing with {len(test_urls)} URLs:")
        for i, url_data in enumerate(test_urls, 1):
            print(f"   {i}. {url_data['title']} at {url_data['company']} ({url_data['source']})")
            print(f"      URL: {url_data['url']}")
        
        # Test individual URL access
        print("\n" + "=" * 70)
        print("🧪 PHASE 1: Individual URL Access & Content Extraction")
        print("=" * 70)
        
        individual_results = []
        
        for i, url_data in enumerate(test_urls[:3], 1):  # Test first 3 URLs
            print(f"\n📍 Test {i}/3: {url_data['title']}")
            print(f"🌐 URL: {url_data['url']}")
            
            # Test navigation and content extraction
            result = access_handler.navigate_to_url(
                url_data['url'], 
                extract_content=True
            )
            
            individual_results.append({
                'test_info': url_data,
                'result': result
            })
            
            if result.get('success'):
                print(f"✅ Access successful!")
                print(f"   📄 Content length: {result.get('content_length', 0):,} chars")
                print(f"   📝 Content type: {result.get('content_type', 'unknown')}")
                
                if result.get('extraction_success'):
                    extracted = result.get('extracted_data', {})
                    print(f"   🎯 Extracted title: {extracted.get('job_title', 'N/A')}")
                    print(f"   🏢 Extracted company: {extracted.get('company', 'N/A')}")
                    print(f"   📍 Extracted location: {extracted.get('location', 'N/A')}")
                else:
                    print(f"   ⚠️  Content extraction failed")
            else:
                print(f"❌ Access failed: {result.get('error', 'Unknown error')}")
        
        # Test batch processing
        print("\n" + "=" * 70)
        print("🧪 PHASE 2: Batch URL Processing")
        print("=" * 70)
        
        # Extract just the URLs for batch processing
        urls_only = [url_data['url'] for url_data in test_urls]
        
        print(f"🚀 Processing {len(urls_only)} URLs in batch mode...")
        
        batch_results = access_handler.access_multiple_urls(
            urls=urls_only,
            max_urls=5,
            save_results=True
        )
        
        # Analyze results
        print("\n" + "=" * 70)
        print("📊 COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        successful_individual = sum(1 for r in individual_results if r['result'].get('success'))
        successful_extractions = sum(1 for r in individual_results if r['result'].get('extraction_success'))
        
        successful_batch = sum(1 for r in batch_results if r.get('success'))
        successful_batch_extractions = sum(1 for r in batch_results if r.get('extraction_success'))
        
        print(f"📍 Individual Tests ({len(individual_results)} URLs):")
        print(f"   ✅ Successful access: {successful_individual}/{len(individual_results)} ({successful_individual/len(individual_results)*100:.1f}%)")
        print(f"   🔍 Successful extraction: {successful_extractions}/{successful_individual} ({successful_extractions/successful_individual*100:.1f}% of successful)" if successful_individual > 0 else "   🔍 Successful extraction: 0/0")
        
        print(f"\n📦 Batch Tests ({len(batch_results)} URLs):")
        print(f"   ✅ Successful access: {successful_batch}/{len(batch_results)} ({successful_batch/len(batch_results)*100:.1f}%)")
        print(f"   🔍 Successful extraction: {successful_batch_extractions}/{successful_batch} ({successful_batch_extractions/successful_batch*100:.1f}% of successful)" if successful_batch > 0 else "   🔍 Successful extraction: 0/0")
        
        # Overall assessment
        total_tests = len(individual_results) + len(batch_results)
        total_successful = successful_individual + successful_batch
        total_extractions = successful_extractions + successful_batch_extractions
        
        print(f"\n🎯 OVERALL ACCESS PHASE PERFORMANCE:")
        print(f"   🌐 Total URL access attempts: {total_tests}")
        print(f"   ✅ Total successful accesses: {total_successful} ({total_successful/total_tests*100:.1f}%)")
        print(f"   🔍 Total successful extractions: {total_extractions} ({total_extractions/total_successful*100:.1f}% of successful)" if total_successful > 0 else "   🔍 Total successful extractions: 0")
        
        # Final verdict
        if total_successful / total_tests >= 0.8:  # 80% success rate
            print(f"\n🎉 ACCESS PHASE: EXCELLENT PERFORMANCE!")
            print(f"   💪 High success rate indicates robust navigation")
            if total_extractions / total_successful >= 0.5:  # 50% extraction rate
                print(f"   🧠 Good content extraction capabilities")
            else:
                print(f"   ⚠️  Content extraction needs improvement")
        elif total_successful / total_tests >= 0.5:  # 50% success rate
            print(f"\n✅ ACCESS PHASE: GOOD PERFORMANCE")
            print(f"   📈 Decent success rate, some reliability issues")
        else:
            print(f"\n⚠️  ACCESS PHASE: NEEDS IMPROVEMENT")
            print(f"   🔧 Low success rate indicates configuration or API issues")
        
        # Cleanup
        access_handler.close()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Comprehensive Access test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print(f"🚀 Starting comprehensive Access Phase test...")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = test_comprehensive_access()
    
    if success:
        print(f"\n✅ Test completed successfully!")
    else:
        print(f"\n❌ Test failed. Check configuration and try again.")
    
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}") 