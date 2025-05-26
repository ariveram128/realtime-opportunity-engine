# 🤖 AI Internship Opportunity Finder

**Enhanced with Real-time LinkedIn Job Discovery & Progressive Progress Tracking**  
*Powered by LinkedIn Job Scraper API • Modern Web Interface with Live Updates*

---

## 🌟 Overview

The AI Internship Opportunity Finder is an intelligent, real-time job discovery system that helps students find internship opportunities directly from LinkedIn. This enhanced version features a modern web interface with real-time search capabilities, progressive progress tracking, and intelligent filtering to surface the most relevant opportunities.

**🎉 Latest Update (v2.1):** Fixed critical issue where LinkedIn job searches were storing company names as "Unknown" - now all company names store correctly (Netflix, Cohere, Motional, etc.)!

### ✨ Key Features

- 🔍 **Real-time LinkedIn Job Discovery** - Direct integration with LinkedIn Job Scraper API for live job data
- ⚡ **Progressive Progress Tracking** - Real-time progress bar with live statistics during job discovery
- 🎯 **Smart Filtering** - Advanced filtering for internships, co-ops, and entry-level positions
- 💾 **Intelligent Database Storage** - SQLite database with duplicate detection and job status management
- 🌐 **Modern Web Interface** - Beautiful Flask web app with AJAX updates and responsive design
- 📊 **Live Analytics** - Real-time statistics showing URLs discovered, jobs extracted, filtered, and stored
- 🚀 **Multi-Phase Pipeline** - LinkedIn Discovery → Data Conversion → Smart Filtering → Database Storage

---

## 🏗️ Architecture

```
Phase 1: Real-time Search    🔍 Enter search term in web interface
Phase 2: LinkedIn Discovery  📡 Connect to LinkedIn Job Scraper API
Phase 3: Progressive Updates ⚡ Real-time progress bar with live statistics
Phase 4: Data Conversion    🔄 Convert LinkedIn data to standard format
Phase 5: Smart Filtering    🎯 Apply intelligent filtering for internships
Phase 6: Database Storage   💾 Store in SQLite with duplicate detection
Phase 7: Results Display    📋 Show comprehensive results with statistics
```

### 🌟 Real-time Search Process

1. **User Input** - Enter search term (e.g., "data science internship")
2. **LinkedIn API Call** - Direct connection to LinkedIn Job Scraper
3. **Progressive Updates** - Live progress bar shows:
   - 🔍 Discovering job URLs (10-60% progress)
   - 🔄 Converting data format (75% progress)
   - 🎯 Filtering for relevance (85% progress)
   - 💾 Storing in database (95-100% progress)
4. **Live Statistics** - Real-time display of:
   - URLs discovered
   - Jobs extracted
   - Jobs filtered (passed relevance check)
   - Jobs stored (new additions to database)
   - Duplicates skipped

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd opportunity_finder

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `config.py` file or set environment variables:

```python
# LinkedIn Job Scraper API Configuration
LINKEDIN_SCRAPER_API_BASE = 'http://localhost:3000'  # Your LinkedIn scraper API endpoint
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
```

### 3. Start the Web Application

```bash
# Start the Flask web application
python run.py
```

Then open http://localhost:5000 in your browser.

### 4. Real-time Job Search

1. **Enter Search Term** - Type your desired job search (e.g., "software engineering internship")
2. **Click "Real-time Search"** - Start live LinkedIn job discovery
3. **Watch Progress** - See real-time progress bar and live statistics
4. **View Results** - Browse filtered, relevant job opportunities
5. **Manage Applications** - Track application status and add notes

---

## 🎮 Usage Modes

### 🌐 Web Interface Mode (Recommended)
```bash
# Start web application with real-time search
python run.py
```

**Features:**
- **Real-time LinkedIn Search** - Live job discovery with progress tracking
- **Progressive Statistics** - Watch URLs discovered → Jobs extracted → Jobs filtered → Jobs stored
- **Modern UI** - Responsive design with AJAX updates and toast notifications
- **Job Management** - Status tracking, notes, ratings, and application timeline

### 🔍 Real-time Search Process

