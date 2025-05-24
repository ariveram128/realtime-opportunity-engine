#!/usr/bin/env python3
"""
Test script for Access Phase - Navigate to discovered job URLs and extract content
"""

import json
import sys
import os
from datetime import datetime
import argparse
from pathlib import Path

# Import our handlers
from brightdata_handler import BrightDataAccessHandler, test_connection


def load_discovery_results(filename: str = None) -> dict:
    """
    Load discovery results from JSON file
    
    Args:
        filename: Specific file to load (or find the most recent)
    
    Returns:
        Dict containing discovery results
    """
    if filename:
        if not os.path.exists(filename):
            raise FileNotFoundError(f"Discovery results file not found: {filename}")
        
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # Find the most recent discovery results file
    discovery_files = list(Path('.').glob('discovery_results_*.json'))
    
    if not discovery_files:
        raise FileNotFoundError(
            "No discovery results files found. Please run discovery phase first or specify a file."
        )
    
    # Sort by modification time and get the most recent
    latest_file = max(discovery_files, key=lambda p: p.stat().st_mtime)
    print(f"📂 Loading discovery results from: {latest_file}")
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_urls_from_discovery(discovery_data: dict) -> list:
    """
    Extract all URLs from discovery data
    
    Args:
        discovery_data: Discovery results data
    
    Returns:
        List of URLs to access
    """
    urls = []
    
    # Check if discovery data has the expected structure
    if 'analysis' in discovery_data and 'extracted_urls' in discovery_data['analysis']:
        # New format from our discovery results
        extracted_urls = discovery_data['analysis']['extracted_urls']
        
        for source, source_urls in extracted_urls.items():
            urls.extend(source_urls)
            print(f"📌 Loaded {len(source_urls)} URLs from {source}")
    
    elif 'discovered_urls' in discovery_data:
        # Alternative format
        for source, source_urls in discovery_data['discovered_urls'].items():
            urls.extend(source_urls)
            print(f"📌 Loaded {len(source_urls)} URLs from {source}")
    
    else:
        print("⚠️  Unexpected discovery data format. Trying to extract URLs manually...")
        # Try to find URLs in any nested structure
        def find_urls(obj, collected_urls):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key in ['urls', 'extracted_urls', 'discovered_urls'] and isinstance(value, list):
                        collected_urls.extend([url for url in value if isinstance(url, str) and url.startswith('http')])
                    else:
                        find_urls(value, collected_urls)
            elif isinstance(obj, list):
                for item in obj:
                    find_urls(item, collected_urls)
        
        find_urls(discovery_data, urls)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen and url.startswith('http'):
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls


