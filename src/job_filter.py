"""
Job Filtering Module for AI Internship Opportunity Finder
Inspired by LinkedIn Job Scraper's filtering approach
Filters jobs based on configurable criteria to remove irrelevant postings
"""

import re
from typing import Dict, List, Tuple
from config import FILTERING_CONFIG
import logging

logger = logging.getLogger(__name__)


class JobFilter:
    """
    Filters job postings based on configurable criteria
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize job filter with configuration
        
        Args:
            config (Dict): Filtering configuration, defaults to FILTERING_CONFIG
        """
        self.config = config or FILTERING_CONFIG
        
        # Compile regex patterns for better performance
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for filtering"""
        # Title include patterns (job must match at least one)
        self.title_include_patterns = [
            re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            for keyword in self.config.get('title_include', [])
        ]
        
        # Title exclude patterns (job fails if matches any)
        self.title_exclude_patterns = [
            re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            for keyword in self.config.get('title_exclude', [])
        ]
        
        # Description exclude patterns
        self.description_exclude_patterns = [
            re.compile(keyword, re.IGNORECASE)
            for keyword in self.config.get('description_exclude', [])
        ]
        
        # Software keyword patterns
        self.software_patterns = [
            re.compile(rf'\b{re.escape(keyword)}\b', re.IGNORECASE)
            for keyword in self.config.get('software_keywords', [])
        ]
    
    def filter_job(self, job_data: Dict) -> Tuple[bool, str]:
        """
        Filter a single job posting
        
        Args:
            job_data (Dict): Job data to filter
        
        Returns:
            Tuple[bool, str]: (passes_filter, reason_if_rejected)
        """
        title = job_data.get('job_title', '') or ''
        description = job_data.get('description', '') or ''
        company = job_data.get('company', '') or ''
        location = job_data.get('location', '') or ''
        
        # Filter 1: Check if title contains required internship keywords
        if not self._title_contains_internship_keywords(title):
            return False, "Title doesn't contain internship keywords"
        
        # Filter 2: Check for excluded title keywords
        if self._title_contains_excluded_keywords(title):
            excluded_keyword = self._get_excluded_title_keyword(title)
            return False, f"Title contains excluded keyword: {excluded_keyword}"
        
        # Filter 3: Check for excluded companies
        if self._is_excluded_company(company):
            return False, f"Company is in exclusion list: {company}"
        
        # Filter 4: Check for excluded description keywords
        if self._description_contains_excluded_keywords(description):
            excluded_keyword = self._get_excluded_description_keyword(description)
            return False, f"Description contains excluded keyword: {excluded_keyword}"
        
        # Filter 5: Check minimum description length
        if len(description) < self.config.get('min_description_length', 100):
            return False, f"Description too short: {len(description)} characters"
        
        # Filter 6: Check for software-related keywords (for software internships)
        if not self._contains_software_keywords(title + ' ' + description):
            return False, "No software-related keywords found"
        
        # Filter 7: Language detection (basic check for English)
        if not self._is_english_content(description):
            return False, "Content not in English"
        
        # All filters passed
        return True, "Passed all filters"
    
    def _title_contains_internship_keywords(self, title: str) -> bool:
        """Check if title contains at least one internship keyword"""
        if not self.title_include_patterns:
            return True  # No filtering if no patterns defined
        
        return any(pattern.search(title) for pattern in self.title_include_patterns)
    
    def _title_contains_excluded_keywords(self, title: str) -> bool:
        """Check if title contains any excluded keywords"""
        return any(pattern.search(title) for pattern in self.title_exclude_patterns)
    
    def _get_excluded_title_keyword(self, title: str) -> str:
        """Get the first excluded keyword found in title"""
        for pattern in self.title_exclude_patterns:
            match = pattern.search(title)
            if match:
                return match.group(0)
        return ""
    
    def _description_contains_excluded_keywords(self, description: str) -> bool:
        """Check if description contains any excluded keywords"""
        return any(pattern.search(description) for pattern in self.description_exclude_patterns)
    
    def _get_excluded_description_keyword(self, description: str) -> str:
        """Get the first excluded keyword found in description"""
        for pattern in self.description_exclude_patterns:
            match = pattern.search(description)
            if match:
                return match.group(0)
        return ""
    
    def _is_excluded_company(self, company: str) -> bool:
        """Check if company is in exclusion list"""
        excluded_companies = self.config.get('company_exclude', [])
        company_lower = company.lower()
        
        return any(
            excluded.lower() in company_lower or company_lower in excluded.lower()
            for excluded in excluded_companies
        )
    
    def _contains_software_keywords(self, text: str) -> bool:
        """Check if text contains software-related keywords"""
        if not self.software_patterns:
            return True  # No filtering if no patterns defined
        
        return any(pattern.search(text) for pattern in self.software_patterns)
    
    def _is_english_content(self, text: str) -> bool:
        """Basic check if content is in English"""
        # Simple heuristic: check for common English words
        english_indicators = [
            'the', 'and', 'or', 'to', 'of', 'in', 'for', 'with', 'as', 'you', 'we', 'our'
        ]
        
        text_lower = text.lower()
        english_word_count = sum(1 for word in english_indicators if f' {word} ' in text_lower)
        
        # If we find at least 3 common English words, consider it English
        return english_word_count >= 3
    
    def filter_job_batch(self, jobs: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filter a batch of jobs
        
        Args:
            jobs (List[Dict]): List of job data dictionaries
        
        Returns:
            Tuple[List[Dict], List[Dict]]: (passed_jobs, rejected_jobs_with_reasons)
        """
        passed_jobs = []
        rejected_jobs = []
        
        for job in jobs:
            passes_filter, reason = self.filter_job(job)
            
            if passes_filter:
                passed_jobs.append(job)
                logger.debug(f"Job passed: {job.get('job_title', 'Unknown')} at {job.get('company', 'Unknown')}")
            else:
                job['rejection_reason'] = reason
                rejected_jobs.append(job)
                logger.debug(f"Job rejected: {job.get('job_title', 'Unknown')} - {reason}")
        
        logger.info(f"Filtered {len(jobs)} jobs: {len(passed_jobs)} passed, {len(rejected_jobs)} rejected")
        return passed_jobs, rejected_jobs
    
    def get_filter_stats(self, rejected_jobs: List[Dict]) -> Dict:
        """
        Get statistics about why jobs were rejected
        
        Args:
            rejected_jobs (List[Dict]): List of rejected jobs with reasons
        
        Returns:
            Dict: Statistics about rejection reasons
        """
        rejection_counts = {}
        
        for job in rejected_jobs:
            reason = job.get('rejection_reason', 'Unknown')
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
        
        return {
            'total_rejected': len(rejected_jobs),
            'rejection_reasons': rejection_counts,
            'most_common_reason': max(rejection_counts.items(), key=lambda x: x[1])[0] if rejection_counts else None
        }
    
    def update_config(self, new_config: Dict):
        """
        Update filtering configuration
        
        Args:
            new_config (Dict): New configuration to merge
        """
        self.config.update(new_config)
        self._compile_patterns()
        logger.info("Filter configuration updated")


