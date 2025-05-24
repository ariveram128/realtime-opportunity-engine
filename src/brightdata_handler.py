"""
Bright Data SERP API Handler
This module handles the integration with Bright Data's SERP API to discover
internship opportunities from LinkedIn Jobs and Indeed.com

Access Phase: Navigate to discovered URLs and extract job content
"""

import os
import json
import requests
import urllib.parse
from typing import Dict, List, Optional
from dotenv import load_dotenv
from datetime import datetime
import time
import re

# Load environment variables
load_dotenv()


class BrightDataSERPHandler:
    """
    Handler for Bright Data SERP API to search for internship opportunities
    """
    
    def __init__(self):
        """
        Initialize the SERP handler with API credentials from environment variables
        """
        self.api_key = os.getenv('BRIGHT_DATA_API_KEY')
        self.serp_zone = os.getenv('BRIGHT_DATA_SERP_ZONE')
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 30))
        self.max_results = int(os.getenv('MAX_RESULTS_PER_SEARCH', 20))
        
        if not self.api_key or not self.serp_zone:
            raise ValueError(
                "Missing required environment variables. "
                "Please set BRIGHT_DATA_API_KEY and BRIGHT_DATA_SERP_ZONE in your .env file"
            )
        
        # Bright Data Direct API endpoint (recommended method)
        self.api_endpoint = "https://api.brightdata.com/request"
        
        # Session for connection reuse
        self.session = requests.Session()
        
        # Set up headers for Direct API access
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def construct_search_query(self, search_term: str, site: str) -> str:
        """
        Construct a Google search query for finding internships on specific sites
        
        Args:
            search_term (str): The internship search term (e.g., "software engineering internship")
            site (str): The website to search on (e.g., "linkedin.com/jobs", "indeed.com")
        
        Returns:
            str: Formatted search query for Google
        """
        # More specific search patterns to find individual job postings
        if 'linkedin.com' in site:
            # Target LinkedIn job posting URLs with specific ID patterns
            query = f'site:linkedin.com/jobs/view/ {search_term} internship OR intern'
        elif 'indeed.com' in site:
            # Target Indeed job posting URLs with viewjob pattern
            query = f'site:indeed.com/viewjob {search_term} internship OR intern'
        else:
            # Fallback for other sites
            query = f'site:{site} {search_term} internship'
        
        return query
    
    def search_linkedin_jobs(self, search_term: str) -> Dict:
        """
        Search for internships on LinkedIn Jobs using SERP API
        
        Args:
            search_term (str): The internship search term
        
        Returns:
            Dict: Raw JSON response from SERP API
        """
        query = self.construct_search_query(search_term, "linkedin.com/jobs")
        return self._perform_search(query, "LinkedIn Jobs")
    
    def search_indeed_jobs(self, search_term: str) -> Dict:
        """
        Search for internships on Indeed using SERP API
        
        Args:
            search_term (str): The internship search term
        
        Returns:
            Dict: Raw JSON response from SERP API
        """
        query = self.construct_search_query(search_term, "indeed.com")
        return self._perform_search(query, "Indeed")
    
    def _perform_search(self, query: str, source_name: str) -> Dict:
        """
        Perform the actual SERP API search using Direct API access
        
        Args:
            query (str): The search query to execute
            source_name (str): Name of the source for logging purposes
        
        Returns:
            Dict: Raw JSON response from SERP API
        """
        print(f"\n🔍 Searching {source_name} for: {query}")
        
        # Construct the target URL for Google search with proper encoding
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.google.com/search?q={encoded_query}&gl=us&hl=en&num={self.max_results}"
        
        # Request payload for Bright Data Direct API
        payload = {
            "zone": self.serp_zone,
            "url": search_url,
            "format": "json",  # Get JSON response
            "country": "us"  # Target country
        }
        
        try:
            print(f"📡 Making request to Bright Data API...")
            print(f"🎯 Target URL: {search_url}")
            
            # Make request to Bright Data Direct API
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse the JSON response
            try:
                response_data = response.json()
                
                # Check if this is a Bright Data response with HTML in the body
                if 'body' in response_data and 'status_code' in response_data:
                    print(f"📋 Bright Data response format detected (status: {response_data.get('status_code')})")
                    html_content = response_data['body']
                    
                    # Extract URLs from the HTML body
                    extracted_urls = self._extract_urls_from_html(html_content)
                    
                    # Format URLs into search results structure
                    formatted_search_results = [{'link': url} for url in extracted_urls]
                    
                    result = {
                        'source': source_name,
                        'query': query,
                        'target_url': search_url,
                        'status_code': response_data.get('status_code', response.status_code),
                        'response_length': len(html_content),
                        'search_results': formatted_search_results,
                        'full_response': response_data,  # Store complete response
                        'results_count': len(formatted_search_results),
                        'success': True,
                        'is_json': True,
                        'parsing_method': 'brightdata_html_extraction'
                    }
                    print(f"✅ Successfully extracted {len(formatted_search_results)} URLs from {source_name} HTML content")
                    return result
                
                # Check for traditional SERP API format  
                search_results_list = []
                if 'organic' in response_data:
                    search_results_list = response_data['organic']
                elif 'results' in response_data:
                    search_results_list = response_data['results']
                elif isinstance(response_data, list):
                    search_results_list = response_data

                result = {
                    'source': source_name,
                    'query': query,
                    'target_url': search_url,
                    'status_code': response.status_code,
                    'response_length': len(response.text),
                    'search_results': search_results_list,
                    'full_response': response_data,
                    'results_count': len(search_results_list),
                    'success': True,
                    'is_json': True,
                    'parsing_method': 'traditional_serp_format'
                }
                print(f"✅ Successfully parsed traditional SERP JSON from {source_name}, found {len(search_results_list)} items")
                return result
                
            except json.JSONDecodeError:
                print(f"⚠️ {source_name}: Response was not valid JSON. Attempting direct HTML parse.")
                html_content = response.text
                extracted_urls_from_html = self._extract_urls_from_html(html_content)
                
                # Format these URLs into a structure that extract_urls_from_search_results expects
                formatted_search_results = [{'link': url} for url in extracted_urls_from_html]

                result = {
                    'source': source_name,
                    'query': query,
                    'target_url': search_url,
                    'status_code': response.status_code,
                    'response_length': len(html_content),
                    'search_results': formatted_search_results,
                    'full_response': html_content,
                    'results_count': len(formatted_search_results),
                    'success': True,
                    'is_json': False,
                    'parsing_method': 'direct_html_fallback'
                }
                print(f"✅ Successfully extracted {len(formatted_search_results)} URLs via direct HTML parsing from {source_name}")
                return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error searching {source_name}: {str(e)}")
            
            # Try to get more detailed error information
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = f"{str(e)} - Response: {e.response.text}"
                except:
                    pass
            
            return {
                'source': source_name,
                'query': query,
                'target_url': search_url,
                'error': error_details,
                'success': False
            }
    
    def _extract_urls_from_html(self, html_content: str) -> List[str]:
        """
        Extracts URLs from Google search results HTML content.
        This handles Google redirect URLs and filters for LinkedIn/Indeed job postings.
        """
        import urllib.parse
        import re
        
        job_urls = []
        
        # Multiple regex patterns to catch different URL formats in Google search results
        url_patterns = [
            # Direct LinkedIn job URLs in href attributes
            r'href="(https://(?:www\.)?linkedin\.com/jobs/view/[^"]*)"',
            
            # LinkedIn URLs in Google redirect format  
            r'url=(https://(?:www\.)?linkedin\.com/jobs/view/[^&"]*)',
            
            # Indeed job URLs in href attributes
            r'href="(https://(?:www\.)?indeed\.com/viewjob[^"]*)"',
            
            # Indeed URLs in Google redirect format
            r'url=(https://(?:www\.)?indeed\.com/viewjob[^&"]*)',
            
            # General pattern for job URLs (backup)
            r'(https://(?:www\.)?(?:linkedin\.com/jobs/view|indeed\.com/viewjob)/[^\s"&<>]*)',
        ]
        
        for pattern in url_patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            for url in matches:
                # URL decode to handle encoded characters
                decoded_url = urllib.parse.unquote(url)
                
                # Clean up common Google redirect artifacts
                if 'linkedin.com/jobs/view' in decoded_url or 'indeed.com/viewjob' in decoded_url:
                    # Remove Google tracking parameters
                    if '&ved=' in decoded_url:
                        decoded_url = decoded_url.split('&ved=')[0]
                    if '&usg=' in decoded_url:
                        decoded_url = decoded_url.split('&usg=')[0]
                    
                    # Ensure HTTPS
                    if decoded_url.startswith('http://'):
                        decoded_url = decoded_url.replace('http://', 'https://')
                    
                    # Add if not already present and is valid job URL
                    if decoded_url not in job_urls and self._is_valid_job_url(decoded_url):
                        job_urls.append(decoded_url)
        
        # Additional extraction for URLs that might be split across lines or escaped
        # Look for LinkedIn job IDs and construct URLs
        linkedin_id_pattern = r'linkedin\.com/jobs/view/([a-zA-Z0-9\-]+(?:-at-[a-zA-Z0-9\-]+)?-?\d+)'
        linkedin_ids = re.findall(linkedin_id_pattern, html_content, re.IGNORECASE)
        
        for job_id in linkedin_ids:
            constructed_url = f"https://www.linkedin.com/jobs/view/{job_id}"
            if constructed_url not in job_urls and self._is_valid_job_url(constructed_url):
                job_urls.append(constructed_url)
        
        # Look for Indeed job IDs
        indeed_id_pattern = r'indeed\.com/viewjob\?jk=([a-f0-9]+)'
        indeed_ids = re.findall(indeed_id_pattern, html_content, re.IGNORECASE)
        
        for job_id in indeed_ids:
            constructed_url = f"https://www.indeed.com/viewjob?jk={job_id}"
            if constructed_url not in job_urls and self._is_valid_job_url(constructed_url):
                job_urls.append(constructed_url)
        
        print(f"      🔍 HTML parsing extracted {len(job_urls)} job URLs from {len(re.findall(r'href=', html_content))} total URLs")
        
        return job_urls
        
    def _is_valid_job_url(self, url: str) -> bool:
        """
        Validates if a URL is a proper job posting URL
        """
        if not url or len(url) < 10:
            return False
            
        # LinkedIn job URLs should contain /jobs/view/ and typically end with a number
        if 'linkedin.com/jobs/view' in url:
            # Should have job ID format (usually ends with numbers)
            return bool(re.search(r'/jobs/view/[\w\-]+-\d+/?$', url))
        
        # Indeed job URLs should contain /viewjob?jk= followed by a job key
        if 'indeed.com/viewjob' in url:
            return 'jk=' in url and bool(re.search(r'jk=[a-f0-9]+', url))
        
        return False
    
    def search_all_sources(self, search_term: str) -> List[Dict]:
        """
        Search for internships across all supported job sites
        
        Args:
            search_term (str): The internship search term
        
        Returns:
            List[Dict]: Results from all sources
        """
        print(f"\n🚀 Starting comprehensive internship search for: '{search_term}'")
        print("=" * 60)
        
        results = []
        
        # Search LinkedIn Jobs
        linkedin_results = self.search_linkedin_jobs(search_term)
        results.append(linkedin_results)
        
        # Search Indeed
        indeed_results = self.search_indeed_jobs(search_term)
        results.append(indeed_results)
        
        print("\n" + "=" * 60)
        print("🎯 Search Summary:")
        
        successful_searches = [r for r in results if r.get('success', False)]
        failed_searches = [r for r in results if not r.get('success', False)]
        
        print(f"✅ Successful searches: {len(successful_searches)}")
        print(f"❌ Failed searches: {len(failed_searches)}")
        
        if failed_searches:
            print("\nFailed sources:")
            for result in failed_searches:
                print(f"  - {result['source']}: {result.get('error', 'Unknown error')}")
        
        return results
    
    def close(self):
        """
        Close the session
        """
        self.session.close()


