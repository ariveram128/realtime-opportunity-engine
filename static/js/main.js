/**
 * Professional Job Search Platform JavaScript
 * Enhanced interactions, animations, and user experience
 */

// ========== Global Variables & Configuration ==========
const AppConfig = {
    animations: {
        duration: 300,
        easing: 'ease-out'
    },
    debounce: {
        search: 500,
        resize: 250
    },
    api: {
        timeout: 30000
    },
    session: {
        key: 'job_finder_session_id'
    }
};

// ========== Utility Functions ==========
class Utils {
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, wait) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, wait);
            }
        };
    }

    static formatDate(dateString) {
        if (!dateString) return 'Recently';
        
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;
        const days = Math.floor(diff / (1000 * 60 * 60 * 24));
        
        if (days === 0) return 'Today';
        if (days === 1) return 'Yesterday';
        if (days < 7) return `${days} days ago`;
        if (days < 30) return `${Math.floor(days / 7)} weeks ago`;
        if (days < 365) return `${Math.floor(days / 30)} months ago`;
        return `${Math.floor(days / 365)} years ago`;
    }

    static showToast(message, type = 'info', duration = 5000) {
        const toastContainer = document.getElementById('toast-container') || this.createToastContainer();
        const toast = this.createToast(message, type);
        
        toastContainer.appendChild(toast);
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 100);
        
        // Auto remove
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    static createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    }

    static createToast(message, type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle'
        };

        const colors = {
            success: 'text-success',
            error: 'text-danger',
            warning: 'text-warning',
            info: 'text-info'
        };

        const toast = document.createElement('div');
        toast.className = `toast align-items-center border-0 fade`;
        toast.setAttribute('role', 'alert');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="${icons[type]} ${colors[type]} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close me-2 m-auto" onclick="this.closest('.toast').remove()"></button>
            </div>
        `;
        
        return toast;
    }

    static animateCounter(element, target, duration = 2000) {
        const start = parseInt(element.textContent) || 0;
        const increment = (target - start) / (duration / 16);
        let current = start;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
                current = target;
                clearInterval(timer);
            }
            element.textContent = Math.floor(current);
        }, 16);
    }

    static getSessionId() {
        // Get session ID from localStorage or create a new one
        let sessionId = localStorage.getItem(AppConfig.session.key);
        if (!sessionId) {
            // If no session ID exists, we'll use the one from the server on first request
            this.fetchSessionIdFromServer();
            sessionId = localStorage.getItem(AppConfig.session.key) || 'default';
        }
        return sessionId;
    }
    
    static async fetchSessionIdFromServer() {
        try {
            const response = await fetch('/api/session');
            if (response.ok) {
                const data = await response.json();
                if (data.success && data.session_id) {
                    localStorage.setItem(AppConfig.session.key, data.session_id);
                    return data.session_id;
                }
            }
        } catch (error) {
            console.error('Error fetching session ID:', error);
        }
        return null;
    }
}

// ========== Enhanced Search Functionality ==========
class SearchManager {
    constructor() {
        this.searchInput = document.getElementById('search');
        this.currentRequest = null;
        this.init();
    }

    init() {
        if (this.searchInput) {
            this.setupLiveSearch();
            this.setupSearchEnhancements();
        }
    }

    setupLiveSearch() {
        const debouncedSearch = Utils.debounce((query) => {
            if (query.length >= 2) {
                this.performLiveSearch(query);
            }
        }, AppConfig.debounce.search);

        this.searchInput.addEventListener('input', (e) => {
            const query = e.target.value.trim();
            debouncedSearch(query);
        });
    }

    setupSearchEnhancements() {
        // Add search suggestions
        this.createSearchSuggestions();
        
        // Enhanced search button
        const searchBtn = this.searchInput.closest('form')?.querySelector('button[type="submit"]');
        if (searchBtn) {
            searchBtn.addEventListener('click', (e) => {
                this.enhanceSearchExperience(e);
            });
        }
    }

    createSearchSuggestions() {
        const suggestions = [
            'Software Engineering Internship',
            'Data Science Internship',
            'Machine Learning Engineer',
            'Frontend Developer Intern',
            'Backend Developer Intern',
            'Full Stack Developer',
            'Product Manager Intern',
            'UX/UI Designer Intern'
        ];

        const datalist = document.createElement('datalist');
        datalist.id = 'search-suggestions';
        
        suggestions.forEach(suggestion => {
            const option = document.createElement('option');
            option.value = suggestion;
            datalist.appendChild(option);
        });

        this.searchInput.setAttribute('list', 'search-suggestions');
        this.searchInput.parentNode.appendChild(datalist);
    }

    async performLiveSearch(query) {
        // Cancel previous request
        if (this.currentRequest) {
            this.currentRequest.abort();
        }

        try {
            this.currentRequest = new AbortController();
            
            // Show loading state
            this.showSearchLoading();
            
            const response = await fetch('/api/live_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query }),
                signal: this.currentRequest.signal
            });

            if (response.ok) {
                const results = await response.json();
                this.displayLiveResults(results);
            }
        } catch (error) {
            if (error.name !== 'AbortError') {
                console.error('Live search error:', error);
            }
        } finally {
            this.hideSearchLoading();
        }
    }

    showSearchLoading() {
        const searchContainer = this.searchInput.closest('.search-container');
        if (searchContainer) {
            searchContainer.classList.add('loading');
        }
    }

    hideSearchLoading() {
        const searchContainer = this.searchInput.closest('.search-container');
        if (searchContainer) {
            searchContainer.classList.remove('loading');
        }
    }

    displayLiveResults(results) {
        // Implementation for live search results display
        console.log('Live search results:', results);
    }

    enhanceSearchExperience(event) {
        const button = event.target;
        const originalText = button.innerHTML;
        
        // Add loading animation
        button.innerHTML = '<span class="loading-spinner me-2"></span>Searching...';
        button.disabled = true;
        
        // Reset after form submission
        setTimeout(() => {
            button.innerHTML = originalText;
            button.disabled = false;
        }, 2000);
    }
}

// ========== Job Card Enhancements ==========
class JobCardManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupJobCardAnimations();
        this.setupStatusButtons();
        this.setupQuickActions();
        this.observeJobCards();
    }

    setupJobCardAnimations() {
        const jobCards = document.querySelectorAll('.job-card');
        
        jobCards.forEach((card, index) => {
            // Staggered animation on load
            card.style.animationDelay = `${index * 0.1}s`;
            card.classList.add('slide-up');
            
            // Enhanced hover effects
            card.addEventListener('mouseenter', () => {
                this.enhanceCardHover(card);
            });
            
            card.addEventListener('mouseleave', () => {
                this.resetCardHover(card);
            });
        });
    }

    enhanceCardHover(card) {
        // Add subtle glow effect
        card.style.boxShadow = '0 8px 25px rgba(0, 102, 204, 0.15)';
        
        // Slightly scale up
        card.style.transform = 'translateY(-5px) scale(1.02)';
    }

    resetCardHover(card) {
        card.style.boxShadow = '';
        card.style.transform = '';
    }

    setupStatusButtons() {
        document.addEventListener('click', async (e) => {
            const statusButton = e.target.closest('.btn-status');
            if (statusButton) {
                await this.handleStatusChange(statusButton);
                return; // Prevent further actions if it was a status button
            }

            const viewDetailsButton = e.target.closest('.btn-view-details');
            if (viewDetailsButton) {
                this.showJobDetailsModal(viewDetailsButton);
            }
        });
    }

    async handleStatusChange(button) {
        const jobId = button.dataset.jobId;
        const newStatus = button.dataset.status;
        
        if (!jobId || !newStatus) return;

        // Visual feedback
        const originalText = button.textContent;
        button.innerHTML = '<span class="loading-spinner me-1"></span>Updating...';
        button.disabled = true;

        try {
            const response = await fetch('/api/update_job_status', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    job_id: jobId,
                    status: newStatus
                })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.updateJobCardStatus(jobId, newStatus);
                    Utils.showToast(`Job status updated to ${newStatus}`, 'success');
                } else {
                    throw new Error(result.error || 'Update failed');
                }
            } else {
                throw new Error('Network error');
            }
        } catch (error) {
            console.error('Status update error:', error);
            Utils.showToast('Failed to update job status', 'error');
        } finally {
            button.textContent = originalText;
            button.disabled = false;
        }
    }

    updateJobCardStatus(jobId, newStatus) {
        const jobCard = document.querySelector(`[data-job-id="${jobId}"]`);
        if (jobCard) {
            // Remove old status classes
            jobCard.className = jobCard.className.replace(/status-\w+/g, '');
            // Add new status class
            jobCard.classList.add(`status-${newStatus}`);
            
            // Update status badge
            const statusBadge = jobCard.querySelector('.status-badge');
            if (statusBadge) {
                statusBadge.textContent = newStatus.charAt(0).toUpperCase() + newStatus.slice(1);
                statusBadge.className = `status-badge badge bg-${this.getStatusColor(newStatus)}`;
            }

            // Animate the change
            jobCard.classList.add('bounce-in');
            setTimeout(() => jobCard.classList.remove('bounce-in'), 600);
        }
    }

    getStatusColor(status) {
        const colors = {
            'new': 'primary',
            'interested': 'info',
            'applied': 'warning',
            'interview': 'success',
            'rejected': 'danger',
            'hidden': 'secondary'
        };
        return colors[status] || 'primary';
    }

    setupQuickActions() {
        // Setup quick action tooltips and handlers
        const quickActionBtns = document.querySelectorAll('[data-quick-action]');
        
        quickActionBtns.forEach(btn => {
            // Add tooltips
            if (!btn.hasAttribute('title')) {
                const action = btn.dataset.quickAction;
                btn.setAttribute('title', `Quick ${action}`);
            }
            
            // Enhanced click handling
            btn.addEventListener('click', (e) => {
                this.handleQuickAction(e);
            });
        });
    }

    handleQuickAction(event) {
        const button = event.target.closest('[data-quick-action]');
        const action = button.dataset.quickAction;
        
        // Add ripple effect
        this.createRippleEffect(button, event);
        
        // Handle specific actions
        switch (action) {
            case 'favorite':
                this.toggleFavorite(button);
                break;
            case 'share':
                this.shareJob(button);
                break;
            case 'notes':
                this.openNotesModal(button);
                break;
        }
    }

    createRippleEffect(element, event) {
        const ripple = document.createElement('span');
        const rect = element.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;
        
        ripple.style.width = ripple.style.height = size + 'px';
        ripple.style.left = x + 'px';
        ripple.style.top = y + 'px';
        ripple.className = 'ripple';
        
        element.style.position = 'relative';
        element.style.overflow = 'hidden';
        element.appendChild(ripple);
        
        setTimeout(() => ripple.remove(), 600);
    }

    showJobDetailsModal(button) {
        const jobCard = button.closest('.professional-job-card');
        const title = jobCard.dataset.jobTitle;
        const company = jobCard.dataset.jobCompany;
        const location = jobCard.dataset.jobLocation;
        const description = jobCard.dataset.description;
        const url = jobCard.dataset.jobUrl;

        document.getElementById('modalJobTitle').textContent = title;
        document.getElementById('modalJobCompany').textContent = company;
        document.getElementById('modalJobLocation').textContent = location;
        // Sanitize and set description if needed, for now, direct text
        document.getElementById('modalJobDescription').textContent = description; 
        document.getElementById('modalJobLink').href = url;

        const modalElement = document.getElementById('jobDetailModal');
        const modal = bootstrap.Modal.getInstance(modalElement) || new bootstrap.Modal(modalElement);
        modal.show();
    }

    observeJobCards() {
        // Intersection Observer for lazy loading animations
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                    observer.unobserve(entry.target);
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '50px'
        });

        document.querySelectorAll('.job-card').forEach(card => {
            observer.observe(card);
        });
    }
}

// ========== MCP Search Enhancement ==========
class MCPSearchManager {
    constructor() {
        this.modal = null;
        this.modalInstance = null;
        this.statusPollingInterval = null;
        this.searchInProgress = false;
    }
    
    init() {
        this.setupMCPModal();
        this.setupMCPSearch();
        this.initializeBrightDataBranding();
        
        // Attach to global mcp search button
        document.querySelectorAll('.mcp-search-btn').forEach(btn => {
            btn.addEventListener('click', () => this.showMCPModal());
        });
    }
    
    initializeBrightDataBranding() {
        // Add Bright Data challenge branding elements
        document.querySelectorAll('.mcp-action-badge').forEach(badge => {
            badge.addEventListener('mouseenter', () => {
                badge.style.transform = 'scale(1.1)';
            });
            
            badge.addEventListener('mouseleave', () => {
                badge.style.transform = '';
            });
        });
    }

    setupMCPModal() {
        const mcpModal = document.getElementById('mcpSearchModal');
        if (mcpModal) {
            this.modal = mcpModal;
            
            // Initialize Bootstrap modal
            this.modalInstance = new bootstrap.Modal(mcpModal);
            
            mcpModal.addEventListener('show.bs.modal', () => {
                this.resetMCPModalState();
            });
            
            // Fix for modal backdrop not being removed
            mcpModal.addEventListener('hidden.bs.modal', () => {
                // Remove any lingering backdrop
                const backdrops = document.querySelectorAll('.modal-backdrop');
                backdrops.forEach(backdrop => {
                    backdrop.remove();
                });
                document.body.classList.remove('modal-open');
                document.body.style.overflow = '';
                document.body.style.paddingRight = '';
            });
            
            // Add event listeners for MCP action explanations
            document.querySelectorAll('[data-mcp-action]').forEach(element => {
                element.addEventListener('click', (e) => {
                    const action = e.currentTarget.getAttribute('data-mcp-action');
                    this.showActionExplanation(action);
                });
            });
            
            // Set up the search form submission
            const searchForm = document.getElementById('mcpSearchForm');
            if (searchForm) {
                searchForm.addEventListener('submit', (e) => {
                    e.preventDefault();
                    this.executeMCPSearch();
                });
            }
        }
    }

    setupMCPSearch() {
        // No need to add click handlers as we're using data-bs-toggle="modal" now
        // Just ensure we have the modal instance ready
        const mcpModal = document.getElementById('mcpSearchModal');
        if (mcpModal && !this.modalInstance) {
            this.modal = mcpModal;
            this.modalInstance = new bootstrap.Modal(mcpModal);
        }
    }

    showMCPModal() {
        if (this.modalInstance) {
            this.modalInstance.show();
        } else {
            // Fallback if modalInstance is not initialized
            const mcpModal = document.getElementById('mcpSearchModal');
            if (mcpModal) {
                this.modal = mcpModal;
                this.modalInstance = new bootstrap.Modal(mcpModal);
                this.modalInstance.show();
            } else {
                console.error('MCP modal element not found');
            }
        }
    }

    resetMCPModalState() {
        // Reset all MCP modal elements to initial state
        const elements = {
            config: document.getElementById('mcpConfig'),
            progress: document.getElementById('mcpProgress'),
            results: document.getElementById('mcpResults'),
            error: document.getElementById('mcpError')
        };

        if (elements.config) elements.config.style.display = 'block';
        if (elements.progress) elements.progress.style.display = 'none';
        if (elements.results) elements.results.style.display = 'none';
        if (elements.error) elements.error.style.display = 'none';

        // Reset form
        const form = document.getElementById('mcpSearchForm');
        if (form) form.reset();

        // Reset progress
        this.updateMCPProgress(0, 'Ready to start Bright Data MCP search...');
        
        // Reset action badges
        document.querySelectorAll('[data-mcp-action]').forEach(badge => {
            badge.classList.remove('badge-primary');
            badge.classList.add('badge-secondary');
        });
    }

    showActionExplanation(action) {
        const explanations = {
            'DISCOVER': 'The DISCOVER action uses AI to find relevant job opportunities across the web, leveraging Bright Data\'s extensive network to identify potential matches.',
            'ACCESS': 'The ACCESS action navigates complex websites, bypassing challenges that traditional scrapers can\'t handle, to retrieve comprehensive job listings.',
            'EXTRACT': 'The EXTRACT action uses AI to pull structured data from job listings, ensuring accurate and complete information retrieval.',
            'INTERACT': 'The INTERACT action analyzes job opportunities using AI, providing personalized recommendations and insights.'
        };
        
        const explanation = explanations[action] || 'This is one of the four key MCP actions powered by Bright Data.';
        
        // Show a toast with the explanation
        Utils.showToast(explanation, 'info', 8000);
    }

    async executeMCPSearch() {
        const searchTerm = document.getElementById('mcpSearchTerm')?.value?.trim();
        const maxResults = document.getElementById('mcpMaxResults')?.value || 5;

        if (!searchTerm) {
            Utils.showToast('Please enter a search term', 'warning');
            return;
        }

        try {
            // Get session ID
            const sessionId = Utils.getSessionId();
            
            // Switch to progress view
            this.showMCPProgress();

            // Start MCP search
            const response = await fetch('/api/mcp_search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    search_term: searchTerm,
                    max_results: parseInt(maxResults),
                    session_id: sessionId
                })
            });

            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    this.startMCPStatusPolling();
                    Utils.showToast('Bright Data MCP search started successfully', 'success');
                } else {
                    this.showMCPError(result.error || 'Failed to start MCP search');
                }
            } else {
                this.showMCPError('Failed to connect to server');
            }
        } catch (error) {
            console.error('MCP search error:', error);
            this.showMCPError('An error occurred while starting the search');
        }
    }

    showMCPProgress() {
        document.getElementById('mcpConfig').style.display = 'none';
        document.getElementById('mcpProgress').style.display = 'block';
        document.getElementById('mcpResults').style.display = 'none';
        document.getElementById('mcpError').style.display = 'none';
    }

    showMCPResults() {
        document.getElementById('mcpConfig').style.display = 'none';
        document.getElementById('mcpProgress').style.display = 'none';
        document.getElementById('mcpResults').style.display = 'block';
        document.getElementById('mcpError').style.display = 'none';
    }

    showMCPError(errorMessage) {
        document.getElementById('mcpConfig').style.display = 'none';
        document.getElementById('mcpProgress').style.display = 'none';
        document.getElementById('mcpResults').style.display = 'none';
        document.getElementById('mcpError').style.display = 'block';
        
        const errorElement = document.getElementById('errorMessage');
        if (errorElement) {
            errorElement.textContent = errorMessage;
        }
    }

    startMCPStatusPolling() {
        this.statusInterval = setInterval(async () => {
            try {
                const response = await fetch('/api/mcp_search/status');
                if (response.ok) {
                    const status = await response.json();
                    this.updateMCPStatus(status);

                    if (!status.is_running) {
                        this.stopMCPStatusPolling();
                        if (status.error) {
                            this.showMCPError(status.error);
                        } else {
                            this.showMCPSearchComplete(status);
                        }
                    }
                }
            } catch (error) {
                console.error('Status polling error:', error);
            }
        }, 1000);
    }

    stopMCPStatusPolling() {
        if (this.statusInterval) {
            clearInterval(this.statusInterval);
            this.statusInterval = null;
        }
    }

    updateMCPStatus(status) {
        // Update progress bar
        this.updateMCPProgress(status.progress, status.current_phase);

        // Update action badges
        this.updateMCPActionBadges(status.current_action);

        // Update statistics
        this.updateMCPStatistics(status.results);
    }

    updateMCPProgress(progress, phase) {
        const progressBar = document.querySelector('#mcpProgress .progress-bar');
        const phaseText = document.querySelector('#mcpProgress .phase-text');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;
            progressBar.textContent = `${Math.round(progress)}%`;
        }

        if (phaseText) {
            phaseText.textContent = phase;
        }
    }

    updateMCPActionBadges(currentAction) {
        const actions = ['DISCOVER', 'ACCESS', 'EXTRACT', 'INTERACT'];
        
        actions.forEach(action => {
            const badge = document.querySelector(`[data-mcp-action="${action}"]`);
            if (badge) {
                if (action === currentAction) {
                    badge.classList.add('badge-primary');
                    badge.classList.remove('badge-secondary');
                } else {
                    badge.classList.add('badge-secondary');
                    badge.classList.remove('badge-primary');
                }
            }
        });
        
        // Add pulsing animation to current action
        if (currentAction) {
            const activeBadges = document.querySelectorAll(`[data-mcp-action="${currentAction}"]`);
            activeBadges.forEach(badge => {
                badge.classList.add('active-action');
                setTimeout(() => {
                    badge.classList.remove('active-action');
                }, 2000);
            });
        }
    }

    updateMCPStatistics(results) {
        const stats = {
            'discovered-count': results.discovered_urls || 0,
            'accessed-count': results.accessed_pages || 0,
            'extracted-count': results.extracted_jobs || 0,
            'analyzed-count': results.analyzed_jobs || 0
        };

        Object.entries(stats).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                Utils.animateCounter(element, value);
            }
        });
    }

    showMCPSearchComplete(status) {
        this.showMCPResults();
        
        // Update final statistics
        const finalStats = {
            'discovered-final': status.results.discovered_urls || 0,
            'accessed-final': status.results.accessed_pages || 0,
            'extracted-final': status.results.extracted_jobs || 0,
            'analyzed-final': status.results.analyzed_jobs || 0
        };
        
        Object.entries(finalStats).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                Utils.animateCounter(element, value);
            }
        });
        
        // Show completion message
        Utils.showToast('Bright Data MCP search completed successfully!', 'success');
        
        // Update results summary
        const resultsText = document.getElementById('mcpResultsText');
        if (resultsText && status.results) {
            const totalJobs = status.results.analyzed_jobs || 0;
            resultsText.textContent = `Found and analyzed ${totalJobs} internship opportunities with Bright Data MCP enhanced AI insights.`;
        }
        
        // Show the View Jobs button
        document.getElementById('viewJobsBtn').style.display = 'inline-block';
    }

    async cancelMCPSearch() {
        try {
            const response = await fetch('/api/mcp_search/cancel', {
                method: 'POST'
            });

            if (response.ok) {
                const result = await response.json();
                this.stopMCPStatusPolling();
                this.resetMCPModalState();
                Utils.showToast('MCP search cancelled', 'info');
            }
        } catch (error) {
            console.error('Cancel error:', error);
            Utils.showToast('Failed to cancel search', 'error');
        }
    }

    viewMCPJobs() {
        // Close modal and redirect to enhanced view
        const modal = bootstrap.Modal.getInstance(document.getElementById('mcpSearchModal'));
        if (modal) modal.hide();
        
        // Add enhanced filter parameter
        window.location.href = '/?status=new';
    }
}

// ========== Statistics Dashboard ==========
class StatsDashboard {
    constructor() {
        this.init();
    }

    init() {
        this.animateStatsOnLoad();
        this.setupStatsHover();
    }

    animateStatsOnLoad() {
        const statsNumbers = document.querySelectorAll('.stats-number');
        
        statsNumbers.forEach((element, index) => {
            const targetValue = parseInt(element.textContent) || 0;
            element.textContent = '0';
            
            setTimeout(() => {
                Utils.animateCounter(element, targetValue);
            }, index * 200);
        });
    }

    setupStatsHover() {
        const statsCards = document.querySelectorAll('.stats-card');
        
        statsCards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px) scale(1.05)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = '';
            });
        });
    }
}

// ========== Responsive Navigation ==========
class NavigationManager {
    constructor() {
        this.init();
    }

    init() {
        this.setupMobileMenu();
        this.setupScrollEffects();
    }

    setupMobileMenu() {
        // Enhanced mobile menu behavior
        const navbar = document.querySelector('.navbar');
        const navbarToggler = document.querySelector('.navbar-toggler');
        
        if (navbarToggler) {
            navbarToggler.addEventListener('click', () => {
                navbar.classList.toggle('mobile-menu-open');
            });
        }
    }

    setupScrollEffects() {
        let lastScrollTop = 0;
        const navbar = document.querySelector('.navbar');
        
        window.addEventListener('scroll', Utils.throttle(() => {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            
            if (scrollTop > lastScrollTop && scrollTop > 100) {
                // Scrolling down
                navbar.style.transform = 'translateY(-100%)';
            } else {
                // Scrolling up
                navbar.style.transform = 'translateY(0)';
            }
            
            lastScrollTop = scrollTop;
        }, 100));
    }
}

// ========== Application Initialization ==========
class JobSearchApp {
    constructor() {
        this.components = {};
        this.init();
    }

    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeComponents());
        } else {
            this.initializeComponents();
        }
    }

    initializeComponents() {
        try {
            // Initialize all components
            this.components.search = new SearchManager();
            this.components.jobCards = new JobCardManager();
            this.components.mcpSearch = new MCPSearchManager();
            this.components.stats = new StatsDashboard();
            this.components.navigation = new NavigationManager();
            
            // Setup global event listeners
            this.setupGlobalEvents();
            
            // Initialize any remaining interactive elements
            this.initializeTooltips();
            this.initializeModals();
            
            console.log('Job Search App initialized successfully');
        } catch (error) {
            console.error('Error initializing Job Search App:', error);
        }
    }

    setupGlobalEvents() {
        // Handle form submissions with enhanced UX
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.tagName === 'FORM') {
                this.enhanceFormSubmission(form, e);
            }
        });

        // Handle keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });

        // Handle window resize
        window.addEventListener('resize', Utils.debounce(() => {
            this.handleWindowResize();
        }, AppConfig.debounce.resize));
    }

    enhanceFormSubmission(form, event) {
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn && !submitBtn.disabled) {
            // Add loading state
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<span class="loading-spinner me-2"></span>Processing...';
            submitBtn.disabled = true;
            
            // Reset after a delay (the form submission will handle the actual navigation)
            setTimeout(() => {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
            }, 2000);
        }
    }

    handleKeyboardShortcuts(event) {
        // Ctrl/Cmd + K for search focus
        if ((event.ctrlKey || event.metaKey) && event.key === 'k') {
            event.preventDefault();
            const searchInput = document.getElementById('search');
            if (searchInput) {
                searchInput.focus();
                searchInput.select();
            }
        }
        
        // Escape to close modals
        if (event.key === 'Escape') {
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                const modalInstance = bootstrap.Modal.getInstance(modal);
                if (modalInstance) modalInstance.hide();
            });
        }
    }

    handleWindowResize() {
        // Responsive adjustments
        const sidebar = document.querySelector('.sidebar');
        const mainContent = document.querySelector('.main-content');
        
        if (window.innerWidth < 768) {
            // Mobile adjustments
            document.body.classList.add('mobile-view');
        } else {
            document.body.classList.remove('mobile-view');
        }
    }

    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"], [title]'));
        tooltipTriggerList.forEach(tooltipTriggerEl => {
            if (!tooltipTriggerEl.hasAttribute('data-bs-toggle')) {
                tooltipTriggerEl.setAttribute('data-bs-toggle', 'tooltip');
            }
            new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initializeModals() {
        // Enhanced modal behavior
        const modals = document.querySelectorAll('.modal');
        modals.forEach(modal => {
            modal.addEventListener('show.bs.modal', (e) => {
                // Add backdrop blur effect
                document.body.classList.add('modal-backdrop-blur');
            });
            
            modal.addEventListener('hidden.bs.modal', (e) => {
                // Remove backdrop blur effect
                document.body.classList.remove('modal-backdrop-blur');
            });
        });
    }
}

// ========== Global Functions (for compatibility) ==========
// MCP Search Functions
window.executeMCPSearch = function() {
    if (window.jobSearchApp?.components?.mcpSearch) {
        window.jobSearchApp.components.mcpSearch.executeMCPSearch();
    }
};

window.cancelMCPSearch = function() {
    if (window.jobSearchApp?.components?.mcpSearch) {
        window.jobSearchApp.components.mcpSearch.cancelMCPSearch();
    }
};

window.viewMCPJobs = function() {
    if (window.jobSearchApp?.components?.mcpSearch) {
        window.jobSearchApp.components.mcpSearch.viewMCPJobs();
    }
};

// Initialize the application
window.jobSearchApp = new JobSearchApp();

// Add CSS for ripple effect and additional animations
const additionalStyles = `
<style>
.ripple {
    position: absolute;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.6);
    transform: scale(0);
    animation: ripple-animation 0.6s linear;
    pointer-events: none;
}