class LocationFilter:
    """
    Specialized filter for location-based filtering
    """
    
    def __init__(self, preferred_locations: List[str] = None):
        """
        Initialize location filter
        
        Args:
            preferred_locations (List[str]): List of preferred locations
        """
        self.preferred_locations = [loc.lower() for loc in (preferred_locations or [])]
    
    def is_preferred_location(self, location: str) -> bool:
        """
        Check if location matches preferences
        
        Args:
            location (str): Job location
        
        Returns:
            bool: True if location is preferred or no preferences set
        """
        if not self.preferred_locations:
            return True  # No location filtering if no preferences
        
        if not location:
            return False
        
        location_lower = location.lower()
        
        # Check for exact matches or partial matches
        return any(
            pref in location_lower or location_lower in pref
            for pref in self.preferred_locations
        ) or 'remote' in location_lower  # Always include remote jobs


def test_job_filter():
    """Test job filtering functionality"""
    filter_engine = JobFilter()
    
    # Test jobs
    test_jobs = [
        {
            'job_title': 'Software Engineering Intern - Summer 2025',
            'company': 'Good Company',
            'description': 'We are looking for a software engineering intern to join our team. You will work with Python, JavaScript, and React to build amazing applications.',
            'location': 'San Francisco, CA'
        },
        {
            'job_title': 'Senior Software Engineer',
            'company': 'Another Company',
            'description': 'Senior position requiring 5+ years of experience in software development.',
            'location': 'New York, NY'
        },
        {
            'job_title': 'Clinical Research Internship',
            'company': 'Medical Corp',
            'description': 'Internship in clinical research for medical devices. Healthcare experience required.',
            'location': 'Boston, MA'
        },
        {
            'job_title': 'Data Science Intern',
            'company': 'Tech Startup',
            'description': 'Short desc',  # Too short
            'location': 'Remote'
        }
    ]
    
    # Filter jobs
    passed, rejected = filter_engine.filter_job_batch(test_jobs)
    
    print(f"Passed jobs: {len(passed)}")
    for job in passed:
        print(f"  - {job['job_title']} at {job['company']}")
    
    print(f"\nRejected jobs: {len(rejected)}")
    for job in rejected:
        print(f"  - {job['job_title']}: {job['rejection_reason']}")
    
    # Get filter stats
    stats = filter_engine.get_filter_stats(rejected)
    print(f"\nFilter statistics: {stats}")


if __name__ == "__main__":
    test_job_filter() 