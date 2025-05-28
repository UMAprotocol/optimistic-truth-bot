/**
 * Helper functions for query.html - displays data from the LLM Oracle API
 * This file reuses the showDetails function from app.js
 */

// Immediately set auth bypass cookie for deep links
document.cookie = 'auth_token=deeplink_bypass; Path=/;';

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
        
        // Set up toggle buttons for collapsible content
        setupToggleButtons();
        
        // Fix the Full JSON Data section
        fixFullJsonDataSection(data);
    } else {
        showError('Error: showDetails function not available');
    }
}

/**
 * Fix the Full JSON Data section to properly display the complete JSON
 */
function fixFullJsonDataSection(data) {
    // Find the Full JSON Data section
    const fullJsonSection = document.querySelector('#detailsModalBody .detail-section:last-child');
    if (!fullJsonSection || !fullJsonSection.textContent.includes('Full JSON Data')) {
        return;
    }
    
    // Find the pre element containing the JSON
    const preElement = fullJsonSection.querySelector('.card-body pre');
    if (!preElement) {
        return;
    }
    
    // Format the data object as a JSON string with proper indentation
    const formattedJson = JSON.stringify(data, null, 2);
    
    // Just set the text content directly without any syntax highlighting
    preElement.textContent = formattedJson;
    
    // Add some basic styling to make it readable
    preElement.style.fontFamily = 'monospace';
    preElement.style.whiteSpace = 'pre-wrap';
    preElement.style.wordBreak = 'break-word';
    preElement.style.maxHeight = '500px';
    preElement.style.overflow = 'auto';
    preElement.style.padding = '10px';
    preElement.style.backgroundColor = '#f8f9fa';
}

/**
 * Set up the toggle buttons for expandable content sections
 * This replicates the functionality from the modal shown event in app.js
 */
function setupToggleButtons() {
    const modalBody = document.getElementById('detailsModalBody');
    if (!modalBody) return;
    
    // Apply syntax highlighting to all code blocks
    if (window.Prism) {
        Prism.highlightAllUnder(modalBody);
    }
    
    // Set up toggle buttons for collapsible content
    document.querySelectorAll('#detailsModalBody .toggle-content-btn').forEach(btn => {
        // Remove any existing event listeners to prevent duplicates
        const newBtn = btn.cloneNode(true);
        btn.parentNode.replaceChild(newBtn, btn);
        
        // Add the event listener to the new button
        newBtn.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.toggle('collapsed');
                
                // If this is a code section, also toggle the Prism highlighting
                if (targetElement.querySelector('code') && window.Prism) {
                    Prism.highlightElement(targetElement.querySelector('code'));
                }
            }
        });
    });
    
    // Set up JSON property toggle buttons
    document.querySelectorAll('#detailsModalBody .json-property-key').forEach(key => {
        key.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();
            
            // Toggle the collapsed class on the key
            this.classList.toggle('collapsed');
            
            // Find the next sibling which should be the JSON value to toggle
            const valueElement = this.nextElementSibling;
            if (valueElement && valueElement.classList.contains('json-value')) {
                valueElement.classList.toggle('collapsed');
            }
        });
    });
    
    // Find and process all journey steps - especially code_runner steps
    const steps = document.querySelectorAll('#detailsModalBody .journey-step');
    steps.forEach((step, stepIndex) => {
        // Check if this is a code runner step by looking at the step content
        if (step.textContent.toLowerCase().includes('code_runner') || 
            step.querySelector('[data-actor="code_runner"]')) {
            
            // Find all code blocks and ensure they are visible
            const codeBlocks = step.querySelectorAll('.code-block, .code-content, .content-collapsible');
            codeBlocks.forEach((block, i) => {
                // Make sure each code element has an ID
                if (!block.id) {
                    block.id = `code-runner-step-${stepIndex}-code-${i}`;
                }
                
                // Remove the collapsed class to make code visible
                block.classList.remove('collapsed');
                
                // If this block contains Python code, highlight it
                if (block.querySelector('code.language-python') && window.Prism) {
                    Prism.highlightElement(block.querySelector('code.language-python'));
                }
            });
            
            // Also make sure any code field is properly displayed
            const codeField = step.querySelector('[data-field="code"]');
            if (codeField) {
                codeField.classList.remove('collapsed');
                if (codeField.nextElementSibling) {
                    codeField.nextElementSibling.classList.remove('collapsed');
                }
            }
            
            // Find any buttons that might control visibility of code sections
            const toggleButtons = step.querySelectorAll('.toggle-content-btn');
            toggleButtons.forEach(btn => {
                const targetId = btn.getAttribute('data-target');
                if (targetId && targetId.includes('code')) {
                    const targetEl = document.getElementById(targetId);
                    if (targetEl) {
                        targetEl.classList.remove('collapsed');
                    }
                }
            });
        }
    });
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