def run_access_phase_test(discovery_file: str = None, max_urls: int = 5, sample_only: bool = False):
    """
    Run the Access Phase test using discovered URLs
    
    Args:
        discovery_file: Specific discovery results file to use
        max_urls: Maximum number of URLs to test
        sample_only: If True, just sample URLs from different sources
    """
    print("🚀 Access Phase Test - Job URL Navigation & Content Extraction")
    print("=" * 70)
    
    # Test connection first
    if not test_connection():
        print("❌ Failed to connect to Bright Data API")
        return False
    
    try:
        # Load discovery results
        print("\n📂 Loading discovery results...")
        discovery_data = load_discovery_results(discovery_file)
        
        if 'search_term' in discovery_data:
            print(f"🎯 Original search term: '{discovery_data['search_term']}'")
        
        if 'timestamp' in discovery_data:
            print(f"📅 Discovery timestamp: {discovery_data['timestamp']}")
        
        # Extract URLs
        print("\n🔗 Extracting URLs from discovery results...")
        all_urls = extract_urls_from_discovery(discovery_data)
        
        if not all_urls:
            print("❌ No URLs found in discovery results")
            return False
        
        print(f"✅ Found {len(all_urls)} total URLs")
        
        # Sample URLs if requested
        if sample_only:
            # Try to get a mix from different sources
            linkedin_urls = [url for url in all_urls if 'linkedin.com' in url]
            indeed_urls = [url for url in all_urls if 'indeed.com' in url]
            
            test_urls = []
            
            # Take some from each source
            if linkedin_urls:
                test_urls.extend(linkedin_urls[:max_urls//2])
                print(f"📌 Selected {len(linkedin_urls[:max_urls//2])} LinkedIn URLs for testing")
            
            if indeed_urls:
                remaining = max_urls - len(test_urls)
                test_urls.extend(indeed_urls[:remaining])
                print(f"📌 Selected {len(indeed_urls[:remaining])} Indeed URLs for testing")
        else:
            test_urls = all_urls[:max_urls]
        
        if not test_urls:
            print("❌ No URLs selected for testing")
            return False
        
        print(f"\n🎯 Testing access to {len(test_urls)} URLs (limited from {len(all_urls)} total)")
        
        # Initialize Access Handler
        print("\n🔧 Initializing Bright Data Access Handler...")
        access_handler = BrightDataAccessHandler()
        
        # Run Access Phase
        results = access_handler.access_multiple_urls(
            urls=test_urls,
            max_urls=max_urls,
            save_results=True
        )
        
        # Close handler
        access_handler.close()
        
        # Display results summary
        print(f"\n📊 Access Phase Test Complete!")
        print("=" * 70)
        
        successful_accesses = [r for r in results if r.get('success', False)]
        successful_extractions = [r for r in results if r.get('extraction_success', False)]
        
        print(f"🌐 URLs tested: {len(test_urls)}")
        print(f"✅ Successful accesses: {len(successful_accesses)}")
        print(f"🔍 Successful extractions: {len(successful_extractions)}")
        
        if successful_extractions:
            print(f"\n📋 Sample extracted data:")
            for i, result in enumerate(successful_extractions[:3], 1):
                extracted = result.get('extracted_data', {})
                print(f"   {i}. {extracted.get('job_title', 'No title')} at {extracted.get('company', 'No company')}")
                print(f"      Source: {extracted.get('source', 'Unknown')} | Location: {extracted.get('location', 'N/A')}")
        
        # Show any errors
        failed_results = [r for r in results if not r.get('success', False)]
        if failed_results:
            print(f"\n❌ Failed accesses ({len(failed_results)}):")
            for result in failed_results[:3]:  # Show first 3 errors
                print(f"   • {result.get('url', 'Unknown URL')}: {result.get('error', 'Unknown error')}")
        
        return len(successful_accesses) > 0
        
    except Exception as e:
        print(f"❌ Access Phase test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point for Access Phase testing"""
    parser = argparse.ArgumentParser(
        description="Test Access Phase - Navigate to discovered job URLs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Use latest discovery results, test 5 URLs
  %(prog)s --max-urls 10                      # Test 10 URLs
  %(prog)s --discovery-file results.json     # Use specific discovery file
  %(prog)s --sample-only                     # Get mixed sample from different sources
        """
    )
    
    parser.add_argument('--discovery-file', '-f', type=str,
                        help='Specific discovery results file to use')
    parser.add_argument('--max-urls', '-n', type=int, default=5,
                        help='Maximum number of URLs to test (default: 5)')
    parser.add_argument('--sample-only', '-s', action='store_true',
                        help='Sample URLs from different sources rather than taking first N')
    
    args = parser.parse_args()
    
    success = run_access_phase_test(
        discovery_file=args.discovery_file,
        max_urls=args.max_urls,
        sample_only=args.sample_only
    )
    
    if success:
        print(f"\n✨ Test completed successfully!")
        print(f"💡 Next steps:")
        print(f"   • Review access_results_*.json for detailed results")
        print(f"   • Integrate Access Phase into main pipeline")
        print(f"   • Consider implementing Extract and Interact phases")
    else:
        print(f"\n❌ Test failed. Check configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main() 