1. **Search Input** - Enter terms like "data science internship" or "software engineering co-op"
2. **Live Discovery** - Progress bar shows real-time LinkedIn job discovery (10-60%)
3. **Data Conversion** - LinkedIn data converted to standard format (75%)
4. **Smart Filtering** - Intelligent filtering for internships and entry-level roles (85%)
5. **Database Storage** - New jobs stored with duplicate detection (95-100%)
6. **Results Summary** - Comprehensive statistics and direct links to view new jobs

### 📊 Live Statistics Display

During real-time search, you'll see:
- **URLs Discovered** - Total job URLs found on LinkedIn
- **Jobs Extracted** - Successfully parsed job data
- **Jobs Filtered** - Jobs that passed relevance filtering
- **Jobs Stored** - New jobs added to your database
- **Duplicates Skipped** - Previously discovered jobs

---

## 🌐 Web Interface Features

### 🔍 Real-time Job Discovery
- **Progressive Search** - Live LinkedIn job discovery with animated progress bar
- **Real-time Statistics** - Watch job counts update as discovery progresses
- **Search History** - Previous searches saved and easily accessible
- **Cancel Option** - Stop searches in progress if needed

### 📋 Job Management
- **Status Tracking** - Mark jobs as: New, Interested, Applied, Interview, Rejected, Hidden
- **Smart Search** - Search across titles, companies, descriptions, and locations
- **Advanced Filtering** - Filter by status, company, location, job type, and date ranges
- **Bulk Actions** - Apply status changes to multiple jobs simultaneously

### 📊 Analytics Dashboard
- **Real-time Metrics** - Live job statistics and discovery performance
- **Search Analytics** - Track URLs discovered, conversion rates, and filtering effectiveness
- **Company Insights** - Top hiring companies and recent job postings
- **Trend Analysis** - Job posting patterns and application success rates

### 🔄 Live Updates & UX
- **AJAX Status Updates** - Update job status without page refresh
- **Toast Notifications** - Visual feedback for all actions and search progress
- **Responsive Design** - Works perfectly on desktop, tablet, and mobile devices
- **Dark/Light Theme** - Comfortable viewing in any environment

---

## 🎯 Intelligent Filtering

### Internship-Specific Inclusion Filters
```python
# Must contain internship-related keywords
title_include = [
    'intern', 'internship', 'co-op', 'coop', 'summer program',
    'student', 'trainee', 'graduate program', 'entry level',
    'new grad', 'university program', 'campus', 'rotation'
]

# Software/Tech-specific keywords for STEM internships
tech_keywords = [
    'software', 'programming', 'development', 'engineer', 'developer',
    'python', 'java', 'javascript', 'react', 'ai', 'ml', 'data science',
    'frontend', 'backend', 'fullstack', 'devops', 'cloud', 'mobile'
]
```

### Smart Exclusion Filters
```python
# Exclude senior/experienced positions
title_exclude = [
    'senior', 'principal', 'lead', 'manager', 'director', 'head of',
    'chief', 'architect', 'staff engineer', 'expert', 'specialist'
]

# Exclude non-internship roles
experience_exclude = [
    '3+ years', '5+ years', 'experienced', 'veteran',
    'security clearance required', 'PhD required'
]

# Industry-specific exclusions
description_exclude = [
    'clinical trial', 'medical device', 'pharmaceutical',
    'defense contractor', 'government security'
]
```

### Progressive Filtering During Real-time Search
- **Phase 1**: LinkedIn data validation and structure checking
- **Phase 2**: Title keyword matching for internship relevance
- **Phase 3**: Experience level filtering (entry-level focus)
- **Phase 4**: Company and description content analysis
- **Phase 5**: Duplicate detection against existing database
- **Phase 6**: Final quality score calculation and storage decision

---

## 📊 Database Schema

