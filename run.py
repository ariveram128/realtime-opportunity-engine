#!/usr/bin/env python3
"""
Entry point for AI Internship Opportunity Finder Web Application
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.app import app

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
