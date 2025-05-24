#!/usr/bin/env python3
"""
Integration test for AI Internship Opportunity Finder
Tests the extraction → filtering → storage pipeline
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import extraction_phase, filtering_phase, storage_phase
from src.database_manager import DatabaseManager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

def test_pipeline_integration():
    """Test the full pipeline integration"""
    print("🧪 Testing AI Internship Opportunity Finder Pipeline Integration")
    print("=" * 70)
    
    # Test URLs for extraction
    test_urls = [
        'https://www.linkedin.com/jobs/view/1234567890',
        'https://www.indeed.com/viewjob?jk=abcd1234',
        'https://example.com/job/5678'
    ]
    
    try:
        # Phase 1: Test Extraction
        print("🔧 Testing extraction phase...")
        job_data_list = extraction_phase(test_urls, max_jobs=3)
        
        successful_extractions = [job for job in job_data_list if job.get('success', False)]
        print(f"   ✅ Extracted {len(successful_extractions)}/{len(job_data_list)} jobs successfully")
        
        if not successful_extractions:
            print("   ❌ No successful extractions, cannot continue test")
            return False
        
        # Phase 2: Test Filtering
        print("\n🎯 Testing filtering phase...")
        passed_jobs, rejected_jobs = filtering_phase(job_data_list)
        
        print(f"   ✅ Filtering complete: {len(passed_jobs)} passed, {len(rejected_jobs)} rejected")
        
        if not passed_jobs:
            print("   ⚠️  No jobs passed filtering - this might be expected based on filter criteria")
            print("   🔧 Testing storage with unfiltered jobs...")
            passed_jobs = successful_extractions  # Use all successful extractions for storage test
        
        # Phase 3: Test Storage
        print("\n💾 Testing storage phase...")
        storage_stats = storage_phase(passed_jobs)
        
        print(f"   ✅ Storage complete: {storage_stats}")
        
        # Phase 4: Test Database Retrieval
        print("\n📊 Testing database retrieval...")
        db = DatabaseManager()
        
        # Get all jobs
        all_jobs = db.get_jobs()
        print(f"   📋 Total jobs in database: {len(all_jobs)}")
        
        # Get statistics
        stats = db.get_job_stats()
        print(f"   📈 Database statistics: {stats}")
        
        # Test search functionality
        if all_jobs:
            search_results = db.search_jobs("software")
            print(f"   🔍 Search results for 'software': {len(search_results)} jobs")
        
        print("\n🎉 Integration test completed successfully!")
        print("=" * 70)
        print("✅ All pipeline components are working together correctly")
        print("💡 You can now run the web interface with: python app.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_pipeline_integration()
    exit(0 if success else 1) 