class BrightDataAccessHandler:
    """
    Handler for Bright Data Access Phase - Navigate to job URLs and extract content
    """
    
    def __init__(self, web_scraping_zone: str = None):
        """
        Initialize the Access handler with API credentials
        
        Args:
            web_scraping_zone: Optional specific zone for web scraping (uses Web Unlocker zone by default)
        """
        self.api_key = os.getenv('BRIGHT_DATA_API_KEY')
        
        # Prioritize Web Unlocker, then Web Zone, then SERP Zone as a last resort
        self.web_zone = (
            web_scraping_zone or
            os.getenv('BRIGHT_DATA_WEB_UNLOCKER_ZONE') or
            os.getenv('BRIGHT_DATA_WEB_ZONE') or
            os.getenv('BRIGHT_DATA_SERP_ZONE')
        )
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', 45))
        
        if not self.api_key or not self.web_zone:
            raise ValueError(
                "Missing required environment variables. "
                "Please set BRIGHT_DATA_API_KEY and either BRIGHT_DATA_WEB_UNLOCKER_ZONE, "
                "BRIGHT_DATA_WEB_ZONE, or BRIGHT_DATA_SERP_ZONE."
            )
        
        # Bright Data Direct API endpoint
        self.api_endpoint = "https://api.brightdata.com/request"
        
        # Session for connection reuse
        self.session = requests.Session()
        
        # Set up headers for Direct API access
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Rate limiting configuration
        self.rate_limit_delay = float(os.getenv('RATE_LIMIT_DELAY', 2.0))
        self.last_request_time = 0
    
    def navigate_to_url(self, url: str, extract_content: bool = True) -> Dict:
        """
        Navigate to a specific URL and extract its content
        
        Args:
            url (str): The URL to navigate to
            extract_content (bool): Whether to extract structured content
        
        Returns:
            Dict: Response containing the page content and metadata
        """
        # Apply rate limiting
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            sleep_time = self.rate_limit_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f}s")
            time.sleep(sleep_time)
        
        print(f"\n🌐 Navigating to: {url}")
        # Request payload for Bright Data Direct API
        payload = {
            "zone": self.web_zone,
            "url": url,
            "format": "raw",  # Get raw HTML content
            "country": "us"
        }
        
        try:
            self.last_request_time = time.time()
            
            print(f"📡 Making request to Bright Data Web API...")
            print(f"🎯 Target URL: {url}")
            print(f"⚙️  Zone: {self.web_zone}")
            
            # Make request to Bright Data Direct API
            response = self.session.post(
                self.api_endpoint,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            # Parse response
            content_type = response.headers.get('content-type', '').lower()
            raw_content = response.text
            
            # Determine if we got HTML content
            is_html = 'html' in content_type or raw_content.strip().startswith('<!DOCTYPE') or '<html' in raw_content[:1000]
            
            result = {
                'url': url,
                'status_code': response.status_code,
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'content_type': content_type,
                'content_length': len(raw_content),
                'is_html': is_html,
                'raw_content': raw_content,
                'headers': dict(response.headers)
            }
            
            # Extract structured content if requested and we have HTML
            if extract_content and is_html:
                extracted_data = self._extract_job_data(url, raw_content)
                result['extracted_data'] = extracted_data
                result['extraction_success'] = extracted_data.get('success', False)
            
            print(f"✅ Successfully accessed {url}")
            print(f"   📄 Content length: {len(raw_content)} characters")
            print(f"   📝 Content type: {content_type}")
            if extract_content and 'extracted_data' in result:
                print(f"   🔍 Extraction success: {result['extraction_success']}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error accessing {url}: {str(e)}")
            
            # Try to get more detailed error information
            error_details = str(e)
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_details = f"{str(e)} - Response: {e.response.text[:500]}"
                except:
                    pass
            
            return {
                'url': url,
                'success': False,
                'error': error_details,
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_job_data(self, url: str, html_content: str) -> Dict:
        """
        Extract structured job data from HTML content
        
        Args:
            url (str): The job URL
            html_content (str): Raw HTML content
        
        Returns:
            Dict: Extracted job data
        """
        try:
            extracted_data = {
                'success': False,
                'url': url,
                'extraction_method': 'regex_patterns',
                'extracted_at': datetime.now().isoformat()
            }
            
            # Determine the site type
            if 'linkedin.com' in url:
                extracted_data.update(self._extract_linkedin_job_data(html_content))
            elif 'indeed.com' in url:
                extracted_data.update(self._extract_indeed_job_data(html_content))
            else:
                extracted_data.update(self._extract_generic_job_data(html_content))
            
            return extracted_data
            
        except Exception as e:
            return {
                'success': False,
                'url': url,
                'error': f"Extraction failed: {str(e)}",
                'extracted_at': datetime.now().isoformat()
            }
    
    def _extract_linkedin_job_data(self, html_content: str) -> Dict:
        """Extract job data from LinkedIn job page"""
        data = {'source': 'LinkedIn'}
        
        # Extract job title
        title_patterns = [
            r'<h1[^>]*class="[^"]*job-title[^"]*"[^>]*>([^<]+)</h1>',
            r'<h1[^>]*>([^<]*(?:intern|internship)[^<]*)</h1>',
            r'"jobTitle"[^:]*:\s*"([^"]*)"',
            r'<title>([^|]*)\s*\|[^<]*LinkedIn</title>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['job_title'] = match.group(1).strip()
                break
        
        # Extract company name
        company_patterns = [
            r'<span[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</span>',
            r'"companyName"[^:]*:\s*"([^"]*)"',
            r'<a[^>]*href="[^"]*company[^"]*"[^>]*>([^<]+)</a>',
            r'<h4[^>]*class="[^"]*company[^"]*"[^>]*>([^<]+)</h4>'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['company'] = match.group(1).strip()
                break
        
        # Extract location
        location_patterns = [
            r'<span[^>]*class="[^"]*location[^"]*"[^>]*>([^<]+)</span>',
            r'"jobLocation"[^:]*:\s*"([^"]*)"',
            r'<div[^>]*class="[^"]*job-criteria[^"]*"[^>]*>.*?location.*?<span[^>]*>([^<]+)</span>',
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                data['location'] = match.group(1).strip()
                break
        
        # Extract job description (first few sentences)
        desc_patterns = [
            r'<div[^>]*class="[^"]*job-description[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*class="[^"]*description[^"]*"[^>]*>(.*?)</div>',
            r'"jobDescription"[^:]*:\s*"([^"]*)"'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                desc_html = match.group(1)
                # Clean up HTML tags and get first 500 chars
                desc_text = re.sub(r'<[^>]+>', ' ', desc_html)
                desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                data['description'] = desc_text[:500] + '...' if len(desc_text) > 500 else desc_text
                break
        
        # Extract job type/employment type
        if re.search(r'\b(intern|internship)\b', html_content, re.IGNORECASE):
            data['job_type'] = 'Internship'
        
        # Success if we got at least title or company
        data['success'] = bool(data.get('job_title') or data.get('company'))
        
        return data
    
    def _extract_indeed_job_data(self, html_content: str) -> Dict:
        """Extract job data from Indeed job page"""
        data = {'source': 'Indeed'}
        
        # Extract job title
        title_patterns = [
            r'<h1[^>]*class="[^"]*jobsearch-JobInfoHeader-title[^"]*"[^>]*>([^<]+)</h1>',
            r'<h1[^>]*>([^<]*(?:intern|internship)[^<]*)</h1>',
            r'"title"[^:]*:\s*"([^"]*)"',
            r'<title>([^|]*)\s*-[^<]*Indeed</title>'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['job_title'] = match.group(1).strip()
                break
        
        # Extract company name
        company_patterns = [
            r'<span[^>]*class="[^"]*companyName[^"]*"[^>]*>([^<]+)</span>',
            r'<a[^>]*data-jk[^>]*>([^<]+)</a>',
            r'"companyName"[^:]*:\s*"([^"]*)"'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['company'] = match.group(1).strip()
                break
        
        # Extract location  
        location_patterns = [
            r'<div[^>]*class="[^"]*companyLocation[^"]*"[^>]*>([^<]+)</div>',
            r'"jobLocation"[^:]*:\s*"([^"]*)"'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['location'] = match.group(1).strip()
                break
        
        # Extract job description
        desc_patterns = [
            r'<div[^>]*class="[^"]*jobsearch-jobDescriptionText[^"]*"[^>]*>(.*?)</div>',
            r'<div[^>]*id="jobDescriptionText"[^>]*>(.*?)</div>'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE | re.DOTALL)
            if match:
                desc_html = match.group(1)
                # Clean up HTML tags and get first 500 chars
                desc_text = re.sub(r'<[^>]+>', ' ', desc_html)
                desc_text = re.sub(r'\s+', ' ', desc_text).strip()
                data['description'] = desc_text[:500] + '...' if len(desc_text) > 500 else desc_text
                break
        
        # Extract job type
        if re.search(r'\b(intern|internship)\b', html_content, re.IGNORECASE):
            data['job_type'] = 'Internship'
        
        # Success if we got at least title or company
        data['success'] = bool(data.get('job_title') or data.get('company'))
        
        return data
    
    def _extract_generic_job_data(self, html_content: str) -> Dict:
        """Extract job data from generic job page"""
        data = {'source': 'Generic'}
        
        # Generic title extraction
        title_patterns = [
            r'<h1[^>]*>([^<]*(?:intern|internship)[^<]*)</h1>',
            r'<title>([^<]*(?:intern|internship)[^<]*)</title>',
            r'"title"[^:]*:\s*"([^"]*(?:intern|internship)[^"]*)"'
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                data['job_title'] = match.group(1).strip()
                break
        
        # Generic description extraction (first paragraph with 'intern')
        desc_patterns = [
            r'<p[^>]*>([^<]*intern[^<]*)</p>',
            r'<div[^>]*>([^<]*intern[^<]*)</div>'
        ]
        
        for pattern in desc_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                desc_text = match.group(1).strip()
                data['description'] = desc_text[:300] + '...' if len(desc_text) > 300 else desc_text
                break
        
        # Extract job type
        if re.search(r'\b(intern|internship)\b', html_content, re.IGNORECASE):
            data['job_type'] = 'Internship'
        
        data['success'] = bool(data.get('job_title'))
        
        return data
    
    def access_multiple_urls(self, urls: List[str], max_urls: int = None, save_results: bool = True) -> List[Dict]:
        """
        Access multiple URLs and extract their content
        
        Args:
            urls (List[str]): List of URLs to access
            max_urls (int): Maximum number of URLs to process
            save_results (bool): Whether to save results to file
        
        Returns:
            List[Dict]: List of access results
        """
        if max_urls and len(urls) > max_urls:
            urls = urls[:max_urls]
            print(f"📊 Limiting access to {max_urls} URLs")
        
        print(f"\n🚀 Access Phase: Navigating to {len(urls)} URLs")
        print("=" * 60)
        
        results = []
        successful_count = 0
        failed_count = 0
        
        for i, url in enumerate(urls, 1):
            print(f"\n📍 Processing {i}/{len(urls)}: {url}")
            
            result = self.navigate_to_url(url, extract_content=True)
            results.append(result)
            
            if result.get('success'):
                successful_count += 1
                if result.get('extraction_success'):
                    extracted = result.get('extracted_data', {})
                    print(f"   ✅ Extracted: {extracted.get('job_title', 'No title')} at {extracted.get('company', 'No company')}")
                else:
                    print(f"   ⚠️  Content accessed but extraction failed")
            else:
                failed_count += 1
                print(f"   ❌ Access failed: {result.get('error', 'Unknown error')}")
        
        print("\n" + "=" * 60)
        print(f"🎯 Access Phase Summary:")
        print(f"   🌐 URLs processed: {len(urls)}")
        print(f"   ✅ Successful accesses: {successful_count}")
        print(f"   ❌ Failed accesses: {failed_count}")
        print(f"   📈 Success rate: {successful_count/len(urls)*100:.1f}%")
        
        # Count successful extractions
        successful_extractions = sum(1 for r in results if r.get('extraction_success'))
        print(f"   🔍 Successful extractions: {successful_extractions}")
        print(f"   📊 Extraction rate: {successful_extractions/successful_count*100:.1f}% of successful accesses" if successful_count > 0 else "")
        
        # Save results if requested
        if save_results:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"access_results_{timestamp}.json"
            
            save_data = {
                'phase': 'access',
                'timestamp': datetime.now().isoformat(),
                'summary': {
                    'total_urls': len(urls),
                    'successful_accesses': successful_count,
                    'failed_accesses': failed_count,
                    'successful_extractions': successful_extractions,
                    'success_rate': successful_count/len(urls)*100,
                    'extraction_rate': successful_extractions/successful_count*100 if successful_count > 0 else 0
                },
                'results': results
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {filename}")
        
        return results
    
    def close(self):
        """Close the session"""
        self.session.close()


# Alias for backward compatibility and new main.py
BrightDataHandler = BrightDataSERPHandler


def test_connection():
    """
    Test function to verify Bright Data SERP API connection
    """
    try:
        handler = BrightDataSERPHandler()
        print("✅ BrightDataSERPHandler initialized successfully")
        print(f"📊 Configuration:")
        print(f"  - API Key: {'*' * 20}{handler.api_key[-4:] if len(handler.api_key) > 4 else '****'}")
        print(f"  - SERP Zone: {handler.serp_zone}")
        print(f"  - Timeout: {handler.timeout}s")
        print(f"  - Max Results: {handler.max_results}")
        print(f"  - API Endpoint: {handler.api_endpoint}")
        return True
    except Exception as e:
        print(f"❌ Failed to initialize BrightDataSERPHandler: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the handler
    test_connection()
