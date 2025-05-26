#!/usr/bin/env python3
"""
Test Session Isolation Functionality

This script tests that the session isolation features are working correctly
by simulating multiple users and verifying that their job data remains isolated.
"""

import sys
import os
import unittest
import json
import uuid
import random
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database_manager import DatabaseManager
from config import DATABASE_CONFIG

class TestSessionIsolation(unittest.TestCase):
    """Test cases for session isolation functionality"""
    
    def setUp(self):
        """Set up test environment with in-memory database"""
        # Use in-memory database for testing
        self.db = DatabaseManager(':memory:')
        
        # Create test session IDs
        self.session_1 = str(uuid.uuid4())
        self.session_2 = str(uuid.uuid4())
        
        # Sample job data
        self.job_data_template = {
            'source': 'Test',
            'job_type': 'Full-time',
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 1000
            }
        }
        
        # Create sample jobs for each session
        self.session_1_jobs = self._create_test_jobs(self.session_1, 5, "Company A")
        self.session_2_jobs = self._create_test_jobs(self.session_2, 5, "Company B")
    
    def _create_test_jobs(self, session_id, count, company_prefix):
        """Create test job data for a session"""
        jobs = []
        for i in range(count):
            job = self.job_data_template.copy()
            job.update({
                'url': f'https://example.com/job/{session_id[:8]}/{i}',
                'job_title': f'Test Job {i} for Session {session_id[:8]}',
                'company': f'{company_prefix} {i}',
                'location': f'Location {i}',
                'description': f'Job description {i} for session {session_id[:8]}',
                'session_id': session_id
            })
            jobs.append(job)
        return jobs
    
    def test_insert_jobs_with_sessions(self):
        """Test inserting jobs with different session IDs"""
        # Insert jobs for session 1
        for job in self.session_1_jobs:
            self.assertTrue(self.db.insert_job(job))
        
        # Insert jobs for session 2
        for job in self.session_2_jobs:
            self.assertTrue(self.db.insert_job(job))
        
        # Verify total job count
        all_jobs = self.db.get_jobs(limit=100)
        self.assertEqual(len(all_jobs), 10)
    
    def test_get_jobs_by_session(self):
        """Test retrieving jobs filtered by session ID"""
        # Insert all test jobs
        for job in self.session_1_jobs + self.session_2_jobs:
            self.db.insert_job(job)
        
        # Get jobs for session 1
        session_1_jobs = self.db.get_jobs(session_id=self.session_1)
        self.assertEqual(len(session_1_jobs), 5)
        for job in session_1_jobs:
            self.assertEqual(job['session_id'], self.session_1)
        
        # Get jobs for session 2
        session_2_jobs = self.db.get_jobs(session_id=self.session_2)
        self.assertEqual(len(session_2_jobs), 5)
        for job in session_2_jobs:
            self.assertEqual(job['session_id'], self.session_2)
    
    def test_job_exists_with_session(self):
        """Test job_exists with session filtering"""
        # Insert a job for session 1
        test_job = self.session_1_jobs[0]
        self.db.insert_job(test_job)
        
        # Generate job_id for the test job
        job_id = self.db.generate_job_id(
            test_job['url'],
            test_job['job_title'],
            test_job['company']
        )
        
        # Job should exist globally
        self.assertTrue(self.db.job_exists(job_id))
        
        # Job should exist in session 1
        self.assertTrue(self.db.job_exists(job_id, self.session_1))
        
        # Job should NOT exist in session 2
        self.assertFalse(self.db.job_exists(job_id, self.session_2))
    
    def test_get_job_stats_by_session(self):
        """Test getting job statistics filtered by session"""
        # Insert all test jobs
        for job in self.session_1_jobs + self.session_2_jobs:
            self.db.insert_job(job)
        
        # Update status for some jobs in session 1
        session_1_job_ids = [
            self.db.generate_job_id(job['url'], job['job_title'], job['company'])
            for job in self.session_1_jobs
        ]
        self.db.update_job_status(session_1_job_ids[0], 'Applied')
        self.db.update_job_status(session_1_job_ids[1], 'Interview')
        
        # Update status for some jobs in session 2
        session_2_job_ids = [
            self.db.generate_job_id(job['url'], job['job_title'], job['company'])
            for job in self.session_2_jobs
        ]
        self.db.update_job_status(session_2_job_ids[0], 'Rejected')
        
        # Get stats for session 1
        stats_1 = self.db.get_job_stats(session_id=self.session_1)
        self.assertEqual(stats_1['total_jobs'], 5)
        self.assertIn('Applied', stats_1['by_status'])
        self.assertIn('Interview', stats_1['by_status'])
        self.assertNotIn('Rejected', stats_1['by_status'])
        
        # Get stats for session 2
        stats_2 = self.db.get_job_stats(session_id=self.session_2)
        self.assertEqual(stats_2['total_jobs'], 5)
        self.assertIn('Rejected', stats_2['by_status'])
        self.assertNotIn('Applied', stats_2['by_status'])
        self.assertNotIn('Interview', stats_2['by_status'])
    
    def test_search_jobs_by_session(self):
        """Test searching jobs with session filtering"""
        # Insert all test jobs
        for job in self.session_1_jobs + self.session_2_jobs:
            self.db.insert_job(job)
        
        # Search for "Test Job" in session 1
        results_1 = self.db.search_jobs("Test Job", session_id=self.session_1)
        self.assertEqual(len(results_1), 5)
        for job in results_1:
            self.assertEqual(job['session_id'], self.session_1)
        
        # Search for "Test Job" in session 2
        results_2 = self.db.search_jobs("Test Job", session_id=self.session_2)
        self.assertEqual(len(results_2), 5)
        for job in results_2:
            self.assertEqual(job['session_id'], self.session_2)
        
        # Search for "Company A" in session 1 (should find all)
        results_a1 = self.db.search_jobs("Company A", session_id=self.session_1)
        self.assertEqual(len(results_a1), 5)
        
        # Search for "Company A" in session 2 (should find none)
        results_a2 = self.db.search_jobs("Company A", session_id=self.session_2)
        self.assertEqual(len(results_a2), 0)
    
    def test_duplicate_job_across_sessions(self):
        """Test that identical jobs can exist in different sessions"""
        # Create identical job data for both sessions
        identical_job_1 = {
            'url': 'https://example.com/job/identical',
            'source': 'Test',
            'job_title': 'Identical Job',
            'company': 'Same Company',
            'description': 'Same description',
            'job_type': 'Full-time',
            'session_id': self.session_1,
            'extraction_metadata': {
                'extracted_at': datetime.now().isoformat(),
                'content_length': 1000
            }
        }
        
        identical_job_2 = identical_job_1.copy()
        identical_job_2['session_id'] = self.session_2
        
        # Insert both jobs
        self.assertTrue(self.db.insert_job(identical_job_1))
        self.assertTrue(self.db.insert_job(identical_job_2))
        
        # Get jobs for each session
        session_1_jobs = self.db.get_jobs(session_id=self.session_1)
        session_2_jobs = self.db.get_jobs(session_id=self.session_2)
        
        # Each session should have one job
        self.assertEqual(len(session_1_jobs), 1)
        self.assertEqual(len(session_2_jobs), 1)
        
        # Jobs should have the same title but different session IDs
        self.assertEqual(session_1_jobs[0]['job_title'], 'Identical Job')
        self.assertEqual(session_2_jobs[0]['job_title'], 'Identical Job')
        self.assertEqual(session_1_jobs[0]['session_id'], self.session_1)
        self.assertEqual(session_2_jobs[0]['session_id'], self.session_2)

if __name__ == '__main__':
    unittest.main() 