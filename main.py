"""
Enhanced Main Entry Point for AI Internship Opportunity Finder
Integrates: Discovery → Extraction → Filtering → Database Storage
"""

import json
import sys
import argparse
import os
from datetime import datetime
from typing import List, Dict
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import our components
from brightdata_handler import BrightDataSERPHandler, test_connection
from database_manager import DatabaseManager
from job_filter import JobFilter
from config import validate_config, SEARCH_CONFIG, FILTERING_CONFIG


def extract_urls_from_search_results(search_results: List[Dict], target_domain: str) -> List[str]:
    """
    Extract job URLs from search results
    
    Args:
        search_results: List of search result dictionaries
        target_domain: Domain to filter for (e.g., "linkedin.com", "indeed.com")
    
    Returns:
        List of valid job URLs
    """
    urls = []
    
    for result in search_results:
        # Extract URL from search result
        url = result.get('url') or result.get('link')
        if url and target_domain in url and is_job_listing_url(url):
            urls.append(url)
        
        # Also check in title links if available
        if 'title_link' in result:
            title_url = result['title_link']
            if title_url and target_domain in title_url and is_job_listing_url(title_url):
                urls.append(title_url)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def is_job_listing_url(url: str) -> bool:
    """
    Check if a URL appears to be a job listing page
    
    Args:
        url (str): URL to check
    
    Returns:
        bool: True if it looks like a job listing URL
    """
    url_lower = url.lower()
    
    # Filter out obvious non-job URLs first
    invalid_patterns = [
        '/search?', 'google.com', 'ved=', 'udm=', 'fbs=', 'sca_esv=', 'ictx=',
        '/help/', '/about/', '/privacy/', '/terms/'
    ]
    
    if any(pattern in url_lower for pattern in invalid_patterns):
        return False
    
    # LinkedIn job listing patterns
    if 'linkedin.com' in url_lower:
        if '/jobs/view/' in url_lower and any(char.isdigit() for char in url_lower.split('/')[-1]):
            return True
        if '/jobs/' in url_lower and any(char.isdigit() for char in url_lower):
            excluded_patterns = ['/jobs/data-science-intern-jobs', '/jobs/search', '/jobs/collections', '/jobs/internship-jobs']
            if not any(pattern in url_lower for pattern in excluded_patterns):
                return True
        return False
    
    # Indeed job listing patterns
    elif 'indeed.com' in url_lower:
        if '/viewjob' in url_lower and 'jk=' in url_lower:
            return True
        excluded_patterns = ['/q-', '/jobs.html', '/career-advice', '/salaries/', '/companies/']
        if any(pattern in url_lower for pattern in excluded_patterns):
            return False
        return False
    
    return False


