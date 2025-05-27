#!/usr/bin/env python3
"""
Script to test and fix database initialization issues
"""

import sqlite3
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database_manager import DatabaseManager

def test_database_init():
    """Test database initialization"""
    print("🔧 Testing database initialization...")
    
    # Initialize database manager
    db_path = "data/internship_opportunities.db"
    print(f"📁 Using database path: {db_path}")
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Initialize database manager
    db = DatabaseManager(db_path)
    
    # Check if tables were created
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📊 Available tables: {tables}")
    
    # Check specific tables
    required_tables = ['job_postings', 'search_log']
    for table in required_tables:
        if table in tables:
            print(f"✅ {table} table exists")
            
            # Get table schema
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"   📋 Columns: {[col[1] for col in columns]}")
            
            # Get count
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   📊 Record count: {count}")
        else:
            print(f"❌ {table} table missing")
    
    conn.close()
    
    return db

def add_test_data(db):
    """Add some test data to verify functionality"""
    print("\n🧪 Adding test data...")
    
    # Test job insertion
    test_job = {
        'job_id': 'test_job_001',
        'url': 'https://example.com/job/test',
        'source': 'test',
        'job_title': 'Test Software Engineer Intern',
        'company': 'Test Company',
        'location': 'Test City, TC',
        'description': 'This is a test job description for a software engineering internship role.',
        'session_id': 'test_session_001'
    }
    
    success = db.insert_job(test_job)
    print(f"💾 Job insertion: {'✅ Success' if success else '❌ Failed'}")
    
    # Test search log
    db.log_search_event('test_session_001', 'software engineering intern', 5, 3, 60.0)
    print("📝 Search event logged")
    
    # Get stats to verify
    stats = db.get_job_stats('test_session_001')
    print(f"📊 Test stats: {stats}")
    
    avg_accuracy = db.get_average_search_accuracy('test_session_001')
    print(f"💯 Average accuracy: {avg_accuracy}%")

def main():
    """Main test function"""
    print("🚀 Database Test & Fix Script")
    print("=" * 50)
    
    try:
        # Test database initialization
        db = test_database_init()
        
        # Add test data
        add_test_data(db)
        
        print("\n✅ Database test completed successfully!")
        print("🎯 Try accessing the Analytics Dashboard now.")
        
    except Exception as e:
        print(f"\n❌ Error during database test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
