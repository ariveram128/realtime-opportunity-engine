#!/usr/bin/env python3
"""
Monitor the LinkedIn search and verify company names are correctly stored
"""

import time
import requests
import json
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database_manager import DatabaseManager

def monitor_search():
    """Monitor the search progress and results"""
    print("🔍 Monitoring LinkedIn search progress...")
    print("=" * 50)
    
    db = DatabaseManager()
    initial_job_count = len(db.get_jobs(limit=1000))
    print(f"📊 Initial job count in database: {initial_job_count}")
    
    last_progress = -1
    search_completed = False
    
    while not search_completed:
        try:
            # Check search status
            response = requests.get('http://127.0.0.1:5000/api/realtime_search/status', timeout=5)
            status = response.json()
            
            is_running = status.get('is_running', False)
            progress = status.get('progress', 0)
            phase = status.get('current_phase', 'Unknown')
            
            # Only print updates when progress changes
            if progress != last_progress:
                print(f"⏳ Progress: {progress}% - {phase}")
                last_progress = progress
            
            # Check if search completed
            if not is_running and progress > 0:
                search_completed = True
                
                if status.get('error'):
                    print(f"❌ Search failed: {status['error']}")
                    return False
                else:
                    results = status.get('results', {})
                    jobs_stored = results.get('jobs_stored', 0)
                    print(f"✅ Search completed! {jobs_stored} jobs stored")
                    
                    # Check the new jobs in database
                    final_job_count = len(db.get_jobs(limit=1000))
                    new_jobs_count = final_job_count - initial_job_count
                    print(f"📊 Total jobs in database: {final_job_count} (+{new_jobs_count} new)")
                    
                    # Check the most recent jobs to see if company names are correct
                    if new_jobs_count > 0:
                        print("\n🔍 Checking company names in newly stored jobs...")
                        recent_jobs = db.get_jobs(limit=min(10, new_jobs_count))
                        
                        success_count = 0
                        for i, job in enumerate(recent_jobs[:new_jobs_count]):
                            company = job.get('company', 'None')
                            source = job.get('source', '')
                            title = job.get('job_title', 'Unknown')
                            
                            if company and company != 'None' and company != 'Unknown':
                                print(f"   ✅ Job {i+1}: '{title}' at '{company}' (Source: {source})")
                                success_count += 1
                            else:
                                print(f"   ❌ Job {i+1}: '{title}' at '{company}' (Source: {source}) - COMPANY NAME ISSUE!")
                        
                        print(f"\n📊 Company Name Fix Results:")
                        print(f"   ✅ Jobs with correct company names: {success_count}/{new_jobs_count}")
                        print(f"   ❌ Jobs with missing company names: {new_jobs_count - success_count}/{new_jobs_count}")
                        
                        if success_count == new_jobs_count:
                            print("🎉 ALL JOBS HAVE CORRECT COMPANY NAMES! Fix is working perfectly!")
                        elif success_count > 0:
                            print("⚠️ Some jobs have correct company names, some don't. Partial fix success.")
                        else:
                            print("❌ No jobs have correct company names. Fix may not be working.")
                    
                    return True
            
            time.sleep(2)  # Check every 2 seconds
            
        except requests.RequestException:
            print("⚠️ Could not connect to Flask app. Is it running?")
            time.sleep(5)
        except KeyboardInterrupt:
            print("\n⏹️ Monitoring stopped by user")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    monitor_search()
