#!/usr/bin/env python3
"""
AI Internship Opportunity Finder - Web Interface
Enhanced Flask application for managing job applications
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

# Local imports
from database_manager import DatabaseManager
from config import WEB_CONFIG

# Initialize Flask app
app = Flask(__name__)
app.secret_key = WEB_CONFIG.get('secret_key', 'dev-key-change-in-production')

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Search page with advanced filters"""
    return render_template('search.html')


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


if __name__ == '__main__':
    app.run(
        host=WEB_CONFIG['host'],
        port=WEB_CONFIG['port'],
        debug=WEB_CONFIG['debug']
    ) 