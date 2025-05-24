#!/usr/bin/env python3
"""
Add sample jobs for testing search functionality
"""

import sys
import os

# Add the parent directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.database_manager import DatabaseManager
from datetime import datetime, timedelta
import json

def add_sample_jobs():
    """Add diverse sample jobs to test search functionality"""
    db = DatabaseManager()
    
    sample_jobs = [
        {
            'url': 'https://linkedin.com/jobs/software-engineer-intern-google-2025',
            'source': 'LinkedIn',
            'job_title': 'Software Engineer Intern - Summer 2025',
            'company': 'Google',
            'location': 'Mountain View, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Join Google as a Software Engineer Intern! Work on cutting-edge projects using Python, Java, and machine learning. Build scalable systems and collaborate with world-class engineers.',
            'requirements': 'Currently pursuing CS degree, knowledge of Python/Java, strong problem-solving skills',
            'salary': '$8,000/month',
            'company_size': '100,000+ employees',
            'sector': 'Technology',
            'posted_date': '2024-12-01',
            'extracted_at': datetime.now().isoformat(),
            'content_length': 250,
            'status': 'New'
        },
        {
            'url': 'https://indeed.com/jobs/data-science-intern-microsoft-2025',
            'source': 'Indeed',
            'job_title': 'Data Science Intern',
            'company': 'Microsoft',
            'location': 'Seattle, WA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Microsoft is seeking a Data Science Intern to work on AI and machine learning projects. Use Python, R, and Azure to analyze large datasets and build predictive models.',
            'requirements': 'Statistics/Data Science background, Python, SQL, machine learning experience',
            'salary': '$7,500/month',
            'company_size': '50,000-100,000 employees',
            'sector': 'Technology',
            'posted_date': '2024-11-28',
            'extracted_at': (datetime.now() - timedelta(days=1)).isoformat(),
            'content_length': 280,
            'status': 'New'
        },
        {
            'url': 'https://linkedin.com/jobs/frontend-developer-intern-meta-2025',
            'source': 'LinkedIn',
            'job_title': 'Frontend Developer Intern',
            'company': 'Meta',
            'location': 'Menlo Park, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Build user interfaces for billions of users! Work with React, JavaScript, and modern web technologies. Collaborate with designers and product managers.',
            'requirements': 'JavaScript, React, HTML/CSS, portfolio of projects',
            'salary': '$8,500/month',
            'company_size': '50,000-100,000 employees',
            'sector': 'Technology',
            'posted_date': '2024-11-30',
            'extracted_at': (datetime.now() - timedelta(hours=12)).isoformat(),
            'content_length': 220,
            'status': 'New'
        },
        {
            'url': 'https://indeed.com/jobs/mobile-developer-intern-apple-2025',
            'source': 'Indeed',
            'job_title': 'iOS Developer Intern',
            'company': 'Apple',
            'location': 'Cupertino, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Develop innovative iOS applications! Work with Swift, SwiftUI, and cutting-edge mobile technologies. Create apps used by millions worldwide.',
            'requirements': 'Swift programming, iOS development, computer science background',
            'salary': '$9,000/month',
            'company_size': '100,000+ employees',
            'sector': 'Technology',
            'posted_date': '2024-12-02',
            'extracted_at': (datetime.now() - timedelta(hours=6)).isoformat(),
            'content_length': 195,
            'status': 'New'
        },
        {
            'url': 'https://linkedin.com/jobs/backend-engineer-intern-netflix-2025',
            'source': 'LinkedIn',
            'job_title': 'Backend Engineer Intern',
            'company': 'Netflix',
            'location': 'Los Gatos, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Build the infrastructure that powers Netflix! Work with Java, Python, and distributed systems. Handle massive scale and streaming technologies.',
            'requirements': 'Java or Python, distributed systems knowledge, algorithms and data structures',
            'salary': '$8,200/month',
            'company_size': '10,000-50,000 employees',
            'sector': 'Entertainment',
            'posted_date': '2024-11-29',
            'extracted_at': (datetime.now() - timedelta(days=2)).isoformat(),
            'content_length': 240,
            'status': 'New'
        },
        {
            'url': 'https://indeed.com/jobs/machine-learning-intern-openai-2025',
            'source': 'Indeed',
            'job_title': 'Machine Learning Research Intern',
            'company': 'OpenAI',
            'location': 'San Francisco, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Research and develop cutting-edge AI models! Work on large language models, computer vision, and reinforcement learning. Contribute to the future of AI.',
            'requirements': 'Machine learning background, Python, PyTorch/TensorFlow, research experience',
            'salary': '$10,000/month',
            'company_size': '1,000-5,000 employees',
            'sector': 'Technology',
            'posted_date': '2024-12-03',
            'extracted_at': (datetime.now() - timedelta(hours=3)).isoformat(),
            'content_length': 290,
            'status': 'New'
        },
        {
            'url': 'https://linkedin.com/jobs/product-management-intern-airbnb-2025',
            'source': 'LinkedIn',
            'job_title': 'Product Management Intern',
            'company': 'Airbnb',
            'location': 'San Francisco, CA',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Drive product strategy for travel experiences! Work with engineering and design teams. Analyze user data and create product roadmaps.',
            'requirements': 'Business or technical background, analytical skills, product thinking',
            'salary': '$7,000/month',
            'company_size': '5,000-10,000 employees',
            'sector': 'Technology',
            'posted_date': '2024-11-27',
            'extracted_at': (datetime.now() - timedelta(days=3)).isoformat(),
            'content_length': 180,
            'status': 'New'
        },
        {
            'url': 'https://indeed.com/jobs/cybersecurity-intern-remote-2025',
            'source': 'Indeed',
            'job_title': 'Cybersecurity Analyst Intern',
            'company': 'CrowdStrike',
            'location': 'Remote',
            'job_type': 'Internship',
            'experience_level': 'Entry Level',
            'description': 'Protect organizations from cyber threats! Learn about threat detection, incident response, and security analysis. Work remotely with a global team.',
            'requirements': 'Cybersecurity interest, networking knowledge, security certifications preferred',
            'salary': '$6,500/month',
            'company_size': '5,000-10,000 employees',
            'sector': 'Technology',
            'posted_date': '2024-11-26',
            'extracted_at': (datetime.now() - timedelta(days=4)).isoformat(),
            'content_length': 210,
            'status': 'New'
        }
    ]
    
    print("🚀 Adding sample jobs for search testing...")
    added_count = 0
    
    for job_data in sample_jobs:
        if db.insert_job(job_data):
            added_count += 1
            print(f"✅ Added: {job_data['job_title']} at {job_data['company']}")
        else:
            print(f"⚠️  Skipped (duplicate): {job_data['job_title']} at {job_data['company']}")
    
    print(f"\n🎉 Added {added_count} new jobs!")
    
    # Show current database stats
    stats = db.get_job_stats()
    print(f"📊 Total jobs in database: {stats['total_jobs']}")
    print(f"📈 Companies: {len(stats.get('top_companies', {}))}")
    print(f"📍 Locations: {len(stats.get('top_locations', {}))}")

if __name__ == '__main__':
    add_sample_jobs() 