@keyframes ripple-animation {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

.modal-backdrop-blur {
    backdrop-filter: blur(5px);
}

.mobile-view .sidebar {
    margin-bottom: 2rem;
}

.mobile-view .job-card {
    margin-bottom: 1rem;
}

.loading {
    position: relative;
}

.loading::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    z-index: 1000;
    display: flex;
    align-items: center;
    justify-content: center;
}

.navbar {
    transition: transform 0.3s ease;
}

.mobile-menu-open {
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}
</style>
`;

document.head.insertAdjacentHTML('beforeend', additionalStyles);

// ========== Document Ready & Initialization ==========

document.addEventListener('DOMContentLoaded', () => {
    // Initialize core components
    const searchManager = new SearchManager();
    const jobCardManager = new JobCardManager();
    const mcpSearchManager = new MCPSearchManager();
    const statsDashboard = new StatsDashboard();
    const navigationManager = new NavigationManager();

    // Initialize tooltips (Bootstrap 5)
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize professional animations
    if (typeof window.initializeProfessionalAnimations === 'function') {
        window.initializeProfessionalAnimations();
    }

    // Enhanced scroll effects for navbar
    const navbar = document.querySelector('.navbar');
    if (navbar) {
        window.addEventListener('scroll', Utils.throttle(() => {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }, 100));
    }

    // MCP Search Form Submission
    const mcpSearchForm = document.getElementById('mcpSearchForm');
    if (mcpSearchForm) {
        mcpSearchForm.addEventListener('submit', (event) => {
            event.preventDefault();
            mcpSearchManager.executeMCPSearch();
        });
    }

    // MCP Cancel Button
    const mcpCancelBtn = document.getElementById('cancelMCPSearch');
    if (mcpCancelBtn) {
        mcpCancelBtn.addEventListener('click', () => {
            mcpSearchManager.cancelMCPSearch();
        });
    }

    // Global event listener for view details buttons (if added dynamically)
    // This is a fallback, preferred method is in JobCardManager's setupStatusButtons
    // document.body.addEventListener('click', function(event) {
    //     const viewDetailsButton = event.target.closest('.btn-view-details');
    //     if (viewDetailsButton) {
    //         jobCardManager.showJobDetailsModal(viewDetailsButton);
    //     }
    // });

    console.log('Professional Job Platform Initialized');
});
