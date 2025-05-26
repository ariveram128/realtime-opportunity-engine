# 🤖 Realtime Opportunity Engine

**AI-Powered Internship Discovery with Bright Data MCP**  
*Built for the #brightdatachallenge • Leveraging Model Context Protocol*

---

## 🌟 Overview

The Realtime Opportunity Engine is an intelligent job discovery system that helps students find internship opportunities in real-time. Built for the Bright Data Real-Time AI Agents Challenge, this application leverages Bright Data's Model Context Protocol (MCP) to provide enhanced job search capabilities through four key actions: DISCOVER, ACCESS, EXTRACT, and INTERACT.

**🏆 #brightdatachallenge Entry:** This project demonstrates how AI agents can leverage real-time web data to solve real-world problems.

### ✨ Key Features

- 🔍 **DISCOVER** - Find relevant internship opportunities across the web using Bright Data's extensive network
- 🔐 **ACCESS** - Navigate complex job sites with Bright Data MCP to bypass challenges traditional scrapers can't handle
- 📊 **EXTRACT** - Pull structured job data at scale with intelligent parsing and LLM-powered content extraction
- 🤖 **INTERACT** - Analyze opportunities with AI to provide personalized recommendations and insights
- 💾 **Session Isolation** - Multi-user support with session-based data isolation
- 🌐 **Modern Web Interface** - Beautiful Flask web app with AJAX updates and responsive design
- 📈 **Real-time Analytics** - Live statistics showing progress across all four MCP actions

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Bright Data MCP Architecture               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────┐      ┌───────────────┐      ┌─────────────────┐
│   DISCOVER  │─────▶│     ACCESS    │────▶│     EXTRACT     │─────┐
└─────────────┘      └───────────────┘      └─────────────────┘     │
       ▲                                                            │
       │                                                            ▼
┌─────────────────────────────┐                           ┌─────────────────┐
│ User Interface & Experience │◀──────────────────────────│    INTERACT     │
└─────────────────────────────┘                           └─────────────────┘
```

### 🌟 Bright Data MCP Actions

1. **DISCOVER** - AI-enhanced job discovery across the web
   - Finds relevant internship opportunities using intelligent search
   - Leverages Bright Data's extensive network for comprehensive results

2. **ACCESS** - Context-aware navigation of job sites
   - Bypasses challenges that traditional scrapers can't handle
   - Navigates complex job portals with human-like behavior

3. **EXTRACT** - LLM-powered content extraction
   - Pulls structured data from job listings with high accuracy
   - Ensures complete information retrieval from diverse sources

4. **INTERACT** - AI-powered job analysis and recommendations
   - Analyzes opportunities to provide personalized insights
   - Evaluates job fit and provides intelligent recommendations

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd realtime-opportunity-engine

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file with your Bright Data credentials:

```
BRIGHTDATA_API_KEY=your_api_key
BRIGHTDATA_ACCOUNT_ID=your_account_id
LINKEDIN_DATASET_ID=your_dataset_id
```

### 3. Start the Web Application

```bash
# Start the Flask web application
python run.py
```

Then open http://localhost:5000 in your browser.

### 4. MCP-Enhanced Job Search

1. **Click "MCP Search"** - Open the Bright Data MCP search modal
2. **Enter Search Term** - Type your desired job search (e.g., "software engineering intern")
3. **Start MCP Search** - Begin the four-phase MCP process
4. **Watch Progress** - See real-time progress across all four MCP actions
5. **View Results** - Browse AI-enhanced job opportunities with intelligent insights

---

## 🎮 Bright Data MCP Integration

### 🌐 MCP Server Connection
The application connects to Bright Data's MCP server to enable all four key actions:

```python
async with BrightDataMCPHandler() as mcp_handler:
    # DISCOVER - AI-enhanced job discovery
    discover_result = await mcp_handler.discover_opportunities(
        search_query=search_term,
        location="United States",
        max_results=max_results
    )
    
    # ACCESS - Context-aware page navigation
    for url in job_urls:
        access_result = await mcp_handler.access_job_page(
            job_url=url,
            context={"anti_bot_bypass": True, "context_aware": True}
        )
    
    # EXTRACT - LLM-powered content extraction
    for page in accessed_pages:
        extract_result = await mcp_handler.extract_job_data(
            html_content=page['page_data']['html_content'],
            url=page['url'],
            context={"llm_powered": True, "intelligent_parsing": True}
        )
    
    # INTERACT - Personalized analysis and recommendations
    for job in extracted_jobs:
        interact_result = await mcp_handler.interact_and_analyze(
            job_data=job,
            user_profile={'search_term': search_term, 'preferences': {}}
        )