def discovery_phase(search_term: str, max_results: int = None) -> Dict:
    """
    Phase 1: Discover job listing URLs using SERP API
    
    Args:
        search_term: The internship search term
        max_results: Maximum results to collect
    
    Returns:
        Dict containing discovered URLs and metadata
    """
    print("🔍 Phase 1: Job URL Discovery")
    print("=" * 50)
    
    # Test connection first
    if not test_connection():
        logger.error("Failed to connect to Bright Data SERP API")
        return {'success': False, 'error': 'Connection failed'}
    
    print(f"🎯 Searching for: '{search_term}'")
    if max_results:
        print(f"📊 Max results per source: {max_results}")
    
    # Initialize handler and perform search
    handler = BrightDataSERPHandler()
    results = handler.search_all_sources(search_term)
    handler.close()
    
    # Extract URLs from results
    discovered_urls = {}
    total_urls = 0
    
    for result in results:
        if result.get('success', False):
            source_name = result['source']
            target_domain = 'linkedin.com' if 'linkedin' in source_name.lower() else 'indeed.com'
            
            # Extract from search results if available
            search_results = result.get('search_results', [])
            if search_results:
                urls = extract_urls_from_search_results(search_results, target_domain)
            else:
                # For now, return empty list if no search results
                # In future, could implement HTML parsing fallback
                urls = []
            
            discovered_urls[source_name] = urls[:max_results] if max_results else urls
            total_urls += len(discovered_urls[source_name])
            
            print(f"✅ {source_name}: Found {len(discovered_urls[source_name])} URLs")

            # Save raw response for debugging if it's the first one
            if results.index(result) == 0 and result.get('full_response'): # Save only the first one
                debug_filename = f"debug_serp_response_{source_name.replace(' ', '_')}.json"
                try:
                    with open(debug_filename, 'w', encoding='utf-8') as f_debug:
                        json.dump(result['full_response'], f_debug, indent=2)
                    print(f"🔍 Saved raw SERP response (JSON) for {source_name} to {debug_filename}")
                except TypeError: # If full_response is not JSON serializable (e.g. already a string/HTML)
                    with open(debug_filename.replace('.json','.txt'), 'w', encoding='utf-8') as f_debug:
                        f_debug.write(str(result['full_response']))
                    print(f"🔍 Saved raw SERP response (TEXT) for {source_name} to {debug_filename.replace('.json','.txt')}")

        elif not result.get('success'): # Check if search itself failed
            print(f"❌ {source_name}: Search failed.")
            if result.get('error'):
                print(f"❌ Error: {result['error']}")
        else: # Success was true, but no URLs found in discovered_urls[source_name]
            print(f"🟡 {source_name}: Search successful, but no relevant URLs extracted.")
            if result.get('results_count', 0) == 0 and result.get('error'): # e.g. HTML fallback disabled
                 print(f"💭 Note: {result['error']}")
            elif result.get('results_count', 0) == 0:
                 print(f"💭 Note: The search returned 0 results from the API or post-processing.")
    
    discovery_data = {
        'success': True,
        'search_term': search_term,
        'timestamp': datetime.now().isoformat(),
        'discovered_urls': discovered_urls,
        'total_urls': total_urls,
        'raw_results': results
    }
    
    print(f"\n📊 Discovery Summary:")
    print(f"   🔗 Total URLs discovered: {total_urls}")
    print(f"   📅 Timestamp: {discovery_data['timestamp']}")
    
    return discovery_data


def extraction_phase(urls: List[str], max_jobs: int = None) -> List[Dict]:
    """
    Phase 2: Extract structured job data from URLs
    
    Args:
        urls: List of job URLs to extract data from
        max_jobs: Maximum number of jobs to extract
    
    Returns:
        List of extracted job data dictionaries
    """
    print(f"\n🔧 Phase 2: Job Data Extraction")
    print("=" * 50)
    
    # Limit URLs if specified
    if max_jobs and len(urls) > max_jobs:
        urls = urls[:max_jobs]
        print(f"📊 Limiting extraction to {max_jobs} jobs")
    
    print(f"🎯 Extracting data from {len(urls)} URLs")
    
    # Import data extractor
    try:
        from data_extractor import JobDataExtractor
        extractor = JobDataExtractor()
        job_data_list = extractor.extract_multiple_jobs(urls, max_jobs or len(urls))
        extractor.close()
        
        successful_extractions = [job for job in job_data_list if job.get('success', False)]
        failed_extractions = [job for job in job_data_list if not job.get('success', False)]
        
        print(f"\n📊 Extraction Summary:")
        print(f"   ✅ Successful: {len(successful_extractions)}")
        print(f"   ❌ Failed: {len(failed_extractions)}")
        print(f"   📈 Success rate: {len(successful_extractions)/len(job_data_list)*100:.1f}%")
        
        return job_data_list
        
    except ImportError:
        print("⚠️  Data extractor not available, creating mock data for testing")
        # Create mock job data for testing when extractor is not available
        mock_jobs = []
        for i, url in enumerate(urls[:5]):  # Create 5 mock jobs
            mock_job = {
                'success': True,
                'url': url,
                'source': 'LinkedIn' if 'linkedin.com' in url else 'Indeed',
                'job_title': f'Software Engineering Intern {i+1}',
                'company': f'Tech Company {i+1}',
                'location': 'San Francisco, CA',
                'job_type': 'Internship',
                'description': 'Exciting internship opportunity for software engineering students...',
                'extraction_metadata': {
                    'extracted_at': datetime.now().isoformat(),
                    'content_length': 1500
                }
            }
            mock_jobs.append(mock_job)
        
        print(f"📋 Created {len(mock_jobs)} mock job entries for testing")
        return mock_jobs


