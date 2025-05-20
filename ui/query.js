/**
 * Helper functions for query.html - displays data from the LLM Oracle API
 * This file reuses the showDetails function from app.js
 */

/**
 * Parse URL parameters
 */
function getUrlParams() {
    const params = {};
    const queryString = window.location.search.substring(1);
    const pairs = queryString.split('&');
    
    for (const pair of pairs) {
        const [key, value] = pair.split('=');
        if (key && value) {
            params[decodeURIComponent(key)] = decodeURIComponent(value);
        }
    }
    
    return params;
}

/**
 * Fetch query data from the API
 */
async function fetchQueryData() {
    // Get parameters from URL
    const params = getUrlParams();
    const apiBase = 'https://api.ai.uma.xyz';
    let apiUrl = '';
    
    // Determine which endpoint to use based on parameters
    if (params.query_id) {
        apiUrl = `${apiBase}/query?query_id=${params.query_id}`;
    } else if (params.condition_id) {
        apiUrl = `${apiBase}/query?condition_id=${params.condition_id}`;
    } else if (params.transaction_hash) {
        apiUrl = `${apiBase}/query?transaction_hash=${params.transaction_hash}`;
    } else if (params.question_id) {
        apiUrl = `${apiBase}/question/${params.question_id}`;
    } else {
        showError('No valid query parameters provided. Please include query_id, condition_id, transaction_hash, or question_id.');
        return;
    }
    
    // Add full=true parameter if not already included
    if (!apiUrl.includes('full=')) {
        apiUrl += apiUrl.includes('?') ? '&full=true' : '?full=true';
    }
    
    try {
        const response = await fetch(apiUrl);
        
        if (!response.ok) {
            throw new Error(`API request failed with status ${response.status}`);
        }
        
        const data = await response.json();
        
        // Handle different response formats
        if (Array.isArray(data) && data.length > 0) {
            // For query endpoint, it returns an array
            displayQueryResult(data[0]);
        } else if (data && typeof data === 'object') {
            // For question endpoint, it returns a single object
            displayQueryResult(data);
        } else {
            showError('No data found for the specified parameters.');
        }
    } catch (error) {
        showError(`Error fetching data: ${error.message}`);
        console.error('API Error:', error);
    }
}

/**
 * Display the query result using the modal's showDetails function
 */
function displayQueryResult(data) {
    // Hide loading indicator
    const loadingContainer = document.getElementById('loadingContainer');
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
    
    // Set up temporary data structure expected by showDetails
    if (typeof window.currentData === 'undefined') {
        window.currentData = [];
    }
    
    // Add data to currentData array
    window.currentData[0] = data;
    
    // Call showDetails function from app.js
    if (typeof window.showDetails === 'function') {
        window.showDetails(data, 0);
        
        // Show the modal container
        const detailsModal = document.getElementById('detailsModal');
        if (detailsModal) {
            detailsModal.style.display = 'block';
        }
        
        // Prevent modal backdrop and body lock on standalone page
        document.body.classList.add('modal-open-standalone');
        document.body.classList.remove('modal-open');
        document.body.style.overflow = 'auto';
        document.body.style.paddingRight = '0';
        
        // Remove any modal backdrop if it exists
        const backdrop = document.querySelector('.modal-backdrop');
        if (backdrop) {
            backdrop.classList.add('standalone-backdrop');
        }
    } else {
        showError('Error: showDetails function not available');
    }
}

/**
 * Show error message
 */
function showError(message) {
    const errorContainer = document.getElementById('errorContainer');
    const loadingContainer = document.getElementById('loadingContainer');
    
    if (errorContainer) {
        errorContainer.textContent = message;
        errorContainer.style.display = 'block';
    }
    
    if (loadingContainer) {
        loadingContainer.style.display = 'none';
    }
}

/**
 * Check if ONLY_DEEPLINKS environment flag is set
 */
async function checkEnvFlags() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            
            // Check for ONLY_DEEPLINKS flag
            if (config.only_deeplinks === true) {
                // Hide "Back to Dashboard" button when ONLY_DEEPLINKS is set
                const dashboardButton = document.querySelector('a[href="index.html"]');
                if (dashboardButton) {
                    dashboardButton.style.display = 'none';
                }
                
                // If ONLY_DEEPLINKS is set, we create a cookie to bypass auth for deep links
                // This allows direct access to query pages without login
                document.cookie = 'auth_token=deeplink_bypass; Path=/;';
            }
        }
    } catch (error) {
        console.warn('Could not fetch environment flags:', error);
        // Don't show error to user as this is not critical
    }
}

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', () => {
    fetchQueryData();
    checkEnvFlags();
});