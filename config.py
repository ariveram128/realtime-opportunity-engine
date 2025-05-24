"""
Configuration settings for AI Internship Opportunity Finder
Enhanced with advanced filtering and job management capabilities
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bright Data API Configuration
BRIGHT_DATA_API_KEY = os.getenv('BRIGHT_DATA_API_KEY')
BRIGHT_DATA_SERP_ZONE = os.getenv('BRIGHT_DATA_SERP_ZONE')
BRIGHT_DATA_WEB_ZONE = os.getenv('BRIGHT_DATA_WEB_ZONE')  # For Access Phase web scraping
BRIGHT_DATA_WEB_UNLOCKER_ZONE = os.getenv('BRIGHT_DATA_WEB_UNLOCKER_ZONE') # For Access Phase Web Unlocker
REQUEST_TIMEOUT = int(os.getenv('REQUEST_TIMEOUT', 30))
RATE_LIMIT_DELAY = float(os.getenv('RATE_LIMIT_DELAY', 2.0))  # Access Phase rate limiting

# Database Configuration
DATABASE_CONFIG = {
    'db_path': 'internship_opportunities.db',
    'jobs_table': 'job_postings',
    'filtered_jobs_table': 'filtered_jobs'
}

# Search Configuration
SEARCH_CONFIG = {
    'max_jobs_per_search': 50,
    'max_pages_per_source': 3,
    'search_delay': 1,  # seconds between requests
    'days_to_scrape': 30,  # only get jobs posted in last 30 days
}

# Job Filtering Configuration
FILTERING_CONFIG = {
    # Keywords that MUST be present in job title (at least one)
    'title_include': [
        'intern', 'internship', 'co-op', 'coop', 'summer', 'student',
        'trainee', 'graduate program', 'entry level'
    ],
    
    # Keywords that will EXCLUDE jobs if found in title
    'title_exclude': [
        'senior', 'principal', 'lead', 'manager', 'director', 'head of',
        'vp ', 'vice president', 'chief', 'architect', 'staff engineer',
        'clinical', 'medical', 'nurse', 'doctor', 'pharmacy', 'healthcare'
    ],
    
    # Keywords that will EXCLUDE jobs if found in description
    'description_exclude': [
        'security clearance required', 'top secret clearance', 'must be citizen',
        'clinical trial', 'medical device', 'pharmaceutical', 'healthcare',
        'minimum 5 years', 'minimum 3 years', 'senior level', 'expert level'
    ],
    
    # Companies to exclude (add companies you don't want to work for)
    'company_exclude': [
        'pyramid scheme inc', 'bad company ltd'  # Example entries
    ],
    
    # Required keywords for specific internship types
    'software_keywords': [
        'software', 'programming', 'development', 'engineer', 'developer',
        'coding', 'computer science', 'python', 'java', 'javascript', 'react',
        'frontend', 'backend', 'full stack', 'web development', 'mobile',
        'ios', 'android', 'data science', 'machine learning', 'ai'
    ],
    
    # Language filter (jobs must be in these languages)
    'languages': ['en'],  # English only
    
    # Location preferences
    'preferred_locations': [
        'remote', 'san francisco', 'new york', 'seattle', 'austin', 'boston'
    ],
    
    # Minimum job description length (filter out low-quality posts)
    'min_description_length': 100
}

# Web Interface Configuration
WEB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5000,
    'debug': True,
    'jobs_per_page': 20,
    'auto_refresh_minutes': 30
}

# Job Status Configuration
JOB_STATUS = {
    'new': 'New',
    'interested': 'Interested', 
    'applied': 'Applied',
    'interview': 'Interview',
    'rejected': 'Rejected',
    'hidden': 'Hidden',
    'not_interested': 'Not Interested'
}

# Search Queries Configuration
DEFAULT_SEARCH_QUERIES = [
    {
        'keywords': 'software engineering internship',
        'location': 'United States',
        'additional_terms': ['summer 2025', 'fall 2024', 'spring 2025']
    },
    {
        'keywords': 'data science internship',
        'location': 'United States',
        'additional_terms': ['machine learning', 'analytics', 'python']
    },
    {
        'keywords': 'computer science internship',
        'location': 'United States',
        'additional_terms': ['programming', 'development', 'tech']
    }
]

# OpenAI Configuration (optional, for future AI features)
OPENAI_CONFIG = {
    'api_key': os.getenv('OPENAI_API_KEY'),
    'model': 'gpt-4',
    'max_tokens': 1000
}

# Logging Configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'log_file': 'internship_finder.log'
}

# Target Job Sites
JOB_SITES = {
    'linkedin': 'linkedin.com/jobs',
    'indeed': 'indeed.com'
}

# Search Configuration
SEARCH_KEYWORDS = {
    'general': ['internship', 'intern', 'student', 'entry level'],
    'software': ['software', 'engineering', 'developer', 'programming', 'coding', 'tech'],
    'data': ['data', 'analytics', 'science', 'machine learning', 'AI'],
    'business': ['business', 'finance', 'consulting', 'marketing', 'sales'],
    'design': ['design', 'UX', 'UI', 'creative', 'graphic'],
    'research': ['research', 'lab', 'academic', 'scientific']
}

# Output Configuration
OUTPUT_DIR = 'search_results'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# User Agent for requests
DEFAULT_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

# Rate limiting
REQUESTS_PER_MINUTE = int(os.getenv('REQUESTS_PER_MINUTE', 10))
DELAY_BETWEEN_REQUESTS = 60 / REQUESTS_PER_MINUTE  # seconds

# Validation
def validate_config():
    """
    Validate that all required configuration is present
    
    Returns:
        bool: True if config is valid, False otherwise
    """
    missing_vars = []
    
    if not BRIGHT_DATA_API_KEY:
        missing_vars.append('BRIGHT_DATA_API_KEY')
    
    if not BRIGHT_DATA_SERP_ZONE:
        missing_vars.append('BRIGHT_DATA_SERP_ZONE')
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please create a .env file with the following variables:")
        for var in missing_vars:
            print(f"  {var}=your_value_here")
        return False
    
    return True


def get_search_keywords_for_term(search_term):
    """
    Get relevant keywords based on the search term
    
    Args:
        search_term (str): The search term to analyze
    
    Returns:
        list: List of relevant keywords
    """
    term_lower = search_term.lower()
    relevant_keywords = SEARCH_KEYWORDS['general'].copy()
    
    for category, keywords in SEARCH_KEYWORDS.items():
        if category == 'general':
            continue
        
        if any(keyword in term_lower for keyword in keywords):
            relevant_keywords.extend(keywords)
    
    return list(set(relevant_keywords))  # Remove duplicates
