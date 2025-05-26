#!/usr/bin/env python3
"""
Test script for Bright Data Dataset API integration
"""

import os
import json
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import our module
from src.brightdata_dataset_api import BrightDataDatasetAPI

def main():
    """Test the Bright Data Dataset API"""
    print("Testing Bright Data Dataset API...")
    
    # Initialize the API client
    api = BrightDataDatasetAPI()
    
    # Print the API key (first few chars)
    api_key = api.api_key or "Not set"
    if len(api_key) > 8:
        api_key = f"{api_key[:8]}...{api_key[-4:]}"
    print(f"API Key: {api_key}")
    print(f"Snapshot ID: {api.snapshot_id}")
    
    # Get jobs
    print("Fetching jobs...")
    jobs = api.get_jobs(limit=3)
    print(f"Found {len(jobs)} jobs")
    
    if jobs:
        # Print first job summary
        first_job = jobs[0]
        print("\nFirst job summary:")
        print(f"Title: {first_job.get('job_title', 'Unknown')}")
        print(f"Company: {first_job.get('company_name', 'Unknown')}")
        print(f"Location: {first_job.get('job_location', 'Unknown')}")
        print(f"URL: {first_job.get('url', 'Unknown')}")
        
        # Convert to standard format
        print("\nConverting to standard format...")
        standard_jobs = api.convert_to_standard_format(jobs)
        print(f"Converted {len(standard_jobs)} jobs")
        
        if standard_jobs:
            print("\nFirst standard job:")
            first_std_job = standard_jobs[0]
            print(f"Title: {first_std_job.get('job_title', 'Unknown')}")
            print(f"Company: {first_std_job.get('company', 'Unknown')}")
            print(f"Location: {first_std_job.get('location', 'Unknown')}")
            print(f"URL: {first_std_job.get('url', 'Unknown')}")
    
    # Check job progress
    print("\nChecking job progress...")
    progress = api.get_job_progress()
    print(f"Progress: {json.dumps(progress, indent=2)}")

if __name__ == "__main__":
    main() 