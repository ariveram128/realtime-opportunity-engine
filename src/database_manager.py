"""
Database Manager for AI Internship Opportunity Finder
Inspired by LinkedIn Job Scraper's database approach
Handles SQLite operations for job storage and management
"""

import sqlite3
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config import DATABASE_CONFIG, JOB_STATUS
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations for internship opportunities
    """
    
    def __init__(self, db_path: str = None):
        """
        Initialize database connection and create tables if they don't exist
        
        Args:
            db_path (str): Path to SQLite database file
        """
        self.db_path = db_path or DATABASE_CONFIG['db_path']
        self.jobs_table = DATABASE_CONFIG['jobs_table']
        self.filtered_jobs_table = DATABASE_CONFIG['filtered_jobs_table']
        
        # For in-memory databases, keep a persistent connection
        self._conn = None
        if self.db_path == ':memory:':
            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        
        self.init_database()
    
    def _get_connection(self):
        """Get database connection (persistent for in-memory, new for file-based)"""
        if self._conn:
            return self._conn
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Create database tables if they don't exist"""
        conn = self._get_connection()
        close_conn = not self._conn  # Only close if not persistent
        
        try:
            cursor = conn.cursor()
            
            # Main jobs table
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.jobs_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT UNIQUE NOT NULL,
                    url TEXT NOT NULL,
                    source TEXT NOT NULL,
                    job_title TEXT,
                    company TEXT,
                    location TEXT,
                    job_type TEXT,
                    experience_level TEXT,
                    description TEXT,
                    requirements TEXT,
                    salary TEXT,
                    company_size TEXT,
                    sector TEXT,
                    employees_info TEXT,
                    posted_date TEXT,
                    application_deadline TEXT,
                    extracted_at TEXT NOT NULL,
                    content_length INTEGER,
                    status TEXT DEFAULT 'new',
                    applied_date TEXT,
                    notes TEXT,
                    rating INTEGER,
                    raw_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Filtered jobs table (jobs that passed filtering criteria)
            cursor.execute(f'''
                CREATE TABLE IF NOT EXISTS {self.filtered_jobs_table} (
                    id INTEGER PRIMARY KEY,
                    job_id TEXT UNIQUE NOT NULL,
                    filter_reason TEXT,
                    filtered_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (job_id) REFERENCES {self.jobs_table} (job_id)
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_job_id ON {self.jobs_table} (job_id)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_company ON {self.jobs_table} (company)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_location ON {self.jobs_table} (location)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_status ON {self.jobs_table} (status)')
            cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_extracted_at ON {self.jobs_table} (extracted_at)')
            
            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")
            
        except sqlite3.Error as e:
            logger.error(f"Error initializing database: {e}")
            raise
        finally:
            if close_conn:
                conn.close()
    
    def generate_job_id(self, url: str, title: str, company: str) -> str:
        """
        Generate a unique job ID based on URL, title, and company
        
        Args:
            url (str): Job URL
            title (str): Job title
            company (str): Company name
        
        Returns:
            str: Unique job ID hash
        """
        # Create a unique identifier from URL, title, and company
        content = f"{url}|{title or ''}|{company or ''}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def job_exists(self, job_id: str) -> bool:
        """
        Check if a job already exists in the database
        
        Args:
            job_id (str): Unique job ID
        
        Returns:
            bool: True if job exists, False otherwise
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            cursor.execute(f'SELECT 1 FROM {self.jobs_table} WHERE job_id = ?', (job_id,))
            result = cursor.fetchone() is not None
            return result
        except sqlite3.OperationalError as e:
            # Table doesn't exist yet
            logger.warning(f"Table doesn't exist: {e}")
            return False
        except sqlite3.Error as e:
            logger.error(f"Error checking job existence: {e}")
            return False
        finally:
            if close_conn:
                conn.close()
    
    def insert_job(self, job_data: Dict) -> bool:
        """
        Insert a new job into the database
        
        Args:
            job_data (Dict): Job data extracted from job posting
        
        Returns:
            bool: True if inserted successfully, False if duplicate
        """
        # Generate unique job ID
        job_id = self.generate_job_id(
            job_data.get('url', ''),
            job_data.get('job_title', ''),
            job_data.get('company', '')
        )
        
        # Check if job already exists
        if self.job_exists(job_id):
            logger.debug(f"Job already exists: {job_id}")
            return False
        
        # Prepare data for insertion
        insert_data = {
            'job_id': job_id,
            'url': job_data.get('url', ''),
            'source': job_data.get('source', ''),
            'job_title': job_data.get('job_title'),
            'company': job_data.get('company'),
            'location': job_data.get('location'),
            'job_type': job_data.get('job_type'),
            'experience_level': job_data.get('experience_level'),
            'description': job_data.get('description'),
            'requirements': job_data.get('requirements'),
            'salary': job_data.get('salary'),
            'company_size': job_data.get('company_size'),
            'sector': job_data.get('sector'),
            'employees_info': job_data.get('employees_info'),
            'posted_date': job_data.get('posted_date'),
            'application_deadline': job_data.get('application_deadline'),
            'extracted_at': job_data.get('extraction_metadata', {}).get('extracted_at', datetime.now().isoformat()),
            'content_length': job_data.get('extraction_metadata', {}).get('content_length', 0),
            'raw_data': json.dumps(job_data)
        }
        
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            placeholders = ', '.join(['?' for _ in insert_data])
            columns = ', '.join(insert_data.keys())
            values = list(insert_data.values())
            
            cursor.execute(f'''
                INSERT INTO {self.jobs_table} ({columns})
                VALUES ({placeholders})
            ''', values)
            
            conn.commit()
            logger.info(f"Inserted job: {job_data.get('job_title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error inserting job: {e}")
            return False
        finally:
            if close_conn:
                conn.close()
    
    def update_job_status(self, job_id: str, status: str, notes: str = None) -> bool:
        """
        Update job status (applied, rejected, interview, etc.)
        
        Args:
            job_id (str): Unique job ID
            status (str): New status
            notes (str): Optional notes
        
        Returns:
            bool: True if updated successfully
        """
        if status not in JOB_STATUS.values():
            logger.error(f"Invalid status: {status}")
            return False
        
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            update_data = {
                'status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            if status == 'applied':
                update_data['applied_date'] = datetime.now().isoformat()
            
            if notes:
                update_data['notes'] = notes
            
            set_clause = ', '.join([f"{k} = ?" for k in update_data.keys()])
            values = list(update_data.values()) + [job_id]
            
            cursor.execute(f'''
                UPDATE {self.jobs_table}
                SET {set_clause}
                WHERE job_id = ?
            ''', values)
            
            conn.commit()
            logger.info(f"Updated job {job_id} status to {status}")
            return True
            
        except sqlite3.Error as e:
            logger.error(f"Error updating job status: {e}")
            return False
        finally:
            if close_conn:
                conn.close()
    
    def get_jobs(self, status: str = None, limit: int = 100, offset: int = 0) -> List[Dict]:
        """
        Retrieve jobs from database with optional filtering
        
        Args:
            status (str): Filter by status (optional)
            limit (int): Maximum number of jobs to return
            offset (int): Number of jobs to skip
        
        Returns:
            List[Dict]: List of job dictionaries
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            query = f'SELECT * FROM {self.jobs_table}'
            params = []
            
            if status:
                query += ' WHERE status = ?'
                params.append(status)
            
            query += ' ORDER BY extracted_at DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error retrieving jobs: {e}")
            return []
        finally:
            if close_conn:
                conn.close()
    
    def get_job_stats(self) -> Dict:
        """
        Get statistics about jobs in the database
        
        Returns:
            Dict: Statistics including counts by status, company, etc.
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total jobs
            cursor.execute(f'SELECT COUNT(*) FROM {self.jobs_table}')
            stats['total_jobs'] = cursor.fetchone()[0]
            
            # Jobs by status
            cursor.execute(f'''
                SELECT status, COUNT(*) 
                FROM {self.jobs_table} 
                GROUP BY status
            ''')
            stats['by_status'] = dict(cursor.fetchall())
            
            # Jobs by company (top 10)
            cursor.execute(f'''
                SELECT company, COUNT(*) 
                FROM {self.jobs_table} 
                WHERE company IS NOT NULL
                GROUP BY company 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            ''')
            stats['top_companies'] = dict(cursor.fetchall())
            
            # Jobs by location (top 10)
            cursor.execute(f'''
                SELECT location, COUNT(*) 
                FROM {self.jobs_table} 
                WHERE location IS NOT NULL
                GROUP BY location 
                ORDER BY COUNT(*) DESC 
                LIMIT 10
            ''')
            stats['top_locations'] = dict(cursor.fetchall())
            
            # Recent jobs (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute(f'''
                SELECT COUNT(*) 
                FROM {self.jobs_table} 
                WHERE extracted_at >= ?
            ''', (week_ago,))
            stats['recent_jobs'] = cursor.fetchone()[0]
            
            return stats
        except sqlite3.Error as e:
            logger.error(f"Error getting job stats: {e}")
            return {'total_jobs': 0, 'by_status': {}, 'top_companies': {}, 'top_locations': {}, 'recent_jobs': 0}
        finally:
            if close_conn:
                conn.close()
    
    def search_jobs(self, query: str, fields: List[str] = None) -> List[Dict]:
        """
        Search jobs by text query in specified fields
        
        Args:
            query (str): Search query
            fields (List[str]): Fields to search in
        
        Returns:
            List[Dict]: Matching jobs
        """
        if not fields:
            fields = ['job_title', 'company', 'description', 'location']
        
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Build search conditions
            conditions = []
            params = []
            
            for field in fields:
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{query}%")
            
            where_clause = " OR ".join(conditions)
            
            cursor.execute(f'''
                SELECT * FROM {self.jobs_table}
                WHERE ({where_clause})
                AND status != 'hidden'
                ORDER BY extracted_at DESC
            ''', params)
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Error searching jobs: {e}")
            return []
        finally:
            if close_conn:
                conn.close()
    
    def cleanup_old_jobs(self, days: int = 90) -> int:
        """
        Remove jobs older than specified days
        
        Args:
            days (int): Number of days to keep
        
        Returns:
            int: Number of jobs removed
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                DELETE FROM {self.jobs_table}
                WHERE extracted_at < ? AND status NOT IN ('applied', 'interview')
            ''', (cutoff_date,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Cleaned up {deleted_count} old jobs")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error cleaning up jobs: {e}")
            return 0
        finally:
            if close_conn:
                conn.close()
    
    def delete_job(self, job_id: str) -> bool:
        """
        Delete a single job by job_id
        
        Args:
            job_id (str): Unique job ID
        
        Returns:
            bool: True if deleted successfully
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                DELETE FROM {self.jobs_table}
                WHERE job_id = ?
            ''', (job_id,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logger.info(f"Deleted job: {job_id}")
            
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Error deleting job {job_id}: {e}")
            return False
        finally:
            if close_conn:
                conn.close()
    
    def delete_jobs_by_status(self, status: str) -> int:
        """
        Delete all jobs with a specific status
        
        Args:
            status (str): Status to delete
        
        Returns:
            int: Number of jobs deleted
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            cursor.execute(f'''
                DELETE FROM {self.jobs_table}
                WHERE status = ?
            ''', (status,))
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Deleted {deleted_count} jobs with status: {status}")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error deleting jobs by status {status}: {e}")
            return 0
        finally:
            if close_conn:
                conn.close()
    
    def delete_all_jobs(self) -> int:
        """
        Delete ALL jobs from the database (use with caution!)
        
        Returns:
            int: Number of jobs deleted
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            # First get count for logging
            cursor.execute(f'SELECT COUNT(*) FROM {self.jobs_table}')
            total_count = cursor.fetchone()[0]
            
            # Delete all jobs
            cursor.execute(f'DELETE FROM {self.jobs_table}')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.warning(f"Deleted ALL {deleted_count} jobs from database")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error deleting all jobs: {e}")
            return 0
        finally:
            if close_conn:
                conn.close()
    
    def remove_duplicate_jobs(self) -> int:
        """
        Remove duplicate jobs (keeping the most recent one)
        
        Returns:
            int: Number of duplicate jobs removed
        """
        conn = self._get_connection()
        close_conn = not self._conn
        
        try:
            cursor = conn.cursor()
            
            # Find duplicates based on URL, job_title, and company
            cursor.execute(f'''
                DELETE FROM {self.jobs_table}
                WHERE id NOT IN (
                    SELECT MIN(id)
                    FROM {self.jobs_table}
                    GROUP BY url, job_title, company
                )
            ''')
            
            deleted_count = cursor.rowcount
            conn.commit()
            
            logger.info(f"Removed {deleted_count} duplicate jobs")
            return deleted_count
        except sqlite3.Error as e:
            logger.error(f"Error removing duplicate jobs: {e}")
            return 0
        finally:
            if close_conn:
                conn.close()
    
    def close(self):
        """Close database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None


def test_database():
    """Test database functionality"""
    db = DatabaseManager(':memory:')  # Use in-memory database for testing
    
    # Test job insertion
    test_job = {
        'url': 'https://example.com/job/123',
        'source': 'LinkedIn',
        'job_title': 'Software Engineering Intern',
        'company': 'Test Company',
        'location': 'San Francisco, CA',
        'job_type': 'Internship',
        'description': 'Great internship opportunity...',
        'extraction_metadata': {
            'extracted_at': datetime.now().isoformat(),
            'content_length': 1500
        }
    }
    
    success = db.insert_job(test_job)
    print(f"Job insertion: {'Success' if success else 'Failed'}")
    
    # Test duplicate prevention
    duplicate = db.insert_job(test_job)
    print(f"Duplicate prevention: {'Success' if not duplicate else 'Failed'}")
    
    # Test job retrieval
    jobs = db.get_jobs()
    print(f"Retrieved {len(jobs)} jobs")
    
    # Test stats
    stats = db.get_job_stats()
    print(f"Database stats: {stats}")


if __name__ == "__main__":
    test_database() 