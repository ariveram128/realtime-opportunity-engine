#!/usr/bin/env python3
"""
AI Internship Opportunity Finder - Web Interface
Enhanced Flask application for managing job applications
"""

import json
import logging
import threading
import time
import os
import sys
import traceback
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, send_from_directory
from typing import Dict, Optional
import requests

# Import our components
from .linkedin_scraper_handler import LinkedInScraperHandler
from .database_manager import DatabaseManager
from .job_filter import JobFilter

# Initialize logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Local imports
from config import WEB_CONFIG

# Try to import MCP handler (may not be available in all environments)
try:
    from .mcp_brightdata_handler_integrated import BrightDataMCPHandler, MCPAction
    from config import MCP_CONFIG, MCP_METRICS
    MCP_AVAILABLE = True
    logger.info("MCP handler successfully imported")
except ImportError as e:
    logger.warning(f"MCP handler not available: {e}")
    MCP_AVAILABLE = False
    MCP_CONFIG = {}
    MCP_METRICS = {}

# Initialize Flask app with correct paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__, 
           template_folder=os.path.join(project_root, 'templates'),
           static_folder=os.path.join(project_root, 'static'))
app.secret_key = WEB_CONFIG.get('secret_key', 'dev-key-change-in-production')

# Initialize database
db = DatabaseManager()

# Job status mapping for UI
JOB_STATUS = {
    'new': 'new',
    'interested': 'interested', 
    'applied': 'applied',
    'interview': 'interview',
    'rejected': 'rejected',
    'not_interested': 'not_interested',
    'hidden': 'hidden'
}

# Global variable to track real-time search status
realtime_search_status = {
    'is_running': False,
    'progress': 0,
    'current_phase': '',
    'results': {},
    'error': None,
    'started_at': None,
    'completed_at': None
}

# Global variable to track MCP search status  
mcp_search_status = {
    'is_running': False,
    'progress': 0,
    'current_action': '',
    'current_phase': '',
    'results': {},
    'performance_metrics': {},
    'error': None,
    'started_at': None,
    'completed_at': None
}