```

### 📊 MCP Performance Metrics

The application tracks performance metrics for each MCP action:

```python
performance_metrics = {
    'discover_time_saved': f"{MCP_METRICS['discover_improvement']}x faster",
    'access_efficiency': f"{(MCP_METRICS['access_improvement'] - 1) * 100:.0f}% improvement",
    'extraction_accuracy': f"{(MCP_METRICS['extract_improvement'] - 1) * 100:.0f}% better",
    'analysis_depth': f"{(MCP_METRICS['interact_improvement'] - 1) * 100:.0f}% more insights",
    'overall_enhancement': f"{(MCP_METRICS['overall_improvement'] - 1) * 100:.0f}% overall improvement"
}
```

---

## 🌐 Web Interface Features

### 🔍 MCP-Enhanced Job Discovery
- **Four-Phase Process** - Watch as the application progresses through all four MCP actions
- **Real-time Statistics** - See live counts for each MCP action (Discover, Access, Extract, Interact)
- **Progress Visualization** - Animated progress bar with current action highlighting
- **Action Badges** - Visual indicators show which MCP action is currently active

### 📋 Job Management with Session Isolation
- **Multi-User Support** - Session-based data isolation ensures users only see their own jobs
- **Status Tracking** - Mark jobs as: New, Interested, Applied, Interview, Rejected, Hidden
- **Smart Search** - Search across titles, companies, descriptions, and locations
- **Advanced Filtering** - Filter by status, company, location, job type, and date ranges

### 📊 Analytics Dashboard
- **MCP Performance Metrics** - See how Bright Data MCP enhances job discovery
- **Action Success Rates** - Track success rates for each MCP action
- **Company Insights** - Top hiring companies and recent job postings
- **Job Market Trends** - Analysis of internship opportunities by location and field

---

## 🔄 How It Works: The MCP Advantage

### Traditional Job Search vs. MCP-Enhanced Search

```
┌───────────────────────────┐     ┌───────────────────────────┐
│   Traditional Approach    │     │    MCP-Enhanced Approach  │
├───────────────────────────┤     ├───────────────────────────┤
│ ❌ Limited to public APIs  │     │ ✅ DISCOVER across the web │
│ ❌ Blocked by anti-scraping│     │ ✅ ACCESS protected sites  │
│ ❌ Unstructured raw data   │     │ ✅ EXTRACT structured data │
│ ❌ No intelligent analysis │     │ ✅ INTERACT with AI insights│
└───────────────────────────┘     └───────────────────────────┘
```

### MCP Action Flow

1. **DISCOVER** - The application uses Bright Data's network to find relevant internship opportunities across multiple job sites, not just limited to a single source.

2. **ACCESS** - Unlike traditional scrapers that get blocked, the MCP server navigates complex job sites with human-like behavior, accessing protected content.

3. **EXTRACT** - LLM-powered extraction pulls structured data from diverse job listings, ensuring complete information retrieval with high accuracy.

4. **INTERACT** - AI analysis evaluates each opportunity, providing personalized recommendations and insights to help users find the best matches.

---

## 📊 Database Schema

### Jobs Table with Session Isolation
```sql
CREATE TABLE job_postings (
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
);
```

---

## 🏆 Bright Data Challenge Submission

This project was created for the Bright Data Real-Time AI Agents Challenge. It demonstrates how AI agents can leverage real-time web data to solve real-world problems, specifically in the domain of internship and job discovery.

### Challenge Requirements Met

- ✅ **Utilizes all four MCP actions** - DISCOVER, ACCESS, EXTRACT, and INTERACT
- ✅ **Improves AI performance** - Shows how real-time web data enhances job search capabilities
- ✅ **Solves a real-world problem** - Helps students find relevant internship opportunities
- ✅ **Deployed and functional** - Complete web application with user-friendly interface

### Hashtags
#brightdatachallenge #devchallenge #ai #webdev

---

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

*Built with ❤️ for the Bright Data Real-Time AI Agents Challenge*
