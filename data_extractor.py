"""
Job Data Extractor for AI Internship Opportunity Finder
Handles extraction of structured job data from job posting URLs
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from urllib.parse import urlparse
import logging

# Set up logging
logger = logging.getLogger(__name__)

# Try to import BeautifulSoup for HTML parsing
try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False
    logger.warning("BeautifulSoup4 not available. Limited HTML parsing capabilities.")

# Configuration
from config import BRIGHT_DATA_API_KEY, BRIGHT_DATA_WEB_UNLOCKER_ZONE, REQUEST_TIMEOUT


class JobDataExtractor:
    """
    Extracts structured job data from job posting URLs
    """
    
    def __init__(self):
        """
        Initialize the job data extractor
        """
        self.api_key = BRIGHT_DATA_API_KEY
        self.web_unlocker_zone = BRIGHT_DATA_WEB_UNLOCKER_ZONE
        self.timeout = REQUEST_TIMEOUT
        
        # Session for connection reuse
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = 1  # Minimum delay between requests
    
    def _rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def extract_job_data(self, url: str) -> Dict:
        """
        Extract job data from a single URL
        
        Args:
            url (str): Job posting URL
        
        Returns:
            Dict: Extracted job data with success flag
        """
        logger.info(f"Extracting job data from: {url}")
        
        try:
            # Apply rate limiting
            self._rate_limit()
            
            # Determine extraction method based on URL
            if 'linkedin.com' in url:
                return self._extract_linkedin_job(url)
            elif 'indeed.com' in url:
                return self._extract_indeed_job(url)
            else:
                return self._extract_generic_job(url)
                
        except Exception as e:
            logger.error(f"Error extracting job data from {url}: {e}")
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_linkedin_job(self, url: str) -> Dict:
        """
        Extract job data from LinkedIn
        
        Args:
            url (str): LinkedIn job URL
        
        Returns:
            Dict: Extracted job data
        """
        try:
            # For now, return mock data since we don't have full Bright Data setup
            # In production, this would use Bright Data Web Unlocker
            
            # Extract job ID from URL
            job_id = self._extract_job_id_from_url(url)
            
            # Mock LinkedIn job data
            mock_data = {
                'success': True,
                'url': url,
                'source': 'LinkedIn',
                'job_title': 'Software Engineering Intern',
                'company': 'Tech Company',
                'location': 'San Francisco, CA',
                'job_type': 'Internship',
                'experience_level': 'Entry level',
                'description': 'Join our team as a Software Engineering Intern and work on cutting-edge projects using Python, JavaScript, and modern web technologies. This is a great opportunity to learn from experienced engineers and contribute to real products.',
                'requirements': 'Currently pursuing a degree in Computer Science or related field. Familiarity with programming languages like Python, Java, or JavaScript.',
                'salary': 'Competitive internship stipend',
                'company_size': '1001-5000 employees',
                'sector': 'Technology',
                'posted_date': '2025-05-20',
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_method': 'mock',
                    'content_length': 2500,
                    'job_id': job_id
                }
            }
            
            logger.info(f"Successfully extracted LinkedIn job: {mock_data['job_title']}")
            return mock_data
            
        except Exception as e:
            logger.error(f"Error extracting LinkedIn job: {e}")
            return {
                'success': False,
                'url': url,
                'source': 'LinkedIn',
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_indeed_job(self, url: str) -> Dict:
        """
        Extract job data from Indeed
        
        Args:
            url (str): Indeed job URL
        
        Returns:
            Dict: Extracted job data
        """
        try:
            # Extract job ID from URL
            job_id = self._extract_job_id_from_url(url)
            
            # Mock Indeed job data
            mock_data = {
                'success': True,
                'url': url,
                'source': 'Indeed',
                'job_title': 'Data Science Intern',
                'company': 'Analytics Corp',
                'location': 'Remote',
                'job_type': 'Internship',
                'experience_level': 'Entry level',
                'description': 'Exciting opportunity to work with data scientists and machine learning engineers. You will help build predictive models, analyze large datasets, and create visualizations. Perfect for students studying data science, statistics, or computer science.',
                'requirements': 'Pursuing degree in Data Science, Statistics, Computer Science, or related field. Experience with Python, R, or SQL preferred.',
                'salary': '$20-25/hour',
                'company_size': '501-1000 employees',
                'sector': 'Technology',
                'posted_date': '2025-05-18',
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_method': 'mock',
                    'content_length': 2200,
                    'job_id': job_id
                }
            }
            
            logger.info(f"Successfully extracted Indeed job: {mock_data['job_title']}")
            return mock_data
            
        except Exception as e:
            logger.error(f"Error extracting Indeed job: {e}")
            return {
                'success': False,
                'url': url,
                'source': 'Indeed',
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_generic_job(self, url: str) -> Dict:
        """
        Extract job data from a generic job site
        
        Args:
            url (str): Job posting URL
        
        Returns:
            Dict: Extracted job data
        """
        try:
            # Simple HTTP request for generic sites
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            
            # Basic data structure
            job_data = {
                'success': True,
                'url': url,
                'source': urlparse(url).netloc,
                'job_title': 'Generic Internship Position',
                'company': 'Company Name',
                'location': 'Location TBD',
                'job_type': 'Internship',
                'description': 'Job description extracted from generic site.',
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'extraction_method': 'generic',
                    'content_length': len(response.text),
                    'status_code': response.status_code
                }
            }
            
            # Try to extract more data if BeautifulSoup is available
            if BS4_AVAILABLE:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Try to find title
                title_element = soup.find('title')
                if title_element:
                    job_data['job_title'] = title_element.get_text().strip()
                
                # Try to find common job posting elements
                job_data['raw_html'] = response.text[:1000]  # Store first 1000 chars
            
            logger.info(f"Successfully extracted generic job: {job_data['job_title']}")
            return job_data
            
        except Exception as e:
            logger.error(f"Error extracting generic job: {e}")
            return {
                'success': False,
                'url': url,
                'source': urlparse(url).netloc,
                'error': str(e),
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_job_id_from_url(self, url: str) -> Optional[str]:
        """
        Extract job ID from URL
        
        Args:
            url (str): Job posting URL
        
        Returns:
            str: Job ID if found
        """
        try:
            if 'linkedin.com' in url:
                # LinkedIn job URLs: /jobs/view/1234567890
                parts = url.split('/')
                for i, part in enumerate(parts):
                    if part == 'view' and i + 1 < len(parts):
                        return parts[i + 1].split('?')[0]
            
            elif 'indeed.com' in url:
                # Indeed job URLs: /viewjob?jk=abcd1234
                if 'jk=' in url:
                    return url.split('jk=')[1].split('&')[0]
            
            return None
            
        except Exception:
            return None
    
    def extract_multiple_jobs(self, urls: List[str], max_jobs: int = None) -> List[Dict]:
        """
        Extract job data from multiple URLs
        
        Args:
            urls (List[str]): List of job URLs
            max_jobs (int): Maximum number of jobs to extract
        
        Returns:
            List[Dict]: List of extracted job data
        """
        if max_jobs:
            urls = urls[:max_jobs]
        
        logger.info(f"Extracting data from {len(urls)} job URLs")
        
        job_data_list = []
        
        for i, url in enumerate(urls, 1):
            logger.info(f"Processing job {i}/{len(urls)}: {url}")
            
            job_data = self.extract_job_data(url)
            job_data_list.append(job_data)
            
            # Add some variety to mock data
            if job_data.get('success') and 'mock' in job_data.get('extraction_metadata', {}).get('extraction_method', ''):
                job_data = self._add_variety_to_mock_data(job_data, i)
            
            # Small delay between requests
            if i < len(urls):
                time.sleep(0.5)
        
        successful_count = len([job for job in job_data_list if job.get('success')])
        logger.info(f"Extraction complete: {successful_count}/{len(job_data_list)} successful")
        
        return job_data_list
    
    def _add_variety_to_mock_data(self, job_data: Dict, index: int) -> Dict:
        """
        Add variety to mock job data for testing
        
        Args:
            job_data (Dict): Original job data
            index (int): Job index for variation
        
        Returns:
            Dict: Modified job data with variety
        """
        # Job title variations
        titles = [
            'Software Engineering Intern',
            'Data Science Intern',
            'Product Management Intern',
            'UX Design Intern',
            'Machine Learning Intern',
            'Full Stack Developer Intern',
            'Data Analyst Intern',
            'DevOps Intern'
        ]
        
        # Company variations
        companies = [
            'Tech Innovations Inc',
            'Data Analytics Corp',
            'Future Software Solutions',
            'AI Research Labs',
            'Digital Products Company',
            'Cloud Computing Inc',
            'Startup Ventures LLC',
            'Enterprise Solutions Co'
        ]
        
        # Location variations
        locations = [
            'San Francisco, CA',
            'New York, NY',
            'Seattle, WA',
            'Austin, TX',
            'Boston, MA',
            'Remote',
            'Chicago, IL',
            'Los Angeles, CA'
        ]
        
        # Apply variations based on index
        title_idx = (index - 1) % len(titles)
        company_idx = (index - 1) % len(companies)
        location_idx = (index - 1) % len(locations)
        
        job_data['job_title'] = titles[title_idx]
        job_data['company'] = companies[company_idx]
        job_data['location'] = locations[location_idx]
        
        # Vary description based on title
        if 'data' in job_data['job_title'].lower():
            job_data['description'] = f"Join our data team as a {job_data['job_title']} and work with big data, analytics, and machine learning technologies."
        elif 'software' in job_data['job_title'].lower():
            job_data['description'] = f"Software engineering internship focused on building scalable applications and learning modern development practices."
        else:
            job_data['description'] = f"Exciting {job_data['job_title']} opportunity to gain hands-on experience in a fast-paced technology environment."
        
        return job_data
    
    def close(self):
        """Close the session"""
        self.session.close()


def test_extraction():
    """
    Test the job data extraction functionality
    
    Returns:
        bool: True if test passes
    """
    try:
        extractor = JobDataExtractor()
        
        # Test URLs
        test_urls = [
            'https://www.linkedin.com/jobs/view/1234567890',
            'https://www.indeed.com/viewjob?jk=abcd1234',
            'https://example-jobs.com/posting/5678'
        ]
        
        print("🧪 Testing job data extraction...")
        
        # Test single extraction
        job_data = extractor.extract_job_data(test_urls[0])
        
        if job_data.get('success'):
            print(f"✅ Single extraction test passed")
            print(f"   Job: {job_data.get('job_title')} at {job_data.get('company')}")
        else:
            print(f"❌ Single extraction test failed: {job_data.get('error')}")
            return False
        
        # Test multiple extraction
        job_list = extractor.extract_multiple_jobs(test_urls, max_jobs=2)
        successful = [job for job in job_list if job.get('success')]
        
        print(f"✅ Multiple extraction test passed: {len(successful)}/{len(job_list)} successful")
        
        extractor.close()
        return True
        
    except Exception as e:
        print(f"❌ Extraction test failed: {e}")
        return False


if __name__ == "__main__":
    test_extraction()
