"""
Bright Data Dataset API Integration
Handles interaction with Bright Data's LinkedIn Dataset API
"""

import os
import json
import logging
import time
import requests
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class BrightDataDatasetAPI:
    """
    Client for Bright Data Dataset API to fetch LinkedIn job listings
    """
    
    def __init__(self):
        """Initialize the Bright Data Dataset API client"""
        self.api_key = os.getenv('BRIGHT_DATA_API_KEY')
        self.snapshot_id = os.getenv('BRIGHT_DATA_SNAPSHOT_ID', 's_mb2nxqys1f43vbp3bf')
        self.base_url = os.getenv('BRIGHT_DATA_DATASET_API_URL', 'https://api.brightdata.com/datasets/v3')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 60))
        
        if not self.api_key:
            logger.warning("BRIGHT_DATA_API_KEY not found in environment variables")
        
        logger.info(f"BrightDataDatasetAPI initialized with snapshot ID: {self.snapshot_id}")
    
    def get_jobs(self, limit: int = 50, keyword: str = None) -> List[Dict]:
        """
        Fetch jobs from the Bright Data Dataset API
        
        Args:
            limit: Maximum number of jobs to return (applied after fetching)
            keyword: Optional keyword to filter jobs
            
        Returns:
            List of job dictionaries
        """
        if not self.api_key:
            logger.error("Cannot fetch jobs: BRIGHT_DATA_API_KEY not set")
            return []
        
        try:
            url = f"{self.base_url}/snapshot/{self.snapshot_id}"
            params = {
                "format": "json",
                "limit": 100  # Request more jobs than needed to ensure we have enough after filtering
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            logger.info(f"Fetching jobs from Bright Data Dataset API: {url}")
            response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
            
            if response.status_code == 200:
                jobs = response.json()
                logger.info(f"Successfully fetched {len(jobs)} jobs from Bright Data Dataset API")
                
                # Filter by keyword if provided, using more flexible matching
                if keyword and isinstance(jobs, list):
                    keywords = keyword.lower().split()
                    filtered_jobs = []
                    
                    for job in jobs:
                        # Check multiple fields for any keyword match
                        job_text = (
                            job.get('job_title', '').lower() + ' ' +
                            job.get('job_summary', '').lower() + ' ' +
                            job.get('company_name', '').lower() + ' ' +
                            job.get('job_description', '').lower() + ' ' +
                            job.get('job_location', '').lower() + ' ' +
                            job.get('job_skills', '').lower() + ' ' +
                            job.get('job_industry', '').lower()
                        )
                        
                        # Consider a match if any keyword is found or if related terms are found
                        related_terms = self._expand_search_terms(keywords)
                        if any(kw in job_text for kw in keywords) or any(term in job_text for term in related_terms):
                            filtered_jobs.append(job)
                    
                    logger.info(f"Filtered to {len(filtered_jobs)} jobs matching keywords '{keyword}'")
                    jobs = filtered_jobs
                    
                    # If we have too few results, try a more lenient approach
                    if len(jobs) < 5:
                        logger.info("Too few results, trying more lenient matching")
                        jobs = response.json()  # Reset to all jobs
                        filtered_jobs = []
                        
                        # Use partial matching instead
                        for job in jobs:
                            job_text = (
                                job.get('job_title', '').lower() + ' ' +
                                job.get('job_summary', '').lower()
                            )
                            
                            # Match if any part of any keyword is found
                            if any(kw in job_text for kw in keywords) or any(any(part in job_text for part in kw.split()) for kw in keywords):
                                filtered_jobs.append(job)
                        
                        logger.info(f"Lenient filtering found {len(filtered_jobs)} jobs")
                        jobs = filtered_jobs
                
                # Apply limit after filtering
                if limit and isinstance(jobs, list) and len(jobs) > limit:
                    jobs = jobs[:limit]
                    logger.info(f"Limited to {len(jobs)} jobs")
                
                # If no jobs found, return empty list to trigger fallback to demo data
                if not jobs:
                    logger.warning(f"No jobs found matching '{keyword}', will use demo data")
                
                return jobs
            else:
                logger.error(f"Failed to fetch jobs: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching jobs from Bright Data Dataset API: {e}")
            return []
    
    def _expand_search_terms(self, keywords: List[str]) -> List[str]:
        """
        Expand search terms with related keywords
        
        Args:
            keywords: List of original keywords
            
        Returns:
            List of expanded keywords
        """
        expansions = {
            'software': ['dev', 'development', 'programming', 'coding', 'engineer', 'engineering'],
            'engineering': ['engineer', 'technical', 'technology', 'development'],
            'computer': ['computing', 'computational', 'software', 'hardware', 'tech'],
            'data': ['analytics', 'analysis', 'science', 'scientist', 'mining'],
            'web': ['frontend', 'backend', 'fullstack', 'full-stack', 'developer'],
            'machine': ['learning', 'ml', 'ai', 'artificial', 'intelligence'],
            'design': ['ux', 'ui', 'user', 'interface', 'experience']
        }
        
        expanded = []
        for kw in keywords:
            expanded.append(kw)
            for key, values in expansions.items():
                if key in kw or any(kw in val for val in values):
                    expanded.extend(values)
        
        return list(set(expanded))
    
    def get_job_progress(self) -> Dict:
        """
        Check the progress of the job snapshot
        
        Returns:
            Dictionary with progress information
        """
        if not self.api_key:
            logger.error("Cannot check progress: BRIGHT_DATA_API_KEY not set")
            return {"error": "API key not set"}
        
        try:
            url = f"{self.base_url}/progress/{self.snapshot_id}"
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.get(url, headers=headers, timeout=self.timeout)
            
            if response.status_code == 200:
                progress_data = response.json()
                logger.info(f"Job progress: {progress_data}")
                return progress_data
            else:
                logger.error(f"Failed to check job progress: {response.status_code} - {response.text}")
                return {"error": f"HTTP {response.status_code}"}
                
        except Exception as e:
            logger.error(f"Error checking job progress: {e}")
            return {"error": str(e)}
    
    def convert_to_standard_format(self, jobs: List[Dict]) -> List[Dict]:
        """
        Convert Bright Data job format to our standard job format
        
        Args:
            jobs: List of jobs from Bright Data API
            
        Returns:
            List of jobs in standard format
        """
        standard_jobs = []
        
        for job in jobs:
            try:
                # Generate a unique job ID
                job_id = job.get('job_posting_id', '')
                
                # Extract job data
                standard_job = {
                    'job_id': job_id,
                    'job_title': job.get('job_title', 'Unknown Title'),
                    'company': job.get('company_name', 'Unknown Company'),
                    'location': job.get('job_location', 'Unknown Location'),
                    'description': job.get('job_summary', ''),
                    'url': job.get('url', ''),
                    'status': 'new',
                    'source': 'LinkedIn via Bright Data',
                    'extracted_at': job.get('timestamp') or time.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    'job_type': 'Internship' if 'intern' in job.get('job_title', '').lower() else job.get('job_employment_type', 'Full-time'),
                    'raw_data': json.dumps(job)
                }
                
                standard_jobs.append(standard_job)
                
            except Exception as e:
                logger.error(f"Error converting job to standard format: {e}")
                continue
        
        logger.info(f"Converted {len(standard_jobs)} jobs to standard format")
        return standard_jobs


# For testing
if __name__ == "__main__":
    api = BrightDataDatasetAPI()
    jobs = api.get_jobs(limit=5)
    print(f"Fetched {len(jobs)} jobs")
    
    if jobs:
        print("First job:")
        print(json.dumps(jobs[0], indent=2))
        
        standard_jobs = api.convert_to_standard_format(jobs)
        print(f"Converted to {len(standard_jobs)} standard jobs")
        print("First standard job:")
        print(json.dumps(standard_jobs[0], indent=2)) 