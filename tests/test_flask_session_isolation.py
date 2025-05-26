#!/usr/bin/env python3
"""
Test Flask Session Isolation

This script tests that session isolation works correctly at the Flask API level.
"""

import sys
import os
import unittest
import json
import tempfile
import shutil
from flask import session, Flask

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.app import app, db, get_or_create_session_id

class TestFlaskSessionIsolation(unittest.TestCase):
    """Test cases for Flask session isolation"""
    
    def setUp(self):
        """Set up test environment"""
        # Create a temporary directory for the test database
        self.test_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.test_dir, 'test.db')
        
        # Configure app for testing
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test_key'
        app.config['DATABASE_PATH'] = self.db_path
        
        # Create a test client
        self.client = app.test_client()
        
        # Create a test database
        db.db_path = self.db_path
        db.init_database()
        
        # Sample job data
        self.test_job = {
            'url': 'https://example.com/job/123',
            'source': 'Test',
            'job_title': 'Software Engineer',
            'company': 'Test Company',
            'location': 'Remote',
            'job_type': 'Full-time',
            'description': 'Test job description',
            'extraction_metadata': {
                'extracted_at': '2023-05-25T12:00:00',
                'content_length': 1000
            }
        }
    
    def tearDown(self):
        """Clean up after tests"""
        # Close database connection
        if db._conn:
            db._conn.close()
            db._conn = None
        
        # Remove temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_session_creation(self):
        """Test that sessions are created correctly"""
        with app.test_request_context():
            # Session should not exist initially
            self.assertNotIn('session_id', session)
            
            # Get or create session ID
            session_id = get_or_create_session_id()
            
            # Session ID should now exist
            self.assertIn('session_id', session)
            self.assertEqual(session['session_id'], session_id)
            
            # Should return the same ID on subsequent calls
            session_id2 = get_or_create_session_id()
            self.assertEqual(session_id, session_id2)
    
    def test_different_sessions_see_different_jobs(self):
        """Test that different sessions see different jobs"""
        # Create two test clients with different sessions
        client1 = app.test_client()
        client2 = app.test_client()
        
        # Add a job through client 1's session
        with client1.session_transaction() as sess1:
            sess1['session_id'] = 'test_session_1'
        
        # Simulate job discovery for client 1
        job1 = self.test_job.copy()
        job1['session_id'] = 'test_session_1'
        db.insert_job(job1)
        
        # Add a different job through client 2's session
        with client2.session_transaction() as sess2:
            sess2['session_id'] = 'test_session_2'
        
        job2 = self.test_job.copy()
        job2['job_title'] = 'Data Scientist'
        job2['session_id'] = 'test_session_2'
        db.insert_job(job2)
        
        # Client 1 should only see job 1
        response1 = client1.get('/')
        self.assertIn(b'Software Engineer', response1.data)
        self.assertNotIn(b'Data Scientist', response1.data)
        
        # Client 2 should only see job 2
        response2 = client2.get('/')
        self.assertIn(b'Data Scientist', response2.data)
        self.assertNotIn(b'Software Engineer', response2.data)
    
    def test_job_detail_respects_session(self):
        """Test that job detail page respects session isolation"""
        # Create a job for session 1
        job1 = self.test_job.copy()
        job1['session_id'] = 'test_session_1'
        db.insert_job(job1)
        
        # Get the job ID
        job_id = db.generate_job_id(job1['url'], job1['job_title'], job1['company'])
        
        # Client 1 should be able to access the job
        client1 = app.test_client()
        with client1.session_transaction() as sess1:
            sess1['session_id'] = 'test_session_1'
        
        response1 = client1.get(f'/job/{job_id}')
        self.assertEqual(response1.status_code, 200)
        
        # Client 2 should not be able to access the job
        client2 = app.test_client()
        with client2.session_transaction() as sess2:
            sess2['session_id'] = 'test_session_2'
        
        response2 = client2.get(f'/job/{job_id}')
        self.assertEqual(response2.status_code, 302)  # Should redirect

if __name__ == '__main__':
    unittest.main() 