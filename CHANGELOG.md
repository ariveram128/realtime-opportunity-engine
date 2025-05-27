# Opportunity Finder Changelog

All notable changes to the Opportunity Finder application will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
- Potential enhancements to search analytics visualizations
- Additional filtering options for search history

## [1.2.0] - 2025-05-26

### Added
- Enhanced search analytics dashboard on the statistics page:
  - Search performance summary with metrics (total searches, accuracy stats)
  - Search accuracy trends over time (last 30 days)
  - Search accuracy distribution chart
  - Top search queries analytics
  - Recent search history list
- Five new database methods for detailed search analytics:
  - `get_search_history()`: Retrieves recent search history with accuracy metrics
  - `get_search_accuracy_trends()`: Retrieves search accuracy trends over time
  - `get_search_accuracy_distribution()`: Gets distribution of search accuracy ranges
  - `get_search_query_analytics()`: Gets analytics for most searched queries
  - `get_search_performance_summary()`: Gets overall search performance summary

### Fixed
- Fixed indentation issues in database_manager.py
- Corrected syntax errors in search analytics methods
- Ensured methods correctly use `search_timestamp` column name

## [1.1.0] - 2025-05-25

### Added
- Real-time search functionality with progress indicators
- LinkedIn job search integration using BrightData API
- AI-powered search accuracy calculation:
  - NLP-based similarity using sentence transformers (all-MiniLM-L6-v2 model)
  - Cosine similarity calculations between search queries and job content
  - Relevance threshold of 0.6 for determining job match quality
- Search log table in database to track:
  - User search queries
  - Number of results shown
  - Number of relevant results (based on NLP)
  - AI accuracy percentage
  - Search timestamp
- Average System Search Accuracy metric in statistics dashboard:
  - Session-specific accuracy tracking
  - Visual stats card with bullseye icon in glassmorphism theme
- Job filtering based on relevance and keywords
- Basic search analytics tracking

### Changed
- Improved database schema with a new search_log table
- Enhanced job detail page with more information
- Upgraded UI with modern design elements
- Updated dependencies to include sentence-transformers and scikit-learn

### Fixed
- Resolved issue with duplicate jobs appearing in search results
- Fixed company name extraction from LinkedIn data

## [1.0.0] - 2025-04-24

### Added
- Initial release of Opportunity Finder
- Basic job search and management functionality
- Job status tracking (new, interested, applied, interview, rejected)
- Database storage for job listings
- Simple statistics dashboard
- User session management