def filtering_phase(job_data_list: List[Dict]) -> tuple:
    """
    Phase 3: Filter jobs using intelligent criteria
    
    Args:
        job_data_list: List of extracted job data
    
    Returns:
        Tuple of (passed_jobs, rejected_jobs)
    """
    print(f"\n🎯 Phase 3: Intelligent Job Filtering")
    print("=" * 50)
    
    # Initialize filter
    job_filter = JobFilter(FILTERING_CONFIG)
    
    # Extract only successful jobs for filtering
    successful_jobs = [job for job in job_data_list if job.get('success', False)]
    
    if not successful_jobs:
        print("⚠️  No successful job extractions to filter")
        return [], []
    
    print(f"🔍 Filtering {len(successful_jobs)} extracted jobs")
    
    # Apply filtering
    passed_jobs, rejected_jobs = job_filter.filter_job_batch(successful_jobs)
    
    # Get filter statistics
    filter_stats = job_filter.get_filter_stats(rejected_jobs)
    
    print(f"\n📊 Filtering Summary:")
    print(f"   ✅ Passed: {len(passed_jobs)}")
    print(f"   ❌ Rejected: {len(rejected_jobs)}")
    print(f"   📈 Pass rate: {len(passed_jobs)/len(successful_jobs)*100:.1f}%")
    
    if filter_stats['rejection_reasons']:
        print(f"\n🔍 Top Rejection Reasons:")
        for reason, count in list(filter_stats['rejection_reasons'].items())[:5]:
            print(f"   • {reason}: {count}")
    
    return passed_jobs, rejected_jobs


def storage_phase(passed_jobs: List[Dict]) -> Dict:
    """
    Phase 4: Store filtered jobs in database
    
    Args:
        passed_jobs: List of jobs that passed filtering
    
    Returns:
        Dict with storage statistics
    """
    print(f"\n💾 Phase 4: Database Storage")
    print("=" * 50)
    
    if not passed_jobs:
        print("⚠️  No jobs to store")
        return {'stored': 0, 'duplicates': 0, 'errors': 0}
    
    # Initialize database manager
    db = DatabaseManager()
    
    stored_count = 0
    duplicate_count = 0
    error_count = 0
    
    print(f"💿 Storing {len(passed_jobs)} filtered jobs")
    
    for job in passed_jobs:
        try:
            if db.insert_job(job):
                stored_count += 1
            else:
                duplicate_count += 1
        except Exception as e:
            logger.error(f"Error storing job: {e}")
            error_count += 1
    
    storage_stats = {
        'stored': stored_count,
        'duplicates': duplicate_count,
        'errors': error_count,
        'total_processed': len(passed_jobs)
    }
    
    print(f"\n📊 Storage Summary:")
    print(f"   💾 Stored: {stored_count}")
    print(f"   🔄 Duplicates: {duplicate_count}")
    print(f"   ❌ Errors: {error_count}")
    
    # Get updated database stats
    db_stats = db.get_job_stats()
    print(f"   📈 Total jobs in database: {db_stats.get('total_jobs', 0)}")
    
    return storage_stats