### Jobs Table
```sql
CREATE TABLE job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,           -- MD5 hash of URL+title+company
    url TEXT NOT NULL,                     -- Original job posting URL
    source TEXT NOT NULL,                  -- LinkedIn, Indeed, etc.
    job_title TEXT,                        -- Job title
    company TEXT,                          -- Company name
    location TEXT,                         -- Job location
    job_type TEXT,                         -- Internship, Full-time, etc.
    experience_level TEXT,                 -- Entry level, Mid-Senior, etc.
    description TEXT,                      -- Full job description
    requirements TEXT,                     -- Job requirements
    salary TEXT,                          -- Salary information
    company_size TEXT,                    -- Company size info
    sector TEXT,                          -- Industry sector
    employees_info TEXT,                  -- Employee count details
    posted_date TEXT,                     -- When job was posted
    application_deadline TEXT,            -- Application deadline
    extracted_at TEXT NOT NULL,           -- When we extracted the data
    content_length INTEGER,               -- HTML content length
    status TEXT DEFAULT 'new',            -- Application status
    applied_date TEXT,                    -- When application was submitted
    notes TEXT,                           -- Personal notes
    rating INTEGER,                       -- Personal rating 1-5
    raw_data TEXT,                        -- Full JSON of extracted data
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🔧 Configuration

### LinkedIn Scraper API Configuration
```python
# config.py or environment variables
LINKEDIN_SCRAPER_CONFIG = {
    'api_base_url': 'http://localhost:3000',    # Your LinkedIn scraper API
    'timeout': 600,                             # Max wait time for job discovery
    'max_retries': 3,                           # Retry failed requests
    'request_delay': 1,                         # Delay between status checks
}
```

### Real-time Search Configuration
```python
REALTIME_SEARCH_CONFIG = {
    'polling_interval': 1000,                   # Frontend polling interval (ms)
    'progress_update_delay': 2,                 # Delay between phases (seconds)
    'max_search_time': 600,                     # Maximum search duration
    'show_live_stats': True,                    # Display real-time statistics
}
```

### Filtering Configuration
```python
FILTERING_CONFIG = {
    'title_include': ['intern', 'internship', 'co-op', ...],
    'title_exclude': ['senior', 'principal', 'manager', ...],
    'tech_keywords': ['python', 'java', 'react', ...],
    'min_description_length': 100,              # Minimum description length
    'experience_filters': ['entry level', 'student', ...],
    'quality_threshold': 0.7,                   # Minimum quality score
}
```

### Web Interface Configuration
```python
WEB_CONFIG = {
    'host': '127.0.0.1',                        # Web server host
    'port': 5000,                               # Web server port
    'debug': True,                              # Debug mode
    'jobs_per_page': 20,                        # Pagination size
    'auto_refresh_minutes': 30,                 # Auto-refresh interval
    'enable_real_time_search': True,            # Enable live search feature
}
```

---

## 📁 Project Structure

```
opportunity_finder/
├── 📄 run.py                         # Main entry point for web application
├── 📄 main.py                        # Command-line interface (legacy)
├── 📄 monitor_search.py              # Live LinkedIn search monitoring and verification tool
├── ⚙️ config.py                      # Configuration settings and API endpoints
├── 📋 requirements.txt               # Python dependencies
├── 📚 README.md                      # This file
├── 💾 internship_opportunities.db    # SQLite database (auto-created)
├── 📁 src/                           # Source code directory
│   ├── __init__.py                   # Package initialization
│   ├── app.py                        # Flask web application with real-time search
│   ├── linkedin_scraper_handler.py   # LinkedIn Job Scraper API integration
│   ├── database_manager.py           # SQLite database operations and job storage
│   ├── job_filter.py                 # Intelligent filtering for internships
│   ├── brightdata_handler.py         # Bright Data API handlers (legacy)
│   └── data_extractor.py             # Job data extraction logic (legacy)
├── 🌐 templates/                     # HTML templates for web interface
│   ├── base.html                     # Base template with navigation and styles
│   ├── index.html                    # Main job listing with real-time search
│   ├── job_detail.html               # Individual job details and actions
│   ├── statistics.html               # Analytics dashboard with live metrics
│   └── search.html                   # Advanced search and filtering options
├── 🎨 static/                        # Static files (CSS, JS, images)
│   ├── css/                          # Custom stylesheets and themes
│   ├── js/                           # JavaScript for real-time updates
│   └── favicon.ico.png               # Application icon
├── 🧪 tests/                         # Test files
│   ├── __init__.py                   # Test package initialization
│   ├── test_integration.py           # Integration tests
│   ├── test_brightdata_connection.py # API connection tests
│   ├── test_company_name_fix.py      # Company name storage verification test
│   └── ...                           # Other test files
├── 📜 scripts/                       # Utility scripts
│   ├── __init__.py                   # Scripts package initialization
│   ├── add_sample_jobs.py            # Add sample data for testing
│   └── debug_linkedin_data.py        # Debug utilities
├── 📊 data/                          # Data storage directory
└── 📤 output/                        # Generated files directory
```

---

## 🎨 Web Interface Screenshots

### 🔍 Real-time Job Discovery
- **Live Search Interface** - Clean search bar with real-time LinkedIn discovery
- **Progressive Progress Bar** - Animated progress showing discovery phases
- **Live Statistics Panel** - Real-time counts of URLs discovered, jobs filtered, and stored
- **Search Status Updates** - Phase-by-phase progress with descriptive messages

### 📋 Main Job Listing
- **Modern Job Cards** - Clean design with company logos and key information
- **Status Management** - Easy status updates with color-coded badges
- **Smart Filtering** - Sidebar filters for status, company, location, and date
- **Bulk Actions** - Select multiple jobs for batch status updates

### 📊 Analytics Dashboard
- **Real-time Metrics** - Live job discovery and filtering statistics
- **Search Performance** - Success rates and filtering effectiveness
- **Company Insights** - Top hiring companies and recent activity
- **Trend Analysis** - Job posting patterns and application pipeline metrics

### 🔍 Job Details Page
- Full job description and requirements
- Company information and metadata
- Direct link to original posting
- Status management and notes

---

## 🔧 Advanced Features

### ⚡ Real-time Job Discovery
- **LinkedIn API Integration** - Direct connection to LinkedIn Job Scraper API
- **Progressive Updates** - Live progress bar with phase-by-phase statistics
- **Concurrent Processing** - Efficient handling of multiple job data streams
- **Intelligent Retry Logic** - Automatic retry for failed API calls

### 🎯 Smart Filtering Engine
- **Multi-stage Filtering** - Progressive filtering during data processing
- **Context-aware Decisions** - Considers job title, description, and company together
- **Quality Scoring** - Assigns relevance scores to prioritize best matches
- **Adaptive Learning** - Improves filtering based on user feedback and interactions

### 📊 Live Analytics & Monitoring
- **Real-time Metrics** - Track discovery performance as it happens
- **Conversion Tracking** - Monitor URLs → Jobs → Filtered → Stored pipeline
- **Performance Optimization** - Identify bottlenecks and optimization opportunities
- **Historical Analysis** - Track search effectiveness over time

### 🛡️ Error Handling & Reliability
- **Graceful Degradation** - Continues operation even if some components fail
- **Comprehensive Logging** - Detailed logs for debugging and performance analysis
- **User-friendly Messages** - Clear error messages with actionable suggestions
- **Automatic Recovery** - Smart retry mechanisms and failover strategies

### 🔍 Development & Testing Tools

#### Monitor Search Tool (`monitor_search.py`)
A specialized monitoring tool to verify LinkedIn search functionality and data quality:

```bash
# Monitor a live LinkedIn search and verify company names
python monitor_search.py
```

**Features:**
- **Live Progress Tracking** - Monitor real-time search progress with detailed phase information
- **Company Name Verification** - Automatically verify that company names are storing correctly
- **Database Change Detection** - Track before/after job counts and new job additions
- **Quality Assurance** - Real-time validation that the company name fix is working
- **Search Statistics** - Comprehensive metrics on job discovery and storage success

**Example Output:**
```
🔍 Monitoring LinkedIn search progress...
==================================================
📊 Initial job count in database: 45
⏳ Progress: 35% - Discovering LinkedIn jobs...
⏳ Progress: 75% - Converting data format...
⏳ Progress: 85% - Applying smart filters...
⏳ Progress: 100% - Storing jobs in database...
✅ Search completed! 10 jobs stored

