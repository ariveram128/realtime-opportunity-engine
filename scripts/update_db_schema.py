#!/usr/bin/env python3
"""
Database Schema Migration Script

This script updates the database schema to add session_id column
and modify the unique constraint to include session_id.
"""

import os
import sys
import sqlite3
import logging

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import DATABASE_CONFIG

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_schema():
    """Update the database schema to support session isolation"""
    db_path = DATABASE_CONFIG['db_path']
    jobs_table = DATABASE_CONFIG['jobs_table']
    
    logger.info(f"Updating schema for database at {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if session_id column already exists
        cursor.execute(f"PRAGMA table_info({jobs_table})")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'session_id' not in columns:
            logger.info(f"Adding session_id column to {jobs_table} table")
            
            # Create a new table with the updated schema
            cursor.execute(f'''
                CREATE TABLE {jobs_table}_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT NOT NULL,
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
                    session_id TEXT DEFAULT 'default',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(job_id, session_id)
                )
            ''')
            
            # Copy data from old table to new table
            logger.info("Migrating existing data to new schema")
            cursor.execute(f'''
                INSERT INTO {jobs_table}_new (
                    id, job_id, url, source, job_title, company, location, job_type,
                    experience_level, description, requirements, salary, company_size,
                    sector, employees_info, posted_date, application_deadline,
                    extracted_at, content_length, status, applied_date, notes,
                    rating, raw_data, created_at, updated_at
                )
                SELECT
                    id, job_id, url, source, job_title, company, location, job_type,
                    experience_level, description, requirements, salary, company_size,
                    sector, employees_info, posted_date, application_deadline,
                    extracted_at, content_length, status, applied_date, notes,
                    rating, raw_data, created_at, updated_at
                FROM {jobs_table}
            ''')
            
            # Drop the old table and rename the new one
            logger.info("Replacing old table with new schema")
            cursor.execute(f"DROP TABLE {jobs_table}")
            cursor.execute(f"ALTER TABLE {jobs_table}_new RENAME TO {jobs_table}")
            
            # Recreate indexes
            logger.info("Recreating indexes")
            cursor.execute(f'CREATE INDEX idx_job_id ON {jobs_table} (job_id)')
            cursor.execute(f'CREATE INDEX idx_company ON {jobs_table} (company)')
            cursor.execute(f'CREATE INDEX idx_location ON {jobs_table} (location)')
            cursor.execute(f'CREATE INDEX idx_status ON {jobs_table} (status)')
            cursor.execute(f'CREATE INDEX idx_extracted_at ON {jobs_table} (extracted_at)')
            cursor.execute(f'CREATE INDEX idx_session_id ON {jobs_table} (session_id)')
            
            # Commit the changes
            conn.commit()
            logger.info("Schema update completed successfully")
        else:
            logger.info("session_id column already exists, no update needed")
    
    except sqlite3.Error as e:
        logger.error(f"Error updating schema: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    update_schema() 