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
        Requires BRIGHT_DATA_API_KEY environment variable
        """
        self.api_key = os.getenv('BRIGHT_DATA_API_KEY')
        if not self.api_key:
            raise ValueError("BRIGHT_DATA_API_KEY environment variable is required")
            
        # Initialize rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # seconds between requests
        
        # Initialize session
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })
        
        # Bright Data API endpoint
        self.api_endpoint = "https://api.brightdata.com/datasets/v3/trigger"
        
        # Multiple dataset IDs to try (in case one is deprecated)
        self.dataset_ids = [
            "gd_l7q7zkzd03yqhb5lm",  # Updated LinkedIn dataset ID
            "gd_lpfll7v5hcqtkxl6l",  # Original dataset ID (fallback)
            "gd_lnkd_jobs_v1",       # Alternative dataset ID
        ]
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            logger.info(f"⏳ Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def discover_jobs_by_keyword(self, keyword: str, max_results: int = 20) -> Dict:
        """
        Discover LinkedIn jobs using keyword search
        Uses Bright Data's specialized LinkedIn dataset for job discovery by keyword.
        """
        logger.info(f"🔍 Discovering LinkedIn jobs for keyword: '{keyword}'")

        # Dataset ID for "Linkedin job listings information - Discover new jobs by keyword"
        # as per Bright Data documentation examples.
        dataset_id = "gd_lpfll7v5hcqtkxl6l"

        self._rate_limit() # Ensure rate limiting is applied

        try:
            # Payload for keyword-based discovery
            payload = [
                {
                    "keyword": keyword,
                    "location": "United States",
                    "country": "US",
                }
            ]

            # API endpoint
            url = "https://api.brightdata.com/datasets/v3/trigger"

            # Query parameters as per documentation for keyword discovery
            params = {
                "dataset_id": dataset_id,
                "type": "discover_new", # Crucial for discovery
                "discover_by": "keyword", # Crucial for discovery
                "limit_per_input": max_results,
                "format": "json",
                "uncompressed_webhook": True, # Recommended for easier debugging
                "include_errors": True
            }

            # Make the request using the initialized session
            logger.info(f"📡 Making LinkedIn discovery request to dataset '{dataset_id}' with keyword '{keyword}'...")
            response = self.session.post(
                url,
                params=params,
                json=payload, # Send data as JSON body
                timeout=60 # Increased timeout for discovery requests
            )

            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            result = response.json()

            logger.info(f"API Response: {result}")


            if result.get("status") == "running" and result.get("snapshot_id"):
                logger.info(f"✅ Job discovery initiated successfully. Snapshot ID: {result['snapshot_id']}")
                return {
                    "success": True,
                    "snapshot_id": result["snapshot_id"],
                    "status": "initiated",
                    "dataset_id_used": dataset_id
                }
            elif result.get("snapshot_id"): # Sometimes status might not be 'running' immediately
                logger.warning(f"⚠️ Job discovery request accepted, but status is '{result.get('status')}'. Snapshot ID: {result['snapshot_id']}")
                return {
                    "success": True, # Treat as success if snapshot_id is returned
                    "snapshot_id": result["snapshot_id"],
                    "status": result.get("status", "unknown_initiated"),
                    "dataset_id_used": dataset_id
                }
            else:
                error_message = result.get("error", "Unknown error: No snapshot_id in response and status not 'running'")
                logger.error(f"❌ LinkedIn API request failed: {error_message}. Response: {result}")
                return {"success": False, "error": error_message, "dataset_id_used": dataset_id}

        except requests.exceptions.HTTPError as http_err:
            error_content = "No content"
            try:
                error_content = http_err.response.json()
            except ValueError: # If response is not JSON
                error_content = http_err.response.text
            logger.error(f"❌ HTTP error during LinkedIn discovery: {http_err.response.status_code} {http_err.response.reason}. Content: {error_content}")
            return {"success": False, "error": f"HTTP {http_err.response.status_code}: {http_err.response.reason}. Details: {error_content}", "dataset_id_used": dataset_id}
        except requests.exceptions.RequestException as req_err:
            logger.error(f"❌ Request exception during LinkedIn discovery: {str(req_err)}")
            return {"success": False, "error": f"Request failed: {str(req_err)}", "dataset_id_used": dataset_id}
        except ValueError as val_err: # Handles JSON decoding errors or missing snapshot_id
            logger.error(f"❌ Value error (e.g., JSON decoding, missing fields) in LinkedIn discovery: {str(val_err)}. API Response was: {response.text if 'response' in locals() else 'Response object not available'}")
            return {"success": False, "error": f"Data processing error: {str(val_err)}", "dataset_id_used": dataset_id}
        except Exception as e:
            logger.error(f"❌ Unexpected error in LinkedIn discovery: {str(e)}", exc_info=True)
            return {"success": False, "error": f"Unexpected error: {str(e)}", "dataset_id_used": dataset_id}
    
    def _try_discovery_with_dataset(self, keyword: str, max_results: int, dataset_id: str) -> Dict:
        """
        Try job discovery with a specific dataset ID
        """
        # Prepare request payload for LinkedIn keyword discovery
        payload = [
            {
                "keyword": keyword,
                "location": "United States",
                "country": "US",
            }
        ]
        
        # Query parameters for discovery scraper
        params = {
            "dataset_id": dataset_id,
            "type": "discover_new",
            "discover_by": "keyword",
            "limit_per_input": max_results,
            "format": "json",
            "uncompressed_webhook": True,
            "include_errors": True
        }
        
        try:
            logger.info(f"📡 Making LinkedIn discovery request with dataset {dataset_id}...")
            
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            if response_data.get('status') == 'running':
                snapshot_id = response_data.get('snapshot_id')
                logger.info(f"📊 Job discovery initiated, snapshot ID: {snapshot_id}")
                
                return {
                    'success': True,
                    'source': 'LinkedIn Jobs Discovery',
                    'keyword': keyword,
                    'snapshot_id': snapshot_id,
                    'dataset_id': dataset_id,
                    'status': 'running',
                    'timestamp': datetime.now().isoformat()
                }
            else:
                error_msg = response_data.get('error', f'Unexpected status: {response_data.get("status")}')
                return {
                    'success': False,
                    'source': 'LinkedIn Jobs Discovery',
                    'keyword': keyword,
                    'dataset_id': dataset_id,
                    'error': error_msg,
                    'timestamp': datetime.now().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'source': 'LinkedIn Jobs Discovery',
                'keyword': keyword,
                'dataset_id': dataset_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _generate_demo_data(self, keyword: str, max_results: int) -> Dict:
        """
        Generate demo data when API fails
        """
        logger.info(f"🎭 Generating demo data for keyword: '{keyword}'")
        
        # Create realistic demo jobs based on keyword
        demo_jobs = []
        companies = ["TechCorp Inc.", "DataScience Solutions", "AI Innovations", "StartupX", "BigTech Co."]
        locations = ["San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Remote"]
        
        for i in range(min(max_results, 5)):
            job_id = f"demo_linkedin_{int(time.time())}_{i}"
            demo_jobs.append({
                "job_id": job_id,
                "title": f"{keyword.title()} Internship",
                "company": companies[i % len(companies)],
                "location": locations[i % len(locations)],
                "url": f"https://linkedin.com/jobs/view/{job_id}",
                "description": f"Exciting {keyword} internship opportunity with hands-on experience in cutting-edge technology. This role offers mentorship, real-world projects, and potential for full-time conversion.",
                "posted_date": datetime.now().strftime('%Y-%m-%d'),
                "job_type": "Internship",
                "experience_level": "Entry level",
                "source": "LinkedIn (Demo)",
                "demo_data": True
            })
        
        return {
            'success': True,
            'source': 'LinkedIn Jobs Discovery (Demo)',
            'keyword': keyword,
            'jobs': demo_jobs,
            'demo_mode': True,
            'timestamp': datetime.now().isoformat()
        }
    
    def convert_to_standard_format(self, jobs_data: List[Dict]) -> List[Dict]:
        """
        Convert LinkedIn job data to standard format
        
        Args:
            jobs_data (List[Dict]): Raw job data from LinkedIn API
        
        Returns:
            List[Dict]: Standardized job data
        """
        standardized_jobs = []
        
        logger.info(f"Starting conversion of {len(jobs_data)} jobs to standard format")
        
        for i, job in enumerate(jobs_data):
            try:
                # Log the raw data first
                logger.info(f"Raw job data for job {i}:")
                logger.info(f"  company_name: {job.get('company_name')}")
                logger.info(f"  job_title: {job.get('job_title')}")
                logger.info(f"  location: {job.get('job_location')}")
                
                if isinstance(job, dict):
                    # Extract job data with fallbacks
                    job_title = job.get('job_title') or f"Internship Opportunity {i+1}"
                    company = job.get('company_name')  # Get company_name from LinkedIn API
                    if not company or not company.strip():
                        logger.warning(f"Missing company name for job {i}, job_title: {job_title}")
                        company = "Unknown Company"
                    location = job.get('job_location') or "Location TBD"
                    description = job.get('job_summary') or job.get('job_description_formatted') or "Job description not available"
                    url = job.get('url') or f"https://linkedin.com/jobs/view/demo_{i}"
                    
                    # Additional fields from API
                    job_type = job.get('job_employment_type') or job.get('job_type', 'Internship')
                    experience_level = job.get('job_seniority_level') or 'Entry level'
                    posted_date = job.get('job_posted_date') or datetime.now().strftime('%Y-%m-%d')
                    
                    # Generate unique job ID
                    import hashlib
                    unique_data = f"{job_title}_{company}_{int(time.time())}_{i}"
                    job_id = f"linkedin_{hashlib.md5(unique_data.encode()).hexdigest()[:8]}"
                    
                    standardized_job = {
                        'job_id': job_id,
                        'job_title': job_title,
                        'company': company,  # This should be the company name from LinkedIn
                        'location': location,
                        'description': description,
                        'url': url,
                        'job_type': job_type,
                        'experience_level': experience_level,
                        'posted_date': posted_date,
                        'source': 'LinkedIn',
                        'extracted_at': datetime.now().isoformat(),
                        'status': 'new',
                        'demo_data': job.get('demo_data', False)
                    }
                    
                    # Log the standardized data
                    logger.info(f"Standardized job {i}:")
                    logger.info(f"  Title: {standardized_job['job_title']}")
                    logger.info(f"  Company: {standardized_job['company']}")
                    logger.info(f"  Location: {standardized_job['location']}")
                    
                    standardized_jobs.append(standardized_job)
                else:
                    logger.error(f"Job {i} is not a dictionary: {type(job)}")
                    
            except Exception as e:
                logger.error(f"Error converting job {i}: {str(e)}", exc_info=True)
                continue
        
        logger.info(f"✅ Converted {len(standardized_jobs)} jobs to standard format")
        return standardized_jobs
    
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
                
                status = status_data.get('status', 'unknown')
                progress = status_data.get('progress', 0)
                
                logger.info(f"📊 LinkedIn Status: {status}, Progress: {progress}%")
                
                if status == 'completed':
                    logger.info(f"✅ LinkedIn scraping completed! Downloading results...")
                    
                    download_response = self.session.get(download_url, timeout=60)
                    download_response.raise_for_status()
                    job_data = download_response.json()
                    
                    logger.info(f"📊 Downloaded {len(job_data) if isinstance(job_data, list) else 1} job records")
                    # Log the first job item if data is a list and not empty
                    if isinstance(job_data, list) and job_data:
                        logger.info(f"🔍 Raw first job item from API: {json.dumps(job_data[0], indent=2)}")
                    return job_data
                    
                elif status == 'failed':
                    error = status_data.get('error', 'Unknown error')
                    logger.error(f"❌ LinkedIn scraping failed: {error}")
                    return None
                    
                elif status == 'ready':
                    logger.info(f"📊 LinkedIn status is 'ready' - attempting to download results...")
                    
                    try:
                        download_response = self.session.get(download_url, timeout=60)
                        download_response.raise_for_status()
                        job_data = download_response.json()
                        
                        if isinstance(job_data, list) and len(job_data) > 0:
                            logger.info(f"✅ Successfully downloaded {len(job_data)} job records from 'ready' status")
                            # Log the first job item if data is a list and not empty
                            if job_data: # Ensure job_data is not an empty list
                                logger.info(f"🔍 Raw first job item from API (ready status): {json.dumps(job_data[0], indent=2)}")
                            return job_data
                        else:
                            logger.info(f"📊 'Ready' status but no data yet, continuing to wait...")
                    except Exception as e:
                        logger.info(f"📊 'Ready' status but download not available yet: {e}")
                
                # Wait before next check
                time.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error checking status: {e}")
                time.sleep(check_interval)
        
        logger.warning(f"⏰ LinkedIn scraping timed out after {max_wait_time} seconds")
        return None
    
    def close(self):
        """Close the session"""
        self.session.close()


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