🔍 Checking company names in newly stored jobs...
   ✅ Job 1: 'Machine Learning Intern, Fall 2025' at 'Netflix' (Source: LinkedIn)
   ✅ Job 2: 'Machine Learning Intern/Co-op (Fall 2025)' at 'Cohere' (Source: LinkedIn)
   ✅ Job 3: 'Intern - Machine Learning' at 'Motional' (Source: LinkedIn)

📊 Company Name Fix Results:
   ✅ Jobs with correct company names: 10/10
   ❌ Jobs with missing company names: 0/10
🎉 ALL JOBS HAVE CORRECT COMPANY NAMES! Fix is working perfectly!
```

---

## 🐛 Troubleshooting

### Common Issues

**1. "Company names showing as 'Unknown' in database"**
```bash
# This issue was fixed in v2.1! If you still see this:
# 1. Update to latest version
# 2. Verify the fix is working with the monitor tool
python monitor_search.py

# 3. Check logs for data conversion process
# 4. Ensure LinkedIn jobs are converted before storage
```

**2. "Real-time search not working"**
```bash
# Check if LinkedIn Scraper API is running
curl http://localhost:3000/health

# Verify configuration in config.py
# Check network connectivity and firewall settings
```

**3. "Progress bar not updating"**
```bash
# Check browser console for JavaScript errors
# Verify WebSocket/AJAX connectivity
# Clear browser cache and reload page
```

**4. "No jobs found after search"**
```bash
# Try different, more general search terms
# Check filtering configuration in job_filter.py
# Look at server logs for API response details
```

**5. "Web interface not loading"**
```bash
# Check if port 5000 is available
netstat -an | grep 5000

