"""
LinkedIn Scraper Handler for AI Internship Opportunity Finder
Uses Bright Data's specialized LinkedIn scrapers for more reliable job discovery
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)


class LinkedInScraperHandler:
    """
    Handler for Bright Data's LinkedIn-specific scrapers
    Uses purpose-built scrapers instead of generic SERP API
    """
    
    def __init__(self):
        """
        Initialize the LinkedIn scraper handler
        """
        self.api_key = os.getenv('BRIGHT_DATA_API_KEY')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 60))
        
        if not self.api_key:
            raise ValueError(
                "Missing BRIGHT_DATA_API_KEY environment variable. "
                "Please set this in your .env file"
            )
        
        # Bright Data API endpoint
        self.api_endpoint = "https://api.brightdata.com/datasets/v3/trigger"
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 2  # Minimum delay between requests
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def discover_jobs_by_keyword(self, keyword: str, max_results: int = 20) -> Dict:
        """
        Discover LinkedIn jobs using keyword search
        Uses: "Linkedin job listings information - discover by keyword"
        
        Args:
            keyword (str): Search keyword (e.g., "software engineering intern")
            max_results (int): Maximum number of jobs to return
        
        Returns:
            Dict: Search results with job data
        """
        logger.info(f"🔍 Discovering LinkedIn jobs for keyword: '{keyword}'")
        
        # Apply rate limiting
        self._rate_limit()
        
        # Prepare request payload for LinkedIn keyword discovery
        # Using discovery format based on official Bright Data docs
        payload = [
            {
                "keyword": keyword,  # Required field for discovery
                "location": "United States",  # Optional but recommended
                "country": "US",  # Country filter
                # Additional optional filters could be added here
            }
        ]
        
        # Query parameters for discovery scraper
        params = {
            "dataset_id": "gd_lpfll7v5hcqtkxl6l",  # LinkedIn jobs dataset ID from docs
            "type": "discover_new",  # Discovery type
            "discover_by": "keyword",  # Discovery method
            "limit_per_input": max_results,  # Limit results per input
            "format": "json",
            "uncompressed_webhook": True,
            "include_errors": True
        }
        
        try:
            logger.info(f"📡 Making LinkedIn discovery request...")
            logger.info(f"🎯 Keyword: {keyword}, Max Results: {max_results}")
            logger.info(f"🌍 Location: United States, Country: US")
            
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            logger.info(f"📊 API Response: {response_data}")
            
            # Check if the request was successful
            if response_data.get('snapshot_id'):
                snapshot_id = response_data.get('snapshot_id')
                logger.info(f"📊 LinkedIn job discovery initiated, snapshot ID: {snapshot_id}")
                
                # Wait for completion and get results
                job_data = self._wait_for_completion(snapshot_id)
                
                if job_data:
                    # Limit results to max_results
                    limited_jobs = job_data[:max_results] if len(job_data) > max_results else job_data
                    
                    logger.info(f"✅ Successfully discovered {len(limited_jobs)} LinkedIn jobs (from {len(job_data)} total)")
                    return {
                        'success': True,
                        'source': 'LinkedIn Jobs Discovery',
                        'keyword': keyword,
                        'jobs_found': len(limited_jobs),
                        'job_data': limited_jobs,
                        'timestamp': datetime.now().isoformat(),
                        'snapshot_id': snapshot_id
                    }
                else:
                    logger.warning(f"⚠️ No job data received for keyword: {keyword}")
                    return {
                        'success': False,
                        'source': 'LinkedIn Jobs Discovery',
                        'keyword': keyword,
                        'error': 'No job data received',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                error_msg = response_data.get('error', 'Unknown error - no snapshot_id returned')
                logger.error(f"❌ LinkedIn discovery request failed: {error_msg}")
                return {
                    'success': False,
                    'source': 'LinkedIn Jobs Discovery',
                    'keyword': keyword,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error with LinkedIn discovery request: {e}")
            return {
                'success': False,
                'source': 'LinkedIn Jobs Discovery',
                'keyword': keyword,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _wait_for_completion(self, snapshot_id: str, max_wait_time: int = 300) -> Optional[List[Dict]]:
        """
        Wait for scraping job to complete and retrieve results
        
        Args:
            snapshot_id (str): The snapshot ID from the initial request
            max_wait_time (int): Maximum time to wait in seconds
        
        Returns:
            List[Dict]: Job data if successful, None otherwise
        """
        start_time = time.time()
        check_interval = 10  # Check every 10 seconds
        
        status_url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        download_url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
        
        logger.info(f"⏳ Waiting for LinkedIn scraping to complete (max {max_wait_time}s)...")
        
        while time.time() - start_time < max_wait_time:
            try:
                # Check status
                status_response = self.session.get(status_url, timeout=30)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get('status')
                progress = status_data.get('progress', 0)
                
                logger.info(f"📊 Status: {status}, Progress: {progress}%")
                
                # Handle completed status
                if status == 'completed':
                    logger.info(f"✅ Scraping completed! Downloading results...")
                    
                    # Download results
                    download_response = self.session.get(download_url, timeout=60)
                    download_response.raise_for_status()
                    
                    job_data = download_response.json()
                    
                    if isinstance(job_data, list) and len(job_data) > 0:
                        logger.info(f"📥 Downloaded {len(job_data)} job records")
                        return job_data
                    else:
                        logger.warning(f"⚠️ Downloaded data is empty or invalid format")
                        return None
                
                # Handle ready status - attempt to download results
                elif status == 'ready':
                    logger.info(f"📊 Status is 'ready' - attempting to download results...")
                    
                    try:
                        # Try to download results
                        download_response = self.session.get(download_url, timeout=60)
                        download_response.raise_for_status()
                        
                        job_data = download_response.json()
                        
                        if isinstance(job_data, list) and len(job_data) > 0:
                            logger.info(f"✅ Successfully downloaded {len(job_data)} job records from 'ready' status")
                            return job_data
                        else:
                            logger.info(f"📊 'Ready' status but no data yet, continuing to wait...")
                    
                    except Exception as e:
                        logger.info(f"📊 'Ready' status but download not available yet: {e}")
                        # Continue waiting
                
                elif status == 'failed':
                    error = status_data.get('error', 'Unknown error')
                    logger.error(f"❌ Scraping failed: {error}")
                    return None
                
                # For running status or other statuses, continue waiting
                elif status in ['running', 'pending', 'queued']:
                    logger.info(f"⏳ Still {status}, waiting...")
                
                else:
                    logger.warning(f"⚠️ Unknown status: {status}")
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"❌ Error checking status: {e}")
                time.sleep(check_interval)
        
        logger.error(f"⏰ Timeout: Scraping did not complete within {max_wait_time} seconds")
        return None
    
    def collect_job_by_url(self, job_url: str) -> Dict:
        """
        Collect detailed job data from specific LinkedIn job URL
        Uses: "Linkedin job listings information - collect by URL"
        
        Args:
            job_url (str): LinkedIn job URL
        
        Returns:
            Dict: Detailed job data
        """
        logger.info(f"🔗 Collecting LinkedIn job data from URL: {job_url}")
        
        # Apply rate limiting
        self._rate_limit()
        
        # Prepare request payload for LinkedIn URL collection
        payload = {
            "dataset_id": "gd_l7q4dp3lc7j2e38kf0",  # LinkedIn job listings - collect by URL
            "include_errors": True,
            "format": "json",
            "uncompressed_webhook": True,
            "data": [
                {
                    "url": job_url
                }
            ]
        }
        
        try:
            logger.info(f"📡 Making request to LinkedIn Job Collection API...")
            
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get('status') == 'running':
                snapshot_id = response_data.get('snapshot_id')
                logger.info(f"📊 Job collection initiated, snapshot ID: {snapshot_id}")
                
                # Wait for completion and get results
                job_data = self._wait_for_completion(snapshot_id)
                
                if job_data and len(job_data) > 0:
                    job_info = job_data[0]  # Should be single job
                    logger.info(f"✅ Successfully collected job: {job_info.get('title', 'Unknown')}")
                    return {
                        'success': True,
                        'source': 'LinkedIn Job Collection',
                        'url': job_url,
                        'job_data': job_info,
                        'timestamp': datetime.now().isoformat(),
                        'snapshot_id': snapshot_id
                    }
                else:
                    return {
                        'success': False,
                        'source': 'LinkedIn Job Collection',
                        'url': job_url,
                        'error': 'No job data received',
                        'timestamp': datetime.now().isoformat()
                    }
            else:
                error_msg = response_data.get('error', 'Unknown error')
                return {
                    'success': False,
                    'source': 'LinkedIn Job Collection',
                    'url': job_url,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error with LinkedIn collection request: {e}")
            return {
                'success': False,
                'source': 'LinkedIn Job Collection',
                'url': job_url,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def search_multiple_keywords(self, keywords: List[str], max_results_per_keyword: int = 10) -> List[Dict]:
        """
        Search for jobs using multiple keywords
        
        Args:
            keywords (List[str]): List of keywords to search
            max_results_per_keyword (int): Max results per keyword
        
        Returns:
            List[Dict]: Combined results from all keyword searches
        """
        logger.info(f"🔍 Searching LinkedIn for {len(keywords)} keywords")
        
        all_results = []
        
        for i, keyword in enumerate(keywords, 1):
            logger.info(f"📋 Processing keyword {i}/{len(keywords)}: '{keyword}'")
            
            result = self.discover_jobs_by_keyword(keyword, max_results_per_keyword)
            all_results.append(result)
              # Rate limiting between keywords
            if i < len(keywords):
                time.sleep(3)
        
        return all_results
    
    def close(self):
        """Close the session"""
        self.session.close()
    
    def _safe_get(self, job_data, key, default=''):
        """
        Safely get a value from job data, handling different data types
        
        Args:
            job_data: The job data (should be dict)
            key: The key to get
            default: Default value if key not found
            
        Returns:
            The value or default
        """
        try:
            if isinstance(job_data, dict):
                return job_data.get(key, default)
            else:
                logger.warning(f"⚠️ Expected dict but got {type(job_data)} when accessing key '{key}'")
                return default
        except Exception as e:
            logger.warning(f"⚠️ Error accessing key '{key}': {e}")
            return default
    
    def convert_to_standard_format(self, linkedin_data: List[Dict]) -> List[Dict]:
        """
        Convert LinkedIn scraper data to our standard format
        
        Args:
            linkedin_data: Raw data from LinkedIn scraper
        
        Returns:
            List[Dict]: Standardized job data
        """
        standardized_jobs = []
        
        logger.info(f"🔄 Converting {len(linkedin_data)} LinkedIn jobs to standard format")
        logger.debug(f"📊 Input data type: {type(linkedin_data)}")
          # Add more detailed debugging for the data structure
        if isinstance(linkedin_data, list) and len(linkedin_data) > 0:
            logger.debug(f"📊 First item type: {type(linkedin_data[0])}")
            logger.debug(f"📊 First item preview: {str(linkedin_data[0])[:500] if linkedin_data[0] else 'None'}")
            
            # Log the first few items to understand the structure
            for idx in range(min(3, len(linkedin_data))):
                item = linkedin_data[idx]
                logger.debug(f"📊 Item {idx+1} - Type: {type(item)}, Content: {str(item)[:300]}")
                if isinstance(item, (list, tuple)) and len(item) > 0:
                    logger.debug(f"📊 Item {idx+1} - First element: {type(item[0])}, {str(item[0])[:200]}")
        
        for i, job in enumerate(linkedin_data):
            try:                # Debug: Log job structure with more details
                logger.debug(f"📊 Job {i+1} type: {type(job)}")
                
                # Handle different data structures that LinkedIn might return
                original_job = job  # Keep reference for debugging
                
                if isinstance(job, dict):
                    logger.debug(f"📊 Job {i+1} keys: {list(job.keys())}")
                elif isinstance(job, list):
                    logger.warning(f"⚠️ Job {i+1} is a list with {len(job)} items: {str(job)[:100]}")
                    # If job is a list, try different extraction strategies
                    if len(job) > 0:
                        if isinstance(job[0], dict):
                            logger.info(f"📊 Using first dict item from job list: {i+1}")
                            job = job[0]
                        elif isinstance(job[0], list) and len(job[0]) > 0:
                            # Handle nested lists
                            logger.info(f"📊 Job {i+1} is nested list, trying to extract dict")
                            nested_item = job[0][0] if isinstance(job[0][0], dict) else job[0]
                            if isinstance(nested_item, dict):
                                job = nested_item
                            else:
                                logger.warning(f"⚠️ Job {i+1} nested structure doesn't contain dict, skipping")
                                continue
                        else:
                            logger.warning(f"⚠️ Job {i+1} list doesn't contain suitable data, skipping")
                            continue
                    else:
                        logger.warning(f"⚠️ Job {i+1} is empty list, skipping")
                        continue
                elif isinstance(job, (str, int, float)):
                    logger.warning(f"⚠️ Job {i+1} is primitive type {type(job)}: {str(job)[:100]}, skipping")
                    continue
                else:
                    logger.warning(f"⚠️ Job {i+1} is unknown type: {type(job)}, skipping")
                    continue
                
                # Final validation - ensure we have a dictionary
                if not isinstance(job, dict):
                    logger.error(f"❌ Job {i+1} could not be converted to dict (final type: {type(job)})")
                    logger.debug(f"❌ Original job data: {str(original_job)[:300]}")
                    continue
                
                # Extract and clean job data using correct LinkedIn field names
                # Use safe access with comprehensive error handling
                try:
                    standardized_job = {
                        'job_id': self._safe_get(job, 'job_posting_id', f"linkedin_{len(standardized_jobs)}"),
                        'job_title': self._safe_get(job, 'job_title', 'No Title Available'),
                        'company': self._safe_get(job, 'company_name', 'Unknown Company'),
                        'location': self._safe_get(job, 'job_location', 'Location Not Specified'),
                        'description': self._safe_get(job, 'job_summary', ''),
                        'url': self._safe_get(job, 'url', ''),
                        'job_type': self._safe_get(job, 'job_employment_type', 'Not Specified'),
                        'seniority_level': self._safe_get(job, 'job_seniority_level', 'Not Specified'),
                        'industries': self._safe_get(job, 'job_industries', ''),
                        'company_url': self._safe_get(job, 'company_url', ''),
                        'company_logo': self._safe_get(job, 'company_logo', ''),
                        'country_code': self._safe_get(job, 'country_code', ''),
                        'extracted_at': datetime.now().isoformat(),
                        'status': 'new',
                        'source': 'LinkedIn Jobs Discovery',
                        'raw_data': json.dumps(job) if isinstance(job, (dict, list)) else str(job)
                    }
                except Exception as field_error:
                    logger.error(f"❌ Error extracting fields from job {i+1}: {field_error}")
                    logger.debug(f"📊 Job data causing field error: {str(job)[:500]}")
                    continue
                
                # Clean up data
                for key in standardized_job:
                    if standardized_job[key] is None:
                        standardized_job[key] = ''
                    elif not isinstance(standardized_job[key], str):
                        standardized_job[key] = str(standardized_job[key])
                
                standardized_jobs.append(standardized_job)
                logger.debug(f"✅ Successfully converted job {i+1}: {standardized_job['job_title']}")
                
            except Exception as e:
                logger.error(f"❌ Error converting job {i+1}: {e}")
                logger.debug(f"📊 Problematic job data: {str(job)[:500]}")
                continue
        
        logger.info(f"✅ Successfully converted {len(standardized_jobs)}/{len(linkedin_data)} LinkedIn jobs")
        return standardized_jobs


def test_linkedin_scraper():
    """
    Test the LinkedIn scraper functionality
    """
    try:
        scraper = LinkedInScraperHandler()
        
        print("🧪 Testing LinkedIn Job Discovery...")
        
        # Test keyword search
        test_keyword = "software engineering intern"
        result = scraper.discover_jobs_by_keyword(test_keyword, max_results=5)
        
        if result.get('success'):
            jobs = result.get('job_data', [])
            print(f"✅ Discovery test passed: Found {len(jobs)} jobs")
            
            if jobs:
                # Show first job as example
                first_job = jobs[0]
                print(f"   📋 Example job: {first_job.get('title', 'No title')}")
                print(f"   🏢 Company: {first_job.get('company', 'No company')}")
                print(f"   📍 Location: {first_job.get('location', 'No location')}")
        else:
            print(f"❌ Discovery test failed: {result.get('error')}")
        
        scraper.close()
        return True
        
    except Exception as e:
        print(f"❌ LinkedIn scraper test failed: {e}")
        return False


if __name__ == "__main__":
    test_linkedin_scraper() 