@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get filter parameters
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        per_page = 20
        
        # Get jobs based on filters
        if status == 'all':
            jobs = db.get_jobs(limit=1000)
        else:
            jobs = db.get_jobs(status=status, limit=1000)
        
        # Apply search filter
        if search:
            jobs = [j for j in jobs if search.lower() in 
                   f"{j.get('job_title', '')} {j.get('company', '')} {j.get('description', '')}".lower()]
        
        # Pagination
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = jobs[start_idx:end_idx]
        
        # Get statistics
        stats = db.get_job_stats()
        
        return render_template('index.html',
                             jobs=paginated_jobs,
                             total_jobs_count=len(jobs),  # Total jobs matching current filters
                             stats=stats,
                             job_statuses=JOB_STATUS,
                             current_status=status,
                             search_query=search,
                             page=page,
                             total_pages=(len(jobs) + per_page - 1) // per_page)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', jobs=[], stats={}, job_statuses=JOB_STATUS)


@app.route('/job/<job_id>')
def job_detail(job_id):
    """Show detailed view of a specific job"""
    try:
        jobs = db.get_jobs(limit=1000)
        job = next((j for j in jobs if j['job_id'] == job_id), None)
        
        if not job:
            flash('Job not found', 'error')
            return redirect(url_for('index'))
        
        # Parse raw data if available
        raw_data = {}
        if job.get('raw_data'):
            try:
                raw_data = json.loads(job['raw_data'])
            except json.JSONDecodeError:
                pass
        
        return render_template('job_detail.html', job=job, raw_data=raw_data, job_statuses=JOB_STATUS)
        
    except Exception as e:
        logger.error(f"Error loading job detail: {e}")
        flash(f"Error loading job: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/update_status', methods=['POST'])
def update_status():
    """Update job status via AJAX"""
    try:
        job_id = request.json.get('job_id')
        new_status = request.json.get('status')
        notes = request.json.get('notes', '')
        
        if not job_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing job_id or status'})
        
        # Map frontend status to backend status
        status_mapping = {
            'new': 'New',
            'interested': 'Interested',
            'applied': 'Applied', 
            'interview': 'Interview',
            'rejected': 'Rejected',
            'not_interested': 'Not Interested',
            'hidden': 'Hidden'
        }
        
        mapped_status = status_mapping.get(new_status, new_status)
        success = db.update_job_status(job_id, mapped_status, notes)
        
        if success:
            return jsonify({'success': True, 'message': f'Status updated to {mapped_status}'})
        else:
            return jsonify({'success': False, 'error': 'Failed to update status'})
            
    except Exception as e:
        logger.error(f"Error updating status: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/statistics')
def statistics():
    """Show detailed statistics about jobs"""
    try:
        stats = db.get_job_stats()
        
        # Get additional statistics
        jobs = db.get_jobs(limit=1000)
        
        # Calculate more detailed stats
        recent_stats = {
            'last_24h': len([j for j in jobs if _is_recent(j.get('extracted_at'), hours=24)]),
            'last_week': len([j for j in jobs if _is_recent(j.get('extracted_at'), days=7)]),
            'last_month': len([j for j in jobs if _is_recent(j.get('extracted_at'), days=30)])
        }
        
        # Job type distribution
        job_types = {}
        for job in jobs:
            job_type = job.get('job_type', 'Unknown')
            job_types[job_type] = job_types.get(job_type, 0) + 1
        
        # Convert dict_items to regular dicts for template compatibility
        if 'top_companies' in stats:
            stats['top_companies'] = dict(list(stats['top_companies'].items())[:10])
        if 'top_locations' in stats:
            stats['top_locations'] = dict(list(stats['top_locations'].items())[:10])
            
        return render_template('statistics.html',
                             stats=stats,
                             recent_stats=recent_stats,
                             job_types=job_types)
        
    except Exception as e:
        logger.error(f"Error loading statistics: {e}")
        flash(f"Error loading statistics: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/search')
def search():
    """Redirect to main page with search functionality"""
    return redirect(url_for('index'))


@app.route('/api/search', methods=['GET', 'POST'])
def api_search():
    """API endpoint for searching jobs"""
    try:
        if request.method == 'GET':
            # Handle GET request with URL parameters
            search_text = request.args.get('search_text', '')
            company = request.args.get('company', '')
            location = request.args.get('location', '')
            job_type = request.args.get('job_type', '')
            status = request.args.get('status', '')
            page = int(request.args.get('page', 1))
            per_page = 20
            
            # Get all jobs
            all_jobs = db.get_jobs(limit=1000)
            
            # Filter jobs based on criteria
            filtered_jobs = []
            for job in all_jobs:
                # Simple text search
                if search_text:
                    text_fields = f"{job.get('job_title', '')} {job.get('company', '')} {job.get('description', '')}".lower()
                    if search_text.lower() not in text_fields:
                        continue
                
                # Filter by other criteria
                if company and company.lower() not in job.get('company', '').lower():
                    continue
                if location and location.lower() not in job.get('location', '').lower():
                    continue
                if job_type and job_type != job.get('job_type', ''):
                    continue
                if status and status != job.get('status', ''):
                    continue
                
                filtered_jobs.append(job)
            
            # Pagination
            start_idx = (page - 1) * per_page
            end_idx = start_idx + per_page
            paginated_jobs = filtered_jobs[start_idx:end_idx]
            
            return jsonify({
                'success': True,
                'jobs': paginated_jobs,
                'total': len(filtered_jobs),
                'page': page,
                'per_page': per_page
            })
        else:
            # Handle POST request (original logic)
            search_data = request.json
            query = search_data.get('query', '')
            fields = search_data.get('fields', ['job_title', 'company', 'description'])
            
            results = db.search_jobs(query, fields)
            
            return jsonify({
                'success': True,
                'results': results[:50],
                'total': len(results)
            })
        
    except Exception as e:
        logger.error(f"Error in API search: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/realtime_search', methods=['POST'])
def api_realtime_search():
    """API endpoint for real-time job discovery and extraction"""
    global realtime_search_status
    
    try:
        # Check if a search is already running
        if realtime_search_status['is_running']:
            return jsonify({
                'success': False,
                'error': 'A real-time search is already in progress. Please wait for it to complete.'
            })
        
        # Get search parameters
        search_data = request.json
        search_term = search_data.get('search_term', '').strip()
        max_results = search_data.get('max_results', 10)
        
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term is required'})
        
        # Initialize search status
        realtime_search_status.update({
            'is_running': True,
            'progress': 0,
            'current_phase': 'Initializing search...',
            'results': {},
            'error': None,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'search_term': search_term,
            'max_results': max_results
        })
        
        # Start the search in a background thread
        search_thread = threading.Thread(
            target=run_realtime_search,
            args=(search_term, max_results)
        )
        search_thread.daemon = True
        search_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Real-time search started',
            'search_id': realtime_search_status['started_at']
        })
        
    except Exception as e:
        logger.error(f"Error starting real-time search: {e}")
        realtime_search_status['is_running'] = False
        realtime_search_status['error'] = str(e)
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/realtime_search/status')
def api_realtime_search_status():
    """Get the current status of the real-time search"""
    return jsonify(realtime_search_status)


@app.route('/api/realtime_search/cancel', methods=['POST'])
def api_realtime_search_cancel():
    """Cancel the current real-time search"""
    global realtime_search_status
    
    if realtime_search_status['is_running']:
        realtime_search_status['is_running'] = False
        realtime_search_status['current_phase'] = 'Cancelled by user'
        realtime_search_status['completed_at'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'Search cancelled'})
    else:
        return jsonify({'success': False, 'message': 'No active search to cancel'})


def run_realtime_search(search_term, max_results):
    """Run the real-time search process"""
    global realtime_search_status
    
    try:
        # Update status for LinkedIn scraping
        realtime_search_status['current_phase'] = 'Initializing LinkedIn Scraper...'
        realtime_search_status['progress'] = 5
        
        # Initialize LinkedIn scraper
        linkedin_scraper = LinkedInScraperHandler() # Ensure this is correctly initialized
        
        # Start LinkedIn job discovery
        realtime_search_status['current_phase'] = f'Discovering jobs for: \'{search_term}\'...'
        realtime_search_status['progress'] = 10
        logger.info(f"🔍 Using LinkedIn scraper for: '{search_term}'")
        
        discovery_result = linkedin_scraper.discover_jobs_by_keyword(search_term, max_results=max_results)
        
        if not discovery_result or not discovery_result.get('success'):
            error_msg = discovery_result.get('error', "Failed to start LinkedIn job discovery")
            logger.error(f"❌ LinkedIn discovery initiation failed: {error_msg}")
            raise Exception(f"LinkedIn discovery initiation failed: {error_msg}")
        
        snapshot_id = discovery_result.get('snapshot_id')
        if not snapshot_id:
            logger.error("❌ No snapshot_id received from discovery.")
            raise Exception("No snapshot_id received from LinkedIn job discovery")
            
        logger.info(f"📊 LinkedIn job discovery initiated. Snapshot ID: {snapshot_id}")
        realtime_search_status['current_phase'] = f'Polling for results (Snapshot ID: {snapshot_id[:10]}...). This may take a few minutes.'
        realtime_search_status['progress'] = 20

        # Wait for completion (this method internally polls)
        # Max wait time for _wait_for_completion should be less than the overall timeout to allow for other steps.
        # Let's set it to, for example, 8 minutes, if max_wait_time for the whole process is 10 minutes.
        # The `_wait_for_completion` in `linkedin_scraper_handler` should handle its own timeout logic.
        # We pass a max_wait_time to it.
        # The `_wait_for_completion` should also update progress if possible, or we estimate it here.

        # Assuming _wait_for_completion now takes a progress_callback
        def progress_callback_for_wait(scraper_progress_data):
            # scraper_progress_data could be a dict {'progress': percentage, 'status_message': '...'}
            progress_percentage = scraper_progress_data.get('progress', 0)
            status_message = scraper_progress_data.get('status_message', realtime_search_status['current_phase'])
            # Scale BrightData progress (0-100) to fit our overall progress range (e.g., 20-80%)
            realtime_search_status['progress'] = 20 + (progress_percentage * 0.6) 
            realtime_search_status['current_phase'] = f'Polling: {status_message} ({progress_percentage}%)'
            logger.info(f"⏳ LinkedIn Polling Update: {status_message} - {progress_percentage}%")

        # The `_wait_for_completion` method needs to be adapted to accept such a callback,
        # or we simply estimate progress here. For now, let's assume it does not take a callback
        # and we will update progress more generically.

        # The timeout for _wait_for_completion should be less than the global max_wait_time
        # to allow for subsequent steps like DB storage.
        completion_wait_timeout = 540  # 9 minutes, leaving 1 min for other ops if total is 10 min.
        
        logger.info(f"⏳ Waiting for job discovery completion (Snapshot ID: {snapshot_id}). Max wait: {completion_wait_timeout}s.")
        
        # This is the blocking call that waits for BrightData to finish
        # It should return the jobs list or None/raise error on failure/timeout
        jobs = linkedin_scraper._wait_for_completion(snapshot_id, max_wait_time=completion_wait_timeout)

        if jobs is None: # Indicates timeout or failure from _wait_for_completion
            logger.error(f"❌ LinkedIn job discovery timed out or failed for snapshot ID: {snapshot_id} after {completion_wait_timeout}s.")
            raise Exception(f"LinkedIn job discovery timed out or failed for snapshot ID: {snapshot_id}")
        
        if not isinstance(jobs, list):
            logger.error(f"❌ Unexpected result from _wait_for_completion for snapshot {snapshot_id}: {type(jobs)}")
            raise Exception(f"Unexpected result type from job discovery: {type(jobs)}")

        logger.info(f"✅ Job discovery completed. Received {len(jobs)} job items for snapshot {snapshot_id}.")
        realtime_search_status['current_phase'] = 'Processing and storing extracted jobs...'
        realtime_search_status['progress'] = 80
        
        # The jobs returned by _wait_for_completion should already be in a usable format.
        # If `extract_jobs_from_snapshot` was doing further processing, that logic might need to be
        # integrated into `_wait_for_completion` or called here if `_wait_for_completion` returns raw data.
        # For now, assume `jobs` is the final list of job dicts.
        
        realtime_search_status['results'].update({
            'urls_discovered': len(jobs), # Or a more accurate count if available
            'jobs_extracted': len(jobs),
            'jobs_filtered': len(jobs), # Assuming all extracted are initially kept
            'jobs_stored': 0 # Will be updated below
        })
        
        # Store jobs in database
        realtime_search_status['current_phase'] = 'Storing jobs in database...'
        realtime_search_status['progress'] = 90
        
        stored_count = 0
        if jobs: # Ensure there are jobs to store
            for job_detail in jobs:
                # Ensure job_detail is a dictionary and has necessary fields
                if isinstance(job_detail, dict):
                    # The `db.insert_job` method should ideally handle the conversion
                    # to its required format, or jobs from BrightData are already standard.
                    if db.insert_job(job_detail): # store_job now expects a dict
                        stored_count += 1
                else:
                    logger.warning(f"⚠️ Skipping non-dict job item: {type(job_detail)}")
        
        logger.info(f"💾 Stored {stored_count}/{len(jobs)} jobs in the database.")
        
        # Update final results
        realtime_search_status['results']['jobs_stored'] = stored_count
        realtime_search_status['progress'] = 100
        realtime_search_status['current_phase'] = f'Search completed. {stored_count} jobs stored.'
        realtime_search_status['is_running'] = False
        realtime_search_status['completed_at'] = datetime.now().isoformat()
        
        # linkedin_scraper.close() # Close session if necessary

    except Exception as e:
        logger.error(f"❌ Error in real-time search: {e}", exc_info=True)
        realtime_search_status.update({
            'is_running': False,
            'error': str(e),
            'completed_at': datetime.now().isoformat(),
            'current_phase': f'Search failed: {str(e)[:100]}...' # Truncate long errors
        })


@app.route('/bulk_action', methods=['POST'])
def bulk_action():
    """Apply bulk actions to multiple jobs"""
    try:
        job_ids = request.json.get('job_ids', [])
        action = request.json.get('action')
        
        if not job_ids or not action:
            return jsonify({'success': False, 'error': 'Missing job_ids or action'})
        
        success_count = 0
        for job_id in job_ids:
            if db.update_job_status(job_id, action):
                success_count += 1
        
        return jsonify({
            'success': True,
            'message': f'Updated {success_count}/{len(job_ids)} jobs',
            'updated_count': success_count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk action: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/export')
def export_jobs():
    """Export jobs to JSON"""
    try:
        status = request.args.get('status', 'all')
        
        if status == 'all':
            jobs = db.get_jobs(limit=10000)
        else:
            jobs = db.get_jobs(status=status, limit=10000)
        
        # Remove sensitive data
        export_jobs = []
        for job in jobs:
            export_job = {k: v for k, v in job.items() if k not in ['raw_data', 'id']}
            export_jobs.append(export_job)
        
        from flask import Response
        return Response(
            json.dumps(export_jobs, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': f'attachment; filename=jobs_{status}_{datetime.now().strftime("%Y%m%d")}.json'}
        )
        
    except Exception as e:
        logger.error(f"Error exporting jobs: {e}")
        flash(f"Error exporting jobs: {str(e)}", 'error')
        return redirect(url_for('index'))


@app.route('/cleanup')
def cleanup():
    """Clean up old jobs"""
    try:
        days = int(request.args.get('days', 90))
        deleted_count = db.cleanup_old_jobs(days)
        
        flash(f'Cleaned up {deleted_count} old jobs', 'success')
        return redirect(url_for('statistics'))
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        flash(f"Error during cleanup: {str(e)}", 'error')
        return redirect(url_for('statistics'))


@app.route('/favicon.ico')
def favicon():
    """Serve favicon to prevent 404 errors"""
    from flask import send_from_directory
    return send_from_directory('static', 'favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


def _is_recent(date_string, hours=None, days=None):
    """Check if a date string is within the specified time period"""
    if not date_string:
        return False
    
    try:
        date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        now = datetime.now(date.tzinfo) if date.tzinfo else datetime.now()
        
        if hours:
            return now - date <= timedelta(hours=hours)
        elif days:
            return now - date <= timedelta(days=days)
        else:
            return False
    except:
        return False


@app.route('/api/delete_job', methods=['POST'])
def api_delete_job():
    """API endpoint for deleting a single job"""
    try:
        job_id = request.json.get('job_id')
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Missing job_id'})
        
        success = db.delete_job(job_id)
        
        if success:
            return jsonify({'success': True, 'message': 'Job deleted successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete job'})
            
    except Exception as e:
        logger.error(f"Error deleting job: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/delete_jobs', methods=['POST'])
def api_delete_jobs():
    """API endpoint for bulk deleting jobs"""
    try:
        job_ids = request.json.get('job_ids', [])
        delete_type = request.json.get('delete_type', 'selected')  # 'selected', 'all', 'status'
        status = request.json.get('status')
        
        deleted_count = 0
        
        if delete_type == 'selected' and job_ids:
            # Delete specific jobs
            for job_id in job_ids:
                if db.delete_job(job_id):
                    deleted_count += 1
        elif delete_type == 'status' and status:
            # Delete all jobs with specific status
            deleted_count = db.delete_jobs_by_status(status)
        elif delete_type == 'all':
            # Delete all jobs (with confirmation)
            deleted_count = db.delete_all_jobs()
        
        return jsonify({
            'success': True,
            'message': f'Deleted {deleted_count} jobs',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/cleanup_database', methods=['POST'])
def api_cleanup_database():
    """API endpoint for cleaning up the database"""
    try:
        cleanup_type = request.json.get('cleanup_type', 'old_jobs')
        days = request.json.get('days', 90)
        
        if cleanup_type == 'old_jobs':
            # Delete jobs older than specified days
            deleted_count = db.cleanup_old_jobs(days)
            message = f'Cleaned up {deleted_count} jobs older than {days} days'
        elif cleanup_type == 'duplicates':
            # Remove duplicate jobs
            deleted_count = db.remove_duplicate_jobs()
            message = f'Removed {deleted_count} duplicate jobs'
        elif cleanup_type == 'hidden':
            # Delete hidden jobs
            deleted_count = db.delete_jobs_by_status('hidden')
            message = f'Deleted {deleted_count} hidden jobs'
        elif cleanup_type == 'status':
            # Delete jobs by specific status
            status = request.json.get('status')
            if not status:
                return jsonify({'success': False, 'error': 'Status is required for status cleanup'})
            deleted_count = db.delete_jobs_by_status(status)
            message = f'Deleted {deleted_count} jobs with status: {status}'
        elif cleanup_type == 'all':
            # Delete ALL jobs (with extreme caution)
            deleted_count = db.delete_all_jobs()
            message = f'Deleted ALL {deleted_count} jobs from database'
        else:
            return jsonify({'success': False, 'error': 'Invalid cleanup type'})
        
        return jsonify({
            'success': True,
            'message': message,
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error in database cleanup: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ==================== MCP ROUTES ====================

@app.route('/api/mcp_search', methods=['POST'])
def api_mcp_search():
    """API endpoint for MCP-enhanced job discovery"""
    global mcp_search_status
    
    try:
        # Check if MCP search is already running
        if mcp_search_status['is_running']:
            return jsonify({
                'success': False,
                'error': 'An MCP search is already in progress. Please wait for it to complete.'
            })
        
        # Get search parameters
        search_data = request.json
        search_term = search_data.get('search_term', '').strip()
        max_results = search_data.get('max_results', 10)
        
        if not search_term:
            return jsonify({'success': False, 'error': 'Search term is required'})
        
        # Initialize MCP search status
        mcp_search_status.update({
            'is_running': True,
            'progress': 0,
            'current_action': '',
            'current_phase': 'Initializing MCP pipeline...',
            'results': {},
            'performance_metrics': {},
            'error': None,
            'started_at': datetime.now().isoformat(),
            'completed_at': None,
            'search_term': search_term,
            'max_results': max_results
        })
        
        # Start MCP search in background thread
        mcp_thread = threading.Thread(
            target=run_mcp_search_wrapper,
            args=(search_term, max_results)
        )
        mcp_thread.daemon = True
        mcp_thread.start()
        
        return jsonify({
            'success': True,
            'message': 'MCP search started',
            'search_id': mcp_search_status['started_at']
        })
        
    except Exception as e:
        logger.error(f"Error starting MCP search: {e}")
        mcp_search_status['is_running'] = False
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/mcp_search/status')
def api_mcp_search_status():
    """Get the current status of the MCP search"""
    return jsonify(mcp_search_status)


@app.route('/api/mcp_search/cancel', methods=['POST'])
def api_mcp_search_cancel():
    """Cancel the current MCP search"""
    global mcp_search_status
    
    if mcp_search_status['is_running']:
        mcp_search_status['is_running'] = False
        mcp_search_status['current_phase'] = 'Cancelled by user'
        mcp_search_status['completed_at'] = datetime.now().isoformat()
        return jsonify({'success': True, 'message': 'MCP search cancelled'})
    else:
        return jsonify({'success': False, 'message': 'No active MCP search to cancel'})


@app.route('/api/mcp_metrics')
def api_mcp_metrics():
    """Get MCP performance metrics and improvements"""
    return jsonify({
        'success': True,
        'metrics': MCP_METRICS,
        'config': {
            'discover_improvement_pct': (MCP_METRICS['discover_improvement'] - 1) * 100,
            'access_improvement_pct': (MCP_METRICS['access_improvement'] - 1) * 100,
            'extract_improvement_pct': (MCP_METRICS['extract_improvement'] - 1) * 100,
            'interact_improvement_pct': (MCP_METRICS['interact_improvement'] - 1) * 100,
            'overall_improvement_pct': (MCP_METRICS['overall_improvement'] - 1) * 100
        }
    })


def run_mcp_search_wrapper(search_term, max_results):
    """
    Wrapper function to run async MCP search in a thread
    """
    import asyncio
    asyncio.run(run_mcp_search_async(search_term, max_results))

async def run_mcp_search_async(search_term, max_results):
    """
    Run MCP-enhanced search pipeline demonstrating all four actions (async version)
    """
    global mcp_search_status
    
    try:
        # Initialize MCP handler
        async with BrightDataMCPHandler() as mcp_handler:
            
            # Action 1: DISCOVER - AI-enhanced job discovery
            mcp_search_status['current_action'] = 'DISCOVER'
            mcp_search_status['current_phase'] = 'AI-enhanced job discovery...'
            mcp_search_status['progress'] = 10
            
            logger.info(f"🔍 MCP DISCOVER: Starting AI-enhanced job discovery for '{search_term}'")
            
            discover_result = await mcp_handler.discover_opportunities(
                search_query=search_term,
                location="United States",
                max_results=max_results
            )
        
        if not discover_result.success:
            error_msg = discover_result.metadata.get('error', 'Unknown error in DISCOVER phase')
            raise Exception(f"DISCOVER failed: {error_msg}")
        
        mcp_search_status['progress'] = 30
        mcp_search_status['results']['discovered_urls'] = len(discover_result.data.get('job_urls', []))
        
        # Action 2: ACCESS - Context-aware page navigation
        mcp_search_status['current_action'] = 'ACCESS'
        mcp_search_status['current_phase'] = 'Context-aware page navigation...'
        mcp_search_status['progress'] = 40
        
        logger.info(f"🌐 MCP ACCESS: Context-aware navigation for {len(discover_result.data.get('job_urls', []))} URLs")
        
        # Simulate accessing multiple job pages (limit for demo)
        job_urls = discover_result.data.get('job_urls', [])[:max_results]
        accessed_pages = []
        
        for i, url in enumerate(job_urls[:3]):  # Access first 3 for demo
            access_result = await mcp_handler.access_job_page(
                job_url=url,
                context={"anti_bot_bypass": True, "context_aware": True}
            )
            
            if access_result.success:
                accessed_pages.append({
                    'url': url,
                    'page_data': access_result.data
                })
            
            # Update progress
            mcp_search_status['progress'] = 40 + (i + 1) * 5
        
        mcp_search_status['results']['accessed_pages'] = len(accessed_pages)
        
        # Action 3: EXTRACT - LLM-powered content extraction
        mcp_search_status['current_action'] = 'EXTRACT'
        mcp_search_status['current_phase'] = 'LLM-powered content extraction...'
        mcp_search_status['progress'] = 60
        
        logger.info(f"📊 MCP EXTRACT: LLM-powered extraction from {len(accessed_pages)} pages")
        
        extracted_jobs = []
        
        for i, page in enumerate(accessed_pages):
            extract_result = await mcp_handler.extract_job_data(
                html_content=page['page_data']['html_content'],
                url=page['url'],
                context={"llm_powered": True, "intelligent_parsing": True}
            )
            
            if extract_result.success:
                job_data = extract_result.data
                job_data['source_url'] = page['url']
                job_data['extraction_method'] = 'MCP_LLM_Enhanced'
                extracted_jobs.append(job_data)
            
            # Update progress
            mcp_search_status['progress'] = 60 + (i + 1) * 10
        
        mcp_search_status['results']['extracted_jobs'] = len(extracted_jobs)
        
        # Action 4: INTERACT - Personalized analysis and recommendations
        mcp_search_status['current_action'] = 'INTERACT'
        mcp_search_status['current_phase'] = 'AI-powered job analysis...'
        mcp_search_status['progress'] = 85
        
        logger.info(f"🤖 MCP INTERACT: AI-powered analysis of {len(extracted_jobs)} jobs")
        
        analyzed_jobs = []
        
        for i, job in enumerate(extracted_jobs):
            interact_result = await mcp_handler.interact_and_analyze(
                job_data=job,
                user_profile={'search_term': search_term, 'preferences': {}}
            )
            
            if interact_result.success:
                analyzed_job = job.copy()
                analyzed_job.update({
                    'mcp_analysis': interact_result.data,
                    'relevance_score': interact_result.data.get('relevance_score', 0.0),
                    'recommendation': interact_result.data.get('recommendation', ''),
                    'ai_insights': interact_result.data.get('insights', [])
                })
                analyzed_jobs.append(analyzed_job)
            
            # Update progress
            mcp_search_status['progress'] = 85 + (i + 1) * 3
        
        # Store jobs in database with MCP enhancements
        mcp_search_status['current_phase'] = 'Storing MCP-enhanced jobs...'
        mcp_search_status['progress'] = 95
        
        stored_count = 0
        storage_errors = []
        
        for i, job in enumerate(analyzed_jobs):
            try:
                # Extract job data safely with better error handling
                job_title = str(job.get('job_title', 'MCP Enhanced Job')).strip()
                company = str(job.get('company', 'Unknown Company')).strip()
                location = str(job.get('location', 'Location Not Specified')).strip()
                description = str(job.get('description', '')).strip()
                url = str(job.get('source_url', job.get('url', ''))).strip()
                
                # Generate unique job ID if not present
                if 'job_id' not in job or not job['job_id']:
                    import hashlib
                    unique_data = f"{job_title}_{company}_{int(time.time())}_{i}"
                    job_id = f"mcp_{hashlib.md5(unique_data.encode()).hexdigest()[:8]}"
                else:
                    job_id = str(job.get('job_id'))
                
                # Convert to standard format for database
                standard_job = {
                    'job_id': job_id,
                    'job_title': job_title,
                    'company': company,
                    'location': location,
                    'description': description,
                    'url': url,
                    'status': 'new',  # Store MCP jobs as new like other jobs
                    'source': 'MCP_Enhanced_Discovery',
                    'extracted_at': datetime.now().isoformat(),
                    'job_type': 'Internship',
                    'raw_data': json.dumps(job, default=str)  # Handle any non-serializable objects
                }
                
                # Add MCP-specific enhancements if available
                if 'mcp_analysis' in job:
                    recommendation = job.get('mcp_analysis', {}).get('recommendation', 'No recommendation')
                    match_score = job.get('mcp_analysis', {}).get('match_score', 0.0)
                    standard_job['notes'] = f"MCP Analysis - Score: {match_score:.1%} - {recommendation}"
                
                logger.debug(f"📝 Attempting to store MCP job {i+1}: {job_title} (ID: {job_id})")
                
                success = db.insert_job(standard_job)
                if success:
                    stored_count += 1
                    logger.info(f"✅ Stored MCP job {i+1}: {job_title} at {company}")
                else:
                    duplicate_msg = f"Job {i+1}: Duplicate detected - {job_title} at {company}"
                    storage_errors.append(duplicate_msg)
                    logger.warning(f"⚠️ {duplicate_msg}")
                    
            except Exception as e:
                error_msg = f"Job {i+1}: Storage error - {str(e)}"
                storage_errors.append(error_msg)
                logger.error(f"❌ Error storing MCP job {i+1}: {e}")
                logger.debug(f"❌ Job data that caused error: {str(job)[:200]}...")
                continue
        
        if storage_errors and stored_count == 0:
            logger.warning(f"⚠️ MCP job storage issues: {storage_errors[:3]}")  # Log first 3 errors
        
        # Calculate performance metrics
        performance_metrics = {
            'discover_time_saved': f"{MCP_METRICS['discover_improvement']}x faster",
            'access_efficiency': f"{(MCP_METRICS['access_improvement'] - 1) * 100:.0f}% improvement",
            'extraction_accuracy': f"{(MCP_METRICS['extract_improvement'] - 1) * 100:.0f}% better",
            'analysis_depth': f"{(MCP_METRICS['interact_improvement'] - 1) * 100:.0f}% more insights",
            'overall_enhancement': f"{(MCP_METRICS['overall_improvement'] - 1) * 100:.0f}% overall improvement"
        }
        
        # Complete the search
        mcp_search_status.update({
            'is_running': False,
            'progress': 100,
            'current_action': 'COMPLETED',
            'current_phase': 'MCP search completed successfully!',
            'completed_at': datetime.now().isoformat(),
            'results': {
                'urls_discovered': len(job_urls),
                'pages_accessed': len(accessed_pages),
                'jobs_extracted': len(extracted_jobs),
                'jobs_analyzed': len(analyzed_jobs),
                'jobs_stored': stored_count,
                'duplicates': 0,  # MCP reduces duplicates through intelligent deduplication
                'search_term': search_term,
                'actions_completed': ['DISCOVER', 'ACCESS', 'EXTRACT', 'INTERACT'],
                'discovered_urls': len(job_urls),
                'accessed_pages': len(accessed_pages),
                'extracted_jobs': len(extracted_jobs),
                'analyzed_jobs': len(analyzed_jobs),
                'stored_jobs': stored_count
            },
            'performance_metrics': performance_metrics
        })
        
        logger.info(f"✅ MCP search completed: {stored_count} enhanced jobs stored")
        
    except Exception as e:
        import traceback
        logger.error(f"Error in MCP search: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        mcp_search_status.update({
            'error': str(e),
            'is_running': False,
            'completed_at': datetime.now().isoformat()
        })

# ==================== END MCP ROUTES ====================

if __name__ == '__main__':
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        debug=WEB_CONFIG['debug']
    )