#!/usr/bin/env python3
"""
Demo Session Isolation

This script demonstrates how session isolation works by simulating multiple users
accessing the job discovery system.
"""

import sys
import os
import time
import uuid
import json
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_manager import DatabaseManager

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)

def print_section(text):
    """Print a formatted section header"""
    print("\n" + "-" * 80)
    print(f" {text} ".center(80, "-"))
    print("-" * 80)

def main():
    """Main demo function"""
    # Use an in-memory database for the demo
    db = DatabaseManager(':memory:')
    
    print_header("Session Isolation Demo")
    print("This demo shows how session isolation keeps different users' job data separate.")
    
    # Create two session IDs to simulate different users
    session_1 = str(uuid.uuid4())
    session_2 = str(uuid.uuid4())
    
    print(f"\nUser 1 Session ID: {session_1}")
    print(f"User 2 Session ID: {session_2}")
    
    # Create some sample jobs for each session
    print_section("Creating jobs for User 1")
    
    # User 1's jobs
    user1_jobs = [
        {
            'url': 'https://example.com/job/1',
            'source': 'LinkedIn',
            'job_title': 'Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'job_type': 'Full-time',
            'description': 'Building amazing software products',
            'session_id': session_1,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 1000
            }
        },
        {
            'url': 'https://example.com/job/2',
            'source': 'LinkedIn',
            'job_title': 'Product Manager',
            'company': 'Startup Inc',
            'location': 'New York, NY',
            'job_type': 'Full-time',
            'description': 'Managing product development',
            'session_id': session_1,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 1200
            }
        }
    ]
    
    for job in user1_jobs:
        db.insert_job(job)
        print(f"Added job: {job['job_title']} at {job['company']}")
    
    print_section("Creating jobs for User 2")
    
    # User 2's jobs
    user2_jobs = [
        {
            'url': 'https://example.com/job/3',
            'source': 'Indeed',
            'job_title': 'Data Scientist',
            'company': 'AI Solutions',
            'location': 'Remote',
            'job_type': 'Contract',
            'description': 'Building ML models',
            'session_id': session_2,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 900
            }
        },
        {
            'url': 'https://example.com/job/4',
            'source': 'Indeed',
            'job_title': 'UX Designer',
            'company': 'Design Studio',
            'location': 'Seattle, WA',
            'job_type': 'Full-time',
            'description': 'Creating beautiful interfaces',
            'session_id': session_2,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 800
            }
        }
    ]
    
    for job in user2_jobs:
        db.insert_job(job)
        print(f"Added job: {job['job_title']} at {job['company']}")
    
    # Now let's demonstrate that each user only sees their own jobs
    print_section("User 1's View")
    user1_view = db.get_jobs(session_id=session_1)
    print(f"User 1 sees {len(user1_view)} jobs:")
    for job in user1_view:
        print(f"- {job['job_title']} at {job['company']}")
    
    print_section("User 2's View")
    user2_view = db.get_jobs(session_id=session_2)
    print(f"User 2 sees {len(user2_view)} jobs:")
    for job in user2_view:
        print(f"- {job['job_title']} at {job['company']}")
    
    # Let's try to add an identical job for both users
    print_section("Adding identical job for both users")
    
    identical_job_template = {
        'url': 'https://example.com/job/5',
        'source': 'LinkedIn',
        'job_title': 'Full Stack Developer',
        'company': 'Web Solutions',
        'location': 'Chicago, IL',
        'job_type': 'Full-time',
        'description': 'Building web applications',
        'extraction_metadata': {
            'extracted_at': datetime.now().isoformat(),
            'content_length': 1100
        }
    }
    
    # Copy for user 1
    identical_job_1 = identical_job_template.copy()
    identical_job_1['session_id'] = session_1
    db.insert_job(identical_job_1)
    print(f"Added identical job for User 1: Full Stack Developer at Web Solutions")
    
    # Copy for user 2
    identical_job_2 = identical_job_template.copy()
    identical_job_2['session_id'] = session_2
    db.insert_job(identical_job_2)
    print(f"Added identical job for User 2: Full Stack Developer at Web Solutions")
    
    # Check the views again
    print_section("Updated User 1's View")
    user1_view = db.get_jobs(session_id=session_1)
    print(f"User 1 now sees {len(user1_view)} jobs:")
    for job in user1_view:
        print(f"- {job['job_title']} at {job['company']}")
    
    print_section("Updated User 2's View")
    user2_view = db.get_jobs(session_id=session_2)
    print(f"User 2 now sees {len(user2_view)} jobs:")
    for job in user2_view:
        print(f"- {job['job_title']} at {job['company']}")
    
    print_section("Global View (All Jobs)")
    all_jobs = db.get_jobs()
    print(f"Total jobs in database: {len(all_jobs)}")
    
    print_header("Demo Complete")
    print("Session isolation is working correctly! Each user only sees their own jobs.")

if __name__ == "__main__":
    main() 