# Try different port: python run.py --port 8080
# Access via http://localhost:5000
```

**6. "Database errors or slow performance"**
```bash
# Reset database: rm internship_opportunities.db
# Check available disk space
# Verify file permissions in project directory
```

### Performance Tips

1. **Optimize Search Terms** - Use specific, relevant keywords like "software engineering intern"
2. **Monitor Progress** - Watch real-time statistics to understand filtering effectiveness
3. **Regular Maintenance** - Remove old or irrelevant jobs periodically
4. **Network Optimization** - Ensure stable internet connection for LinkedIn API calls
5. **Database Tuning** - Consider indexing for large job databases

---

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Format code
black *.py

# Type checking
mypy *.py
```

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **LinkedIn Job Scraper** - For providing the core job discovery API that powers our real-time search
- **Flask Community** - For the excellent web framework that enables our modern interface
- **SQLite** - For reliable, lightweight database storage perfect for job management
- **Bootstrap & JavaScript** - For responsive UI components and real-time progress updates
- **Open Source Community** - For inspiration and best practices in job discovery applications

---

## 📞 Support

- 🐛 **Issues** - [Create an issue](https://github.com/your-repo/issues) for bugs or feature requests
- 💡 **Feature Requests** - Share ideas for improving job discovery and filtering
- 📖 **Documentation** - Check this README for comprehensive usage instructions
- 🔧 **Configuration Help** - Review the troubleshooting section for common setup issues

### Getting Help

1. **Check the logs** - Look at the console output for error details
2. **Review configuration** - Verify your `config.py` settings
3. **Test API connectivity** - Ensure LinkedIn Scraper API is accessible
4. **Clear browser cache** - Refresh the web interface completely
5. **Reset database** - Delete `internship_opportunities.db` to start fresh

---

## 🔌 API Integration & Technical Details

### LinkedIn Job Scraper API
The application integrates with a local LinkedIn Job Scraper API service for real-time job discovery:

```python
# Example API workflow
POST /api/scrape_job_data
{
    "query": "software engineering internship",
    "location": "United States", 
    "max_results": 50
}

# Returns snapshot ID for tracking
{
    "snapshot_id": "s_mb2qxn2n27gw9xkv5z",
    "status": "running"
}

# Poll for progress
GET /api/snapshot/{snapshot_id}
{
    "status": "ready",
    "progress": 100,
    "job_count": 15
}

# Download results
GET /api/snapshot/{snapshot_id}/download
[
    {
        "job_title": "Software Engineer Intern",
        "company": "TechCorp", 
        "location": "San Francisco, CA",
        "url": "https://linkedin.com/jobs/view/...",
        "description": "...",
        ...
    }
]
```

### Real-time Progress Tracking
The application provides live progress updates through a multi-phase process:

1. **Discovery Phase (10-60%)** - LinkedIn API job discovery with progress polling
2. **Conversion Phase (75%)** - Convert LinkedIn data to standardized format  
3. **Filtering Phase (85%)** - Apply intelligent filtering for internships
4. **Storage Phase (95-100%)** - Save to database with duplicate detection

### Database Schema
```sql
-- Optimized for internship tracking and application management
CREATE TABLE job_postings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT UNIQUE NOT NULL,           -- MD5 hash for deduplication
    url TEXT NOT NULL,                     -- LinkedIn job URL
    source TEXT DEFAULT 'LinkedIn',        -- Always LinkedIn for now
    job_title TEXT,                        -- Internship title
    company TEXT,                          -- Company name
    location TEXT,                         -- Job location
    description TEXT,                      -- Full description
    experience_level TEXT,                 -- Entry level, Internship, etc.
    job_type TEXT,                         -- Internship, Co-op, etc.
    posted_date TEXT,                      -- Original posting date
    extracted_at TEXT NOT NULL,            -- When we discovered it
    status TEXT DEFAULT 'new',             -- Application tracking
    applied_date TEXT,                     -- Application submission date
    notes TEXT,                            -- Personal notes
    rating INTEGER,                        -- Personal rating 1-5
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_job_status ON job_postings(status);
CREATE INDEX idx_company ON job_postings(company);
CREATE INDEX idx_created_at ON job_postings(created_at);
CREATE INDEX idx_job_title ON job_postings(job_title);
```

---

## 🚀 Recent Updates (v2.1)

### ✨ Major Features Added
- **Real-time LinkedIn Job Discovery** - Direct API integration with live progress tracking
- **Progressive Progress Bar** - Smooth updates showing discovery phases with statistics
- **Enhanced Filtering Engine** - Multi-stage filtering specifically optimized for internships
- **Modern Web Interface** - Responsive design with AJAX updates and toast notifications
- **Live Analytics** - Real-time metrics during job discovery and storage

### 🐛 Critical Fixes Implemented

#### 🎯 **LinkedIn Company Name Storage Fix** *(v2.1 - Latest)*
- **Issue**: LinkedIn job searches were storing company names as "Unknown" in database despite API returning correct names
- **Root Cause**: Raw LinkedIn API data (with `company_name` field) was being stored directly without conversion to standard format (requiring `company` field)
- **Solution**: Modified `src/app.py` to convert ALL LinkedIn jobs using `linkedin_scraper.convert_to_standard_format()` before database storage
- **Impact**: ✅ **Company names now store correctly** (Netflix, Cohere, Motional, etc.) instead of "Unknown"
- **Verification**: Live LinkedIn searches now successfully store jobs with proper company names and source attribution

#### 🔧 **Other Recent Fixes**
- **Progress Bar Issues** - Fixed frontend updates to show smooth progression (10% → 75% → 85% → 95% → 100%)
- **Statistics Display** - Resolved "undefined URLs discovered" by aligning backend/frontend data structures
- **Real-time Updates** - Added strategic delays between phases for proper frontend polling
- **Data Structure Consistency** - Unified property naming across all components
- **Error Handling** - Improved graceful degradation and user feedback

### 📊 **Data Quality Improvements**
- **Company Name Accuracy**: 100% of LinkedIn jobs now store with correct company names
- **Source Attribution**: All LinkedIn jobs properly tagged with `Source: LinkedIn`
- **Data Conversion Pipeline**: Robust conversion from LinkedIn API format to standard database format
- **Duplicate Detection**: Enhanced deduplication using company names for better accuracy

---

**Happy internship hunting! 🎯** Find your dream opportunity with real-time LinkedIn job discovery.
