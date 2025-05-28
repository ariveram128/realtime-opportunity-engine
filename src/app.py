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
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, Response, send_from_directory, session
from typing import Dict, Optional
import requests
import uuid
import asyncio

# Import our components
from .linkedin_scraper_handler import LinkedInScraperHandler
from .database_manager import DatabaseManager
from .job_filter import JobFilter
from src.nlp_utils import get_embedding, calculate_cosine_similarity

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

SIMILARITY_THRESHOLD = 0.6 # Define a threshold for relevance

# Helper function to get or create a session ID
def get_or_create_session_id():
    """Get existing session ID or create a new one"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return session['session_id']

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        session_id = get_or_create_session_id()
        status = request.args.get('status', 'all')
        search_query_user = request.args.get('search', '') # Renamed to avoid conflict
        page = int(request.args.get('page', 1))
        per_page = 12

        if status == 'all':
            jobs_from_db = db.get_jobs(limit=1000, session_id=session_id)
        else:
            jobs_from_db = db.get_jobs(status=status, limit=1000, session_id=session_id)
        
        jobs_to_display = jobs_from_db
        final_filtered_jobs_for_accuracy_check = []

        if search_query_user:
            jobs_after_keyword_search = [
                j for j in jobs_from_db if search_query_user.lower() in
                f"{j.get('job_title', '')} {j.get('company', '')} {j.get('description', '')}".lower()
            ]
            jobs_to_display = jobs_after_keyword_search
            final_filtered_jobs_for_accuracy_check = jobs_after_keyword_search
            
            if final_filtered_jobs_for_accuracy_check and search_query_user:
                query_embedding = get_embedding(search_query_user)
                num_relevant_nlp = 0
                
                for job in final_filtered_jobs_for_accuracy_check:
                    job_text = f"{job.get('job_title', '')} {job.get('description', '')}"
                    if not job_text.strip():
                        continue
                    job_embedding = get_embedding(job_text)
                    similarity = calculate_cosine_similarity(query_embedding, job_embedding)
                    
                    if similarity >= SIMILARITY_THRESHOLD:
                        num_relevant_nlp += 1
                
                num_shown = len(final_filtered_jobs_for_accuracy_check)
                if num_shown > 0:
                    ai_accuracy = (num_relevant_nlp / num_shown) * 100
                    db.log_search_event(session_id, search_query_user, num_shown, num_relevant_nlp, ai_accuracy)
                else:
                    db.log_search_event(session_id, search_query_user, 0, 0, 0.0) 
            elif search_query_user: 
                 db.log_search_event(session_id, search_query_user, 0, 0, 0.0)
            
        else:
            final_filtered_jobs_for_accuracy_check = jobs_from_db 
            jobs_to_display = jobs_from_db

        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_jobs = jobs_to_display[start_idx:end_idx]
        
        stats_data = db.get_job_stats(session_id=session_id) 

        return render_template('index.html',
                             jobs=paginated_jobs,
                             total_jobs_count=len(jobs_to_display),
                             stats=stats_data, 
                             job_statuses=JOB_STATUS,
                             current_status=status,
                             search_query=search_query_user, 
                             page=page,
                             total_pages=(len(jobs_to_display) + per_page - 1) // per_page)

    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', jobs=[], stats={}, job_statuses=JOB_STATUS, search_query=search_query_user if 'search_query_user' in locals() else '')


@app.route('/job/<job_id>')
def job_detail(job_id):
    """Show detailed view of a specific job"""
    try:
        session_id = get_or_create_session_id()
        jobs = db.get_jobs(limit=1000, session_id=session_id)
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
        session_id = get_or_create_session_id()
        
        if not job_id or not new_status:
            return jsonify({'success': False, 'error': 'Missing job_id or status'})
        
        # Check if the job belongs to this session
        jobs = db.get_jobs(session_id=session_id)
        job_exists = any(j['job_id'] == job_id for j in jobs)
        
        if not job_exists:
            return jsonify({'success': False, 'error': 'Job not found or not accessible'})
        
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
        session_id = get_or_create_session_id()
        stats_data = db.get_job_stats(session_id=session_id) # Renamed stats to stats_data
        
        # Enhanced search analytics
        search_analytics = {
            'average_accuracy': db.get_average_search_accuracy(session_id=session_id),
            'search_history': db.get_search_history(session_id=session_id, limit=10),
            'accuracy_trends': db.get_search_accuracy_trends(session_id=session_id, days=30),
            'accuracy_distribution': db.get_search_accuracy_distribution(session_id=session_id),
            'query_analytics': db.get_search_query_analytics(session_id=session_id, limit=10),
            'performance_summary': db.get_search_performance_summary(session_id=session_id)
        }
        
        jobs = db.get_jobs(limit=1000, session_id=session_id)
        
        recent_stats = {
            'last_24h': len([j for j in jobs if _is_recent(j.get('extracted_at'), hours=24)]),
            'last_week': len([j for j in jobs if _is_recent(j.get('extracted_at'), days=7)]),
            'last_month': len([j for j in jobs if _is_recent(j.get('extracted_at'), days=30)])
        }
        
        job_types = {}
        for job in jobs:
            job_type = job.get('job_type', 'Unknown')
            job_types[job_type] = job_types.get(job_type, 0) + 1
        
        if 'top_companies' in stats_data:
            stats_data['top_companies'] = dict(list(stats_data['top_companies'].items())[:10])
        if 'top_locations' in stats_data:
            stats_data['top_locations'] = dict(list(stats_data['top_locations'].items())[:10])
            
        return render_template('statistics.html',
                             stats=stats_data, # Use renamed variable
                             recent_stats=recent_stats,
                             job_types=job_types,
                             search_analytics=search_analytics)
        
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
        session_id = get_or_create_session_id()
        
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
            all_jobs = db.get_jobs(limit=1000, session_id=session_id)
            
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
    """API endpoint to trigger real-time job search"""
    try:
        # Check if a search is already running
        if realtime_search_status['is_running']:
            return jsonify({
                'success': False,
                'error': 'A search is already in progress'
            })
        
        # Get search parameters
        data = request.json
        search_term = data.get('search_term', '')
        max_results = int(data.get('max_results', 10))
        
        if not search_term:
            return jsonify({
                'success': False,
                'error': 'Search term is required'
            })
        
        # Get session ID
        session_id = get_or_create_session_id()
        
        # Reset search status
        realtime_search_status.update({
            'is_running': True,
            'progress': 0,
            'current_action': 'Initializing search',
            'current_phase': 'init',
            'search_query': search_term,  # Store search query for AI accuracy calculation
            'results': {},
            'error': None,
            'started_at': datetime.now().isoformat(),
            'completed_at': None
        })
        
        # Start search in background thread
        thread = threading.Thread(target=run_realtime_search, args=(search_term, max_results, session_id))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'message': 'Search started'
        })
        
    except Exception as e:
        logger.error(f"Error starting real-time search: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/api/realtime_search/status')
def api_realtime_search_status():
    """Get status of current real-time search"""
    return jsonify(realtime_search_status)


@app.route('/api/realtime_search/cancel', methods=['POST'])
def api_realtime_search_cancel():
    """Cancel ongoing real-time search"""
    if not realtime_search_status['is_running']:
        return jsonify({
            'success': False,
            'error': 'No search is currently running'
        })
    
    # Set status to not running
    realtime_search_status.update({
        'is_running': False,
        'current_action': 'Search cancelled',
        'completed_at': datetime.now().isoformat()
    })
    
    return jsonify({
        'success': True,
        'message': 'Search cancelled'
    })


def run_realtime_search(search_term, max_results, session_id=None):
    """
    Run real-time job search in background thread
    
    Args:
        search_term (str): Search query
        max_results (int): Maximum number of results to return
        session_id (str): Session ID for user isolation
    """
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
        
        # Initialize rotating messages system
        import random
        import time
        
        job_search_tips = [
            "💡 Tip: Tailor your resume for each application to increase your chances!",
            "🎯 Pro tip: Research the company culture before applying",
            "⚡ Did you know? 70% of jobs are never posted publicly - networking is key!",
            "📝 Quick tip: Use action verbs in your resume (achieved, implemented, led)",
            "🌟 Remember: Quality applications beat quantity every time",
            "🔍 Insight: LinkedIn is 40x more effective for B2B lead generation than other platforms",
            "💼 Career hack: Follow up on applications after 1-2 weeks",
            "🎓 Fun fact: Continuous learning makes you 5x more likely to get promoted",
            "🤝 Network tip: Attend virtual industry events and webinars",
            "📊 Analytics show: Personalized cover letters increase response rates by 50%",
            "🚀 Success strategy: Set up Google Alerts for companies you're interested in",
            "💪 Motivation: Every rejection brings you one step closer to the perfect job",
            "🎨 Creative tip: Build a personal portfolio website to showcase your work",
            "📱 Modern approach: Use LinkedIn's 'Open to Work' feature strategically",
            "⏰ Timing matters: Tuesday-Thursday mornings have highest application response rates",
            "🧠 Interview prep: Practice the STAR method for behavioral questions",
            "📈 Career growth: Ask about professional development opportunities in interviews",
            "🌐 Global insight: Remote work has opened 5x more opportunities than before",
            "💡 Innovation tip: Highlight your problem-solving skills with specific examples",
            "🎯 Targeting advice: Focus on roles that match 80% of your skills, not 100%",
            "🔥 Hot tip: Company employees are 5x more likely to respond to connection requests",
            "📚 Learning: Stay updated with industry trends and mention them in interviews",
            "⭐ Standout strategy: Create case studies of your past work achievements",
            "🎪 Interview magic: Prepare thoughtful questions about the role and company",
            "🌟 Personal brand: Consistency across all platforms increases credibility by 3x",
            "🔬 Research hack: Use company's recent news and achievements in your conversations",
            "💎 Value proposition: Clearly articulate what unique value you bring",
            "🎵 Harmony tip: Align your career goals with the company's mission",
            "🏆 Achievement focus: Quantify your accomplishments with specific metrics",
            "🌈 Diversity advantage: Companies with diverse teams are 35% more likely to outperform",
            "🔐 Insider secret: Referrals account for 40% of all hires",
            "⚡ Speed matters: Apply within 48 hours of job posting for best results",
            "🎭 Authenticity wins: Be genuine in interviews - people can sense authenticity",
            "📋 Organization tip: Use a spreadsheet to track all your applications",
            "🌱 Growth mindset: Emphasize your willingness to learn and adapt",
            "🎯 Precision strategy: Customize your LinkedIn headline for each industry",
            "🚀 Launch pad: Volunteer work can open unexpected career opportunities",
            "💫 Networking gold: Alumni networks are underutilized career resources",
            "🎨 Creativity boost: Use infographics in your resume for visual impact",
            "📞 Communication: Follow up calls show initiative and genuine interest",
            "🏅 Excellence standard: Proofread everything - typos can cost opportunities",
            "🌟 Confidence builder: Practice your elevator pitch until it's natural",
            "🔍 Deep dive: Research interviewer backgrounds on LinkedIn beforehand",
            "💡 Illumination: Show enthusiasm for the role and company mission",
            "🎪 Performance art: Job searching is a skill that improves with practice"
        ]
        
        motivational_messages = [
            "🌟 Discovering your next career opportunity...",
            "🚀 Launching search engines across the web...",
            "🎯 Targeting the perfect positions for you...",
            "⚡ Scanning thousands of job listings...",
            "🔍 Filtering through opportunities like a pro...",
            "💼 Building your pathway to success...",
            "🌈 Creating connections between you and great companies...",
            "🏆 Hunting for roles that match your brilliance...",
            "⭐ Mapping out your career constellation...",
            "🎨 Crafting your professional future...",
            "🔥 Igniting opportunities in your field...",
            "💎 Mining for career gems...",
            "🌱 Growing your professional network...",
            "🎪 Orchestrating your career symphony...",
            "🚀 Propelling your career to new heights...",
            "⚡ Energizing your job search with AI power...",
            "🌟 Illuminating hidden opportunities...",
            "🎯 Precision-targeting your ideal roles...",
            "💫 Aligning stars for your career success...",
            "🔮 Revealing your professional destiny..."
        ]
        
        technical_insights = [
            "🤖 AI engines are analyzing job requirements in real-time...",
            "📊 Machine learning algorithms are ranking opportunities...",
            "⚙️ Advanced scrapers are parsing company data...",
            "🔧 Optimizing search parameters for maximum relevance...",
            "📡 Syncing with multiple job platforms simultaneously...",
            "🧠 Neural networks are matching your skills to roles...",
            "⚡ Distributed systems are processing thousands of listings...",
            "🔍 Smart filters are eliminating irrelevant positions...",
            "📈 Analytics engines are predicting job market trends...",
            "🌐 Global databases are being cross-referenced...",
            "💻 Cloud processors are working at lightspeed...",
            "🔄 Real-time APIs are fetching the latest postings...",
            "📋 Intelligent parsers are extracting key job details...",
            "🎪 Sophisticated algorithms are ranking opportunities...",
            "⚡ High-performance computing is accelerating your search..."
        ]
        
        # Combine all message categories
        all_messages = job_search_tips + motivational_messages + technical_insights
        
        # Select initial random message
        initial_message = random.choice(all_messages)
        realtime_search_status['current_phase'] = initial_message
        realtime_search_status['progress'] = 20
        realtime_search_status['_message_rotation'] = {
            'messages': all_messages,
            'last_update': time.time(),
            'current_index': 0
        }

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
            
            # Get rotating message system
            rotation_data = realtime_search_status.get('_message_rotation', {})
            messages = rotation_data.get('messages', [])
            last_update = rotation_data.get('last_update', 0)
            current_index = rotation_data.get('current_index', 0)
            
            # Rotate message every 3-5 seconds
            current_time = time.time()
            if messages and (current_time - last_update) > random.uniform(3, 5):
                current_index = (current_index + 1) % len(messages)
                realtime_search_status['_message_rotation']['current_index'] = current_index
                realtime_search_status['_message_rotation']['last_update'] = current_time
                
                # Use rotating message with progress
                rotating_message = messages[current_index]
                realtime_search_status['current_phase'] = f"{rotating_message} ({progress_percentage}%)"
            else:
                # Keep current message but update percentage
                current_msg = realtime_search_status.get('current_phase', 'Processing...')
                # Remove old percentage and add new one
                if '(' in current_msg and current_msg.endswith('%)'):
                    current_msg = current_msg.rsplit('(', 1)[0].strip()
                realtime_search_status['current_phase'] = f"{current_msg} ({progress_percentage}%)"
            
            # Scale BrightData progress (0-100) to fit our overall progress range (e.g., 20-80%)
            realtime_search_status['progress'] = 20 + (progress_percentage * 0.6) 
            
            logger.info(f"⏳ LinkedIn Polling Update: {progress_percentage}% - {realtime_search_status['current_phase']}")

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
        realtime_search_status['current_phase'] = 'Converting and storing jobs in database...'
        realtime_search_status['progress'] = 90
        
        stored_count = 0
        duplicates_count = 0
        converted_jobs = []  # Initialize outside the if block
        
        if jobs: # Ensure there are jobs to store
            # Convert ALL jobs at once from LinkedIn API format to standard format
            try:
                logger.info(f"🔄 Converting {len(jobs)} jobs from LinkedIn API format to standard format...")
                converted_jobs = linkedin_scraper.convert_to_standard_format(jobs)
                logger.info(f"✅ Successfully converted {len(converted_jobs)} jobs")
                
                # Store each converted job
                for converted_job in converted_jobs:
                    if isinstance(converted_job, dict):
                        # Add session_id to the job data
                        converted_job['session_id'] = session_id
                        
                        # Check if job already exists for this session
                        job_id = db.generate_job_id(
                            converted_job.get('url', ''),
                            converted_job.get('job_title', ''),
                            converted_job.get('company', '')
                        )
                        
                        if db.job_exists(job_id, session_id):
                            duplicates_count += 1
                            continue
                            
                        if db.insert_job(converted_job):
                            stored_count += 1
                        else:
                            duplicates_count += 1
                            logger.debug(f"Job already exists or failed to insert: {converted_job.get('job_title', 'Unknown Title')}")
                    else:
                        logger.warning(f"⚠️ Skipping non-dict converted job: {type(converted_job)}")
                        
            except Exception as e:
                logger.error(f"❌ Error during job conversion: {e}")
                logger.debug(f"🔍 Raw jobs data that failed conversion: {json.dumps(jobs[:2], indent=2)}...")  # Log first 2 jobs only
        
        logger.info(f"💾 Stored {stored_count}/{len(jobs) if jobs else 0} jobs in the database.")
        
        # Calculate and log AI search accuracy for the real-time search
        search_query = realtime_search_status.get('search_query', '')
        if search_query and converted_jobs:
            try:
                logger.info(f"🤖 Calculating AI search accuracy for query: '{search_query}'")
                
                # Import NLP functions
                from .nlp_utils import get_embedding, calculate_cosine_similarity
                
                query_embedding = get_embedding(search_query)
                num_relevant_nlp = 0
                
                for job in converted_jobs:
                    job_text = f"{job.get('job_title', '')} {job.get('description', '')}"
                    if not job_text.strip():
                        continue
                    job_embedding = get_embedding(job_text)
                    similarity = calculate_cosine_similarity(query_embedding, job_embedding)
                    
                    if similarity >= SIMILARITY_THRESHOLD:
                        num_relevant_nlp += 1
                
                num_shown = len(converted_jobs)
                if num_shown > 0:
                    ai_accuracy = (num_relevant_nlp / num_shown) * 100
                    db.log_search_event(session_id, search_query, num_shown, num_relevant_nlp, ai_accuracy)
                    logger.info(f"✅ Logged search accuracy: {ai_accuracy:.2f}% ({num_relevant_nlp}/{num_shown} relevant)")
                else:
                    db.log_search_event(session_id, search_query, 0, 0, 0.0)
                    logger.info("📊 Logged search event with 0 results")
                    
            except Exception as e:
                logger.error(f"❌ Error calculating search accuracy: {e}")
                # Log the search event anyway, even without accuracy
                try:
                    db.log_search_event(session_id, search_query, len(converted_jobs) if converted_jobs else 0, 0, 0.0)
                except Exception as log_error:
                    logger.error(f"❌ Error logging search event: {log_error}")
        
        # Update final results
        realtime_search_status['results'].update({
            'urls_discovered': len(jobs) if jobs else 0,
            'jobs_stored': stored_count,
            'duplicates': duplicates_count
        })
        realtime_search_status['progress'] = 100
        realtime_search_status['current_phase'] = f'Search completed. {stored_count} jobs stored, {duplicates_count} duplicates skipped.'
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
        session_id = get_or_create_session_id()
        
        if not job_id:
            return jsonify({'success': False, 'error': 'Missing job_id'})
        
        # First check if the job belongs to this session
        jobs = db.get_jobs(session_id=session_id)
        job_exists = any(j['job_id'] == job_id for j in jobs)
        
        if not job_exists:
            return jsonify({'success': False, 'error': 'Job not found or not accessible'})
        
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
        session_id = get_or_create_session_id()
        
        # Get all jobs for this session
        jobs = db.get_jobs(session_id=session_id)
        session_job_ids = [j['job_id'] for j in jobs]
        
        deleted_count = 0
        
        if delete_type == 'selected' and job_ids:
            # Delete specific jobs (only if they belong to this session)
            for job_id in job_ids:
                if job_id in session_job_ids and db.delete_job(job_id):
                    deleted_count += 1
        elif delete_type == 'status' and status:
            # Delete all jobs with specific status (only for this session)
            for job in jobs:
                if job['status'] == status and db.delete_job(job['job_id']):
                    deleted_count += 1
        elif delete_type == 'all':
            # Delete all jobs for this session
            for job in jobs:
                if db.delete_job(job['job_id']):
                    deleted_count += 1
        
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
        
        # Get session ID in the request context
        session_id = get_or_create_session_id()
        
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
            args=(search_term, max_results, session_id)
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


def run_mcp_search_wrapper(search_term, max_results, session_id):
    """
    Wrapper function to run async MCP search in a thread
    """
    asyncio.run(run_mcp_search_async(search_term, max_results, session_id))

async def run_mcp_search_async(search_term, max_results, session_id):
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
        
        # Check if DISCOVER was successful
        if not discover_result.success:
            error_msg = discover_result.metadata.get('error', 'Unknown error in DISCOVER phase')
            logger.error(f"❌ MCP search failed: {error_msg}")
            mcp_search_status['error'] = error_msg
            mcp_search_status['is_running'] = False
            mcp_search_status['completed_at'] = datetime.now().isoformat()
            mcp_search_status['progress'] = 100
            return
        
        mcp_search_status['progress'] = 30
        mcp_search_status['results']['discovered_urls'] = len(discover_result.data.get('job_urls', []))
        
        # Get the enhanced jobs data which contains the raw job data from the API
        enhanced_jobs = discover_result.data.get('enhanced_jobs', [])
        
        # Action 2: ACCESS - Context-aware page navigation
        mcp_search_status['current_action'] = 'ACCESS'
        mcp_search_status['current_phase'] = 'Context-aware page navigation...'
        mcp_search_status['progress'] = 40
        
        logger.info(f"🌐 MCP ACCESS: Context-aware navigation for {len(discover_result.data.get('job_urls', []))} URLs")
        
        # Access multiple job pages
        job_urls = discover_result.data.get('job_urls', [])[:max_results]
        accessed_pages = []
        
        for i, url in enumerate(job_urls[:3]):  # Access first 3 for demo
            if not mcp_search_status['is_running']:
                logger.info("MCP search cancelled by user")
                return
                
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
            if not mcp_search_status['is_running']:
                logger.info("MCP search cancelled by user")
                return
                
            # Find the corresponding raw job data from the API
            raw_job_data = None
            for job in enhanced_jobs:
                if job['url'] == page['url']:
                    raw_job_data = job
                    break
            
            extract_result = await mcp_handler.extract_job_data(
                html_content=page['page_data']['html_content'],
                url=page['url'],
                context={"llm_powered": True, "intelligent_parsing": True, "raw_job_data": raw_job_data}
            )
            
            if extract_result.success:
                extracted_jobs.append(extract_result.data)
            
            # Update progress
            mcp_search_status['progress'] = 60 + (i + 1) * 5
        
        mcp_search_status['results']['extracted_jobs'] = len(extracted_jobs)
        
        # Action 4: INTERACT - AI-powered analysis
        mcp_search_status['current_action'] = 'INTERACT'
        mcp_search_status['current_phase'] = 'AI-powered job analysis...'
        mcp_search_status['progress'] = 80
        
        logger.info(f"🤖 MCP INTERACT: AI-powered analysis of {len(extracted_jobs)} jobs")
        
        enhanced_jobs = []
        
        for i, job in enumerate(extracted_jobs):
            if not mcp_search_status['is_running']:
                logger.info("MCP search cancelled by user")
                return
                
            interact_result = await mcp_handler.interact_and_analyze(
                job_data=job,
                user_profile={'search_term': search_term, 'preferences': {}}
            )
            
            if interact_result.success:
                enhanced_jobs.append(interact_result.data)
            
            # Update progress
            mcp_search_status['progress'] = 80 + (i + 1) * 5
        
        mcp_search_status['results']['analyzed_jobs'] = len(enhanced_jobs)
        
        # Store jobs in the database
        stored_count = 0
        
        for job in enhanced_jobs:
            if not mcp_search_status['is_running']:
                logger.info("MCP search cancelled by user")
                return
                
            # Generate a unique job ID
            job_id = str(uuid.uuid4())
            
            # Extract job data
            job_data = {
                'job_id': job_id,
                'url': job['url'],
                'source': 'MCP_' + job.get('source', 'LinkedIn'),
                'job_title': job['title'],
                'company': job['company'],
                'location': job['location'],
                'description': job.get('description', ''),
                'requirements': job.get('requirements', ''),
                'salary': job.get('salary', ''),
                'posted_date': job.get('posted_date', ''),
                'job_type': job.get('job_type', 'Full-time'),
                'experience_level': job.get('experience_level', ''),
                'sector': job.get('industry', ''),
                'extracted_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'content_length': len(job.get('description', '')),
                'status': 'new',
                'session_id': session_id,
                'raw_data': json.dumps(job)
            }
            
            # Insert job into database
            success = db.insert_job(job_data)
            
            if success:
                stored_count += 1
                logger.info(f"✅ Stored MCP job {stored_count}: {job['title']} at {job['company']}")
        
        # Complete the search
        mcp_search_status['progress'] = 100
        mcp_search_status['current_phase'] = 'Search completed successfully'
        mcp_search_status['is_running'] = False
        mcp_search_status['completed_at'] = datetime.now().isoformat()
        mcp_search_status['results']['stored_jobs'] = stored_count
        
        # Get performance metrics
        mcp_search_status['performance_metrics'] = mcp_handler.get_performance_summary()
        
        logger.info(f"✅ MCP search completed: {stored_count} enhanced jobs stored")
        
    except Exception as e:
        logger.error(f"❌ MCP search failed: {str(e)}")
        logger.error(traceback.format_exc())
        mcp_search_status['error'] = str(e)
        mcp_search_status['is_running'] = False
        mcp_search_status['completed_at'] = datetime.now().isoformat()
        mcp_search_status['progress'] = 100

# ==================== END MCP ROUTES ====================

@app.route('/api/session', methods=['GET'])
def api_session():
    """API endpoint to get or create a session ID"""
    try:
        # Get or create session ID
        session_id = get_or_create_session_id()
        
        return jsonify({
            'success': True,
            'session_id': session_id
        })
        
    except Exception as e:
        logger.error(f"Error getting session ID: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

if __name__ == '__main__':
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        debug=WEB_CONFIG['debug']
    )