def run_full_pipeline(search_term: str, max_results: int = None, max_jobs: int = None, skip_filtering: bool = False) -> Dict:
    """
    Run the complete job discovery pipeline
    
    Args:
        search_term: Search term for job discovery
        max_results: Maximum results per source in discovery
        max_jobs: Maximum jobs to process in extraction
        skip_filtering: Skip the filtering phase
    
    Returns:
        Dict with pipeline results and statistics
    """
    print("🚀 AI Internship Opportunity Finder - Full Pipeline")
    print("=" * 60)
    print(f"🎯 Search Term: '{search_term}'")
    if max_results:
        print(f"📊 Max Results per Source: {max_results}")
    if max_jobs:
        print(f"🔧 Max Jobs to Extract: {max_jobs}")
    if skip_filtering:
        print("⚠️  Filtering will be skipped")
    print()
    
    pipeline_start = datetime.now()
    
    # Phase 1: Discovery
    discovery_result = discovery_phase(search_term, max_results)
    if not discovery_result.get('success'):
        return discovery_result
    
    # Collect all URLs
    all_urls = []
    for source_urls in discovery_result['discovered_urls'].values():
        all_urls.extend(source_urls)
    
    if not all_urls:
        return {'success': False, 'error': 'No URLs discovered'}
    
    # Phase 2: Extraction
    job_data_list = extraction_phase(all_urls, max_jobs)
    
    if skip_filtering:
        # Skip filtering, store all successful extractions
        successful_jobs = [job for job in job_data_list if job.get('success', False)]
        storage_stats = storage_phase(successful_jobs)
        passed_jobs = successful_jobs
        rejected_jobs = []
    else:
        # Phase 3: Filtering
        passed_jobs, rejected_jobs = filtering_phase(job_data_list)
        
        # Phase 4: Storage
        storage_stats = storage_phase(passed_jobs)
    
    pipeline_end = datetime.now()
    duration = (pipeline_end - pipeline_start).total_seconds()
    
    # Final summary
    print(f"\n🎉 Pipeline Complete!")
    print("=" * 60)
    print(f"⏱️  Total Duration: {duration:.1f} seconds")
    print(f"🔗 URLs Discovered: {discovery_result['total_urls']}")
    print(f"🔧 Jobs Extracted: {len([j for j in job_data_list if j.get('success')])}")
    if not skip_filtering:
        print(f"🎯 Jobs Passed Filter: {len(passed_jobs)}")
        print(f"❌ Jobs Rejected: {len(rejected_jobs)}")
    print(f"💾 Jobs Stored: {storage_stats['stored']}")
    print(f"🔄 Duplicates Skipped: {storage_stats['duplicates']}")
    
    return {
        'success': True,
        'search_term': search_term,
        'duration': duration,
        'discovery': discovery_result,
        'extraction_count': len([j for j in job_data_list if j.get('success')]),
        'filtering': {
            'passed': len(passed_jobs),
            'rejected': len(rejected_jobs)
        } if not skip_filtering else None,
        'storage': storage_stats
    }


def main():
    """
    Main entry point with enhanced argument parsing
    """
    parser = argparse.ArgumentParser(
        description="AI Internship Opportunity Finder - Enhanced Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "software engineering internship"
  %(prog)s "data science intern" --max-results 30 --max-jobs 15
  %(prog)s "ML internship" --skip-filtering
  %(prog)s --web
  %(prog)s --test-db
        """
    )
    
    parser.add_argument('search_term', nargs='?', help='Search term for internships')
    parser.add_argument('--max-results', type=int, default=SEARCH_CONFIG.get('max_jobs_per_search', 50),
                        help='Maximum results per source (default: 50)')
    parser.add_argument('--max-jobs', type=int, default=20,
                        help='Maximum jobs to extract (default: 20)')
    parser.add_argument('--skip-filtering', action='store_true',
                        help='Skip job filtering phase')
    parser.add_argument('--web', action='store_true',
                        help='Start web interface')
    parser.add_argument('--test-db', action='store_true',
                        help='Test database functionality')
    parser.add_argument('--test-filter', action='store_true',
                        help='Test job filtering functionality')
    parser.add_argument('--interactive', action='store_true',
                        help='Run in interactive mode')
    
    args = parser.parse_args()
    
    # Validate configuration
    if not validate_config():
        sys.exit(1)
    
    # Handle special modes
    if args.web:
        print("🌐 Starting web interface...")
        try:
            from app import app
            from config import WEB_CONFIG
            app.run(host=WEB_CONFIG['host'], port=WEB_CONFIG['port'], debug=WEB_CONFIG['debug'])
        except ImportError:
            print("❌ Web interface dependencies not available")
            sys.exit(1)
    
    elif args.test_db:
        print("🧪 Testing database functionality...")
        from database_manager import test_database
        test_database()
    
    elif args.test_filter:
        print("🧪 Testing job filtering functionality...")
        from job_filter import test_job_filter
        test_job_filter()
    
    elif args.interactive:
        print("🎮 Interactive mode not yet implemented")
        print("💡 Use --web for web interface or provide a search term")
    
    elif args.search_term:
        # Run full pipeline
        result = run_full_pipeline(
            search_term=args.search_term,
            max_results=args.max_results,
            max_jobs=args.max_jobs,
            skip_filtering=args.skip_filtering
        )
        
        if result.get('success'):
            print(f"\n✨ Run 'python app.py' to view results in web interface")
        else:
            print(f"\n❌ Pipeline failed: {result.get('error', 'Unknown error')}")
            sys.exit(1)
    
    else:
        parser.print_help()
        print(f"\n💡 Quick start: {parser.prog} \"software engineering internship\"")


if __name__ == "__main__":
    main()
