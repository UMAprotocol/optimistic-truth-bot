// Global variables to store data and charts
let currentData = [];
let currentExperiment = null;
let experimentsData = [];
let modal = null;
let currentFilter = 'all'; // Track current result filter
let currentSearch = ''; // Track current search term
let currentSourceFilter = 'filesystem'; // Track current source filter
let autoScrollEnabled = true; // Auto-scroll preference
let mongoOnlyResults = false; // Track if we should only show MongoDB results
let disableExperimentRunner = true; // Track if experiment runner is disabled (DISABLED BY DEFAULT NOW)
let singleExperiment = ''; // Track if we're in single experiment mode

// Date filter variables
let currentDateFilters = {
    expiration_timestamp: null,
    request_transaction_block_time: null
};

// Add column preferences with defaults
let columnPreferences = {
    timestamp: true,
    proposal_timestamp: true,
    id: true,
    title: true,
    recommendation: true,
    router_decision: false,
    resolution: true,
    disputed: true,
    correct: true,
    block_number: false,
    proposal_bond: false,
    tags: false,
    expiration_timestamp: false,
    request_timestamp: false,
    request_transaction_block_time: true
};

// Chart variables
let recommendationChart = null;
let resolutionChart = null;

// Experiment runner variables
let activeProcesses = [];
let commandHistory = [];
let currentProcessId = null;

// Global variable to track current sort state
let currentSort = {
    column: 'timestamp', // Default sort column is timestamp
    direction: 'desc'    // Default direction is descending (newest first)
};

// Function to fetch server configuration
async function fetchServerConfig() {
    try {
        const response = await fetch('/api/config');
        if (response.ok) {
            const config = await response.json();
            console.log('Server config:', config);
            
            // Update global settings
            mongoOnlyResults = config.mongo_only_results === true;
            disableExperimentRunner = config.disable_experiment_runner === true;
            singleExperiment = config.single_experiment || '';
            
            // Update UI based on configuration
            const sourceFilterGroup = document.querySelector('.source-filter-group');
            if (sourceFilterGroup) {
                sourceFilterGroup.style.display = mongoOnlyResults ? 'none' : 'block';
            }
            
            // If mongo_only_results is true, force MongoDB source filter
            if (mongoOnlyResults) {
                currentSourceFilter = 'mongodb';
                document.getElementById('filterSourceMongoDB')?.classList.add('active');
                document.getElementById('filterSourceFilesystem')?.classList.remove('active');
            }
            
            // Update UI for single experiment mode
            if (singleExperiment) {
                // Hide experiment selection panel
                const experimentListColumn = document.querySelector('.col-md-4 .card');
                if (experimentListColumn) {
                    experimentListColumn.style.display = 'none';
                }
                
                // Make the result column full width
                const resultColumn = document.querySelector('.col-md-8');
                if (resultColumn) {
                    resultColumn.className = 'col-md-12';
                }
            }
            
            return config;
        }
    } catch (error) {
        console.error('Error fetching server config:', error);
    }
    
    return null;
}

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modal
    modal = new bootstrap.Modal(document.getElementById('detailsModal'));
    
    // Initialize tab functionality
    initializeTabs();
    
    // Fetch server configuration first
    fetchServerConfig().then((config) => {
        // Hide experiment runner tab if disabled
        if (disableExperimentRunner) {
            const experimentTab = document.getElementById('experiment-tab');
            if (experimentTab) {
                experimentTab.parentElement.style.display = 'none';
                
                // Show analytics tab if experiment runner tab is active
                const analyticsTab = document.getElementById('analytics-tab');
                if (experimentTab.classList.contains('active') && analyticsTab) {
                    const tabInstance = new bootstrap.Tab(analyticsTab);
                    tabInstance.show();
                }
            }
        }
        
        // Then load experiments directory data
        loadExperimentsData();
    });

    // Setup tag filter when data is loaded
    document.addEventListener('dataLoaded', setupTagFilter);
    
    // Load saved column preferences
    loadColumnPreferences();
    
    // Initialize column selector
    initializeColumnSelector();

    // Set up search functionality
    document.getElementById('searchBtn')?.addEventListener('click', () => {
        currentSearch = document.getElementById('searchInput').value.trim().toLowerCase();
        applyTableFilter(currentFilter);
    });

    // Handle Enter key in search field
    document.getElementById('searchInput')?.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            currentSearch = this.value.trim().toLowerCase();
            applyTableFilter(currentFilter);
        }
    });

    // Set up filter buttons
    document.getElementById('filterAll')?.addEventListener('click', () => {
        applyFilter('all');
    });

    document.getElementById('filterDisputed')?.addEventListener('click', () => {
        applyFilter('disputed');
    });

    document.getElementById('filterCorrect')?.addEventListener('click', () => {
        applyFilter('correct');
    });

    document.getElementById('filterIncorrect')?.addEventListener('click', () => {
        applyFilter('incorrect');
    });

    document.getElementById('filterIncorrectIgnoringP4')?.addEventListener('click', () => {
        applyFilter('incorrectIgnoringP4');
    });
    
    // Set up source filter buttons if not in mongoOnlyResults mode
    document.getElementById('filterSourceFilesystem')?.addEventListener('click', () => {
        if (!mongoOnlyResults) {
            applySourceFilter('filesystem');
        }
    });
    
    document.getElementById('filterSourceMongoDB')?.addEventListener('click', () => {
        applySourceFilter('mongodb');
    });
    
    // Set up clear tag filter button
    document.getElementById('clearTagFilter')?.addEventListener('click', clearTagFilter);
    
    // Set up date filter controls
    document.getElementById('applyDateFilter')?.addEventListener('click', applyDateFilter);
    document.getElementById('clearDateFilter')?.addEventListener('click', clearDateFilter);
    
    // Set up logout button
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    
    // Set up auto-scroll toggle
    const autoScrollToggle = document.getElementById('autoScrollToggle');
    if (autoScrollToggle) {
        // Initialize from localStorage if available
        const savedAutoScrollPref = localStorage.getItem('autoScrollEnabled');
        if (savedAutoScrollPref !== null) {
            autoScrollEnabled = savedAutoScrollPref === 'true';
        }
        autoScrollToggle.checked = autoScrollEnabled;
        
        autoScrollToggle.addEventListener('change', () => {
            autoScrollEnabled = autoScrollToggle.checked;
            localStorage.setItem('autoScrollEnabled', autoScrollEnabled);
        });
    }
    
    // Set up experiment runner events
    initializeExperimentRunner();

    // Add event listener for modal shown event to apply syntax highlighting and set up toggle buttons
    document.getElementById('detailsModal')?.addEventListener('shown.bs.modal', function () {
        const modalBody = document.getElementById('detailsModalBody');
        
        // Reapply syntax highlighting to all code blocks
        Prism.highlightAllUnder(modalBody);
        
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
                    if (targetElement.querySelector('code')) {
                        Prism.highlightElement(targetElement.querySelector('code'));
                    }
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
                    if (block.querySelector('code.language-python')) {
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
    });
});

// Initialize the tab functionality
function initializeTabs() {
    // Handle main navigation tab clicks
    document.querySelectorAll('#mainNavTabs .nav-link').forEach(tab => {
        tab.addEventListener('click', (event) => {
            // Prevent default hash-based scrolling
            event.preventDefault();
            
            // Store the active tab using Bootstrap's tab API instead of URL hash
            const tabInstance = new bootstrap.Tab(event.target);
            tabInstance.show();
        });
    });
}

// Initialize experiment runner components
function initializeExperimentRunner() {
    // Skip initialization if experiment runner is disabled
    if (disableExperimentRunner) {
        return;
    }
    
    // Setup command form submission
    const form = document.getElementById('experimentForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            const commandInput = document.getElementById('commandInput');
            const command = commandInput.value.trim();
            
            if (command) {
                commandInput.value = '';
                startProcess(command);
                // Reset height after clearing
                autoResizeTextarea(commandInput);
            }
        });
    }
    
    // Setup textarea auto-resize functionality
    const commandInput = document.getElementById('commandInput');
    if (commandInput) {
        // Initial resize
        autoResizeTextarea(commandInput);
        
        // Add event listeners for input changes
        commandInput.addEventListener('input', function() {
            autoResizeTextarea(this);
        });
        
        // Also handle paste events
        commandInput.addEventListener('paste', function() {
            // Use setTimeout to ensure the paste content is in the textarea
            setTimeout(() => autoResizeTextarea(this), 0);
        });
    }
    
    // Setup Python script interactive runner
    const runPythonBtn = document.getElementById('runPythonBtn');
    if (runPythonBtn) {
        runPythonBtn.addEventListener('click', function() {
            const commandInput = document.getElementById('commandInput');
            const command = commandInput.value.trim();
            
            if (command) {
                // Check if it's a Python script
                if (command.endsWith('.py') || command.includes('python')) {
                    commandInput.value = '';
                    // Run with shell=True to enable shell features and in interactive mode
                    startProcess(`python -u ${command}`, true); // Pass true to indicate it's an interactive Python script
                } else {
                    alert('Please enter a Python script command (e.g., proposal_replayer/create_experiment.py)');
                }
            } else {
                alert('Please enter a Python script path');
            }
        });
    }
    
    // Setup interactive input form submission
    const interactiveForm = document.getElementById('interactiveInputForm');
    if (interactiveForm) {
        interactiveForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const inputField = document.getElementById('interactiveInput');
            const input = inputField.value;
            
            if (currentProcessId !== null) {
                // Send input to process (allowing empty strings)
                sendProcessInput(currentProcessId, input);
                inputField.value = '';
            }
        });
    }
    
    // Load command history from localStorage
    loadCommandHistory();
    
    // Initialize buttons
    document.getElementById('clearLogsBtn')?.addEventListener('click', () => {
        clearLogs();
    });
    
    document.getElementById('downloadLogsBtn')?.addEventListener('click', () => {
        downloadLogs();
    });
    
    // Handle timestamp toggle
    const timestampToggle = document.getElementById('showTimestamps');
    if (timestampToggle) {
        timestampToggle.addEventListener('change', () => {
            document.body.classList.toggle('hide-timestamps', !timestampToggle.checked);
        });
    }
    
    // Initialize process list
    loadActiveProcesses();
    
    // Polling for process updates disabled to prevent login redirects
    // setInterval(loadActiveProcesses, 1000); // Once per second is enough for the list
}

// Load command history from storage
function loadCommandHistory() {
    try {
        const storedHistory = localStorage.getItem('commandHistory');
        if (storedHistory) {
            commandHistory = JSON.parse(storedHistory);
            
            // Ensure each entry has a valid ID
            commandHistory.forEach((entry, index) => {
                if (!entry.id) {
                    entry.id = `history_${index}_${Date.now()}`;
                }
                
                // Initialize logs array if not present
                if (!entry.logs) {
                    entry.logs = [];
                }
            });
            
            // Sort by timestamp (newest first)
            commandHistory.sort((a, b) => b.timestamp - a.timestamp);
        }
    } catch (error) {
        console.error('Error loading command history:', error);
        commandHistory = [];
    }
}

// Add a command to history
function addToCommandHistory(command, processId = null) {
    // Don't add empty commands
    if (!command.trim()) {
        return null;
    }
    
    // First, check if we already have an EXACT match for this command with processId
    if (processId) {
        const existingEntryWithId = commandHistory.find(h => h.id === processId);
        if (existingEntryWithId) {
            // Ensure status is up to date
            existingEntryWithId.status = 'running';
            // Save to localStorage
            localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
            return existingEntryWithId;
        }
    }
    
    // Check if we have a recent similar command (last 15 seconds)
    const recentSimilarEntry = commandHistory.find(h => 
        h.command === command && Date.now() - h.timestamp < 15000);
    
    if (recentSimilarEntry) {
        // If process ID is provided, update the existing entry
        if (processId) {
            recentSimilarEntry.id = processId;
            recentSimilarEntry.status = 'running';
        }
        // Save to localStorage
        localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
        return recentSimilarEntry;
    }
    
    // Remove any exact command duplicates before adding new entry
    // This ensures we don't have multiple entries with the same command
    const duplicateIndex = commandHistory.findIndex(h => h.command === command);
    if (duplicateIndex !== -1) {
        commandHistory.splice(duplicateIndex, 1);
    }
    
    // Create new history entry
    const historyEntry = {
        id: processId || `history_${Date.now()}`,
        command: command,
        timestamp: Date.now(),
        status: processId ? 'running' : 'completed',
        logs: []
    };
    
    // Add to beginning of history array
    commandHistory.unshift(historyEntry);
    
    // Limit history to 100 entries
    if (commandHistory.length > 100) {
        commandHistory = commandHistory.slice(0, 100);
    }
    
    // Save to localStorage
    localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
    
    return historyEntry;
}

// Update the history status for a command
function updateCommandHistoryStatus(processId, status) {
    // Find matching history entry for the most recent command with this status
    const processInfo = activeProcesses.find(p => p.id === processId);
    if (!processInfo) return;
    
    const command = processInfo.command;
    const historyEntry = commandHistory.find(h => h.command === command && h.status === 'running');
    
    if (historyEntry) {
        historyEntry.status = status;
        // Save updated history to localStorage
        try {
            localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
        } catch (error) {
            console.error('Error saving command history:', error);
        }
        
        // Update history table
        updateCommandHistoryTable();
    }
}

// Update the command history table
function updateCommandHistoryTable() {
    const tableBody = document.getElementById('historyTableBody');
    const paginationContainer = document.getElementById('historyPagination');
    if (!tableBody) return;
    
    // COMPLETE REWORK: Create a single source of truth for history items
    // A Set of all process IDs already seen to avoid duplicates
    const seenIds = new Set();
    // Also track commands to avoid duplicates with different IDs
    const seenCommands = new Set();
    
    // Make a fresh combined history array with unique items
    let combinedHistory = [];
    
    // First add active processes since they have the most up-to-date info
    activeProcesses.forEach(process => {
        // Add each active process once
        if (!seenIds.has(process.id)) {
            seenIds.add(process.id);
            seenCommands.add(process.command);
            combinedHistory.push({
                id: process.id,
                command: process.command,
                timestamp: process.start_time * 1000, // Convert to milliseconds
                status: process.status,
                logs: process.logs || []
            });
        }
    });
    
    // Then add localStorage history items that aren't already included
    // Sort by timestamp first so we get the newest version of each command
    const sortedHistory = [...commandHistory].sort((a, b) => b.timestamp - a.timestamp);
    
    sortedHistory.forEach(entry => {
        // Skip entries for commands we've already seen, unless this one is failed and we have a not-failed one
        if (seenCommands.has(entry.command)) {
            // Only add a failed/completed entry to replace a running entry
            const existingEntry = combinedHistory.find(h => h.command === entry.command);
            if (existingEntry && existingEntry.status === 'running' && 
                (entry.status === 'failed' || entry.status === 'completed')) {
                // Replace the running entry with this completed/failed one
                const index = combinedHistory.indexOf(existingEntry);
                combinedHistory[index] = entry;
            }
            return;
        }
        
        // Only add if we haven't seen this ID yet
        if (!seenIds.has(entry.id)) {
            seenIds.add(entry.id);
            seenCommands.add(entry.command);
            combinedHistory.push(entry);
        }
    });
    
    // If no items, show empty state
    if (combinedHistory.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">No command history</td>
            </tr>
        `;
        if (paginationContainer) paginationContainer.innerHTML = '';
        return;
    }
    
    // Sort by timestamp (newest first)
    combinedHistory.sort((a, b) => b.timestamp - a.timestamp);
    
    // Pagination settings
    const itemsPerPage = 10;
    const currentPage = parseInt(tableBody.getAttribute('data-current-page') || '1');
    const totalPages = Math.ceil(combinedHistory.length / itemsPerPage);
    
    // Calculate start and end index for the current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, combinedHistory.length);
    
    // Get the items for the current page
    const currentPageItems = combinedHistory.slice(startIndex, endIndex);
    
    // Generate table rows
    tableBody.innerHTML = currentPageItems.map(entry => {
        const formattedTime = formatDate(Math.floor(entry.timestamp / 1000));
        let statusClass = '';
        let statusText = entry.status;
        
        if (entry.status === 'running') {
            statusClass = 'status-running';
            statusText = `<i class="bi bi-play-fill"></i>Running`;
        } else if (entry.status === 'completed') {
            statusClass = 'status-completed';
            statusText = `<i class="bi bi-check-circle"></i>Completed`;
        } else if (entry.status === 'failed' || entry.status === 'stopped') {
            statusClass = 'status-failed';
            statusText = `<i class="bi bi-x-circle"></i>${entry.status === 'failed' ? 'Failed' : 'Stopped'}`;
        } else if (entry.status === 'pending') {
            statusClass = 'status-pending';
            statusText = `<i class="bi bi-hourglass"></i>Pending`;
        }
        
        return `
            <tr class="history-row" data-entry-id="${entry.id}">
                <td>${formattedTime}</td>
                <td class="command-cell" title="${entry.command}"><code>${entry.command}</code></td>
                <td class="${statusClass}">${statusText}</td>
                <td>
                    <div class="btn-group history-actions" role="group">
                        <button class="btn btn-sm btn-outline-primary use-command-btn" title="Use this command">
                            <i class="bi bi-arrow-up-square"></i> Use
                        </button>
                        <button class="btn btn-sm btn-outline-info view-history-logs-btn" title="View logs">
                            <i class="bi bi-file-text"></i> Logs
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Store the current page in the table
    tableBody.setAttribute('data-current-page', currentPage);
    
    // Update pagination controls
    if (paginationContainer) {
        // Only show pagination if we have more than one page
        if (totalPages > 1) {
            let paginationHTML = `
                <nav aria-label="History pagination">
                    <ul class="pagination pagination-sm justify-content-center mb-0">
                        <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                            <a class="page-link" href="#" data-page="prev" aria-label="Previous">
                                <span aria-hidden="true">&laquo;</span>
                            </a>
                        </li>
            `;
            
            // Display up to 5 page numbers, centered around the current page
            const maxVisiblePages = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
            let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
            
            // Adjust if we're near the end
            if (endPage - startPage + 1 < maxVisiblePages) {
                startPage = Math.max(1, endPage - maxVisiblePages + 1);
            }
            
            // Add first page if we're not starting from page 1
            if (startPage > 1) {
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" data-page="1">1</a>
                    </li>
                `;
                if (startPage > 2) {
                    paginationHTML += `
                        <li class="page-item disabled">
                            <a class="page-link" href="#">...</a>
                        </li>
                    `;
                }
            }
            
            // Add page numbers
            for (let i = startPage; i <= endPage; i++) {
                paginationHTML += `
                    <li class="page-item ${i === currentPage ? 'active' : ''}">
                        <a class="page-link" href="#" data-page="${i}">${i}</a>
                    </li>
                `;
            }
            
            // Add last page if we're not ending at the last page
            if (endPage < totalPages) {
                if (endPage < totalPages - 1) {
                    paginationHTML += `
                        <li class="page-item disabled">
                            <a class="page-link" href="#">...</a>
                        </li>
                    `;
                }
                paginationHTML += `
                    <li class="page-item">
                        <a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>
                    </li>
                `;
            }
            
            paginationHTML += `
                        <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                            <a class="page-link" href="#" data-page="next" aria-label="Next">
                                <span aria-hidden="true">&raquo;</span>
                            </a>
                        </li>
                    </ul>
                </nav>
            `;
            
            paginationContainer.innerHTML = paginationHTML;
            
            // Add pagination click event
            document.querySelectorAll('#historyPagination .page-link').forEach(link => {
                link.addEventListener('click', function(e) {
                    e.preventDefault();
                    
                    const page = this.getAttribute('data-page');
                    let newPage = currentPage;
                    
                    if (page === 'prev') {
                        newPage = Math.max(1, currentPage - 1);
                    } else if (page === 'next') {
                        newPage = Math.min(totalPages, currentPage + 1);
                    } else {
                        newPage = parseInt(page);
                    }
                    
                    if (newPage !== currentPage) {
                        tableBody.setAttribute('data-current-page', newPage);
                        updateCommandHistoryTable();
                    }
                });
            });
        } else {
            paginationContainer.innerHTML = '';
        }
    }
    
    // Add click event for command reuse
    document.querySelectorAll('.use-command-btn').forEach(btn => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const row = event.target.closest('.history-row');
            if (row) {
                const entryId = row.getAttribute('data-entry-id');
                const historyEntry = combinedHistory.find(h => h.id === entryId);
                if (historyEntry) {
                    document.getElementById('commandInput').value = historyEntry.command;
                    document.getElementById('commandInput').focus();
                }
            }
        });
    });
    
    // Add click event for viewing logs of history entries
    document.querySelectorAll('.view-history-logs-btn').forEach(btn => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const row = event.target.closest('.history-row');
            if (row) {
                const entryId = row.getAttribute('data-entry-id');
                const historyEntry = combinedHistory.find(h => h.id === entryId);
                if (historyEntry) {
                    showHistoryLogs(historyEntry);
                }
            }
        });
    });
    
    // Add click event to rows for viewing logs
    document.querySelectorAll('.history-row').forEach(row => {
        row.addEventListener('click', () => {
            const entryId = row.getAttribute('data-entry-id');
            const historyEntry = combinedHistory.find(h => h.id === entryId);
            if (historyEntry) {
                showHistoryLogs(historyEntry);
            }
        });
    });
}

// Fetch and display logs for a history entry
async function showHistoryLogs(historyEntry) {
    try {
        if (!historyEntry) {
            console.error('No history entry provided');
            return;
        }
        
        console.log(`Showing logs for history entry: ${historyEntry.id} (${historyEntry.command})`);
        
        // Update current process ID
        currentProcessId = historyEntry.id || null;
        
        // Get the logs container
        const logsContainer = document.getElementById('processLogs');
        const logsTitle = document.getElementById('logsTitle');
        
        if (!logsContainer) {
            console.error('No logs container found');
            return;
        }
        
        // Show loading state
        logsContainer.innerHTML = `
            <div class="text-center mt-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading logs...</span>
                </div>
                <p class="mt-3">Loading logs for: ${historyEntry.command}</p>
            </div>
        `;
        
        // Check if we have cached logs in the history entry
        if (historyEntry.logs && historyEntry.logs.length > 0) {
            // Generate log entries from history
            const logHtml = historyEntry.logs.map(log => {
                const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
                return `<div class="log-entry log-${log.type || 'info'}"><span class="log-timestamp">[${formattedTime}]</span><span class="log-message">${log.message}</span></div>`;
            }).join('');
            
            logsContainer.innerHTML = logHtml;
            
            // Only scroll to bottom if auto-scroll is enabled
            if (autoScrollEnabled) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
            
            // Update the logs title
            if (logsTitle) {
                const statusBadge = historyEntry.status ? 
                    `<span class="badge ${
                        historyEntry.status === 'completed' ? 'bg-success' : 
                        historyEntry.status === 'failed' ? 'bg-danger' : 
                        historyEntry.status === 'stopped' ? 'bg-warning' : 'bg-primary'
                    }">${historyEntry.status}</span>` : '';
                
                logsTitle.innerHTML = `Process Logs: <code>${historyEntry.command}</code> ${statusBadge}`;
            }
            
            return;
        }
        
        // Check if we have another entry with the same command that might have more info
        const matchingEntry = commandHistory.find(h => 
            h.id !== historyEntry.id && 
            h.command === historyEntry.command && 
            h.status !== 'running');
            
        if (matchingEntry && matchingEntry.logs && matchingEntry.logs.length > 0) {
            // Use logs from the matching entry
            console.log(`Using logs from matching entry for the same command`);
            
            // Generate log entries from the matched entry's logs
            const logHtml = matchingEntry.logs.map(log => {
                const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
                return `<div class="log-entry log-${log.type || 'info'}"><span class="log-timestamp">[${formattedTime}]</span><span class="log-message">${log.message}</span></div>`;
            }).join('');
            
            logsContainer.innerHTML = logHtml;
            
            // Only scroll to bottom if auto-scroll is enabled
            if (autoScrollEnabled) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
            
            // Update the logs title
            if (logsTitle) {
                const statusBadge = matchingEntry.status ? 
                    `<span class="badge ${
                        matchingEntry.status === 'completed' ? 'bg-success' : 
                        matchingEntry.status === 'failed' ? 'bg-danger' : 
                        matchingEntry.status === 'stopped' ? 'bg-warning' : 'bg-primary'
                    }">${matchingEntry.status}</span>` : '';
                
                logsTitle.innerHTML = `Process Logs: <code>${matchingEntry.command}</code> ${statusBadge}`;
            }
            
            return;
        }
        
        // Make the API request if we don't have cached logs
        const response = await fetch(`/api/process/${historyEntry.id}`);
        
        if (response.ok) {
            const processData = await response.json();
            console.log(`Retrieved logs for process: ${processData.command}, status: ${processData.status}`);
            
            // Update logs container
            if (logsContainer && processData.logs) {
                // Generate log entries
                if (processData.logs.length > 0) {
                    const logHtml = processData.logs.map(log => {
                        const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
                        return `<div class="log-entry log-${log.type || 'info'}"><span class="log-timestamp">[${formattedTime}]</span><span class="log-message">${log.message}</span></div>`;
                    }).join('');
                    
                    logsContainer.innerHTML = logHtml;
                    
                    // Only scroll to bottom if auto-scroll is enabled
                    if (autoScrollEnabled) {
                        logsContainer.scrollTop = logsContainer.scrollHeight;
                    }
                    
                    // Also update our history entry with these logs for future reference
                    historyEntry.logs = processData.logs;
                    historyEntry.status = processData.status;
                    
                    // Save updated history to localStorage
                    localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
                } else {
                    // No logs found in the response
                    logsContainer.innerHTML = `
                        <div class="text-center p-3">
                            <div class="alert alert-info">
                                <i class="bi bi-info-circle me-2"></i>
                                No logs available for this command
                            </div>
                        </div>
                    `;
                }
            } else {
                logsContainer.innerHTML = `
                    <div class="text-center p-3">
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            No logs container found or logs missing from response
                        </div>
                    </div>
                `;
            }
            
            // Update the logs title
            if (logsTitle) {
                const statusBadge = processData.status ? 
                    `<span class="badge ${
                        processData.status === 'completed' ? 'bg-success' : 
                        processData.status === 'failed' ? 'bg-danger' : 
                        processData.status === 'stopped' ? 'bg-warning' : 'bg-primary'
                    }">${processData.status}</span>` : '';
                
                logsTitle.innerHTML = `Process Logs: <code>${historyEntry.command}</code> ${statusBadge}`;
            }
        } else {
            const errorData = await response.json().catch(() => ({ error: 'Unknown error' }));
            console.error('Failed to fetch logs:', errorData.error || response.statusText);
            throw new Error(`Failed to fetch logs: ${errorData.error || response.statusText}`);
        }
    } catch (error) {
        console.error('Error fetching logs:', error);
        // Show error message
        const logsContainer = document.getElementById('processLogs');
        if (logsContainer) {
            logsContainer.innerHTML = `
                <div class="text-center p-3">
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        Could not retrieve logs for the command: <code>${historyEntry.command}</code>
                    </div>
                    <p>Error: ${error.message}</p>
                    <p>Logs for completed processes may not be available if they were run in a previous session.</p>
                </div>
            `;
        }
        
        // Update the logs title
        const logsTitle = document.getElementById('logsTitle');
        if (logsTitle) {
            logsTitle.innerHTML = `Process Logs: <code>${historyEntry.command}</code> <span class="badge bg-warning text-dark">Not Available</span>`;
        }
    } finally {
        // Switch to the Experiment Runner tab to show logs/error messages
        const experimentTab = document.getElementById('experiment-tab');
        if (experimentTab) {
            const tabInstance = new bootstrap.Tab(experimentTab);
            tabInstance.show();
        }
    }
}

// Fetch logs for a process that may not be active anymore
async function fetchProcessLogs(processId, command) {
    try {
        // Update current process ID
        currentProcessId = processId;
        
        // First try to fetch the logs directly
        const response = await fetch(`/api/process/${processId}`);
        
        if (response.ok) {
            const processData = await response.json();
            
            // Temporarily add to activeProcesses if it's not already there
            if (!activeProcesses.find(p => p.id === processId)) {
                activeProcesses.push(processData);
            }
            
            // Show the logs
            updateProcessLogs(processId);
            
            // Switch to the Experiment Runner tab to see the logs
            const experimentTab = document.getElementById('experiment-tab');
            if (experimentTab) {
                const tabInstance = new bootstrap.Tab(experimentTab);
                tabInstance.show();
            }
        } else {
            // If the specific process API failed, try to find logs in a log file
            showFailedProcessLogs(processId, command);
        }
    } catch (error) {
        console.error('Error fetching process logs:', error);
        showFailedProcessLogs(processId, command);
    }
}

// Show a message when logs can't be found
function showFailedProcessLogs(processId, command) {
    const logsContainer = document.getElementById('processLogs');
    if (logsContainer) {
        logsContainer.innerHTML = `
            <div class="text-center p-3">
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Could not retrieve logs for the command: <code>${command}</code>
                </div>
                <p>Logs for completed processes may not be available if they were run in a previous session.</p>
            </div>
        `;
        
        // Update the logs title
        const logsTitle = document.getElementById('logsTitle');
        if (logsTitle) {
            logsTitle.innerHTML = `Process Logs: <code>${command}</code> <span class="badge bg-warning text-dark">Not Available</span>`;
        }
        
        // Switch to the Experiment Runner tab to see the message
        const experimentTab = document.getElementById('experiment-tab');
        if (experimentTab) {
            const tabInstance = new bootstrap.Tab(experimentTab);
            tabInstance.show();
        }
    }
}

// Start a new process
async function startProcess(command, isInteractive = false) {
    try {
        // Add to command history but don't update the table yet
        const historyEntry = addToCommandHistory(command);
        
        // Show the console logs area immediately with "Starting process" message
        const logsContainer = document.getElementById('processLogs');
        const logsTitle = document.getElementById('logsTitle');
        
        if (logsContainer) {
            logsContainer.innerHTML = `
                <div class="log-entry log-info">
                    <span class="log-timestamp">[${formatLogTime(new Date())}]</span>
                    <span class="log-message">Starting process: ${command}</span>
                </div>
            `;
            // Respect auto-scroll preference
            if (autoScrollEnabled) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        }
        
        if (logsTitle) {
            logsTitle.innerHTML = `Process Logs: <code>${command}</code> <span class="loading-indicator"><i class="bi bi-hourglass"></i> Starting...</span>`;
        }
        
        // Switch to the Experiment Runner tab to show logs
        const experimentTab = document.getElementById('experiment-tab');
        if (experimentTab) {
            const tabInstance = new bootstrap.Tab(experimentTab);
            tabInstance.show();
        }
        
        // Make API request to start the process
        const response = await fetch('/api/process/start', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ command })
        });
        
        if (!response.ok) {
            throw new Error(`Failed to start process: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log('Process started:', data);
        
        // IMPORTANT: The server sends process_id not id
        const processId = data.process_id;
        
        // Update the history entry with the process ID
        updateCommandHistoryStatus(processId, 'running');
        
        // Set as the current process for displaying logs
        currentProcessId = processId;
        
        // Update the process table
        await loadActiveProcesses();
        
        // Start polling for logs
        if (logPollingInterval) {
            clearInterval(logPollingInterval);
        }
        
        // Poll immediately first
        await updateProcessLogs(processId);
        
        // For Python scripts, always show the interactive input initially
        if (isInteractive) {
            toggleInteractiveInput(processId, true);
        }
        
        // Then set up interval polling
        logPollingInterval = setInterval(async () => {
            await updateProcessLogs(processId);
        }, 1000); // Poll every second
        
    } catch (error) {
        console.error('Failed to start process:', error);
        
        const logsContainer = document.getElementById('processLogs');
        if (logsContainer) {
            logsContainer.innerHTML += `
                <div class="log-entry log-error">
                    <span class="log-timestamp">[${formatLogTime(new Date())}]</span>
                    <span class="log-message">Error: ${error.message}</span>
                </div>
            `;
            // Respect auto-scroll preference for errors too
            if (autoScrollEnabled) {
                logsContainer.scrollTop = logsContainer.scrollHeight;
            }
        }
    }
}

// Function to append logs to the display
function appendLogsToDisplay(logsContainer, logs, startIndex) {
    if (!logsContainer || !logs || logs.length === 0) return;
    
    // Remove any spinner
    const existingSpinner = logsContainer.querySelector('.spinner-border');
    if (existingSpinner && existingSpinner.parentElement) {
        existingSpinner.parentElement.remove();
    }
    
    // Store current scroll position information
    const scrollInfo = {
        // More precise detection of manually scrolled position
        atBottom: Math.abs(logsContainer.scrollHeight - logsContainer.scrollTop - logsContainer.clientHeight) < 10,
        initialScrollHeight: logsContainer.scrollHeight,
        initialScrollTop: logsContainer.scrollTop,
        userScrolledUp: logsContainer.scrollHeight > 0 && 
                       logsContainer.scrollTop < logsContainer.scrollHeight - logsContainer.clientHeight - 20
    };
    
    // Track existing log entries to avoid duplicates
    const existingLogEntries = new Set();
    logsContainer.querySelectorAll('.log-entry').forEach(entry => {
        const timestamp = entry.querySelector('.log-timestamp')?.textContent || '';
        const message = entry.querySelector('.log-message')?.textContent || '';
        existingLogEntries.add(`${timestamp}${message}`);
    });
    
    // Keep track of whether we've detected an input prompt
    let waitingForInput = false;
    let lastMessage = '';
    let newLogsAdded = false;
    
    // Loop through each log entry and add it to the display if unique
    logs.forEach((log, index) => {
        if (index < startIndex) return; // Skip logs we've already processed
        
        const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
        const timestampText = `[${formattedTime}]`;
        const messageText = log.message;
        lastMessage = messageText; // Track last message for input prompt detection
        
        // Check if this log entry is already displayed
        const logKey = `${timestampText}${messageText}`;
        if (!existingLogEntries.has(logKey)) {
            const logEntry = document.createElement('div');
            logEntry.className = `log-entry log-${log.type || 'info'}`;
            logEntry.innerHTML = `<span class="log-timestamp">${timestampText}</span><span class="log-message">${messageText}</span>`;
            logsContainer.appendChild(logEntry);
            existingLogEntries.add(logKey);
            newLogsAdded = true;
        }
    });
    
    // Check if the last message appears to be waiting for input
    if (lastMessage) {
        waitingForInput = checkForInputPrompt(lastMessage);
        toggleInteractiveInput(currentProcessId, waitingForInput);
    }
    
    // If no new logs were added, don't change scroll position at all
    if (!newLogsAdded) {
        return;
    }
    
    // Only auto-scroll if enabled AND either:
    // 1. User was already at the bottom OR
    // 2. User prompt requires input
    if ((autoScrollEnabled && scrollInfo.atBottom) || waitingForInput) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
    } else if (!scrollInfo.userScrolledUp) {
        // If user hasn't explicitly scrolled up, maintain relative scroll position
        logsContainer.scrollTop = scrollInfo.initialScrollTop + 
                                 (logsContainer.scrollHeight - scrollInfo.initialScrollHeight);
    }
}

// Load active processes from the API
async function loadActiveProcesses() {
    // Skip API call if experiment runner is disabled
    if (disableExperimentRunner) {
        return;
    }
    
    try {
        const response = await fetch('/api/processes');
        
        if (response.ok) {
            const processes = await response.json();
            
            // Check if any processes changed status
            const previousProcesses = [...activeProcesses];
            activeProcesses = processes;
            
            let shouldUpdateProcessTable = false;
            let shouldUpdateHistoryTable = false;
            
            // Update history statuses if needed
            processes.forEach(process => {
                const prevProcess = previousProcesses.find(p => p.id === process.id);
                
                // Check if status changed or it's a new process
                if (!prevProcess || prevProcess.status !== process.status) {
                    shouldUpdateProcessTable = true;
                    shouldUpdateHistoryTable = true;
                    
                    // Status changed or new process
                    if (process.status === 'completed' || process.status === 'failed' || process.status === 'stopped') {
                        updateCommandHistoryStatus(process.id, process.status);
                    }
                }
                
                // Always check for log changes for the currently selected process
                if (currentProcessId === process.id) {
                    const prevLogs = prevProcess?.logs || [];
                    const currentLogs = process.logs || [];
                    
                    // Only update logs if we have more logs than before
                    // Do NOT update just because the process is running - this causes unwanted scroll resets
                    if (currentLogs.length !== prevLogs.length) {
                        updateProcessLogs(process.id);
                    }
                }
            });
            
            // Only update tables if needed to avoid excessive re-renders
            if (shouldUpdateProcessTable) {
                updateProcessesTable();
            }
            if (shouldUpdateHistoryTable) {
                updateCommandHistoryTable();
            }
        } else if (response.status === 403) {
            // 403 Forbidden response is expected when experiment runner is disabled
            // Set empty processes array and update UI
            activeProcesses = [];
            updateProcessesTable();
            
            // Don't log as error to avoid console spam
            console.log('Process management disabled on this server');
            
            // Set the flag to prevent future API calls
            disableExperimentRunner = true;
        } else {
            console.error('Failed to load processes:', response.status, response.statusText);
        }
    } catch (error) {
        console.error('Error loading processes:', error);
    }
}

// Stop a running process via API
async function stopProcess(processId) {
    try {
        const response = await fetch(`/api/process/stop/${processId}`, {
            method: 'POST'
        });
        
        if (response.ok) {
            console.log('Process stopped:', processId);
            
            // Update history status
            updateCommandHistoryStatus(processId, 'stopped');
            
            // Reload the process list
            await loadActiveProcesses();
            
            // Update the logs for the stopped process
            if (currentProcessId === processId) {
                updateProcessLogs(processId);
            }
        } else {
            console.error('Failed to stop process');
        }
    } catch (error) {
        console.error('Error stopping process:', error);
    }
}

// Update the processes table
function updateProcessesTable() {
    const tableBody = document.getElementById('processesTableBody');
    if (!tableBody) return;
    
    // Filter to only show active/running processes
    const runningProcesses = activeProcesses.filter(p => p.status === 'running' || p.status === 'pending');
    
    if (runningProcesses.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="text-center">No active processes</td>
            </tr>
        `;
        return;
    }
    
    // Sort processes by start time (newest first)
    const sortedProcesses = [...runningProcesses].sort((a, b) => {
        const timeA = a.start_time || 0;
        const timeB = b.start_time || 0;
        return timeB - timeA;
    });
    
    tableBody.innerHTML = sortedProcesses.map(process => {
        const formattedTime = formatDate(process.start_time);
        let statusClass = '';
        let statusText = process.status;
        
        if (process.status === 'running') {
            statusClass = 'status-running';
            statusText = `<i class="bi bi-play-fill"></i> Running`;
        } else if (process.status === 'pending') {
            statusClass = 'status-pending';
            statusText = `<i class="bi bi-hourglass"></i> Pending`;
        }
        
        const processId = process.id || '';
        
        return `
            <tr class="process-row ${processId === currentProcessId ? 'table-active' : ''}" data-process-id="${processId}">
                <td>${formattedTime}</td>
                <td class="command-cell" title="${process.command}"><code>${process.command}</code></td>
                <td class="${statusClass}">${statusText}</td>
                <td style="min-width: 160px;">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary process-action-btn view-logs-btn">
                            <i class="bi bi-file-text"></i>Logs
                        </button>
                        <button class="btn btn-sm btn-outline-danger process-action-btn stop-process-btn">
                            <i class="bi bi-stop-fill"></i>Stop
                        </button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
    
    // Add click event listeners to the action buttons
    document.querySelectorAll('.view-logs-btn').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const row = event.target.closest('.process-row');
            if (row) {
                const processId = row.getAttribute('data-process-id');
                selectProcess(processId);
            }
        });
    });
    
    document.querySelectorAll('.stop-process-btn').forEach((btn) => {
        btn.addEventListener('click', (event) => {
            event.stopPropagation();
            const row = event.target.closest('.process-row');
            if (row) {
                const processId = row.getAttribute('data-process-id');
                stopProcess(processId);
            }
        });
    });
    
    // Add click event to rows for selecting a process
    document.querySelectorAll('.process-row').forEach(row => {
        row.addEventListener('click', () => {
            const processId = row.getAttribute('data-process-id');
            selectProcess(processId);
        });
    });
}

// Select a process and display its logs
function selectProcess(processId) {
    // Update current process
    currentProcessId = processId;
    
    // Highlight selected row
    document.querySelectorAll('.process-row').forEach(row => {
        if (row.getAttribute('data-process-id') === processId) {
            row.classList.add('table-active');
        } else {
            row.classList.remove('table-active');
        }
    });
    
    // Update logs
    updateProcessLogs(processId);
}

// Function to update process logs display
function updateProcessLogs(processId) {
    const logsContainer = document.getElementById('processLogs');
    if (!logsContainer) return;
    
    const process = activeProcesses.find(p => p.id === processId);
    if (!process) {
        logsContainer.innerHTML = `
            <div class="text-center text-muted p-5">
                <i class="bi bi-terminal-x fs-1"></i>
                <p class="mt-3">No process selected</p>
            </div>
        `;
        return;
    }
    
    // Update the logs title with process status
    const logsTitle = document.getElementById('logsTitle');
    if (logsTitle) {
        const statusBadge = process.status ? 
            `<span class="badge ${
                process.status === 'completed' ? 'bg-success' : 
                process.status === 'failed' ? 'bg-danger' : 
                process.status === 'stopped' ? 'bg-warning' : 'bg-primary'
            }">${process.status}</span>` : '';
        
        logsTitle.innerHTML = `Process Logs: <code>${process.command}</code> ${statusBadge}`;
    }
    
    // Cache check: See if we have already rendered these exact logs
    // by comparing log count and the last log message
    const currentLogCount = process.logs?.length || 0;
    
    // Store this information as a data attribute on the container
    const previousLogCount = parseInt(logsContainer.getAttribute('data-log-count') || '0');
    const lastLogMessage = logsContainer.getAttribute('data-last-log') || '';
    const currentLastLog = currentLogCount > 0 ? 
        `${process.logs[currentLogCount-1].timestamp}_${process.logs[currentLogCount-1].message}` : '';
    
    // If log count and last message are the same, no need to re-render
    const sameLogsAsLastTime = currentLogCount === previousLogCount && 
                              lastLogMessage === currentLastLog && 
                              currentLogCount > 0;
                              
    if (sameLogsAsLastTime) {
        // No changes in logs, no need to re-render
        return;
    }
    
    // Check if we have logs
    if (!process.logs || process.logs.length === 0) {
        if (process.status === 'running') {
            // If process is running but has no logs yet, show waiting message
            logsContainer.innerHTML = `
                <div class="log-entry log-info">
                    <span class="log-timestamp">[${formatLogTime(new Date())}]</span>
                    <span class="log-message">Waiting for logs from process...</span>
                </div>
                <div class="text-center mt-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Waiting for logs...</span>
                    </div>
                </div>
            `;
        } else {
            // If process is done but has no logs, show error
            logsContainer.innerHTML = `
                <div class="text-center p-3">
                    <div class="alert alert-warning">
                        <i class="bi bi-exclamation-triangle-fill me-2"></i>
                        No logs available for this process
                    </div>
                </div>
            `;
        }
        
        // Update cache attributes
        logsContainer.setAttribute('data-log-count', '0');
        logsContainer.setAttribute('data-last-log', '');
        
        return;
    }
    
    // Clear container and show all logs
    logsContainer.innerHTML = '';
    appendLogsToDisplay(logsContainer, process.logs, 0);
    
    // Update cache attributes
    logsContainer.setAttribute('data-log-count', currentLogCount.toString());
    logsContainer.setAttribute('data-last-log', currentLastLog);
}

// Format timestamp for logs
function formatLogTime(timestamp) {
    if (!(timestamp instanceof Date)) {
        timestamp = new Date(timestamp);
    }
    
    const hours = timestamp.getHours().toString().padStart(2, '0');
    const minutes = timestamp.getMinutes().toString().padStart(2, '0');
    const seconds = timestamp.getSeconds().toString().padStart(2, '0');
    const milliseconds = timestamp.getMilliseconds().toString().padStart(3, '0');
    return `${hours}:${minutes}:${seconds}.${milliseconds}`;
}

// Clear logs for the current process
function clearLogs() {
    const logsContainer = document.getElementById('processLogs');
    if (logsContainer) {
        logsContainer.innerHTML = `
            <div class="log-entry log-info">
                <span class="log-timestamp">[${formatLogTime(new Date())}]</span>
                <span class="log-message">Logs cleared</span>
            </div>
        `;
    }
}

// Download logs for the current process
function downloadLogs() {
    if (currentProcessId) {
        const process = activeProcesses.find(p => p.id === currentProcessId);
        if (process) {
            const logText = process.logs.map(log => {
                const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
                return `[${formattedTime}] ${log.message}`;
            }).join('\n');
            
            const blob = new Blob([logText], { type: 'text/plain' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `process-${process.id}-logs.txt`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
    }
}

// Initialize charts for the selected experiment
function initializeCharts() {
    try {
        // Destroy existing charts if they exist
        if (recommendationChart) {
            recommendationChart.destroy();
            recommendationChart = null;
        }
        if (resolutionChart) {
            resolutionChart.destroy();
            resolutionChart = null;
        }
        
        // Get chart elements and check if they exist before setting properties
        const recommendationChartEl = document.getElementById('recommendationChart');
        const resolutionChartEl = document.getElementById('resolutionChart');
        
        // Only proceed if the chart elements exist
        if (!recommendationChartEl || !resolutionChartEl) {
            console.warn('Chart elements not found in the DOM, skipping chart initialization');
            return;
        }
        
        // Set fixed height to prevent excessive resizing
        recommendationChartEl.height = 200;
        resolutionChartEl.height = 200;
        
        // Initialize recommendation chart
        const recommendationChartCtx = recommendationChartEl.getContext('2d');
        recommendationChart = new Chart(recommendationChartCtx, {
            type: 'pie',
            data: {
                labels: ['P1', 'P2', 'P3', 'P4'],
                datasets: [{
                    data: [0, 0, 0, 0],
                    backgroundColor: [
                        '#28a745', // p1 - green
                        '#17a2b8', // p2 - teal
                        '#ffc107', // p3 - yellow
                        '#dc3545'  // p4 - red
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
        
        // Initialize resolution chart
        const resolutionChartCtx = resolutionChartEl.getContext('2d');
        resolutionChart = new Chart(resolutionChartCtx, {
            type: 'pie',
            data: {
                labels: ['1', '0', 'Other'],
                datasets: [{
                    data: [0, 0, 0],
                    backgroundColor: [
                        '#28a745', // 1 - green
                        '#dc3545', // 0 - red
                        '#6c757d'  // other - gray
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            boxWidth: 12,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.dataset.data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

// Calculate analytics for the displayed data
function calculateAnalytics(dataArray) {
    let correctCount = 0;
    let incorrectCount = 0;
    let p1Count = 0;
    let p2Count = 0;
    let p3Count = 0;
    let p4Count = 0;
    let resolution1Count = 0;
    let resolution0Count = 0;
    let resolutionOtherCount = 0;
    let p12Total = 0;
    let p12Correct = 0;
    
    // Tag statistics
    const tagStats = {};
    
    // Filter out entries with undefined or null resolved_price_outcome
    const resolvedEntries = dataArray.filter(entry => 
        entry && entry.resolved_price_outcome !== undefined && 
        entry.resolved_price_outcome !== null
    );
    
    // Calculate counts for each entry
    resolvedEntries.forEach(entry => {
        // Standardize recommendation value based on format_version
        let rec = '';
        if (entry.format_version === 2 && entry.result && entry.result.recommendation) {
            // For format_version 2, get recommendation from result section
            rec = entry.result.recommendation.toLowerCase();
        } else {
            // For format_version 1 or undefined format, use legacy fields
            rec = (entry.recommendation || entry.proposed_price_outcome || '').toLowerCase();
        }
        
        // Count recommendations
        if (rec === 'p1') p1Count++;
        else if (rec === 'p2') p2Count++;
        else if (rec === 'p3') p3Count++;
        else if (rec === 'p4') p4Count++;
        
        // Count resolutions - using only resolved_price_outcome
        // Ensure we have a string for comparison
        const resolution = (entry.resolved_price_outcome !== null && 
                           entry.resolved_price_outcome !== undefined) ? 
                           entry.resolved_price_outcome.toString().toLowerCase() : '';
                           
        if (resolution === '1' || resolution === 'p1') resolution1Count++;
        else if (resolution === '0' || resolution === 'p2') resolution0Count++;
        else resolutionOtherCount++;
        
        // Calculate correctness
        const isCorrect = isRecommendationCorrect(entry);
        // Only include in counts if we can determine correctness (not null)
        if (isCorrect === true) {
            correctCount++;
        } else if (isCorrect === false) {
            incorrectCount++;
        }
        
        // Calculate specialized metrics
        if (rec === 'p1' || rec === 'p2') {
            p12Total++;
            if (isCorrect === true) p12Correct++;
        }
        
        // Calculate tag statistics - Check multiple possible tag locations
        let tags = [];
        if (entry.tags && Array.isArray(entry.tags)) {
            tags = entry.tags;
        } else if (entry.proposal_metadata && entry.proposal_metadata.tags && Array.isArray(entry.proposal_metadata.tags)) {
            tags = entry.proposal_metadata.tags;
        } else if (entry.market_data && entry.market_data.tags && Array.isArray(entry.market_data.tags)) {
            tags = entry.market_data.tags;
        }
        
        if (tags.length > 0) {
            tags.forEach(tag => {
                // Initialize tag stats if not already done
                if (!tagStats[tag]) {
                    tagStats[tag] = {
                        total: 0,
                        correct: 0,
                        incorrect: 0,
                        disputed: 0,
                        totalIgnoringP4: 0,
                        correctIgnoringP4: 0,
                        incorrectIgnoringP4: 0
                    };
                }
                
                // Update counts only if correctness can be determined
                tagStats[tag].total++;
                
                if (isCorrect === true) {
                    tagStats[tag].correct++;
                } else if (isCorrect === false) {
                    tagStats[tag].incorrect++;
                }
                
                // Calculate P4-ignoring stats
                // Only count if either recommendation or resolution is not P4
                const isP4Recommendation = rec === 'p4';
                const isP4Resolution = (entry.resolved_price_outcome !== null && 
                                       entry.resolved_price_outcome !== undefined) ?
                                       entry.resolved_price_outcome.toString().toLowerCase() === 'p4' : false;
                                       
                if (!isP4Recommendation && !isP4Resolution) {
                    tagStats[tag].totalIgnoringP4++;
                    if (isCorrect === true) {
                        tagStats[tag].correctIgnoringP4++;
                    } else if (isCorrect === false) {
                        tagStats[tag].incorrectIgnoringP4++;
                    }
                }
                
                if (entry.disputed === true || (entry.market_data && entry.market_data.disputed === true)) {
                    tagStats[tag].disputed++;
                }
            });
        }
    });
    
    // Calculate percentages
    const totalCount = correctCount + incorrectCount;
    const accuracyPercent = totalCount > 0 ? (correctCount / totalCount) * 100 : 0;
    const p12Accuracy = p12Total > 0 ? (p12Correct / p12Total) * 100 : 0;
    
    // Calculate accuracy percentage for each tag
    Object.keys(tagStats).forEach(tag => {
        const stats = tagStats[tag];
        stats.accuracyPercent = stats.total > 0 ? (stats.correct / stats.total) * 100 : 0;
        stats.accuracyPercentIgnoringP4 = stats.totalIgnoringP4 > 0 ? (stats.correctIgnoringP4 / stats.totalIgnoringP4) * 100 : 0;
    });
    
    return {
        correctCount,
        incorrectCount,
        totalCount,
        accuracyPercent,
        p12Accuracy,
        noDataCount: p4Count,
        recommendationCounts: [p1Count, p2Count, p3Count, p4Count],
        resolutionCounts: [resolution1Count, resolution0Count, resolutionOtherCount],
        tagStats: tagStats
    };
}

// Helper function to check if a recommendation is correct
function isRecommendationCorrect(entry) {
    // Only compare if resolved_price_outcome is available and not null
    if (entry.resolved_price_outcome !== undefined && entry.resolved_price_outcome !== null) {
        // Get recommendation based on format_version
        let rec = '';
        if (entry.format_version === 2 && entry.result && entry.result.recommendation) {
            // For format_version 2, get recommendation from result section
            rec = entry.result.recommendation.toLowerCase();
        } else {
            // For format_version 1 or undefined format, use legacy fields or proposed_price_outcome at root
            rec = (entry.recommendation || entry.proposed_price_outcome || '').toLowerCase();
        }
        
        const resolved = entry.resolved_price_outcome.toString().toLowerCase();
        
        // Handle empty or missing recommendation
        if (!rec) return null;
        
        // Direct match (p1 = p1, p2 = p2, etc)
        if (rec === resolved) return true;
        
        // Numeric match (p1 = 1, p2 = 0, etc)
        if (rec === 'p1' && (resolved === '1' || resolved === 'p1')) return true;
        if (rec === 'p2' && (resolved === '0' || resolved === 'p2')) return true;
        if ((rec === 'p3' || rec === 'p4') && (resolved !== '0' && resolved !== '1' && 
                                               resolved !== 'p1' && resolved !== 'p2')) return true;
        
        return false;
    }
    
    // If no resolution is available (unresolved status), don't count it as incorrect
    return null;
}

// Update analytics display including tag accuracy
function updateAnalyticsDisplay(analytics) {
    // If analytics is null or undefined, set default values
    if (!analytics) {
        analytics = {
            correctCount: 0,
            incorrectCount: 0,
            totalCount: 0,
            accuracyPercent: 0,
            p12Accuracy: 0,
            noDataCount: 0,
            recommendationCounts: [0, 0, 0, 0],
            resolutionCounts: [0, 0, 0],
            tagStats: {}
        };
    }
    
    // Update accuracy circle
    const accuracyCircle = document.getElementById('accuracyCircle');
    if (accuracyCircle) {
        // Clear existing content
        accuracyCircle.innerHTML = '';
        
        // Create SVG
        const size = 150;
        const radius = 60;
        const strokeWidth = 12;
        const center = size / 2;
        const circumference = 2 * Math.PI * radius;
        const offset = circumference - (analytics.accuracyPercent / 100) * circumference;
        
        // Create SVG element
        const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('width', size);
        svg.setAttribute('height', size);
        svg.setAttribute('viewBox', `0 0 ${size} ${size}`);
        
        // Create background circle
        const bgCircle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        bgCircle.setAttribute('cx', center);
        bgCircle.setAttribute('cy', center);
        bgCircle.setAttribute('r', radius);
        bgCircle.setAttribute('fill', 'none');
        bgCircle.setAttribute('stroke', '#e9ecef');
        bgCircle.setAttribute('stroke-width', strokeWidth);
        
        // Create progress circle
        const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
        circle.setAttribute('cx', center);
        circle.setAttribute('cy', center);
        circle.setAttribute('r', radius);
        circle.setAttribute('fill', 'none');
        circle.setAttribute('stroke', '#28a745');
        circle.setAttribute('stroke-width', strokeWidth);
        circle.setAttribute('stroke-dasharray', circumference);
        circle.setAttribute('stroke-dashoffset', offset);
        circle.setAttribute('transform', `rotate(-90 ${center} ${center})`);
        
        // Add circles to SVG
        svg.appendChild(bgCircle);
        svg.appendChild(circle);
        
        // Add SVG to container
        accuracyCircle.appendChild(svg);
        
        // Add accuracy text
        const accuracyText = document.createElement('span');
        accuracyText.className = 'accuracy-value';
        accuracyText.textContent = `${Math.round(analytics.accuracyPercent)}%`;
        accuracyCircle.appendChild(accuracyText);
    }
    
    // Update accuracy percentage
    const accuracyPercent = document.getElementById('accuracyPercent');
    if (accuracyPercent) {
        accuracyPercent.textContent = `${Math.round(analytics.accuracyPercent)}%`;
    }
    
    // Update counts - add null checks for each element
    const correctCount = document.getElementById('correctCount');
    if (correctCount) {
        correctCount.textContent = analytics.correctCount;
    }
    
    const incorrectCount = document.getElementById('incorrectCount');
    if (incorrectCount) {
        incorrectCount.textContent = analytics.incorrectCount;
    }
    
    const totalCount = document.getElementById('totalCount');
    if (totalCount) {
        totalCount.textContent = analytics.totalCount;
    }
    
    const noDataCount = document.getElementById('noDataCount');
    if (noDataCount) {
        noDataCount.textContent = analytics.noDataCount;
    }
    
    // Update P1-P2 Accuracy progress bar
    const p12AccuracyBar = document.getElementById('p12Accuracy');
    if (p12AccuracyBar) {
        const p12Value = Math.round(analytics.p12Accuracy);
        p12AccuracyBar.style.width = `${p12Value}%`;
        p12AccuracyBar.setAttribute('aria-valuenow', p12Value);
        p12AccuracyBar.textContent = `${p12Value}%`;
    }
    
    // Update charts
    if (recommendationChart) {
        recommendationChart.data.datasets[0].data = analytics.recommendationCounts;
        recommendationChart.update();
    }
    
    if (resolutionChart) {
        resolutionChart.data.datasets[0].data = analytics.resolutionCounts;
        resolutionChart.update();
    }
    
    // Update tag accuracy section
    updateTagAccuracyDisplay(analytics.tagStats);
}

// Helper function to format date in 24-hour format with seconds
function formatDate(timestamp) {
    // Only return N/A if timestamp is null or undefined, not if it's 0
    if (timestamp === null || timestamp === undefined) return 'N/A';
    
    try {
        // Handle string timestamps that are in ISO format
        if (typeof timestamp === 'string') {
            // Check for DD-MM-YYYY HH:MM format (e.g., "01-04-2025 21:15")
            if (timestamp.match(/^\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}$/)) {
                const [datePart, timePart] = timestamp.split(' ');
                const [day, month, year] = datePart.split('-');
                const [hours, minutes] = timePart.split(':');
                const date = new Date(year, month - 1, day, hours, minutes);
                if (!isNaN(date.getTime())) {
                    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
                }
            }
            
            // Try parsing as ISO format
            if (timestamp.includes('T') || timestamp.includes('-')) {
                const date = new Date(timestamp);
                if (!isNaN(date.getTime())) {
                    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
                }
            }
            
            // Try parsing as numeric string
            if (!isNaN(parseInt(timestamp, 10))) {
                timestamp = parseInt(timestamp, 10);
            } else {
                return timestamp; // Return the string as-is if we can't parse it
            }
        }
        
        // For numeric timestamps, assume Unix timestamp (seconds since epoch)
        if (typeof timestamp === 'number') {
            // If timestamp is in milliseconds (> year 2001), convert to seconds
            if (timestamp > 1000000000000) {
                timestamp = Math.floor(timestamp / 1000);
            }
            
            const date = new Date(timestamp * 1000);
            return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 8);
        }
        
        // Fallback for unknown formats
        return String(timestamp);
    } catch (error) {
        console.warn('Error formatting date:', error, timestamp);
        return String(timestamp);
    }
}

// Format date for display in the experiment table
function formatDisplayDate(dateStr) {
    if (!dateStr) return 'N/A';
    
    // Try to parse the date string
    try {
        // Handle formats like "DD-MM-YYYY HH:MM" (e.g., "01-04-2025 21:15")
        if (dateStr.match(/^\d{2}-\d{2}-\d{4}\s\d{2}:\d{2}$/)) {
            const [datePart, timePart] = dateStr.split(' ');
            return `${datePart} ${timePart}`;
        }
        
        // Handle formats like "DD-MM-YYYY"
        if (dateStr.match(/^\d{2}-\d{2}-\d{4}$/)) {
            return dateStr;
        }
        
        // Handle other date formats - convert to dd-mm-yy
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
            return `${date.getDate().toString().padStart(2, '0')}-${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getFullYear()}`;
        }
        
        return dateStr;
    } catch (e) {
        return dateStr;
    }
}

// Create a transaction link from a hash
function createTxLink(hash) {
    if (!hash || hash === '') return 'N/A';
    
    // Base URL for polygon explorer + specific transaction
    const baseUrl = 'https://polygonscan.com/tx/';
    
    // Format hash for display (first 8 characters + ... + last 6 characters)
    const displayHash = `${hash.substring(0, 8)}...${hash.substring(hash.length - 6)}`;
    
    return `<a href="${baseUrl}${hash}" target="_blank" class="tx-link code-font">${displayHash}</a>`;
}

// Apply a filter to the table
function applyFilter(filter) {
    // Reset active class on filter buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Set active class on the clicked button
    document.getElementById('filter' + filter.charAt(0).toUpperCase() + filter.slice(1))?.classList.add('active');
    
    // Get current tag selections
    const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
    const selectedTags = Array.from(checkboxes).map(cb => cb.value);
    
    // Apply all filters
    applyAllFilters(filter, selectedTags);
}

// Load column preferences from localStorage
function loadColumnPreferences() {
    try {
        const savedPreferences = localStorage.getItem('columnPreferences');
        if (savedPreferences) {
            const parsed = JSON.parse(savedPreferences);
            // Merge with defaults to ensure we have all properties
            columnPreferences = { ...columnPreferences, ...parsed };
        }
        
        // Add any new columns that may not be in saved preferences
        if (columnPreferences.router_decision === undefined) {
            columnPreferences.router_decision = false;
        }
    } catch (error) {
        console.error('Error loading column preferences:', error);
    }
}

// Save column preferences to localStorage
function saveColumnPreferences() {
    try {
        localStorage.setItem('columnPreferences', JSON.stringify(columnPreferences));
    } catch (error) {
        console.error('Error saving column preferences:', error);
    }
}

// Initialize column selector UI for columns and preference management
function initializeColumnSelector() {
    // Build the column selector dropdown content
    const columnSelectorMenu = document.getElementById('columnSelectorMenu');
    if (!columnSelectorMenu) return;
    
    // Create a form for column selections
    columnSelectorMenu.innerHTML = `
        <div class="px-3 py-2">
            <h6 class="dropdown-header">Choose Columns to Display</h6>
            <div class="column-checkbox-container">
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-timestamp" 
                    ${columnPreferences.timestamp ? 'checked' : ''} data-column="timestamp">
                    <label class="form-check-label" for="col-timestamp">Process Date</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-proposal_timestamp"
                    ${columnPreferences.proposal_timestamp ? 'checked' : ''} data-column="proposal_timestamp">
                    <label class="form-check-label" for="col-proposal_timestamp">Proposal Date</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-expiration_timestamp"
                    ${columnPreferences.expiration_timestamp ? 'checked' : ''} data-column="expiration_timestamp">
                    <label class="form-check-label" for="col-expiration_timestamp">Expiration Date</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-request_transaction_block_time"
                    ${columnPreferences.request_transaction_block_time ? 'checked' : ''} data-column="request_transaction_block_time">
                    <label class="form-check-label" for="col-request_transaction_block_time">Proposal Time</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-id"
                    ${columnPreferences.id ? 'checked' : ''} data-column="id">
                    <label class="form-check-label" for="col-id">Query ID</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-title"
                    ${columnPreferences.title ? 'checked' : ''} data-column="title">
                    <label class="form-check-label" for="col-title">Title</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-recommendation"
                    ${columnPreferences.recommendation ? 'checked' : ''} data-column="recommendation">
                    <label class="form-check-label" for="col-recommendation">Recommendation</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-router_decision"
                    ${columnPreferences.router_decision ? 'checked' : ''} data-column="router_decision">
                    <label class="form-check-label" for="col-router_decision">Router Decision</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-resolution"
                    ${columnPreferences.resolution ? 'checked' : ''} data-column="resolution">
                    <label class="form-check-label" for="col-resolution">Resolution</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-disputed"
                    ${columnPreferences.disputed ? 'checked' : ''} data-column="disputed">
                    <label class="form-check-label" for="col-disputed">Disputed</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-correct"
                    ${columnPreferences.correct ? 'checked' : ''} data-column="correct">
                    <label class="form-check-label" for="col-correct">Correct</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-block_number"
                    ${columnPreferences.block_number ? 'checked' : ''} data-column="block_number">
                    <label class="form-check-label" for="col-block_number">Block #</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-proposal_bond"
                    ${columnPreferences.proposal_bond ? 'checked' : ''} data-column="proposal_bond">
                    <label class="form-check-label" for="col-proposal_bond">Proposal Bond</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-tags"
                    ${columnPreferences.tags ? 'checked' : ''} data-column="tags">
                    <label class="form-check-label" for="col-tags">Tags</label>
                </div>
            </div>
            <div class="d-flex justify-content-between mt-3">
                <button class="btn btn-sm btn-outline-secondary" id="resetColumnDefaults">Reset to Defaults</button>
                <button class="btn btn-sm btn-outline-primary" id="applyColumnChanges">Apply</button>
            </div>
        </div>
    `;
    
    // Add event listeners for column selection
    document.querySelectorAll('.column-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const column = this.getAttribute('data-column');
            columnPreferences[column] = this.checked;
        });
    });
    
    // Add event listener for apply button
    document.getElementById('applyColumnChanges')?.addEventListener('click', function() {
        saveColumnPreferences();
        updateTableWithData(currentData);
        
        // Hide the dropdown
        const dropdownEl = document.getElementById('columnSelectorMenu');
        if (dropdownEl) {
            const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('columnSelectorBtn'));
            if (dropdown) dropdown.hide();
        }
    });
    
    // Add event listener for reset defaults button
    document.getElementById('resetColumnDefaults')?.addEventListener('click', function() {
        // Reset to defaults
        columnPreferences = {
            timestamp: true,
            proposal_timestamp: true,
            id: true,
            title: true,
            recommendation: true,
            router_decision: false,
            resolution: true,
            disputed: true,
            correct: true,
            block_number: false,
            proposal_bond: false,
            tags: false,
            expiration_timestamp: false,
            request_timestamp: false,
            request_transaction_block_time: true
        };
        
        // Update checkboxes
        document.querySelectorAll('.column-checkbox').forEach(checkbox => {
            const column = checkbox.getAttribute('data-column');
            checkbox.checked = columnPreferences[column];
        });
        
        // Save preferences and update the table automatically
        saveColumnPreferences();
        updateTableWithData(currentData);
        
        // Hide the dropdown
        const dropdownEl = document.getElementById('columnSelectorMenu');
        if (dropdownEl) {
            const dropdown = bootstrap.Dropdown.getInstance(document.getElementById('columnSelectorBtn'));
            if (dropdown) dropdown.hide();
        }
    });
    
    // Add styles for column selector
    const styleElement = document.createElement('style');
    styleElement.textContent = `
        .column-checkbox-container {
            max-height: 300px;
            overflow-y: auto;
            padding: 0 10px;
            margin-bottom: 10px;
        }
        
        .column-checkbox-container .form-check {
            margin-bottom: 6px;
        }
        
        .tag-badge.small {
            font-size: 0.75rem;
            padding: 0.25em 0.6em;
            margin-right: 2px;
            white-space: nowrap;
        }
    `;
    document.head.appendChild(styleElement);
}

// Load data about available experiment directories
async function loadExperimentsData() {
    try {
        // First clear existing data
        experimentsData = [];
        currentData = [];
        
        // Different endpoint URLs for different data sources
        const sourceUrls = {
            filesystem: '/api/results-directories',
            mongodb: '/api/mongodb/analytics'
        };
        
        // If we're in single experiment mode, we will load just that experiment
        if (singleExperiment) {
            console.log('Running in SINGLE_EXPERIMENT mode for:', singleExperiment);
            
            // Make results section visible and add a loading indicator
            const resultsSection = document.querySelector('.results-section');
            if (resultsSection) {
                // Show the results section
                resultsSection.style.display = 'block';
                
                // Also show the results table card
                const resultsTableCard = document.getElementById('resultsTableCard');
                if (resultsTableCard) {
                    resultsTableCard.style.display = 'block';
                }
                
                // Create loading indicator in the results table body
                const resultsTableBody = document.getElementById('resultsTableBody');
                if (resultsTableBody) {
                    resultsTableBody.innerHTML = `
                        <tr>
                            <td colspan="8" class="text-center p-5">
                                <div id="singleExperimentLoader">
                                    <div class="spinner-border text-primary mb-3" style="width: 3rem; height: 3rem;" role="status">
                                        <span class="visually-hidden">Loading...</span>
                                    </div>
                                    <h4 class="mt-3">Loading Experiment Data</h4>
                                    <p class="text-muted">${singleExperiment}</p>
                                </div>
                            </td>
                        </tr>
                    `;
                }
            }
            
            // Always force MongoDB source when in SINGLE_EXPERIMENT mode
            const source = 'mongodb';
            const directory = singleExperiment;
            
            // Create a mock experiment entry for the single experiment
            experimentsData = [{
                directory: directory,
                path: `mongodb/${directory}`,
                title: directory,
                source: source
            }];
            
            // Fetch experiment metadata from MongoDB first to get proper title and details
            try {
                console.log('Fetching MongoDB metadata for single experiment');
                const metadataResponse = await fetch(`/api/mongodb/experiment/${directory}`);
                if (metadataResponse.ok) {
                    const metadataData = await metadataResponse.json();
                    
                    // Use the first item to get experiment metadata if it's an array
                    const metadataItem = Array.isArray(metadataData) && metadataData.length > 0 
                        ? metadataData[0] : metadataData;
                    
                    // Extract title and other metadata
                    if (metadataItem && metadataItem.metadata && metadataItem.metadata.experiment) {
                        const experimentMetadata = metadataItem.metadata.experiment;
                        
                        // Update the experiment entry with MongoDB data
                        experimentsData[0].title = experimentMetadata.title || directory;
                        experimentsData[0].goal = experimentMetadata.goal || '';
                        experimentsData[0].timestamp = experimentMetadata.timestamp || '';
                        experimentsData[0].metadata = metadataItem.metadata;
                    }
                    
                    console.log('Updated single experiment with MongoDB metadata:', experimentsData[0]);
                }
            } catch(metadataError) {
                console.warn('Error loading MongoDB metadata for single experiment:', metadataError);
                // Continue with basic experiment data if metadata fetch fails
            }
            
            // Directly load the experiment data from MongoDB
            loadExperimentData(directory, source);
            return;
        }
        
        // Continue with normal loading for multiple experiments
        const url = sourceUrls[currentSourceFilter] || sourceUrls.filesystem;
        
        // Try to fetch from the API endpoint
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const responseData = await response.json();
        
        // Check if we have a mongo_only_results flag in the response
        mongoOnlyResults = responseData.mongo_only_results === true;
        
        // Update source filter visibility based on MONGO_ONLY_RESULTS setting
        const sourceFilterGroup = document.querySelector('.source-filter-group');
        if (sourceFilterGroup) {
            sourceFilterGroup.style.display = mongoOnlyResults ? 'none' : 'block';
        }
        
        // If mongo_only_results is true, force MongoDB source filter
        if (mongoOnlyResults) {
            currentSourceFilter = 'mongodb';
        }
        
        // Check if we have a response with mongo_status (format when MongoDB is down)
        if (responseData.mongo_status === 'error') {
            // Use the filesystem results
            experimentsData = responseData.results;
            
            // Show warning about MongoDB being down
            console.warn('MongoDB connection error:', responseData.mongo_error);
            
            // Display warning banner at the top of the page
            const warningBanner = document.createElement('div');
            warningBanner.className = 'alert alert-warning alert-dismissible fade show';
            warningBanner.setAttribute('role', 'alert');
            warningBanner.innerHTML = `
                <strong>Warning:</strong> MongoDB connection failed (${responseData.mongo_error}). 
                Only filesystem data is available.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            // Insert at the top of the main content area
            const mainContent = document.querySelector('.main-content');
            if (mainContent && mainContent.firstChild) {
                mainContent.insertBefore(warningBanner, mainContent.firstChild);
            } else {
                document.body.insertBefore(warningBanner, document.body.firstChild);
            }
            
            // Disable MongoDB filter option
            const mongodbFilterBtn = document.getElementById('filterSourceMongoDB');
            if (mongodbFilterBtn) {
                mongodbFilterBtn.classList.add('disabled');
                mongodbFilterBtn.title = 'MongoDB is currently unavailable';
            }
        } else {
            // Normal case - MongoDB is working
            // Check if we have a results field (new format with MONGO_ONLY_RESULTS)
            if (responseData.results) {
                experimentsData = responseData.results;
                console.log('Using results field from response in loadExperimentsData');
            } else {
                // Legacy format where the response is directly the array
                experimentsData = responseData;
            }
        }
        
        console.log('Loaded experiments data:', experimentsData);
        
        displayExperimentsTable();
    } catch (error) {
        console.error('Error loading experiments data:', error);
        
        // Show error in the table
        const tableBody = document.getElementById('resultsDirectoryTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="3" class="text-center text-danger">
                        Error loading experiments data: ${error.message}
                    </td>
                </tr>
            `;
        }
    }
}

// Display the experiments directory table
function displayExperimentsTable() {
    const tableBody = document.getElementById('resultsDirectoryTableBody');
    if (!tableBody) return;
    
    // If in single experiment mode, don't display the table
    if (singleExperiment) {
        return;
    }
    
    if (experimentsData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td class="text-center">No experiment directories found.</td>
            </tr>
        `;
        return;
    }
    
    // Filter experiments based on source
    let filteredExperiments = [...experimentsData];
    
    // Default to appropriate source filter based on settings
    if (!currentSourceFilter) {
        currentSourceFilter = mongoOnlyResults ? 'mongodb' : 'filesystem';
        
        // Update UI to reflect the chosen filter
        if (mongoOnlyResults) {
            document.getElementById('filterSourceMongoDB')?.classList.add('active');
        } else {
            document.getElementById('filterSourceFilesystem')?.classList.add('active');
        }
    }
    
    // Filter by selected source (but only if mongo_only_results is false)
    if (!mongoOnlyResults) {
        filteredExperiments = filteredExperiments.filter(exp => {
            const isMongoDBSource = exp.source === 'mongodb' || exp.path?.startsWith('mongodb/');
            return (currentSourceFilter === 'mongodb' && isMongoDBSource) || 
                   (currentSourceFilter === 'filesystem' && !isMongoDBSource);
        });
    } else {
        // If mongo_only_results is true, only show MongoDB sources
        filteredExperiments = filteredExperiments.filter(exp => {
            const isMongoDBSource = exp.source === 'mongodb' || exp.path?.startsWith('mongodb/');
            return isMongoDBSource;
        });
    }
    
    // Sort experiments by timestamp (newest first - descending order)
    const sortedExperiments = filteredExperiments.sort((a, b) => {
        // Try to compare timestamps
        const dateA = a.timestamp ? new Date(a.timestamp.replace(/(\d+)[\/\-](\d+)[\/\-](\d+)/, '$3-$2-$1')) : new Date(0);
        const dateB = b.timestamp ? new Date(b.timestamp.replace(/(\d+)[\/\-](\d+)[\/\-](\d+)/, '$3-$2-$1')) : new Date(0);
        return dateB - dateA; // Changed to sort in descending order (newest first)
    });
    
    if (sortedExperiments.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td class="text-center">No experiments found for the selected filter.</td>
            </tr>
        `;
        return;
    }
    
    // Generate table rows with full-width format
    tableBody.innerHTML = sortedExperiments.map(experiment => {
        const isMongoDBSource = experiment.source === 'mongodb' || experiment.path?.startsWith('mongodb/');
        const sourceIcon = isMongoDBSource ? 
            '<i class="bi bi-database-fill me-1" title="MongoDB Data Source"></i>' : 
            '<i class="bi bi-folder-fill me-1" title="Filesystem Data Source"></i>';
        
        // Get proper formatted date using the timestamp
        let formattedDate = 'N/A';
        // First check if there's a timestamp in experiment itself
        if (experiment.timestamp) {
            formattedDate = formatDisplayDate(experiment.timestamp);
        }
        // Then check if it's in the metadata.experiment.timestamp
        else if (experiment.metadata && experiment.metadata.experiment && experiment.metadata.experiment.timestamp) {
            formattedDate = formatDisplayDate(experiment.metadata.experiment.timestamp);
        }
        
        // For MongoDB sources, make sure we're using the experiment metadata
        const experimentGoal = experiment.goal || (experiment.metadata && experiment.metadata.experiment?.goal) || '';
        
        // Only add the toggle button if there's a goal to show
        const toggleButton = experimentGoal ? 
            `<i class="bi bi-chevron-down experiment-toggle" title="Show/hide goal"></i>` : '';
        
        return `
        <tr class="experiment-row" data-directory="${experiment.directory}" data-source="${isMongoDBSource ? 'mongodb' : 'filesystem'}">
            <td>
                <div>
                    <span class="experiment-date">${sourceIcon}${formattedDate}</span>
                    ${experiment.count ? `<span class="badge bg-primary ms-1" style="font-size: 0.75rem;">${experiment.count} items</span>` : ''}
                    ${toggleButton}
                </div>
                <span class="experiment-title">${experiment.title || experiment.directory}</span>
                ${experimentGoal ? `<div class="experiment-description">${experimentGoal}</div>` : ''}
            </td>
        </tr>
    `}).join('');
    
    // Add click event to rows
    document.querySelectorAll('.experiment-row').forEach(row => {
        row.addEventListener('click', (event) => {
            const directory = row.getAttribute('data-directory');
            const source = row.getAttribute('data-source');
            
            // Check if the click was on the toggle button
            if (event.target.classList.contains('experiment-toggle')) {
                event.stopPropagation(); // Prevent row selection
                
                // Toggle description visibility
                const descriptionEl = row.querySelector('.experiment-description');
                const toggleEl = row.querySelector('.experiment-toggle');
                
                if (descriptionEl) {
                    descriptionEl.classList.toggle('expanded');
                    toggleEl.classList.toggle('expanded');
                }
                return;
            }
            
            // Otherwise, handle the normal row click (load experiment)
            loadExperimentData(directory, source);
            
            // Highlight the selected row
            document.querySelectorAll('.experiment-row').forEach(r => {
                r.classList.remove('table-active');
                
                // Collapse descriptions when deselecting rows
                const descEl = r.querySelector('.experiment-description');
                const togEl = r.querySelector('.experiment-toggle');
                if (descEl && descEl.classList.contains('expanded')) {
                    descEl.classList.remove('expanded');
                    if (togEl) togEl.classList.remove('expanded');
                }
            });
            
            row.classList.add('table-active');
            
            // Auto-expand the description of the selected row
            const descriptionEl = row.querySelector('.experiment-description');
            const toggleEl = row.querySelector('.experiment-toggle');
            if (descriptionEl) {
                descriptionEl.classList.add('expanded');
                if (toggleEl) toggleEl.classList.add('expanded');
            }
        });
    });
    
    // Load the first experiment by default if none is selected yet
    if (sortedExperiments.length > 0 && !document.querySelector('.experiment-row.table-active')) {
        const firstRow = document.querySelector('.experiment-row');
        if (firstRow) {
            firstRow.classList.add('table-active');
            const directory = firstRow.getAttribute('data-directory');
            const source = firstRow.getAttribute('data-source');
            loadExperimentData(directory, source);
        }
    }
}

// Load data for a specific experiment
async function loadExperimentData(directory, source) {
    try {
        // Reset current data to prevent showing old data
        currentData = [];
        
        // Find the experiment in our data
        currentExperiment = experimentsData.find(exp => exp.directory === directory);
        if (!currentExperiment) {
            throw new Error(`Experiment directory ${directory} not found`);
        }
        
        // Save the explicit source as part of the experiment data for precise tracking
        if (source) {
            currentExperiment.explicitSource = source;
        }
        
        // Show loading spinner in experiment metadata card instead of content, but only if not in SINGLE_EXPERIMENT mode
        const metadataContainer = document.getElementById('experimentMetadataCard');
        const metadataContent = document.getElementById('experimentMetadataContent');
        if (metadataContainer && metadataContent) {
            if (!singleExperiment) {
                metadataContainer.style.display = 'block';
                metadataContent.innerHTML = `
                    <div class="text-center py-4">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading metadata...</span>
                        </div>
                        <p class="mt-2">Loading experiment metadata...</p>
                    </div>
                `;
            } else {
                // Hide metadata in SINGLE_EXPERIMENT mode
                metadataContainer.style.display = 'none';
            }
        }
        
        // Show loading spinner in analytics dashboard instead of hiding it
        const analyticsDashboard = document.getElementById('analyticsDashboard');
        if (analyticsDashboard) {
            analyticsDashboard.style.display = 'block';
            const analyticsTabs = document.getElementById('analyticsTabs');
            const analyticsTabContent = document.getElementById('analyticsTabContent');
            
            if (analyticsTabs) {
                analyticsTabs.style.display = 'none';
            }
            
            // Store the original content for later restoration
            if (analyticsTabContent) {
                // Save the original content if not already saved
                if (!analyticsTabContent.hasAttribute('data-original-content')) {
                    analyticsTabContent.setAttribute('data-original-content', analyticsTabContent.innerHTML);
                }
                
                // Show loading indicator
                analyticsTabContent.innerHTML = `
                    <div class="text-center py-5">
                        <div class="spinner-border text-primary mb-3" role="status">
                            <span class="visually-hidden">Loading analytics...</span>
                        </div>
                        <p class="mt-2">Loading analytics data...</p>
                    </div>
                `;
            }
        }
        
        document.getElementById('filterControls').style.display = 'none';
        document.getElementById('resultsTableCard').style.display = 'block'; // Keep visible for loading indicator
        document.querySelector('.results-section').style.display = 'block';
        
        // Hide tag filter until we know if we have tags
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = 'none';
        }
        
        // Set the results table title
        const resultsTableTitle = document.getElementById('resultsTableTitle');
        if (resultsTableTitle) {
            resultsTableTitle.textContent = `${currentExperiment.title || directory} Results`;
        }
        
        // REMOVED: Initialize charts for this experiment BEFORE data loading
        // initializeCharts();
        
        // Check the source of the experiment data
        const isMongoDBSource = source === 'mongodb' || 
                               currentExperiment.source === 'mongodb' || 
                               currentExperiment.path?.startsWith('mongodb/');
        
        // Show loading indicator in results table
        document.getElementById('resultsTableBody').innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2 fw-bold">Loading results from ${isMongoDBSource ? 'MongoDB' : currentExperiment.path}...</p>
                    <p>Analytics and data table will appear once loading is complete</p>
                </td>
            </tr>
        `;
        
        // Different data loading based on source
        if (isMongoDBSource) {
            try {
                // Extract experiment ID from the path
                const experimentId = directory;
                
                // Fetch data from MongoDB API
                const response = await fetch(`/api/mongodb/experiment/${experimentId}`);
                
                if (!response.ok) {
                    throw new Error(`Failed to fetch MongoDB data: ${response.status}`);
                }
                
                const jsonData = await response.json();
                
                if (Array.isArray(jsonData)) {
                    currentData = jsonData;
                    console.log(`Successfully loaded ${currentData.length} result items from MongoDB`);
                } else {
                    // Convert single object to array if necessary
                    currentData = [jsonData];
                    console.log(`Loaded single result from MongoDB`);
                }
                
                if (currentData.length === 0) {
                    throw new Error(`No data found for experiment ${experimentId} in MongoDB`);
                }
            } catch (error) {
                console.error('Error loading MongoDB data:', error);
                // Handle display of error below
                throw error;
            }
        } else {
            // Original filesystem loading logic
            try {
                // Track loaded data to prevent duplicates
                const loadedDataIds = new Set();
                
                // Load specific files from the outputs directory since directory browsing might not work
                const response = await fetch(`/api/results-directories`);
                if (response.ok) {
                    // Get the list of files to load for this directory
                    const responseData = await response.json();
                    
                    // Handle the case where MongoDB is down but we still have filesystem data
                    let allDirectories;
                    if (responseData.mongo_status === 'error') {
                        // Extract the results array from the response
                        allDirectories = responseData.results;
                        console.warn('Note: MongoDB is unavailable, using filesystem data only');
                    } else if (responseData.results) {
                        // New structure with results field due to MONGO_ONLY_RESULTS flag
                        allDirectories = responseData.results;
                        console.log('Using results field from response');
                    } else {
                        // Legacy case - response is directly the array of directories
                        allDirectories = responseData;
                    }
                    
                    console.log('All directories:', allDirectories);
                    
                    // Make sure allDirectories is an array before using find
                    if (!Array.isArray(allDirectories)) {
                        console.error('Error: allDirectories is not an array', allDirectories);
                        throw new Error('Directory data is not in the expected format');
                    }
                    
                    const targetDir = allDirectories.find(dir => dir.directory === directory);
                    
                    if (targetDir && targetDir.path) {
                        const outputsDir = `${targetDir.path}/outputs`;
                        
                        // Try to fetch specific JSON files directly
                        const sampleFileNames = await fetchFileList(outputsDir);
                        
                        if (sampleFileNames && sampleFileNames.length > 0) {
                            console.log(`Loading ${sampleFileNames.length} JSON files from ${outputsDir}`);
                            
                            // Use batch API to load files in chunks
                            const batchSize = 20; // Increased batch size for better performance
                            
                            for (let i = 0; i < sampleFileNames.length; i += batchSize) {
                                // Get the current batch of files
                                const batchFiles = sampleFileNames.slice(i, i + batchSize);
                                
                                try {
                                    // Show loading progress
                                    const percentComplete = Math.min(100, Math.round(i / sampleFileNames.length * 100));
                                    document.getElementById('resultsTableBody').innerHTML = `
                                        <tr>
                                            <td colspan="7" class="text-center py-5">
                                                <h4 class="mb-4">Loading Experiment Data</h4>
                                                <div class="progress mb-3" style="height: 25px;">
                                                    <div class="progress-bar progress-bar-striped progress-bar-animated" 
                                                         role="progressbar" style="width: ${percentComplete}%" 
                                                         aria-valuenow="${percentComplete}" aria-valuemin="0" aria-valuemax="100">
                                                        ${percentComplete}%
                                                    </div>
                                                </div>
                                                <p class="mt-3 lead">Batch ${Math.floor(i/batchSize) + 1} of ${Math.ceil(sampleFileNames.length/batchSize)}</p>
                                                <p class="text-muted">Loading files ${i+1} to ${Math.min(i+batchSize, sampleFileNames.length)} of ${sampleFileNames.length}</p>
                                                <p class="small mt-3">Analytics and data tables will appear when loading is complete</p>
                                            </td>
                                        </tr>
                                    `;
                                    
                                    // Use batch API to load multiple files at once
                                    const batchResponse = await fetch(`/api/batch-files?dir=${encodeURIComponent(outputsDir)}&files=${encodeURIComponent(batchFiles.join(','))}`);
                                    
                                    if (batchResponse.ok) {
                                        const batchData = await batchResponse.json();
                                        
                                        // Process the returned files
                                        if (batchData.files) {
                                            Object.entries(batchData.files).forEach(([filename, jsonData]) => {
                                                if (jsonData && typeof jsonData === 'object') {
                                                    // Create a unique ID that includes filename for different runs of the same query
                                                    const dataId = `${jsonData.query_id || jsonData.id || jsonData._id}_${filename}_${jsonData.timestamp || jsonData.unix_timestamp || ''}`;
                                                    
                                                    // Only add if not already added
                                                    if (!loadedDataIds.has(dataId)) {
                                                        loadedDataIds.add(dataId);
                                                        currentData.push(jsonData);
                                                    }
                                                }
                                            });
                                        }
                                        
                                        // Log any errors
                                        if (batchData.errors && Object.keys(batchData.errors).length > 0) {
                                            console.warn('Errors loading some files:', batchData.errors);
                                            
                                            // Try to load files that had errors individually
                                            const errorFiles = Object.keys(batchData.errors);
                                            if (errorFiles.length > 0) {
                                                console.log(`Attempting to load ${errorFiles.length} files that failed in batch individually...`);
                                                await loadFilesIndividually(errorFiles, outputsDir, loadedDataIds);
                                            }
                                        }
                                    } else {
                                        console.warn(`Batch API error: ${batchResponse.status} ${batchResponse.statusText}`);
                                        
                                        // Try an alternative batch API endpoint as fallback
                                        try {
                                            console.log('Trying alternative batch API endpoint...');
                                            // Remove 'results/' from the path if it exists
                                            const alternatePath = outputsDir.startsWith('results/') ? outputsDir.substring(8) : outputsDir;
                                            const alternateBatchResponse = await fetch(`/api/batch-files?dir=${encodeURIComponent(alternatePath)}&files=${encodeURIComponent(batchFiles.join(','))}`);
                                            
                                            if (alternateBatchResponse.ok) {
                                                const alternateBatchData = await alternateBatchResponse.json();
                                                
                                                if (alternateBatchData.files) {
                                                    Object.entries(alternateBatchData.files).forEach(([filename, jsonData]) => {
                                                        if (jsonData && typeof jsonData === 'object') {
                                                            const dataId = jsonData.query_id || jsonData.id || jsonData._id || JSON.stringify(jsonData);
                                                            
                                                            if (!loadedDataIds.has(dataId)) {
                                                                loadedDataIds.add(dataId);
                                                                currentData.push(jsonData);
                                                            }
                                                        }
                                                    });
                                                    
                                                    console.log(`Successfully loaded ${Object.keys(alternateBatchData.files).length} files using alternative path`);
                                                    
                                                    // No need to fall back to individual loading if the alternative batch was successful
                                                    return;
                                                }
                                            }
                                        } catch (altError) {
                                            console.warn('Alternative batch API also failed:', altError);
                                        }
                                        
                                        // Fall back to loading files individually for this batch
                                        await loadFilesIndividually(batchFiles, outputsDir, loadedDataIds);
                                    }
                                } catch (batchError) {
                                    console.warn(`Error loading batch: ${batchError.message}`);
                                    
                                    // Fall back to loading files individually for this batch
                                    await loadFilesIndividually(batchFiles, outputsDir, loadedDataIds);
                                }
                            }
                            
                            // Helper function to load files individually as fallback
                            async function loadFilesIndividually(files, dir, loadedIds) {
                                console.log(`Loading ${files.length} files individually from ${dir}`);
                                let loadedCount = 0;
                                
                                for (const filename of files) {
                                    if (!filename || filename.trim() === '') continue;
                                    
                                    try {
                                        // First try standard path
                                        const fileUrl = `/${dir}/${filename}`;
                                        console.log(`Trying to load: ${fileUrl}`);
                                        
                                        let fileResponse = await fetch(fileUrl);
                                        
                                        // If failed, try without 'results/' prefix
                                        if (!fileResponse.ok && dir.startsWith('results/')) {
                                            const altFileUrl = `/${dir.substring(8)}/${filename}`;
                                            console.log(`First attempt failed, trying: ${altFileUrl}`);
                                            fileResponse = await fetch(altFileUrl);
                                        }
                                        
                                        // If failed again, try with direct 'results' path
                                        if (!fileResponse.ok) {
                                            const directFileUrl = `/results/${filename}`;
                                            console.log(`Second attempt failed, trying: ${directFileUrl}`);
                                            fileResponse = await fetch(directFileUrl);
                                        }
                                        
                                        // If still failed, try with full experiment path
                                        if (!fileResponse.ok && currentExperiment) {
                                            const experimentPath = `/${currentExperiment.path}/outputs/${filename}`;
                                            console.log(`Third attempt failed, trying experiment path: ${experimentPath}`);
                                            fileResponse = await fetch(experimentPath);
                                        }
                                        
                                        if (fileResponse.ok) {
                                            const jsonData = await fileResponse.json();
                                            if (jsonData && typeof jsonData === 'object') {
                                                // Create a unique ID that includes filename for different runs of the same query
                                                const dataId = `${jsonData.query_id || jsonData.id || jsonData._id}_${filename}_${jsonData.timestamp || jsonData.unix_timestamp || ''}`;
                                                
                                                // Only add if not already added
                                                if (!loadedIds.has(dataId)) {
                                                    loadedIds.add(dataId);
                                                    currentData.push(jsonData);
                                                    loadedCount++;
                                                }
                                            }
                                        } else {
                                            console.warn(`All attempts failed loading ${filename}: ${fileResponse.status}`);
                                        }
                                    } catch (fileError) {
                                        console.warn(`Error loading ${filename}: ${fileError.message}`);
                                    }
                                }
                                
                                console.log(`Successfully loaded ${loadedCount} out of ${files.length} files individually`);
                            }
                        } else {
                            throw new Error(`No JSON files found in ${outputsDir}`);
                        }
                    } else {
                        throw new Error(`Could not find path information for directory ${directory}`);
                    }
                } else {
                    throw new Error(`Failed to fetch directory information: ${response.status}`);
                }
                
                // Log what we loaded
                console.log(`Successfully loaded ${currentData.length} result items from filesystem`);
                
                // If we didn't load any data, show error
                if (currentData.length === 0) {
                    throw new Error(`No valid data files found in ${currentExperiment.path}`);
                }
            } catch (error) {
                console.error('Error loading output files:', error);
                // Handle display of error below
                throw error;
            }
        }
        
        // Display results if we have data
        if (currentData.length > 0) {
            // Now show all the sections since data is loaded
            const analyticsDashboard = document.getElementById('analyticsDashboard');
            if (analyticsDashboard) {
                analyticsDashboard.style.display = 'block';
                
                // If in SINGLE_EXPERIMENT mode, add description above analytics
                if (singleExperiment) {
                    // Create description element
                    const descriptionElement = document.createElement('div');
                    descriptionElement.id = 'systemDescription';
                    descriptionElement.className = 'mb-4';
                    descriptionElement.innerHTML = `
                        <div class="alert alert-info mb-4">
                            <p>
                                <strong>Optimistic Truth Bot (OTB)</strong> is a multi-agent system for resolving Polymarket prediction market proposals with high accuracy using large language models.
                                It combines search-based and code execution solvers to process proposals through multi-agent decision-making.
                                The system monitors blockchain events, processes proposals, and submits resolution recommendations.
                                It tracks performance against actual market outcomes for continuous improvement.
                                <a href="https://github.com/UMAprotocol/large-language-oracle" target="_blank">Learn more on GitHub</a>
                            </p>
                        </div>
                    `;
                    
                    // Insert before analytics dashboard
                    const mainContainer = analyticsDashboard.parentNode;
                    if (mainContainer) {
                        mainContainer.insertBefore(descriptionElement, analyticsDashboard);
                    }
                }
                
                // Make sure the tabs are visible again
                const analyticsTabs = document.getElementById('analyticsTabs');
                if (analyticsTabs) {
                    analyticsTabs.style.display = 'flex';
                }
                
                // Restore the original analytics tab content structure
                const analyticsTabContent = document.getElementById('analyticsTabContent');
                if (analyticsTabContent && analyticsTabContent.hasAttribute('data-original-content')) {
                    analyticsTabContent.innerHTML = analyticsTabContent.getAttribute('data-original-content');
                }
            }
            
            document.getElementById('filterControls').style.display = 'flex';
            
            // Display the experiment metadata properly now that data is loaded, but only if not in SINGLE_EXPERIMENT mode
            if (!singleExperiment) {
                displayExperimentMetadata();
            }
            
            // Populate the table with data
            displayResultsData();
            
            // Apply the current filter
            applyTableFilter(currentFilter);
            
            // Initialize charts AFTER the analytics tabs are shown
            initializeCharts();
            
            // Calculate and display analytics
            const analytics = calculateAnalytics(currentData);
            updateAnalyticsDisplay(analytics);
            
            // Trigger custom event to setup tag filter
            const dataLoadedEvent = new CustomEvent('dataLoaded');
            document.dispatchEvent(dataLoadedEvent);
        } else {
            // Keep analytics, filter, and tag filter hidden when there's no data
            document.getElementById('analyticsDashboard').style.display = 'none';
            
            // Remove system description if it exists
            const descriptionElement = document.getElementById('systemDescription');
            if (descriptionElement) {
                descriptionElement.remove();
            }
            
            document.getElementById('filterControls').style.display = 'none';
            const tagFilterCard = document.getElementById('tagFilterCard');
            if (tagFilterCard) {
                tagFilterCard.style.display = 'none';
            }
            
            // Show error message if we couldn't load any data
            document.getElementById('resultsTableBody').innerHTML = `
                <tr>
                    <td colspan="8" class="text-center">No data available</td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading experiment data:', error);
        
        // Keep analytics, filter, and tag filter hidden on error
        document.getElementById('analyticsDashboard').style.display = 'none';
        
        // Remove system description if it exists
        const descriptionElement = document.getElementById('systemDescription');
        if (descriptionElement) {
            descriptionElement.remove();
        }
        
        document.getElementById('filterControls').style.display = 'none';
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = 'none';
        }
        
        // Display experiment metadata even on error, but only if not in SINGLE_EXPERIMENT mode
        if (!singleExperiment) {
            displayExperimentMetadata();
        }
        
        document.getElementById('resultsTableBody').innerHTML = `
            <tr>
                <td colspan="8" class="text-center text-danger">
                    Error loading experiment data: ${error.message}
                </td>
            </tr>
        `;
    }
}

// Display the metadata for the current experiment
function displayExperimentMetadata() {
    if (!currentExperiment) return;
    
    const metadataCard = document.getElementById('experimentMetadataCard');
    const metadataContent = document.getElementById('experimentMetadataContent');
    
    if (!metadataCard || !metadataContent) return;
    
    // Don't show metadata in SINGLE_EXPERIMENT mode
    if (singleExperiment) {
        metadataCard.style.display = 'none';
        return;
    }
    
    // Determine data source - use explicit source if available, otherwise infer
    const isMongoDBSource = currentExperiment.explicitSource === 'mongodb' || 
                           currentExperiment.source === 'mongodb' || 
                           currentExperiment.path?.startsWith('mongodb/');
    
    const sourceType = isMongoDBSource ? 'MongoDB' : 'Filesystem';
    const sourceIcon = isMongoDBSource ? 
        '<i class="bi bi-database-fill" title="MongoDB Data Source"></i>' : 
        '<i class="bi bi-folder-fill" title="Filesystem Data Source"></i>';
    
    // Get all metadata - handle both MongoDB and filesystem structures
    // For MongoDB structure: currentExperiment.metadata.experiment
    // For filesystem structure: currentExperiment.metadata
    let fullMetadata = currentExperiment.metadata || {};
    let experimentInfo = {};
    
    if (fullMetadata.experiment) {
        // MongoDB structure
        experimentInfo = fullMetadata.experiment || {};
    } else {
        // Filesystem structure
        experimentInfo = fullMetadata;
    }
    
    // Get system prompt from metadata - handle various structures
    const systemPrompt = experimentInfo.system_prompt || 
                        fullMetadata.modifications?.system_prompt || 
                        fullMetadata.experiment?.system_prompt;
    
    // Basic metadata display (without description)
    let metadata = `
        <div class="metadata-section">
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Title:</strong>
                </div>
                <div class="col-md-8">
                    ${currentExperiment.title || experimentInfo.title || currentExperiment.directory}
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Directory:</strong>
                </div>
                <div class="col-md-8">
                    <span class="code-font">${currentExperiment.directory}</span>
                </div>
            </div>
            
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Data Source:</strong>
                </div>
                <div class="col-md-8">
                    ${sourceIcon} ${sourceType}
                    ${isMongoDBSource && currentExperiment.count ? `<span class="badge bg-primary ms-2">${currentExperiment.count} items</span>` : ''}
                </div>
            </div>
            
            ${currentExperiment.timestamp || experimentInfo?.timestamp ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Date:</strong>
                </div>
                <div class="col-md-8">
                    ${formatDisplayDate(currentExperiment.timestamp || experimentInfo.timestamp)}
                </div>
            </div>
            ` : ''}
            
            ${currentExperiment.goal || experimentInfo?.goal ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Goal:</strong>
                </div>
                <div class="col-md-8">
                    ${currentExperiment.goal || experimentInfo.goal}
                </div>
            </div>
            ` : ''}
            
            ${experimentInfo?.previous_experiment ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Previous Experiment:</strong>
                </div>
                <div class="col-md-8">
                    ${experimentInfo.previous_experiment}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    // Add MongoDB details if available
    if (isMongoDBSource && fullMetadata) {
        if (fullMetadata.experiment_id || (fullMetadata._id && fullMetadata._id.$oid)) {
            metadata += `<hr><h4>MongoDB Details</h4><div class="metadata-section">`;
            
            if (fullMetadata.experiment_id) {
                metadata += `
                <div class="row mb-3">
                    <div class="col-md-4">
                        <strong>Experiment ID:</strong>
                    </div>
                    <div class="col-md-8">
                        <span class="code-font">${fullMetadata.experiment_id}</span>
                    </div>
                </div>`;
            }
            
            if (fullMetadata._id && fullMetadata._id.$oid) {
                metadata += `
                <div class="row mb-3">
                    <div class="col-md-4">
                        <strong>MongoDB ID:</strong>
                    </div>
                    <div class="col-md-8">
                        <span class="code-font">${fullMetadata._id.$oid}</span>
                    </div>
                </div>`;
            }
            
            metadata += `</div>`;
        }
    }
    
    // Display setup if it exists as a string
    if (typeof experimentInfo?.setup === 'string' && experimentInfo.setup) {
        metadata += `
        <hr>
        <h4>Setup</h4>
        <div class="metadata-section">
            <div class="row">
                <div class="col-md-12">
                    <p>${experimentInfo.setup}</p>
                </div>
            </div>
        </div>`;
    }
    
    // Display modifications if they exist
    if (experimentInfo?.modifications && typeof experimentInfo.modifications === 'object') {
        metadata += `
        <hr>
        <h4>Modifications</h4>
        <div class="metadata-section">`;
        
        Object.entries(experimentInfo.modifications).forEach(([key, value]) => {
            if (key === 'system_prompt') return; // Skip system prompt, handled separately
            
            metadata += `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>${formatKeyName(key)}:</strong>
                </div>
                <div class="col-md-8">`;
            
            if (typeof value === 'object' && value !== null) {
                // For nested objects like bug_fixes
                metadata += `<div class="nested-object">`;
                Object.entries(value).forEach(([subKey, subValue]) => {
                    metadata += `
                    <div class="row mb-2">
                        <div class="col-md-4">
                            <strong>${formatKeyName(subKey)}:</strong>
                        </div>
                        <div class="col-md-8">
                            ${subValue}
                        </div>
                    </div>`;
                });
                metadata += `</div>`;
            } else {
                metadata += `${value}`;
            }
            
            metadata += `
                </div>
            </div>`;
        });
        
        metadata += `</div>`;
    }
    
    // Add system prompt toggle if available
    if (systemPrompt) {
        metadata += `
        <hr>
        <div class="metadata-section">
            <a href="#" id="toggleSystemPrompt" class="d-inline-flex align-items-center">
                <strong>System Prompt</strong> <i class="bi bi-chevron-down ms-1"></i>
            </a>
        </div>`;
    }
    
    // Set the content and show the card
    metadataContent.innerHTML = metadata;
    metadataCard.style.display = 'block';
    
    // Create/update system prompt overlay
    let overlayContainer = document.getElementById('systemPromptOverlay');
    if (!overlayContainer && systemPrompt) {
        overlayContainer = document.createElement('div');
        overlayContainer.id = 'systemPromptOverlay';
        overlayContainer.className = 'system-prompt-overlay';
        overlayContainer.style.display = 'none';
        
        // Close button
        const closeButton = document.createElement('button');
        closeButton.className = 'overlay-close-btn';
        closeButton.innerHTML = '&times;';
        closeButton.onclick = function() {
            overlayContainer.style.display = 'none';
            document.body.style.overflow = 'auto';
        };
        
        // Content container
        const contentDiv = document.createElement('div');
        contentDiv.className = 'overlay-content';
        contentDiv.id = 'systemPromptContent';
        contentDiv.innerHTML = `
            <h3>System Prompt</h3>
            <pre class="system-prompt-pre">${systemPrompt}</pre>
        `;
        
        overlayContainer.appendChild(closeButton);
        overlayContainer.appendChild(contentDiv);
        document.body.appendChild(overlayContainer);
        
        // Add custom styles for the overlay if not already added
        if (!document.getElementById('systemPromptStyles')) {
            const styleElement = document.createElement('style');
            styleElement.id = 'systemPromptStyles';
            styleElement.innerHTML = `
                .system-prompt-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.8);
                    z-index: 1050;
                    overflow-y: auto;
                    padding: 20px;
                }
                
                .overlay-close-btn {
                    position: fixed;
                    top: 20px;
                    right: 30px;
                    font-size: 30px;
                    color: white;
                    background: transparent;
                    border: none;
                    cursor: pointer;
                }
                
                .overlay-content {
                    background-color: white;
                    margin: 30px auto;
                    padding: 25px;
                    width: 80%;
                    max-width: 1000px;
                    border-radius: 10px;
                    box-shadow: 0 5px 15px rgba(0,0,0,0.3);
                }
                
                .system-prompt-pre {
                    white-space: pre-wrap;
                    font-size: 15px;
                    line-height: 1.5;
                    background-color: #f8f9fa;
                    padding: 15px;
                    border-radius: 5px;
                    margin-top: 15px;
                    overflow-x: auto;
                }
                
                .nested-object {
                    padding: 10px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                    margin-bottom: 10px;
                }
            `;
            document.head.appendChild(styleElement);
        }
        
        // Add toggle logic
        document.getElementById('toggleSystemPrompt').addEventListener('click', function(e) {
            e.preventDefault();
            overlayContainer.style.display = 'block';
            document.body.style.overflow = 'hidden';
        });
    } else if (systemPrompt) {
        // Update system prompt content if it already exists
        document.getElementById('systemPromptContent').innerHTML = `
            <h3>System Prompt</h3>
            <pre class="system-prompt-pre">${systemPrompt}</pre>
        `;
        
        // Add toggle logic
        document.getElementById('toggleSystemPrompt').addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('systemPromptOverlay').style.display = 'block';
            document.body.style.overflow = 'hidden';
        });
    }
}

// Display the results data in the table
function displayResultsData() {
    // Remove single experiment loader if it exists
    const singleExperimentLoader = document.getElementById('singleExperimentLoader');
    if (singleExperimentLoader) {
        singleExperimentLoader.remove();
    }
    
    // Show results section and filter controls
    const resultsSection = document.querySelector('.results-section');
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }
    
    const filterControls = document.getElementById('filterControls');
    if (filterControls) {
        filterControls.style.display = 'flex';
    }
    
    const resultsTableCard = document.getElementById('resultsTableCard');
    if (resultsTableCard) {
        resultsTableCard.style.display = 'block';
    }
    
    const analyticsNote = document.getElementById('analyticsNote');
    if (analyticsNote) {
        analyticsNote.style.display = 'block';
    }
    
    // Show the date filter card
    const dateFilterCard = document.getElementById('dateFilterCard');
    if (dateFilterCard) {
        dateFilterCard.style.display = 'block';
    }
    
    // Ensure we have data
    const tableBody = document.getElementById('resultsTableBody');
    if (!tableBody) return;
    
    if (!currentData || currentData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">No data available</td>
            </tr>
        `;
        
        const displayingCount = document.getElementById('displayingCount');
        if (displayingCount) {
            displayingCount.textContent = '0';
        }
        
        const totalEntriesCount = document.getElementById('totalEntriesCount');
        if (totalEntriesCount) {
            totalEntriesCount.textContent = '0';
        }
        
        return;
    }
    
    // Setup tag filter if there are tags
    setupTagFilter();
    
    // Apply the current filter
    applyTableFilter(currentFilter);
}

// Function to update table header based on selected columns
function updateTableHeader() {
    const thead = document.querySelector('#resultsTable thead');
    if (!thead) return;
    
    // Build the header row based on selected columns
    let headerRow = '<tr>';
    
    // Add icon column header (always first)
    headerRow += '<th class="icon-column"></th>';
    
    // Add columns based on preferences
    if (columnPreferences.timestamp) headerRow += '<th class="col-timestamp">Process Time</th>';
    if (columnPreferences.proposal_timestamp) headerRow += '<th class="col-proposal-time">Proposal Time</th>';
    if (columnPreferences.expiration_timestamp) headerRow += '<th class="col-expiration-time">Expiration Time</th>';
    if (columnPreferences.request_transaction_block_time) headerRow += '<th class="col-request-time">Proposal Time</th>';
    if (columnPreferences.id) headerRow += '<th class="col-id">ID</th>';
    if (columnPreferences.title) headerRow += '<th class="col-title">Title</th>';
    if (columnPreferences.recommendation) headerRow += '<th class="col-recommendation">AI Rec</th>';
    if (columnPreferences.router_decision) headerRow += '<th class="col-router">Router</th>';
    if (columnPreferences.resolution) headerRow += '<th class="col-resolution">Res</th>';
    if (columnPreferences.disputed) headerRow += '<th class="col-disputed">Disputed</th>';
    if (columnPreferences.correct) headerRow += '<th class="col-correct">Correct</th>';
    if (columnPreferences.block_number) headerRow += '<th class="col-block-number">Block #</th>';
    if (columnPreferences.proposal_bond) headerRow += '<th class="col-proposal-bond">Bond</th>';
    if (columnPreferences.tags) headerRow += '<th class="col-tags">Tags</th>';
    
    headerRow += '</tr>';
    thead.innerHTML = headerRow;
}

// Helper function to extract run number from filename or item
function extractRunNumber(item, allRunsForSameQuery = null) {
    // First check if run_iteration is available in the data
    if (item.run_iteration !== undefined && item.run_iteration !== null) {
        return item.run_iteration;
    }
    
    // If not, try to extract from filename if available
    const filename = item.filename || item.file_name || item.output_file || '';
    if (filename.includes('_run-')) {
        const runMatch = filename.match(/_run-(\d+)/);
        if (runMatch) {
            return parseInt(runMatch[1]);
        }
    }
    
    // Check metadata for filename
    if (item.metadata && item.metadata.filename) {
        const metaFilename = item.metadata.filename;
        if (metaFilename.includes('_run-')) {
            const runMatch = metaFilename.match(/_run-(\d+)/);
            if (runMatch) {
                return parseInt(runMatch[1]);
            }
        }
    }
    
    // If we have access to all runs for the same query, calculate run number based on chronological order
    if (allRunsForSameQuery && allRunsForSameQuery.length > 1) {
        // Sort all runs by timestamp
        const sortedByTime = [...allRunsForSameQuery].sort((a, b) => {
            const aTime = a.timestamp || a.unix_timestamp || 0;
            const bTime = b.timestamp || b.unix_timestamp || 0;
            return aTime - bTime;
        });
        
        // Find the index of this item in the sorted array + 1 for 1-based run numbers
        const index = sortedByTime.findIndex(run => 
            run.timestamp === item.timestamp && 
            run.query_id === item.query_id
        );
        if (index !== -1) {
            return index + 1;
        }
    }
    
    // Default to 1 (first run)
    return 1;
}

// Deduplicate data by query_id, keeping only the latest run for table display
function deduplicateByQueryId(dataArray) {
    // First pass: group by query_id
    const queryGroups = new Map();
    
    dataArray.forEach(item => {
        // Extract query_id from various possible fields
        const queryId = item.query_id || item.question_id || item._id || item.short_id || item.question_id_short;
        if (!queryId) return;
        
        const key = queryId.toString();
        
        if (!queryGroups.has(key)) {
            queryGroups.set(key, []);
        }
        queryGroups.get(key).push(item);
    });
    
    // Second pass: process each group to determine run numbers and find latest
    return Array.from(queryGroups.values()).map(group => {
        // Calculate run numbers for all items in this group
        group.forEach(item => {
            const runNumber = extractRunNumber(item, group);
            item._calculatedRunNumber = runNumber;
        });
        
        // Sort all runs by calculated run number and timestamp
        const sortedRuns = group.sort((a, b) => {
            const aRun = a._calculatedRunNumber;
            const bRun = b._calculatedRunNumber;
            if (aRun !== bRun) return aRun - bRun;
            return (a.timestamp || a.unix_timestamp || 0) - (b.timestamp || b.unix_timestamp || 0);
        });
        
        // Find the latest run (highest run number, then latest timestamp)
        const latestRun = sortedRuns.reduce((latest, current) => {
            const latestRunNum = latest._calculatedRunNumber;
            const currentRunNum = current._calculatedRunNumber;
            const latestTimestamp = latest.timestamp || latest.unix_timestamp || 0;
            const currentTimestamp = current.timestamp || current.unix_timestamp || 0;
            
            if (currentRunNum > latestRunNum || 
                (currentRunNum === latestRunNum && currentTimestamp > latestTimestamp)) {
                return current;
            }
            return latest;
        });
        
        // Log multi-run cases for debugging
        if (group.length > 1) {
            console.log('Multi-run query found:', {
                query_id: latestRun.query_id?.slice(0, 10) + '...',
                total_runs: group.length,
                latest_run: latestRun._calculatedRunNumber,
                latest_recommendation: latestRun.proposed_price_outcome || latestRun.result?.recommendation,
                filenames: sortedRuns.map(r => r.filename || r.file_name || 'unknown')
            });
        }
        
        // Create the result item based on the latest run
        const item = { ...latestRun };
        item._allRuns = sortedRuns; // Store all runs for this query_id
        item._runCount = sortedRuns.length; // Add run count for display
        
        return item;
    });
}

// Update the table with the provided data
function updateTableWithData(dataArray) {
    const tableBody = document.getElementById('resultsTableBody');
    if (!tableBody) return;
    
    if (!dataArray || dataArray.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="12" class="text-center">No data available</td>
            </tr>
        `;
        document.getElementById('displayingCount').textContent = '0';
        document.getElementById('totalEntriesCount').textContent = '0';
        return;
    }
    
    // Update table header based on column preferences
    updateTableHeader();
    
    // Group data by query_id and keep only the latest run for table display
    const deduplicatedData = deduplicateByQueryId(dataArray);
    
    // Sort the data based on current sort settings
    const sortedData = sortData([...deduplicatedData], currentSort.column, currentSort.direction);
    
    // Pagination handling
    const itemsPerPage = 100;
    const totalPages = Math.ceil(sortedData.length / itemsPerPage);
    let currentPage = parseInt(localStorage.getItem('currentResultsPage') || '1');
    
    // Make sure current page is valid
    if (currentPage < 1 || currentPage > totalPages) {
        currentPage = 1;
    }
    
    // Calculate start and end indices for the current page
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = Math.min(startIndex + itemsPerPage, sortedData.length);
    
    // Get items for the current page
    const currentPageItems = sortedData.slice(startIndex, endIndex);
    
    // Generate table rows for the current page
    tableBody.innerHTML = currentPageItems.map((item, index) => {
        // Safety check for null/undefined items
        if (!item) return '';
        
        const isCorrect = isRecommendationCorrect(item);
        let correctnessClass = '';
        let correctnessIcon = '';
        
        if (isCorrect === true) {
            correctnessClass = 'text-success';
            correctnessIcon = 'bi-check-circle-fill';
        } else if (isCorrect === false) {
            correctnessClass = 'text-danger';
            correctnessIcon = 'bi-x-circle-fill';
        } else {
            // Unresolved status - neutral styling
            correctnessClass = 'text-secondary';
            correctnessIcon = 'bi-dash-circle';
        }
        
        // Determine if we can calculate correctness
        const canCalculateCorrectness = (item.resolved_price_outcome !== undefined && 
                                        item.resolved_price_outcome !== null);
        
        // Check if disputed
        const isDisputed = item.disputed === true;
        const disputedClass = isDisputed ? 'text-warning' : 'text-muted';
        const disputedIcon = isDisputed ? 'bi-exclamation-triangle-fill' : 'bi-dash';
        
        // Extract title
        const title = extractTitle(item);
        
        // Use short ID instead of truncated long ID
        const queryId = item.question_id_short || 
                       (item.query_id ? item.query_id.substring(0, 10) : 
                       (item._id ? item._id.toString().substring(0, 10) : 'N/A'));
        
        // Use standardized recommendation field from the most recent run, with fallbacks
        // Since this item is from deduplicated data, it should already be the latest run
        let recommendation = 'N/A';
        if (item._allRuns && item._allRuns.length > 0) {
            // Find the most recent run and get its recommendation using the same logic
            const latestRun = item._allRuns.reduce((latest, current) => {
                const latestRunIteration = extractRunNumber(latest);
                const currentRunIteration = extractRunNumber(current);
                const latestTimestamp = latest.timestamp || latest.unix_timestamp || 0;
                const currentTimestamp = current.timestamp || current.unix_timestamp || 0;
                
                if (currentRunIteration > latestRunIteration ||
                    (currentRunIteration === latestRunIteration && currentTimestamp > latestTimestamp)) {
                    return current;
                }
                return latest;
            });
            
            recommendation = latestRun.format_version === 2 
                            ? (latestRun.result?.recommendation || latestRun.recommendation || latestRun.proposed_price_outcome || 'N/A')
                            : (latestRun.recommendation || latestRun.proposed_price_outcome || 'N/A');
        } else {
            // Fallback to current item if no _allRuns data
            recommendation = item.format_version === 2 
                            ? (item.result?.recommendation || item.recommendation || item.proposed_price_outcome || 'N/A')
                            : (item.recommendation || item.proposed_price_outcome || 'N/A');
        }
        
        // Use standardized resolution field
        const resolution = item.resolved_price_outcome !== undefined && 
                          item.resolved_price_outcome !== null ? 
                          item.resolved_price_outcome : 'Unresolved';
        
        // Format the timestamp - handle both string and numeric timestamps
        let timestamp = item.timestamp || item.unix_timestamp;
        if (typeof timestamp === 'string' && !isNaN(parseInt(timestamp, 10))) {
            timestamp = parseInt(timestamp, 10);
        }
        
        const formattedDate = formatDate(timestamp);
        
        // Format the proposal timestamp if available
        let proposalTimestamp = item.proposal_timestamp || 0;
        if (typeof proposalTimestamp === 'string' && !isNaN(parseInt(proposalTimestamp, 10))) {
            proposalTimestamp = parseInt(proposalTimestamp, 10);
        }
        
        // Access the proposal date directly from proposal_metadata as a fallback
        const formattedProposalDate = proposalTimestamp ? 
            formatDate(proposalTimestamp) : 
            (item.proposal_metadata && item.proposal_metadata.request_transaction_block_time ? 
                formatDate(item.proposal_metadata.request_transaction_block_time) : 'N/A');
        
        // Format the expiration timestamp if available
        const expirationTimestamp = item.proposal_metadata?.expiration_timestamp || 0;
        const formattedExpirationDate = expirationTimestamp ? formatDate(expirationTimestamp) : 'N/A';
        
        // Format the request transaction block time if available
        const blockTimestamp = item.proposal_metadata?.request_transaction_block_time || 0;
        const formattedBlockTime = blockTimestamp ? formatDate(blockTimestamp) : 'N/A';
        
        // Extract block number from proposal_metadata if available
        const blockNumber = item.proposal_metadata?.block_number || 'N/A';
        
        // Extract proposal bond from proposal_metadata if available
        const proposalBond = item.proposal_metadata?.proposal_bond 
            ? formatBond(item.proposal_metadata.proposal_bond) 
            : 'N/A';
            
        // Format tags
        const formattedTags = item.tags && Array.isArray(item.tags) && item.tags.length > 0
            ? item.tags.map(tag => `<span class="tag-badge small">${tag}</span>`).join(' ')
            : 'None';
        
        // Store the index in the deduplicated array for click handling
        // We'll pass the item data directly rather than relying on currentData lookup
        const deduplicatedDataIndex = index;
        
        // Build the row based on selected columns
        let row = `<tr class="result-row ${recommendation?.toLowerCase() === 'p4' || recommendation?.toLowerCase() === 'p3' ? 'table-warning' : ''}" data-item-index="${deduplicatedDataIndex}">`;
        
        // Add icon as the first cell if available
        // For format_version 2, check proposal_metadata.icon
        let icon = null;
        if (item.format_version === 2) {
            icon = item.proposal_metadata?.icon || null;
        } else {
            icon = item.icon || null;
        }
        
        if (icon) {
            row += `<td class="icon-cell"><img src="${icon}" alt="Question Icon" class="table-icon"></td>`;
        } else {
            row += `<td class="icon-cell"></td>`;
        }
        
        // Add cells based on column preferences
        if (columnPreferences.timestamp) row += `<td>${formattedDate}</td>`;
        if (columnPreferences.proposal_timestamp) row += `<td>${formattedProposalDate}</td>`;
        if (columnPreferences.expiration_timestamp) row += `<td>${formattedExpirationDate}</td>`;
        if (columnPreferences.request_transaction_block_time) row += `<td>${formattedBlockTime}</td>`;
        if (columnPreferences.id) row += `<td class="monospace">${queryId}</td>`;
        if (columnPreferences.title) row += `<td>${title || 'No title'}</td>`;
        if (columnPreferences.recommendation) row += `<td><code>${recommendation}</code></td>`;
        if (columnPreferences.router_decision) row += `<td>${item.router_decision ? item.router_decision.solver || 'N/A' : 'N/A'}</td>`;
        if (columnPreferences.resolution) row += `<td><code>${resolution}</code></td>`;
        if (columnPreferences.disputed) row += `<td><i class="bi ${disputedIcon} ${disputedClass}"></i></td>`;
        if (columnPreferences.correct) row += `<td><i class="bi ${correctnessIcon} ${correctnessClass}"></i></td>`;
        if (columnPreferences.block_number) row += `<td>${blockNumber}</td>`;
        if (columnPreferences.proposal_bond) row += `<td>${proposalBond}</td>`;
        if (columnPreferences.tags) row += `<td>${formattedTags}</td>`;
        
        row += '</tr>';
        return row;
    }).join('');
    
    // Add click event to rows
    document.querySelectorAll('.result-row').forEach(row => {
        row.addEventListener('click', () => {
            // Use the data item index to get the correct data item from the current page
            const itemIndex = parseInt(row.getAttribute('data-item-index'));
            const item = currentPageItems[itemIndex];
            if (item) {
                showDetails(item, itemIndex);
                
                // Add selected class to the clicked row
                document.querySelectorAll('.result-row').forEach(r => r.classList.remove('table-active'));
                row.classList.add('table-active');
            }
        });
        
        // Add context menu for the row
        row.addEventListener('contextmenu', (e) => {
            e.preventDefault();
            
            // Get the item data
            const itemIndex = parseInt(row.getAttribute('data-item-index'));
            const item = currentPageItems[itemIndex];
            
            // Determine which identifier to use (prioritize query_id)
            let queryParam = '';
            if (item.query_id) {
                queryParam = `query_id=${item.query_id}`;
            } else if (item.question_id) {
                queryParam = `question_id=${item.question_id}`;
            } else if (item.condition_id) {
                queryParam = `condition_id=${item.condition_id}`;
            } else if (item.transaction_hash) {
                queryParam = `transaction_hash=${item.transaction_hash}`;
            }
            
            // Open the query page in a new tab
            if (queryParam) {
                window.open(`query.html?${queryParam}`, '_blank');
            }
        });
        
        // Add hover cursor style to indicate clickable rows
        row.style.cursor = 'pointer';
        
        // Add title to indicate right-click option
        row.setAttribute('title', 'Right-click to open in query viewer');
    });
    
    // Update the count display
    const displayingCount = document.getElementById('displayingCount');
    if (displayingCount) {
        displayingCount.textContent = currentPageItems.length;
    }
    
    const totalEntriesCount = document.getElementById('totalEntriesCount');
    if (totalEntriesCount) {
        totalEntriesCount.textContent = sortedData.length;
    }
    
    // Create pagination controls
    createPagination(currentPage, totalPages, 'resultsTable');
    
    // Re-initialize sortable headers after updating
    initializeSortableHeaders();
}

// Helper function to format bond values
function formatBond(bond) {
    if (!bond) return 'N/A';
    
    // Format as number with commas
    const formattedValue = parseInt(bond).toLocaleString();
    return formattedValue;
}

// Apply filter and search to the table
function applyTableFilter(filter) {
    // Get current tag selections
    const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
    const selectedTags = Array.from(checkboxes).map(cb => cb.value);
    
    // Apply all filters
    applyAllFilters(filter, selectedTags);
}

// Show detailed information for a specific data item
function showDetails(data, index) {
    const modalTitle = document.getElementById('detailsModalLabel');
    const modalBody = document.getElementById('detailsModalBody');
    const queryButton = document.querySelector('.view-query-btn');
    
    if (!modalTitle || !modalBody) return;
    
    // Update query button
    if (queryButton) {
        // Determine which identifier to use (prioritize query_id)
        let queryParam = '';
        if (data.query_id) {
            queryParam = `query_id=${data.query_id}`;
        } else if (data.question_id) {
            queryParam = `question_id=${data.question_id}`;
        } else if (data.condition_id) {
            queryParam = `condition_id=${data.condition_id}`;
        } else if (data.transaction_hash) {
            queryParam = `transaction_hash=${data.transaction_hash}`;
        }
        
        // Update button
        if (queryParam) {
            queryButton.href = `query.html?${queryParam}`;
            queryButton.style.display = 'inline-block';
        } else {
            queryButton.style.display = 'none';
        }
    }
    
    // Get title directly from the data using our extraction function
    const title = extractTitle(data) || 'Details';
    
    // Check if this is format_version 2
    const isFormatV2 = data.format_version === 2;
    
    // Set the modal title with icon if available
    // For format_version 2, icon is in proposal_metadata.icon
    let icon = null;
    if (isFormatV2) {
        icon = data.proposal_metadata?.icon || null;
    } else {
        icon = data.icon || null;
    }
    
    if (icon) {
        modalTitle.innerHTML = `<img src="${icon}" alt="Question Icon" class="modal-icon"> ${title}`;
    } else {
        modalTitle.textContent = title;
    }
    
    // Get recommendation from the appropriate location based on format version
    const recommendation = isFormatV2 ? (data.result?.recommendation || 'N/A') : (data.recommendation || 'N/A');
    
    // Check if disputed
    const isDisputed = (isFormatV2 ? data.market_data?.disputed : data.disputed) === true;
    
    // Get proposed price outcome, check at root level first, then check in other locations
    const proposedPrice = data.proposed_price_outcome !== undefined
        ? data.proposed_price_outcome
        : (isFormatV2
            ? (data.market_data?.proposed_price_outcome !== undefined 
                ? data.market_data.proposed_price_outcome 
                : (data.market_data?.proposed_price !== undefined ? data.market_data.proposed_price : 'N/A'))
            : (data.proposed_price !== undefined 
                ? data.proposed_price 
                : (data.proposal_metadata?.proposed_price_outcome !== undefined 
                    ? data.proposal_metadata.proposed_price_outcome 
                    : (data.proposal_metadata?.proposed_price !== undefined ? data.proposal_metadata.proposed_price : 'N/A'))));
    
    // Get correctness state
    const isCorrect = isRecommendationCorrect(data);
    let alertClass = 'alert-secondary';
    let correctnessText = 'Unresolved';
    
    if (isCorrect === true) {
        alertClass = 'alert-success';
        correctnessText = 'Yes';
    } else if (isCorrect === false) {
        alertClass = 'alert-danger';
        correctnessText = 'No';
    }
    
    // Get resolved price from either location
    const resolvedPrice = isFormatV2
        ? (data.market_data?.resolved_price_outcome || data.market_data?.resolved_price || 'Unresolved')
        : (data.resolved_price_outcome || data.resolved_price || 
           data.proposal_metadata?.resolved_price_outcome || data.proposal_metadata?.resolved_price || 'Unresolved');
    
    // Get run count information
    const runCount = data._runCount || 1;
    const allRuns = data._allRuns || [data];
    
    // For multi-run scenarios, show latest run's recommendation in status bar
    // but note that each tab will show its own run's data
    const displayRecommendation = runCount > 1 ? 
        (allRuns[allRuns.length - 1]?.result?.recommendation || 
         allRuns[allRuns.length - 1]?.proposed_price_outcome || 
         recommendation) : recommendation;
    
    // Generate the content with run count in status bar
    let content = `
        <div class="alert ${alertClass} mb-4">
            <strong>Recommendation:</strong> ${displayRecommendation} | 
            <strong>Resolved:</strong> ${data.resolved_price_outcome || 'Unresolved'} | 
            <strong>Proposed:</strong> ${proposedPrice} | 
            <strong>Disputed:</strong> ${isDisputed ? 'Yes' : 'No'} | 
            <strong>Correct:</strong> ${correctnessText} | 
            <strong>Runs Executed:</strong> ${runCount}
        </div>
    `;
    
    // Add tags section if available
    // Check all potential locations for tags
    const tags = data.tags || data.proposal_metadata?.tags || (data.market_data ? data.market_data.tags : null);
    if (tags && Array.isArray(tags) && tags.length > 0) {
        content += `
            <div class="mb-3">
                <strong>Tags:</strong> 
                ${tags.map(tag => `<span class="tag-badge">${tag}</span>`).join('')}
            </div>
        `;
    }
    
    // Add overview section with clickable query ID for copying
    // Handle data from different potential locations
    const query_id = data.query_id || '';
    const short_id = data.question_id_short || data.short_id || '';
    const condition_id = data.condition_id || data.proposal_metadata?.condition_id || (data.market_data ? data.market_data.condition_id : '');
    const process_time = data.timestamp || 0;
    const request_time = data.proposal_metadata?.request_transaction_block_time || 0;
    const expiration_time = data.proposal_metadata?.expiration_timestamp || 0;
    const end_date = data.end_date_iso || data.proposal_metadata?.end_date_iso || (data.market_data ? data.market_data.end_date_iso : 'N/A');
    const game_start_time = data.game_start_time || data.proposal_metadata?.game_start_time || (data.market_data ? data.market_data.game_start_time : null);
    
    content += `
        <div class="detail-section">
            <h4 class="section-title">Overview</h4>
            <div class="card">
                <div class="card-body p-0">
                    <table class="table meta-table mb-0">
                        <tr>
                            <th>Query ID</th>
                            <td>
                                <code class="code-font copy-to-clipboard" title="Click to copy" data-copy="${query_id}" id="copyQueryId">
                                    ${query_id || 'N/A'}
                                </code>
                                <span class="copy-feedback" id="copyFeedback" style="display:none;">Copied!</span>
                            </td>
                        </tr>
                        <tr>
                            <th>Short ID</th>
                            <td>
                                <code class="code-font copy-to-clipboard" title="Click to copy" data-copy="${short_id}" id="copyShortId">
                                    ${short_id || 'N/A'}
                                </code>
                            </td>
                        </tr>
                        <tr>
                            <th>Condition ID</th>
                            <td>
                                <code class="code-font copy-to-clipboard" title="Click to copy" data-copy="${condition_id}" id="copyConditionId">
                                    ${condition_id || 'N/A'}
                                </code>
                            </td>
                        </tr>
                        <tr>
                            <th>Process Time</th>
                            <td>${formatDate(process_time)}</td>
                        </tr>
                        <tr>
                            <th>Proposal Time</th>
                            <td>${formatDate(request_time)}</td>
                        </tr>
                        <tr>
                            <th>Expiration Time</th>
                            <td>${formatDate(expiration_time)}</td>
                        </tr>
                        <tr>
                            <th>End Date</th>
                            <td>${end_date}</td>
                        </tr>
                        ${game_start_time && game_start_time !== 'N/A' ? `
                        <tr>
                            <th>Game Start Time</th>
                            <td>${game_start_time}</td>
                        </tr>
                        ` : ''}
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // For format_version 2, add journey section with run tabs
    if (isFormatV2 && data.journey && Array.isArray(data.journey) && data.journey.length > 0) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Journey</h4>
        `;
        
        // Add run tabs if there are multiple runs
        if (runCount > 1) {
            content += `
                <ul class="nav nav-tabs run-tabs mb-3" id="runTabs" role="tablist">
            `;
            
            // Sort runs by run_iteration and timestamp
            const sortedRuns = allRuns.sort((a, b) => {
                const aRun = extractRunNumber(a);
                const bRun = extractRunNumber(b);
                if (aRun !== bRun) return aRun - bRun;
                return (a.timestamp || 0) - (b.timestamp || 0);
            });
            
            sortedRuns.forEach((run, index) => {
                const runIteration = extractRunNumber(run);
                const isActive = index === sortedRuns.length - 1; // Auto-select the most recent run (last in sorted array)
                const runTimestamp = formatDate(run.timestamp || run.unix_timestamp || 0);
                // Get the actual recommendation for this specific run
                const proposal = run.format_version === 2 
                    ? (run.result?.recommendation || run.proposed_price_outcome || 'N/A')
                    : (run.proposed_price_outcome || run.recommendation || 'N/A');
                
                content += `
                    <li class="nav-item" role="presentation">
                        <button class="nav-link ${isActive ? 'active' : ''}" 
                                id="run-${runIteration}-tab" 
                                data-bs-toggle="tab" 
                                data-bs-target="#run-${runIteration}-content" 
                                type="button" 
                                role="tab" 
                                aria-controls="run-${runIteration}-content" 
                                aria-selected="${isActive}">
                            Run ${runIteration} → ${proposal}
                            <small class="d-block text-muted">${runTimestamp}</small>
                        </button>
                    </li>
                `;
            });
            
            content += `
                </ul>
                <div class="tab-content run-tab-content" id="runTabContent">
            `;
            
            // Add content for each run
            sortedRuns.forEach((run, index) => {
                const runIteration = extractRunNumber(run);
                const isActive = index === sortedRuns.length - 1; // Auto-select the most recent run
                
                content += `
                    <div class="tab-pane fade ${isActive ? 'show active' : ''}" 
                         id="run-${runIteration}-content" 
                         role="tabpanel" 
                         aria-labelledby="run-${runIteration}-tab">
                        <div class="journey-timeline">
                            ${run.journey ? run.journey.map((step, stepIndex) => `
                                <div class="journey-step-card ${step.actor}-step">
                                    <div class="journey-step-header" data-step="${stepIndex}">
                                        <div class="step-info">
                                            <div class="step-number">${step.step}</div>
                                            <span class="step-actor">${formatActorName(step.actor)}</span>
                                            <span class="step-action">${formatActionName(step.action)}</span>
                                            ${step.routing_phase ? `<span class="step-phase">Phase ${step.routing_phase}</span>` : ''}
                                            ${step.attempt ? `<span class="step-attempt">Attempt ${step.attempt}</span>` : ''}
                                        </div>
                                    </div>
                                    <div class="journey-step-body" id="journey-step-body-${runIteration}-${stepIndex}">
                                        ${renderJourneyStepContent(step, `${runIteration}-${stepIndex}`)}
                                    </div>
                                </div>
                            `).join('') : '<p class="text-muted">No journey data available for this run.</p>'}
                        </div>
                        
                        ${run.result ? `
                            <div class="detail-section mt-4">
                                <h4 class="section-title">Run ${runIteration} Result</h4>
                                <div class="card">
                                    <div class="card-body">
                                        <div class="result-info">
                                            <div class="mb-2"><strong>Recommendation:</strong> ${run.result.recommendation || 'N/A'}</div>
                                            ${run.result.reason ? `<div class="mb-2"><strong>Reason:</strong> ${run.result.reason}</div>` : ''}
                                            ${run.result.market_alignment ? `<div class="mb-2"><strong>Market Alignment:</strong> ${run.result.market_alignment}</div>` : ''}
                                            ${run.result.attempted_solvers && run.result.attempted_solvers.length > 0 ? `
                                                <div class="mb-2">
                                                    <strong>Attempted Solvers:</strong>
                                                    ${run.result.attempted_solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('')}
                                                </div>
                                            ` : ''}
                                            ${run.result.routing_attempts ? `<div class="mb-2"><strong>Routing Attempts:</strong> ${run.result.routing_attempts}</div>` : ''}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        
                        
                        ${run.overseer_data || run.overseer_result ? `
                            <div class="detail-section mt-4">
                                <h4 class="section-title">Run ${runIteration} Overseer Data</h4>
                                <div class="card">
                                    <div class="card-body overseer-data">
                                        ${(run.overseer_data || run.overseer_result).attempts ? `<div><strong>Attempts:</strong> ${(run.overseer_data || run.overseer_result).attempts}</div>` : ''}
                                        ${(run.overseer_data || run.overseer_result).market_price_info ? `
                                            <div class="mt-2">
                                                <strong>Market Price Info:</strong> 
                                                <div class="market-price-info">${(run.overseer_data || run.overseer_result).market_price_info}</div>
                                            </div>
                                        ` : ''}
                                        
                                        ${(run.overseer_data || run.overseer_result).recommendation_journey && (run.overseer_data || run.overseer_result).recommendation_journey.length > 0 ? `
                                            <div class="mt-3">
                                                <strong>Recommendation Journey:</strong>
                                                <div class="recommendation-journey mt-2">
                                                    <div class="table-responsive">
                                                        <table class="table table-sm table-striped">
                                                            <thead>
                                                                <tr>
                                                                    <th>Attempt</th>
                                                                    <th>Recommendation</th>
                                                                    <th>Satisfaction</th>
                                                                    <th style="min-width: 200px; width: 40%;">Critique</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody>
                                                                ${(run.overseer_data || run.overseer_result).recommendation_journey.map((journey, jIdx) => `
                                                                    <tr>
                                                                        <td>${journey.attempt}</td>
                                                                        <td>${journey.perplexity_recommendation || journey.code_runner_recommendation || 'N/A'}</td>
                                                                        <td>${formatSatisfactionLevel(journey.overseer_satisfaction_level)}</td>
                                                                        <td class="critique-cell">
                                                                            <div class="critique-preview" id="critique-preview-${runIteration}-${jIdx}">
                                                                                ${journey.critique ? journey.critique.substring(0, 120) + (journey.critique.length > 120 ? '...' : '') : 'N/A'}
                                                                            </div>
                                                                            <div class="critique-full content-collapsible collapsed" id="critique-full-${runIteration}-${jIdx}">
                                                                                ${journey.critique || 'N/A'}
                                                                            </div>
                                                                            ${journey.critique && journey.critique.length > 120 ? `
                                                                                <button class="btn btn-sm btn-link toggle-critique-btn" 
                                                                                    data-preview="critique-preview-${runIteration}-${jIdx}" 
                                                                                    data-target="critique-full-${runIteration}-${jIdx}">
                                                                                    Show more
                                                                                </button>
                                                                            ` : ''}
                                                                        </td>
                                                                    </tr>
                                                                `).join('')}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                    </div>
                `;
            });
            
            content += `
                </div>
            `;
        } else {
            // Single run - show journey directly
            content += `
                <div class="journey-timeline">
                    ${data.journey.map((step, stepIndex) => `
                        <div class="journey-step-card ${step.actor}-step">
                            <div class="journey-step-header" data-step="${stepIndex}">
                                <div class="step-info">
                                    <div class="step-number">${step.step}</div>
                                    <span class="step-actor">${formatActorName(step.actor)}</span>
                                    <span class="step-action">${formatActionName(step.action)}</span>
                                    ${step.routing_phase ? `<span class="step-phase">Phase ${step.routing_phase}</span>` : ''}
                                    ${step.attempt ? `<span class="step-attempt">Attempt ${step.attempt}</span>` : ''}
                                </div>
                            </div>
                            <div class="journey-step-body" id="journey-step-body-${stepIndex}">
                                ${renderJourneyStepContent(step, stepIndex)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        content += `
            </div>
        `;
    }
    
    // Add result section for format_version 2 (only for single runs)
    // For multi-run scenarios, results are shown within each tab
    if (isFormatV2 && data.result && runCount === 1) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Result</h4>
                <div class="card">
                    <div class="card-body">
                        <div class="result-info">
                            <div class="mb-2"><strong>Recommendation:</strong> ${data.result.recommendation || 'N/A'}</div>
                            ${data.result.reason ? `<div class="mb-2"><strong>Reason:</strong> ${data.result.reason}</div>` : ''}
                            ${data.result.market_alignment ? `<div class="mb-2"><strong>Market Alignment:</strong> ${data.result.market_alignment}</div>` : ''}
                            ${data.result.attempted_solvers && data.result.attempted_solvers.length > 0 ? `
                                <div class="mb-2">
                                    <strong>Attempted Solvers:</strong>
                                    ${data.result.attempted_solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('')}
                                </div>
                            ` : ''}
                            ${data.result.routing_attempts ? `<div class="mb-2"><strong>Routing Attempts:</strong> ${data.result.routing_attempts}</div>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add market data section for format_version 2
    if (isFormatV2 && data.market_data) {
        const marketData = data.market_data;
        content += `
            <div class="detail-section">
                <h4 class="section-title">Market Data</h4>
                <div class="card">
                    <div class="card-body">
                        <div class="market-info">
                            ${marketData.proposed_price !== null ? `<div class="mb-2"><strong>Proposed Price:</strong> ${marketData.proposed_price}</div>` : ''}
                            ${marketData.resolved_price !== null ? `<div class="mb-2"><strong>Resolved Price:</strong> ${marketData.resolved_price}</div>` : ''}
                            ${marketData.proposed_price_outcome ? `<div class="mb-2"><strong>Proposed Price Outcome:</strong> ${marketData.proposed_price_outcome}</div>` : ''}
                            ${marketData.resolved_price_outcome ? `<div class="mb-2"><strong>Resolved Price Outcome:</strong> ${marketData.resolved_price_outcome}</div>` : ''}
                            ${marketData.disputed !== undefined ? `<div class="mb-2"><strong>Disputed:</strong> ${marketData.disputed ? 'Yes' : 'No'}</div>` : ''}
                            ${marketData.icon ? `<div class="mb-2"><strong>Icon:</strong> <img src="${marketData.icon}" alt="Market Icon" class="market-icon"></div>` : ''}
                            
                            ${marketData.tokens && marketData.tokens.length > 0 ? `
                                <div class="mt-3">
                                    <strong>Tokens:</strong>
                                    <div class="table-responsive mt-2">
                                        <table class="table table-sm table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Outcome</th>
                                                    <th>Price</th>
                                                    <th>Winner</th>
                                                    <th>Token ID</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${marketData.tokens.map(token => `
                                                    <tr>
                                                        <td>${token.outcome}</td>
                                                        <td>${token.price}</td>
                                                        <td>${token.winner ? 'Yes' : 'No'}</td>
                                                        <td><small class="code-font">${token.token_id}</small></td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            ` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Add multi-operator data section if available
    if (!isFormatV2 && (data.router_result || data.attempted_solvers)) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Multi-Operator Processing</h4>
                <div class="multi-operator-section">
        `;
        
        // Add attempted solvers
        if (data.attempted_solvers && Array.isArray(data.attempted_solvers)) {
            content += `
                <div class="mb-3">
                    <strong>Attempted Solvers:</strong> 
                    ${data.attempted_solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('')}
                </div>
                <div class="mb-3">
                    <strong>Routing Attempts:</strong> ${data.routing_attempts || 1}
                </div>
            `;
        }
        
        // Add router prompt if available
        if (data.router_prompt) {
            content += `
                <div class="card mb-3">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <strong>Router Prompt</strong>
                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="router-prompt-content">
                            <i class="bi bi-arrows-expand"></i> Toggle
                        </button>
                    </div>
                    <div class="card-body content-collapsible collapsed" id="router-prompt-content">
                        <pre class="router-prompt-text">${data.router_prompt}</pre>
                    </div>
                </div>
            `;
        }
        
        // Add router result
        if (data.router_result) {
            const routerResult = data.router_result;
            content += `
                <div class="card mb-3">
                    <div class="card-header">
                        <strong>Router Decision</strong>
                    </div>
                    <div class="card-body">
                        <div class="mb-2">
                            <strong>Selected Solvers:</strong> 
                            ${routerResult.solvers ? routerResult.solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('') : 'N/A'}
                        </div>
                        ${routerResult.reason ? `
                            <div class="router-reason">
                                <strong>Reason:</strong> ${routerResult.reason}
                            </div>
                        ` : ''}
                        ${routerResult.multi_solver_strategy ? `
                            <div class="mt-2">
                                <strong>Multi-Solver Strategy:</strong> ${routerResult.multi_solver_strategy}
                            </div>
                        ` : ''}
                        
                        ${routerResult.prompt ? `
                            <div class="mt-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong>Router Prompt Data:</strong>
                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="router-prompt-data">
                                        <i class="bi bi-arrows-expand"></i> Toggle
                                    </button>
                                </div>
                                <pre class="router-prompt-data mt-2 content-collapsible collapsed" id="router-prompt-data">${formatCodeBlocks(routerResult.prompt)}</pre>
                            </div>
                        ` : ''}
                        
                        ${routerResult.response ? `
                            <div class="mt-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong>Router Response:</strong>
                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="router-response-content">
                                        <i class="bi bi-arrows-expand"></i> Toggle
                                    </button>
                                </div>
                                <pre class="router-response mt-2 content-collapsible collapsed" id="router-response-content">${formatCodeBlocks(routerResult.response)}</pre>
                            </div>
                        ` : ''}
                    </div>
                </div>
            `;
        }
        
        // Add solver results
        if ((data.solver_results && Array.isArray(data.solver_results) && data.solver_results.length > 0) || 
            (data.all_solver_results && Array.isArray(data.all_solver_results) && data.all_solver_results.length > 0)) {
            content += `<h5 class="mb-3">Solver Results</h5>`;
            
            // Create a merged array of solver results
            const solverResultsToRender = [];
            
            // First add all solver_results if available
            if (data.solver_results && Array.isArray(data.solver_results) && data.solver_results.length > 0) {
                // Add a source property to each result
                data.solver_results.forEach(result => {
                    solverResultsToRender.push({
                        ...result,
                        _resultSource: 'solver_results'
                    });
                });
            }
            
            // Then add all_solver_results that aren't already included
            if (data.all_solver_results && Array.isArray(data.all_solver_results) && data.all_solver_results.length > 0) {
                data.all_solver_results.forEach(result => {
                    // Check if this solver result is already in the array
                    const isDuplicate = solverResultsToRender.some(existingResult => 
                        existingResult.solver === result.solver && 
                        existingResult.attempt === result.attempt
                    );
                    
                    if (!isDuplicate) {
                        solverResultsToRender.push({
                            ...result,
                            _resultSource: 'all_solver_results'
                        });
                    }
                });
            }
            
            solverResultsToRender.forEach((solverResult, index) => {
                const executionStatus = solverResult.execution_successful === true ? 
                    '<span class="execution-successful"><i class="bi bi-check-circle-fill"></i> Success</span>' : 
                    '<span class="execution-failed"><i class="bi bi-x-circle-fill"></i> Failed</span>';
                
                content += `
                    <div class="solver-card">
                        <div class="solver-header">
                            <div class="solver-name">${solverResult.solver || 'Unknown Solver'}</div>
                            <div class="d-flex align-items-center">
                                <div class="solver-attempt me-3">Attempt ${solverResult.attempt || index + 1}</div>
                                <div class="me-3">${executionStatus}</div>
                                ${solverResult._resultSource ? `<div><small class="source-badge ${solverResult._resultSource === 'all_solver_results' ? 'all-solvers-badge' : 'primary-solver-badge'}">${solverResult._resultSource === 'all_solver_results' ? 'Additional Result' : 'Primary Result'}</small></div>` : ''}
                            </div>
                        </div>
                        <div class="solver-body">
                            <div><strong>Recommendation:</strong> ${solverResult.recommendation || 'N/A'}</div>
                            
                            ${solverResult.response ? `
                                <div class="mt-2">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong>Response:</strong>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-response-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <pre class="response-text mt-2 content-collapsible collapsed" id="solver-response-${index}">${formatCodeBlocks(solverResult.response)}</pre>
                                </div>
                            ` : ''}
                            
                            ${solverResult.code_generation_prompt || solverResult.solver_result?.code_generation_prompt || solverResult.code_runner_prompt ? `
                                <div class="mt-2">
                                    <div class="d-flex justify-content-between align-items-center">
                                        <strong>Code Generation Prompt:</strong>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="code-generation-prompt-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <pre class="response-text mt-2 content-collapsible" id="code-generation-prompt-${index}">${formatCodeBlocks(solverResult.code_generation_prompt || solverResult.solver_result?.code_generation_prompt || solverResult.code_runner_prompt)}</pre>
                                </div>
                                <script>
                                // Mark these fields as already handled to prevent duplicate display
                                if (solverResult.solver_result) {
                                    if (solverResult.solver_result.code_generation_prompt) {
                                        delete solverResult.solver_result.code_generation_prompt;
                                    }
                                    if (solverResult.solver_result.code_runner_prompt) {
                                        delete solverResult.solver_result.code_runner_prompt;
                                    }
                                }
                                </script>
                            ` : ''}
                            
                            ${solverResult.solver_result && solverResult.solver_result.code ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Generated Code</span>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-code-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <div class="code-content content-collapsible collapsed" id="solver-code-${index}">
                                        <pre><code class="language-python">${solverResult.solver_result.code}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.code ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Generated Code</span>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="code-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <div class="code-content content-collapsible collapsed" id="code-${index}">
                                        <pre><code class="language-python">${solverResult.code}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.code_output ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Code Output</span>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="code-output-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <div class="code-content content-collapsible collapsed" id="code-output-${index}">
                                        <pre><code class="language-plaintext">${solverResult.code_output}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.solver_result && solverResult.solver_result.code_output ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Code Output</span>
                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="sr-code-output-${index}">
                                            <i class="bi bi-arrows-expand"></i> Toggle
                                        </button>
                                    </div>
                                    <div class="code-content content-collapsible collapsed" id="sr-code-output-${index}">
                                        <pre><code class="language-plaintext">${solverResult.solver_result.code_output}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.overseer_result ? `
                                <div class="mt-3">
                                    <strong>Overseer Evaluation:</strong>
                                    <div class="overseer-details mt-2">
                                        <div><strong>Decision:</strong> ${solverResult.overseer_result.decision?.verdict || solverResult.overseer_result.verdict || 'N/A'}</div>
                                        <div class="mt-1"><strong>Reason:</strong> ${solverResult.overseer_result.decision?.reason || solverResult.overseer_result.reason || 'N/A'}</div>
                                        ${solverResult.overseer_result.decision?.critique || solverResult.overseer_result.critique ? `
                                            <div class="mt-1"><strong>Critique:</strong> ${solverResult.overseer_result.decision?.critique || solverResult.overseer_result.critique}</div>
                                        ` : ''}
                                        ${solverResult.overseer_result.decision?.market_alignment ? `
                                            <div class="mt-1"><strong>Market Alignment:</strong> ${solverResult.overseer_result.decision?.market_alignment}</div>
                                        ` : ''}
                                        ${solverResult.overseer_result.decision?.prompt_update ? `
                                            <div class="mt-1"><strong>Prompt Update:</strong> ${solverResult.overseer_result.decision?.prompt_update}</div>
                                        ` : ''}
                                        
                                        ${solverResult.overseer_result.prompt ? `
                                            <div class="mt-3">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <strong>Overseer Prompt:</strong>
                                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-prompt-${index}">
                                                        <i class="bi bi-arrows-expand"></i> Toggle
                                                    </button>
                                                </div>
                                                <pre class="overseer-prompt mt-2 content-collapsible collapsed" id="overseer-prompt-${index}">${formatCodeBlocks(solverResult.overseer_result.prompt)}</pre>
                                            </div>
                                        ` : ''}
                                        
                                        ${solverResult.overseer_result.response ? `
                                            <div class="mt-3">
                                                <div class="d-flex justify-content-between align-items-center">
                                                    <strong>Overseer Response:</strong>
                                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-response-${index}">
                                                        <i class="bi bi-arrows-expand"></i> Toggle
                                                    </button>
                                                </div>
                                                <pre class="overseer-response mt-2 content-collapsible collapsed" id="overseer-response-${index}">${formatCodeBlocks(solverResult.overseer_result.response)}</pre>
                                            </div>
                                        ` : ''}
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.response_metadata ? `
                                <div class="mt-3">
                                    <strong>Response Metadata:</strong>
                                    <div class="card mt-2">
                                        <div class="card-body p-0">
                                            <table class="table meta-table mb-0">
                                                ${Object.entries(solverResult.response_metadata).map(([key, value]) => `
                                                    <tr>
                                                        <th>${formatKeyName(key)}</th>
                                                        <td>${formatValue(value, key)}</td>
                                                    </tr>
                                                `).join('')}
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${/* Display all other solver_result fields not already displayed */ ''}
                            ${solverResult.solver_result && typeof solverResult.solver_result === 'object' ? 
                                Object.entries(solverResult.solver_result)
                                    .filter(([key, _]) => !['code', 'code_output', 'recommendation', 'response', 'solver', 'overseer_result', 'response_metadata'].includes(key))
                                    .map(([key, value]) => `
                                        <div class="mt-3">
                                            <strong>${formatKeyName(key)}:</strong>
                                            <div class="mt-2">${formatValue(value, key)}</div>
                                        </div>
                                    `).join('') : ''}
                        </div>
                    </div>
                `;
            });
            
            content += `</div></div>`;
        }
        
        // Add all_solver_results if they exist and there are results not shown in solver_results
        if (data.all_solver_results && Array.isArray(data.all_solver_results) && data.all_solver_results.length > 0) {
            // Check if solver_results already contains all of these results
            const solverResultsIds = (data.solver_results && Array.isArray(data.solver_results)) 
                ? data.solver_results.map(sr => `${sr.solver}_${sr.attempt}`) 
                : [];
                
            // Filter all_solver_results to only show those not already displayed
            const additionalResults = data.all_solver_results.filter(asr => 
                !solverResultsIds.includes(`${asr.solver}_${asr.attempt}`)
            );
            
            if (additionalResults.length > 0) {
                content += `<h5 class="mb-3 mt-4">Additional Solver Results</h5>`;
                
                additionalResults.forEach((solverResult, index) => {
                    const executionStatus = solverResult.execution_successful === true ? 
                        '<span class="execution-successful"><i class="bi bi-check-circle-fill"></i> Success</span>' : 
                        '<span class="execution-failed"><i class="bi bi-x-circle-fill"></i> Failed</span>';
                    
                    content += `
                        <div class="solver-card">
                            <div class="solver-header">
                                <div class="solver-name">${solverResult.solver || 'Unknown Solver'}</div>
                                <div class="d-flex align-items-center">
                                    <div class="solver-attempt me-3">Attempt ${solverResult.attempt || index + 1}</div>
                                    <div class="me-3">${executionStatus}</div>
                                    <div><small class="source-badge all-solvers-badge">Additional Result</small></div>
                                </div>
                            </div>
                            <div class="solver-body">
                                <div><strong>Recommendation:</strong> ${solverResult.recommendation || 'N/A'}</div>
                                
                                ${solverResult.response ? `
                                    <div class="mt-2">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <strong>Response:</strong>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-solver-response-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <pre class="response-text mt-2 content-collapsible collapsed" id="add-solver-response-${index}">${formatCodeBlocks(solverResult.response)}</pre>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.code_generation_prompt || solverResult.solver_result?.code_generation_prompt || solverResult.code_runner_prompt ? `
                                    <div class="mt-2">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <strong>Code Generation Prompt:</strong>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-code-generation-prompt-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <pre class="response-text mt-2 content-collapsible" id="add-code-generation-prompt-${index}">${formatCodeBlocks(solverResult.code_generation_prompt || solverResult.solver_result?.code_generation_prompt || solverResult.code_runner_prompt)}</pre>
                                    </div>
                                    <script>
                                    // Mark these fields as already handled to prevent duplicate display
                                    if (solverResult.solver_result) {
                                        if (solverResult.solver_result.code_generation_prompt) {
                                            delete solverResult.solver_result.code_generation_prompt;
                                        }
                                        if (solverResult.solver_result.code_runner_prompt) {
                                            delete solverResult.solver_result.code_runner_prompt;
                                        }
                                    }
                                    </script>
                                ` : ''}
                                
                                ${solverResult.solver_result && solverResult.solver_result.code ? `
                                    <div class="code-section">
                                        <div class="code-header">
                                            <span>Generated Code</span>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-solver-code-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <div class="code-content content-collapsible collapsed" id="add-solver-code-${index}">
                                            <pre><code class="language-python">${solverResult.solver_result.code}</code></pre>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.code ? `
                                    <div class="code-section">
                                        <div class="code-header">
                                            <span>Generated Code</span>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-code-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <div class="code-content content-collapsible collapsed" id="add-code-${index}">
                                            <pre><code class="language-python">${solverResult.code}</code></pre>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.code_output ? `
                                    <div class="code-section">
                                        <div class="code-header">
                                            <span>Code Output</span>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-code-output-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <div class="code-content content-collapsible collapsed" id="add-code-output-${index}">
                                            <pre><code class="language-plaintext">${solverResult.code_output}</code></pre>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.solver_result && solverResult.solver_result.code_output ? `
                                    <div class="code-section">
                                        <div class="code-header">
                                            <span>Code Output</span>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-sr-code-output-${index}">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <div class="code-content content-collapsible collapsed" id="add-sr-code-output-${index}">
                                            <pre><code class="language-plaintext">${solverResult.solver_result.code_output}</code></pre>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.overseer_result ? `
                                    <div class="mt-3">
                                        <strong>Overseer Evaluation:</strong>
                                        <div class="overseer-details mt-2">
                                            <div><strong>Decision:</strong> ${solverResult.overseer_result.decision?.verdict || solverResult.overseer_result.verdict || 'N/A'}</div>
                                            <div class="mt-1"><strong>Reason:</strong> ${solverResult.overseer_result.decision?.reason || solverResult.overseer_result.reason || 'N/A'}</div>
                                            ${solverResult.overseer_result.decision?.critique || solverResult.overseer_result.critique ? `
                                                <div class="mt-1"><strong>Critique:</strong> ${solverResult.overseer_result.decision?.critique || solverResult.overseer_result.critique}</div>
                                            ` : ''}
                                            ${solverResult.overseer_result.decision?.market_alignment ? `
                                                <div class="mt-1"><strong>Market Alignment:</strong> ${solverResult.overseer_result.decision?.market_alignment}</div>
                                            ` : ''}
                                            ${solverResult.overseer_result.decision?.prompt_update ? `
                                                <div class="mt-1"><strong>Prompt Update:</strong> ${solverResult.overseer_result.decision?.prompt_update}</div>
                                            ` : ''}
                                            
                                            ${solverResult.overseer_result.prompt ? `
                                                <div class="mt-3">
                                                    <div class="d-flex justify-content-between align-items-center">
                                                        <strong>Overseer Prompt:</strong>
                                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-overseer-prompt-${index}">
                                                            <i class="bi bi-arrows-expand"></i> Toggle
                                                        </button>
                                                    </div>
                                                    <pre class="overseer-prompt mt-2 content-collapsible collapsed" id="add-overseer-prompt-${index}">${formatCodeBlocks(solverResult.overseer_result.prompt)}</pre>
                                                </div>
                                            ` : ''}
                                            
                                            ${solverResult.overseer_result.response ? `
                                                <div class="mt-3">
                                                    <div class="d-flex justify-content-between align-items-center">
                                                        <strong>Overseer Response:</strong>
                                                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="add-overseer-response-${index}">
                                                            <i class="bi bi-arrows-expand"></i> Toggle
                                                        </button>
                                                    </div>
                                                    <pre class="overseer-response mt-2 content-collapsible collapsed" id="add-overseer-response-${index}">${formatCodeBlocks(solverResult.overseer_result.response)}</pre>
                                                </div>
                                            ` : ''}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${solverResult.response_metadata ? `
                                    <div class="mt-3">
                                        <strong>Response Metadata:</strong>
                                        <div class="card mt-2">
                                            <div class="card-body p-0">
                                                <table class="table meta-table mb-0">
                                                    ${Object.entries(solverResult.response_metadata).map(([key, value]) => `
                                                        <tr>
                                                            <th>${formatKeyName(key)}</th>
                                                            <td>${formatValue(value, key)}</td>
                                                        </tr>
                                                    `).join('')}
                                                </table>
                                            </div>
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${/* Display all other solver_result fields not already displayed */ ''}
                                ${solverResult.solver_result && typeof solverResult.solver_result === 'object' ? 
                                    Object.entries(solverResult.solver_result)
                                        .filter(([key, _]) => !['code', 'code_output', 'recommendation', 'response', 'solver', 'overseer_result', 'response_metadata'].includes(key))
                                        .map(([key, value]) => `
                                            <div class="mt-3">
                                                <strong>${formatKeyName(key)}:</strong>
                                                <div class="mt-2">${formatValue(value, key)}</div>
                                            </div>
                                        `).join('') : ''}
                            </div>
                        </div>
                    `;
                });
            }
        }
    }
    
    // Add overseer section for both old and new file structures
    // Only show for single runs, as multi-runs have per-tab overseer data
    const overseerData = data.overseer_data || data.overseer_result || null;
    
    if (overseerData && runCount === 1) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Overseer Data</h4>
                <div class="card">
                    <div class="card-body overseer-data">
                        ${overseerData.attempts ? `<div><strong>Attempts:</strong> ${overseerData.attempts}</div>` : ''}
                        ${overseerData.market_price_info ? `
                            <div class="mt-2">
                                <strong>Market Price Info:</strong> 
                                <div class="market-price-info">${overseerData.market_price_info}</div>
                            </div>
                        ` : ''}
                        
                        ${/* Add overseer prompt if available */
                        data.overseer_prompt || data.solver_1_overseer_prompt ? `
                            <div class="mt-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong>Overseer Prompt:</strong>
                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="main-overseer-prompt">
                                        <i class="bi bi-arrows-expand"></i> Toggle
                                    </button>
                                </div>
                                <pre class="overseer-prompt mt-2 content-collapsible collapsed" id="main-overseer-prompt">${formatCodeBlocks(data.overseer_prompt || data.solver_1_overseer_prompt)}</pre>
                            </div>
                        ` : ''}
                        
                        ${/* Add tokens section if present */
                        overseerData.tokens && overseerData.tokens.length > 0 ?
                        `
                            <div class="mt-3">
                                <strong>Tokens:</strong>
                                <div class="table-responsive mt-2">
                                    <table class="table table-sm table-striped">
                                        <thead>
                                            <tr>
                                                <th>Outcome</th>
                                                <th>Price</th>
                                                <th>Winner</th>
                                                <th>Token ID</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${overseerData.tokens.map(token => `
                                                <tr>
                                                    <td>${token.outcome}</td>
                                                    <td>${token.price}</td>
                                                    <td>${token.winner ? 'Yes' : 'No'}</td>
                                                    <td><small class="code-font">${token.token_id}</small></td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ` : ''}
                        
                        ${/* Display tokens from proposal_metadata as fallback */
                        !overseerData.tokens?.length && (data.proposal_metadata?.tokens?.length || data.tokens?.length) ?
                        `
                            <div class="mt-3">
                                <strong>Tokens:</strong>
                                <div class="table-responsive mt-2">
                                    <table class="table table-sm table-striped">
                                        <thead>
                                            <tr>
                                                <th>Outcome</th>
                                                <th>Price</th>
                                                <th>Winner</th>
                                                <th>Token ID</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${(data.tokens?.length ? data.tokens : data.proposal_metadata?.tokens).map(token => `
                                                <tr>
                                                    <td>${token.outcome}</td>
                                                    <td>${token.price}</td>
                                                    <td>${token.winner ? 'Yes' : 'No'}</td>
                                                    <td><small class="code-font">${token.token_id}</small></td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ` : ''}
                        
                        ${/* Display neg_risk_market_id if present */
                        data.neg_risk_market_id ? `
                            <div class="mt-3">
                                <strong>Negative Risk Market ID:</strong> ${data.neg_risk_market_id}
                            </div>
                        ` : overseerData.neg_risk_market_id ? `
                            <div class="mt-3">
                                <strong>Negative Risk Market ID:</strong> ${overseerData.neg_risk_market_id}
                            </div>
                        ` : data.proposal_metadata?.neg_risk_market_id ? `
                            <div class="mt-3">
                                <strong>Negative Risk Market ID:</strong> ${data.proposal_metadata.neg_risk_market_id}
                            </div>
                        ` : ''}
                        
                        ${overseerData.recommendation_journey && overseerData.recommendation_journey.length > 0 ? `
                            <div class="mt-3">
                                <strong>Recommendation Journey:</strong>
                                <div class="recommendation-journey mt-2">
                                    <div class="table-responsive">
                                        <table class="table table-sm table-striped">
                                            <thead>
                                                <tr>
                                                    <th>Attempt</th>
                                                    <th>Recommendation</th>
                                                    <th>Satisfaction</th>
                                                    <th style="min-width: 200px; width: 40%;">Critique</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${overseerData.recommendation_journey.map((journey, jIdx) => `
                                                    <tr>
                                                        <td>${journey.attempt}</td>
                                                        <td>${journey.perplexity_recommendation || 'N/A'}</td>
                                                        <td>${formatSatisfactionLevel(journey.overseer_satisfaction_level)}</td>
                                                        <td class="critique-cell">
                                                            <div class="critique-preview" id="critique-preview-${jIdx}">
                                                                ${journey.critique ? journey.critique.substring(0, 120) + (journey.critique.length > 120 ? '...' : '') : 'N/A'}
                                                            </div>
                                                            <div class="critique-full content-collapsible collapsed" id="critique-full-${jIdx}">
                                                                ${journey.critique || 'N/A'}
                                                            </div>
                                                            ${journey.critique && journey.critique.length > 120 ? `
                                                                <button class="btn btn-sm btn-link toggle-critique-btn" 
                                                                    data-preview="critique-preview-${jIdx}" 
                                                                    data-target="critique-full-${jIdx}">
                                                                    Show more
                                                                </button>
                                                            ` : ''}
                                                        </td>
                                                    </tr>
                                                `).join('')}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        ` : ''}
                        
                        ${/* Add interactions if available */
                        overseerData.interactions && overseerData.interactions.length > 0 ? `
                            <div class="mt-3">
                                <strong>Interactions:</strong>
                                <div class="accordion mt-2" id="interactionsAccordion">
                                    ${overseerData.interactions.map((interaction, i) => `
                                        <div class="accordion-item">
                                            <h2 class="accordion-header" id="interactionHeading${i}">
                                                <button class="accordion-button collapsed" type="button" data-bs-toggle="collapse" data-bs-target="#interactionCollapse${i}" aria-expanded="false" aria-controls="interactionCollapse${i}">
                                                    Attempt ${interaction.attempt} - ${formatStageName(interaction.stage)}
                                                </button>
                                            </h2>
                                            <div id="interactionCollapse${i}" class="accordion-collapse collapse" aria-labelledby="interactionHeading${i}" data-bs-parent="#interactionsAccordion">
                                                <div class="accordion-body">
                                                    <div class="mb-2"><strong>Interaction Type:</strong> ${interaction.interaction_type || 'N/A'}</div>
                                                    ${interaction.recommendation ? `<div class="mb-2"><strong>Recommendation:</strong> ${interaction.recommendation}</div>` : ''}
                                                    ${interaction.response ? `
                                                        <div class="mb-2">
                                                            <div class="d-flex justify-content-between align-items-center">
                                                                <strong>Response:</strong>
                                                                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="interaction-response-${i}">
                                                                    <i class="bi bi-arrows-expand"></i> Toggle
                                                                </button>
                                                            </div>
                                                            <pre class="response-text mt-2 content-collapsible collapsed" id="interaction-response-${i}">${formatCodeBlocks(interaction.response)}</pre>
                                                        </div>
                                                    ` : ''}
                                                    ${interaction.metadata ? `
                                                        <div class="mt-3">
                                                            <div class="d-flex justify-content-between align-items-center">
                                                                <strong>Metadata:</strong>
                                                                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="interaction-metadata-${i}">
                                                                    <i class="bi bi-arrows-expand"></i> Toggle
                                                                </button>
                                                            </div>
                                                            <pre class="mt-2 metadata-json content-collapsible collapsed" id="interaction-metadata-${i}">${JSON.stringify(interaction.metadata, null, 2)}</pre>
                                                        </div>
                                                    ` : ''}
                                                </div>
                                            </div>
                                        </div>
                                    `).join('')}
                                </div>
                            </div>
                        ` : ''}
                        
                        ${/* Show overseer decision data if available */
                        overseerData.decision ? `
                            <div class="mt-3">
                                <strong>Overseer Decision:</strong>
                                <div class="card mt-2">
                                    <div class="card-body p-0">
                                        <table class="table meta-table mb-0">
                                            <tr>
                                                <th>Verdict</th>
                                                <td>${overseerData.decision.verdict || 'N/A'}</td>
                                            </tr>
                                            <tr>
                                                <th>Reason</th>
                                                <td>${overseerData.decision.reason || 'N/A'}</td>
                                            </tr>
                                            ${overseerData.decision.critique ? `
                                                <tr>
                                                    <th>Critique</th>
                                                    <td>${overseerData.decision.critique}</td>
                                                </tr>
                                            ` : ''}
                                            ${overseerData.decision.market_alignment ? `
                                                <tr>
                                                    <th>Market Alignment</th>
                                                    <td>${overseerData.decision.market_alignment}</td>
                                                </tr>
                                            ` : ''}
                                            ${overseerData.decision.prompt_update ? `
                                                <tr>
                                                    <th>Prompt Update</th>
                                                    <td>${overseerData.decision.prompt_update}</td>
                                                </tr>
                                            ` : ''}
                                        </table>
                                    </div>
                                </div>
                                
                                ${overseerData.decision.response ? `
                                    <div class="mt-3">
                                        <div class="d-flex justify-content-between align-items-center">
                                            <strong>Decision Response:</strong>
                                            <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="decision-response">
                                                <i class="bi bi-arrows-expand"></i> Toggle
                                            </button>
                                        </div>
                                        <pre class="overseer-response mt-2 content-collapsible collapsed" id="decision-response">${formatCodeBlocks(overseerData.decision.response)}</pre>
                                    </div>
                                ` : ''}
                            </div>
                        ` : ''}
                        
                        ${/* Show overseer response if available at root level */
                        overseerData.response && !overseerData.decision?.response ? `
                            <div class="mt-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <strong>Overseer Response:</strong>
                                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-root-response">
                                        <i class="bi bi-arrows-expand"></i> Toggle
                                    </button>
                                </div>
                                <pre class="overseer-response mt-2 content-collapsible collapsed" id="overseer-root-response">${formatCodeBlocks(overseerData.response)}</pre>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add proposal_metadata section if available
    if (data.proposal_metadata) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Proposal Metadata</h4>
                <div class="card">
                    <div class="card-body p-0">
                        <table class="table meta-table mb-0">
                            ${data.proposal_metadata.transaction_hash ? `
                                <tr>
                                    <th>Transaction Hash</th>
                                    <td>${createTxLink(data.proposal_metadata.transaction_hash)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.block_number ? `
                                <tr>
                                    <th>Block Number</th>
                                    <td><a href="https://polygonscan.com/block/${data.proposal_metadata.block_number}" target="_blank">${data.proposal_metadata.block_number}</a></td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.creator ? `
                                <tr>
                                    <th>Creator</th>
                                    <td>${createAddressLink(data.proposal_metadata.creator)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.proposer ? `
                                <tr>
                                    <th>Proposer</th>
                                    <td>${createAddressLink(data.proposal_metadata.proposer)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.bond_currency ? `
                                <tr>
                                    <th>Bond Currency</th>
                                    <td>${createAddressLink(data.proposal_metadata.bond_currency)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.proposal_bond ? `
                                <tr>
                                    <th>Proposal Bond</th>
                                    <td>${formatBond(data.proposal_metadata.proposal_bond)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.reward_amount ? `
                                <tr>
                                    <th>Reward Amount</th>
                                    <td>${formatBond(data.proposal_metadata.reward_amount)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.request_timestamp ? `
                                <tr>
                                    <th>Request Time</th>
                                    <td>${formatDate(data.proposal_metadata.request_timestamp)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.expiration_timestamp ? `
                                <tr>
                                    <th>Expiration Time</th>
                                    <td>${formatDate(data.proposal_metadata.expiration_timestamp)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.request_transaction_block_time ? `
                                <tr>
                                    <th>Block Time</th>
                                    <td>${formatDate(data.proposal_metadata.request_transaction_block_time)}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.resolution_conditions ? `
                                <tr>
                                    <th>Resolution Conditions</th>
                                    <td>${data.proposal_metadata.resolution_conditions}</td>
                                </tr>
                            ` : ''}
                            ${data.proposal_metadata.ancillary_data ? `
                                <tr>
                                    <th>Ancillary Data</th>
                                    <td>
                                        <div class="ancillary-data">${data.proposal_metadata.ancillary_data}</div>
                                    </td>
                                </tr>
                            ` : ''}
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add tokens section if available at root level and not already displayed
    const tokensAlreadyDisplayed = 
        (overseerData?.tokens && overseerData.tokens.length > 0) || 
        (overseerData && (data.proposal_metadata?.tokens?.length > 0 || data.tokens?.length > 0));
    
    if (data.tokens && data.tokens.length > 0 && !tokensAlreadyDisplayed) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Tokens</h4>
                <div class="card">
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm table-striped">
                                <thead>
                                    <tr>
                                        <th>Outcome</th>
                                        <th>Price</th>
                                        <th>Winner</th>
                                        <th>Token ID</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.tokens.map(token => `
                                        <tr>
                                            <td>${token.outcome}</td>
                                            <td>${token.price}</td>
                                            <td>${token.winner ? 'Yes' : 'No'}</td>
                                            <td><small class="code-font">${token.token_id}</small></td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Use the new function for JSON folding instead of simple pre tag
    content = addJsonDataSection(content, data);
    
    // Set the modal content
    modalBody.innerHTML = content;
    
    // Apply syntax highlighting to code blocks
    Prism.highlightAllUnder(modalBody);
    
    // Initialize toggle buttons for code sections
    document.querySelectorAll('.toggle-content-btn').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement.classList.contains('collapsed')) {
                targetElement.classList.remove('collapsed');
                this.innerHTML = `<i class="bi bi-arrows-collapse"></i> Hide`;
            } else {
                targetElement.classList.add('collapsed');
                this.innerHTML = `<i class="bi bi-arrows-expand"></i> ${this.textContent.replace('Hide', 'Show')}`;
            }
            
            // Re-apply syntax highlighting when showing code
            if (!targetElement.classList.contains('collapsed') && 
                (targetElement.classList.contains('language-python') || 
                 targetElement.querySelector('.language-python'))) {
                Prism.highlightElement(targetElement.querySelector('code') || targetElement);
            }
        });
    });
    
    // Add click event for copying to clipboard
    document.querySelectorAll('.copy-to-clipboard').forEach(element => {
        element.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (!textToCopy) return;
            
            // Copy to clipboard
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Show feedback
                const feedback = document.getElementById('copyFeedback');
                if (feedback) {
                    feedback.style.display = 'inline';
                    setTimeout(() => {
                        feedback.style.display = 'none';
                    }, 2000);
                }
                
                // Highlight the element that was copied
                this.classList.add('copied');
                setTimeout(() => {
                    this.classList.remove('copied');
                }, 1000);
            });
        });
    });
    
    
    // Show the modal
    modal.show();
    
    // Add toggle functionality for the collapsible content
    document.querySelectorAll('.toggle-content-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                targetElement.classList.toggle('collapsed');
                
                // Update button icon
                const icon = this.querySelector('i');
                if (icon) {
                    if (targetElement.classList.contains('collapsed')) {
                        icon.classList.remove('bi-arrows-collapse');
                        icon.classList.add('bi-arrows-expand');
                    } else {
                        icon.classList.remove('bi-arrows-expand');
                        icon.classList.add('bi-arrows-collapse');
                    }
                }
            }
        });
    });
    
    
    // Add toggle functionality for journey steps
    document.querySelectorAll('.journey-step-header').forEach(header => {
        header.addEventListener('click', function() {
            const stepIndex = this.getAttribute('data-step');
            const stepBody = document.getElementById(`journey-step-body-${stepIndex}`);
            
            if (stepBody) {
                this.classList.toggle('collapsed');
                stepBody.classList.toggle('collapsed');
            }
        });
    });
    
    // Add toggle functionality for critique content
    document.querySelectorAll('.toggle-critique-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const previewId = this.getAttribute('data-preview');
            const targetId = this.getAttribute('data-target');
            const previewElement = document.getElementById(previewId);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement && previewElement) {
                targetElement.classList.toggle('collapsed');
                previewElement.classList.toggle('hidden');
                
                // Update button text
                if (targetElement.classList.contains('collapsed')) {
                    this.textContent = 'Show more';
                } else {
                    this.textContent = 'Show less';
                }
            }
        });
    });
    
    // Add toggle functionality for Full JSON Data
    document.querySelectorAll('.toggle-json-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const container = this.closest('.detail-section').querySelector('.json-data-container');
            
            if (container) {
                if (container.style.display === 'none') {
                    container.style.display = 'block';
                    this.innerHTML = '<i class="bi bi-arrows-collapse"></i> Hide';
                } else {
                    container.style.display = 'none';
                    this.innerHTML = '<i class="bi bi-arrows-expand"></i> Toggle';
                }
            }
        });
    });
}

// Extracts a title from all potential sources
function extractTitle(item) {
    // First try to extract from ancillary_data as it's the preferred source
    if (item.ancillary_data) {
        const ancillaryMatch = item.ancillary_data.match(/title:\s*([^,\n]+)/i);
        if (ancillaryMatch && ancillaryMatch[1]) {
            return ancillaryMatch[1].trim();
        }
    }
    
    // For format_version 2, try to extract from proposal_metadata.ancillary_data
    if (item.format_version === 2 && item.proposal_metadata?.ancillary_data) {
        const metadataAncillaryMatch = item.proposal_metadata.ancillary_data.match(/title:\s*([^,\n]+)/i);
        if (metadataAncillaryMatch && metadataAncillaryMatch[1]) {
            return metadataAncillaryMatch[1].trim();
        }
    }
    
    // Try to extract from user_prompt next
    if (item.user_prompt) {
        const titleMatch = item.user_prompt.match(/title:\s*([^,\n]+)/i);
        if (titleMatch && titleMatch[1]) {
            return titleMatch[1].trim();
        }
    }
    
    // Try to extract from prompt field
    if (item.prompt && typeof item.prompt === 'string') {
        const promptTitleMatch = item.prompt.match(/title:\s*([^,\n]+)/i);
        if (promptTitleMatch && promptTitleMatch[1]) {
            return promptTitleMatch[1].trim();
        }
    }
    
    // Check title field
    if (item.title && typeof item.title === 'string') {
        return item.title;
    }
    
    // Try experiment metadata fields (for MongoDB)
    if (item.experiment_title) {
        return item.experiment_title;
    }
    
    // Try metadata.experiment.title (for MongoDB)
    if (item.metadata?.experiment?.title) {
        return item.metadata.experiment.title;
    }
    
    // Fallback to proposal_data.prompt first line
    if (item.proposal_data?.prompt) {
        const firstLine = item.proposal_data.prompt.split('\n')[0] || '';
        return firstLine.substring(0, 50) + (firstLine.length > 50 ? '...' : '');
    }
    
    // Use question_id_short
    if (item.question_id_short) {
        return `Question ${item.question_id_short}`;
    }
    
    // Last resort: use query_id or filename
    if (item.query_id) {
        return `Query ${item.query_id.substring(0, 10)}`;
    }
    
    if (item.filename) {
        return item.filename;
    }
    
    // For MongoDB experiment ID as last resort
    if (item.experiment_id) {
        return `Experiment ${item.experiment_id}`;
    }
    
    return 'No title';
}

// Format a key name for display
function formatKeyName(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
}

// Format a value for display
function formatValue(value, key) {
    if (value === null || value === undefined) return 'N/A';
    
    // Special handling for ancillary_data_hex which is very long
    if (key === 'ancillary_data_hex' && typeof value === 'string') {
        return `<pre class="mb-0 hex-data" style="white-space: pre-wrap; word-break: break-all; max-height: 200px; overflow-y: auto;">${value}</pre>`;
    }
    
    if (Array.isArray(value)) {
        if (value.length === 0) return 'Empty Array';
        
        // For short arrays of primitive values, format as comma-separated list
        if (value.length <= 5 && value.every(item => 
            typeof item !== 'object' || item === null)) {
            return value.map(item => formatValue(item)).join(', ');
        }
        
        // For longer arrays or arrays of objects, format as a list
        return `<ul class="mb-0 ps-3">${value.map(item => 
            `<li>${formatValue(item)}</li>`).join('')}</ul>`;
    }
    
    if (typeof value === 'object') {
        // For small objects, format as a simple table
        if (Object.keys(value).length <= 3) {
            let html = '<div class="metadata-section small-object">';
            for (const [objKey, val] of Object.entries(value)) {
                html += `<div><strong>${formatKeyName(objKey)}:</strong> ${formatValue(val, objKey)}</div>`;
            }
            html += '</div>';
            return html;
        }
        
        // For larger objects, format as a table
        try {
            return `<pre class="mb-0 object-data">${JSON.stringify(value, null, 2)}</pre>`;
        } catch (e) {
            return String(value);
        }
    }
    
    if (typeof value === 'boolean') {
        return value ? 'Yes' : 'No';
    }
    
    // Handle timestamps
    if (typeof value === 'number' && value > 1500000000 && value < 2000000000) {
        return formatDate(value);
    }
    
    // Detect and format transaction hashes
    if (typeof value === 'string' && value.match(/^0x[a-fA-F0-9]{64}$/)) {
        return createTxLink(value);
    }
    
    // Detect and format ethereum addresses
    if (typeof value === 'string' && value.match(/^0x[a-fA-F0-9]{40}$/)) {
        return createAddressLink(value);
    }
    
    return String(value);
}

// Create an address link from an ethereum address
function createAddressLink(address) {
    if (!address || address === '') return 'N/A';
    
    // Base URL for polygon explorer + specific address
    const baseUrl = 'https://polygonscan.com/address/';
    
    // Format address for display (first 6 characters + ... + last 4 characters)
    const displayAddress = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
    
    return `<a href="${baseUrl}${address}" target="_blank" class="tx-link code-font">${displayAddress}</a>`;
}

// Function to setup tag filter with 3-column checkbox layout
function setupTagFilter() {
    if (!currentData || currentData.length === 0) return;
    
    // Extract all unique tags from the data
    const allTags = new Set();
    currentData.forEach(item => {
        if (item.tags && Array.isArray(item.tags)) {
            item.tags.forEach(tag => allTags.add(tag));
        }
    });
    
    // Sort tags alphabetically
    const sortedTags = Array.from(allTags).sort();
    
    // Only proceed if we have tags
    if (sortedTags.length > 0) {
        // Get the container for tag checkboxes
        const container = document.getElementById('tagCheckboxContainer');
        if (!container) return;
        
        // Clear the container
        container.innerHTML = '';
        
        // Add a checkbox for each tag
        sortedTags.forEach(tag => {
            const item = document.createElement('div');
            item.className = 'tag-checkbox-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `tag-${tag.replace(/[^a-zA-Z0-9]/g, '-')}`;
            checkbox.className = 'tag-checkbox';
            checkbox.value = tag;
            
            const label = document.createElement('label');
            label.htmlFor = checkbox.id;
            label.textContent = tag;
            
            // Add click event for the label to toggle checkbox
            label.addEventListener('click', (e) => {
                e.preventDefault();
                checkbox.checked = !checkbox.checked;
                applyTagFilter();
            });
            
            // Add change event for the checkbox
            checkbox.addEventListener('change', applyTagFilter);
            
            item.appendChild(checkbox);
            item.appendChild(label);
            container.appendChild(item);
        });
        
        // Show the tag filter card
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = '';
        }
    }
}

// Apply tag filter using checkboxes
function applyTagFilter() {
    const checkboxes = document.querySelectorAll('.tag-checkbox:checked');
    const selectedTags = Array.from(checkboxes).map(cb => cb.value);
    
    // Apply all filters
    applyAllFilters(currentFilter, selectedTags);
}

// Clear tag filter
function clearTagFilter() {
    const checkboxes = document.querySelectorAll('.tag-checkbox');
    checkboxes.forEach(cb => cb.checked = false);
    
    // Apply all filters without tag filters
    applyAllFilters(currentFilter, []);
}

// Apply all filters (correctness, tags, search)
function applyAllFilters(correctnessFilter, tagFilters = []) {
    currentFilter = correctnessFilter;
    
    if (!currentData) return;
    
    let filteredData = [...currentData];
    
    // Apply correctness filter if specified
    if (correctnessFilter === 'correct' || correctnessFilter === 'incorrect' || correctnessFilter === 'disputed' || correctnessFilter === 'incorrectIgnoringP4') {
        filteredData = filteredData.filter(item => {
            if (correctnessFilter === 'disputed') {
                return item.disputed === true;
            } else if (correctnessFilter === 'incorrectIgnoringP4') {
                // Only show incorrect results where AI recommendation was NOT p4
                const isCorrect = isRecommendationCorrect(item);
                const isNotP4 = item.recommendation && item.recommendation.toLowerCase() !== 'p4';
                return isCorrect === false && isNotP4;
            } else {
                const isCorrect = isRecommendationCorrect(item);
                // Skip entries where we can't determine correctness (null)
                if (isCorrect === null) return false;
                return correctnessFilter === 'correct' ? isCorrect === true : isCorrect === false;
            }
        });
    }
    
    // Apply tag filters if specified
    if (tagFilters && tagFilters.length > 0) {
        filteredData = filteredData.filter(item => {
            if (!item.tags || !Array.isArray(item.tags)) return false;
            
            // Check if item has ALL selected tags (AND logic)
            return tagFilters.every(tag => item.tags.includes(tag));
        });
    }
    
    // Apply date filters
    if (currentDateFilters.expiration_timestamp) {
        filteredData = filteredData.filter(item => {
            const expiration = item.proposal_metadata?.expiration_timestamp;
            if (!expiration) return false;
            
            // Filter for items with expiration date on or after the selected date
            return expiration >= currentDateFilters.expiration_timestamp;
        });
    }
    
    if (currentDateFilters.request_transaction_block_time) {
        filteredData = filteredData.filter(item => {
            const blockTime = item.proposal_metadata?.request_transaction_block_time;
            if (!blockTime) return false;
            
            // Filter for items with block time on or after the selected date
            return blockTime >= currentDateFilters.request_transaction_block_time;
        });
    }
    
    // Apply search filter if there's a search term
    if (currentSearch) {
        filteredData = filteredData.filter(item => {
            // Search in query ID
            if (item.query_id?.toLowerCase().includes(currentSearch)) return true;
            
            // Search in recommendation
            if (item.recommendation?.toLowerCase().includes(currentSearch)) return true;
            
            // Search in prompt
            if (item.proposal_data?.prompt?.toLowerCase().includes(currentSearch)) return true;
            
            // Search in title
            const title = extractTitle(item);
            if (title.toLowerCase().includes(currentSearch)) return true;
            
            return false;
        });
    }
    
    // Update table with filtered data
    updateTableWithData(filteredData);
}

// Update tag accuracy display
function updateTagAccuracyDisplay(tagStats) {
    const tagAccuracyTableBody = document.getElementById('tagAccuracyTableBody');
    const tagsTab = document.getElementById('tags-tab');
    
    if (!tagAccuracyTableBody || !tagsTab) return;
    
    // Ensure tagStats is an object
    if (!tagStats || typeof tagStats !== 'object') {
        tagStats = {};
    }
    
    // Only enable tag tab if we have tag stats
    const tagCount = Object.keys(tagStats).length;
    if (tagCount === 0) {
        // Disable the tag tab if no tags
        tagsTab.classList.add('disabled');
        tagsTab.setAttribute('tabindex', '-1');
        
        // Make sure we show the "Overall" tab
        document.getElementById('overall-tab')?.click();
        
        // Clear table
        tagAccuracyTableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center text-muted">No tag data available</td>
            </tr>
        `;
        return;
    }
    
    // Enable tag tab
    tagsTab.classList.remove('disabled');
    tagsTab.removeAttribute('tabindex');
    
    // Sort tags by total count (descending)
    const sortedTags = Object.keys(tagStats).sort((a, b) => 
        tagStats[b].total - tagStats[a].total
    );
    
    // Create rows for each tag
    tagAccuracyTableBody.innerHTML = sortedTags.map(tag => {
        const stats = tagStats[tag] || { 
            total: 0, 
            correct: 0, 
            incorrect: 0, 
            accuracyPercent: 0,
            totalIgnoringP4: 0,
            correctIgnoringP4: 0,
            incorrectIgnoringP4: 0,
            accuracyPercentIgnoringP4: 0
        };
        
        // Ensure we have valid numbers
        const total = stats.total || 0;
        const correct = stats.correct || 0;
        const incorrect = stats.incorrect || 0;
        
        // Recalculate accuracy to ensure it's correct
        const accuracyPercent = total > 0 ? (correct / total) * 100 : 0;
        
        // Calculate P4-ignoring accuracy
        const totalIgnoringP4 = stats.totalIgnoringP4 || 0;
        const correctIgnoringP4 = stats.correctIgnoringP4 || 0;
        const accuracyPercentIgnoringP4 = totalIgnoringP4 > 0 ? (correctIgnoringP4 / totalIgnoringP4) * 100 : 0;
        
        const accuracyClass = accuracyPercent >= 80 ? 'high-accuracy' : 
                             (accuracyPercent >= 50 ? 'medium-accuracy' : 'low-accuracy');
                             
        const accuracyClassIgnoringP4 = accuracyPercentIgnoringP4 >= 80 ? 'high-accuracy' : 
                                       (accuracyPercentIgnoringP4 >= 50 ? 'medium-accuracy' : 'low-accuracy');
        
        return `
            <tr>
                <td><span class="tag-badge">${tag}</span></td>
                <td>${total}</td>
                <td class="accuracy-cell ${accuracyClass}">${accuracyPercent.toFixed(1)}%</td>
                <td class="accuracy-cell ${accuracyClassIgnoringP4}">${accuracyPercentIgnoringP4.toFixed(1)}%</td>
                <td>${correct}</td>
                <td>${incorrect}</td>
            </tr>
        `;
    }).join('');
    
    // Add click handler to show the tag tab when clicking on a tag badge in the UI
    document.querySelectorAll('.tag-badge').forEach(badge => {
        badge.style.cursor = 'pointer';
        badge.title = 'View tag accuracy statistics';
        
        badge.addEventListener('click', (event) => {
            event.stopPropagation();
            // Switch to the tags tab
            document.getElementById('tags-tab')?.click();
        });
    });
}

// Format stage names for better readability
function formatStageName(stage) {
    if (!stage) return '';
    
    // Handle standard formatting
    return stage.replace(/_/g, ' ')
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')
        .replace(/(\d+)$/, ' $1'); // Add space before any trailing number
}

// Format satisfaction level with appropriate styling
function formatSatisfactionLevel(level) {
    if (!level) return '';
    
    let cssClass = 'satisfaction-default';
    
    if (level.includes('satisfied')) {
        cssClass = 'satisfaction-satisfied';
    } else if (level.includes('not_satisfied')) {
        cssClass = 'satisfaction-not-satisfied';
    } else if (level.includes('retry')) {
        cssClass = 'satisfaction-retry';
    }
    
    return `<span class="${cssClass}">${formatKeyName(level)}</span>`;
}

// Handle logout
function handleLogout() {
    // Clear the auth token cookie
    document.cookie = 'auth_token=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    
    // Redirect to login page
    window.location.href = '/login';
}

// Apply a source filter
function applySourceFilter(source) {
    // If mongoOnlyResults is true, we can only use MongoDB
    if (mongoOnlyResults && source !== 'mongodb') {
        console.warn('Cannot change source when MONGO_ONLY_RESULTS is enabled');
        return;
    }
    
    // Update current source filter
    currentSourceFilter = source;
    
    // Reset active class on source filter buttons
    document.querySelectorAll('.source-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Set active class on the clicked button
    if (source === 'filesystem') {
        document.getElementById('filterSourceFilesystem')?.classList.add('active');
    } else if (source === 'mongodb') {
        document.getElementById('filterSourceMongoDB')?.classList.add('active');
    }
    
    // Update the experiment list
    displayExperimentsTable();
}

// Function to handle sending input to a running process
async function sendProcessInput(processId, input) {
    try {
        // Send the input to the API
        const response = await fetch(`/api/process/input/${processId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ input: input })
        });
        
        if (response.ok) {
            // Add the input to the logs display with a different style
            const logsContainer = document.getElementById('processLogs');
            if (logsContainer) {
                const formattedTime = formatLogTime(new Date());
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry log-input';
                logEntry.innerHTML = `<span class="log-timestamp">[${formattedTime}]</span><span class="log-message">&gt; ${input}</span>`;
                logsContainer.appendChild(logEntry);
                
                // Only scroll to bottom if auto-scroll is enabled
                if (autoScrollEnabled) {
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }
            }
            
            // For better UX, immediately fetch new logs to show the response
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Fetch updated logs
            const process = activeProcesses.find(p => p.id === processId);
            if (process) {
                updateProcessLogs(processId);
            }
        } else {
            console.error('Failed to send input to process');
            const errorData = await response.json();
            alert(`Error: ${errorData.error || 'Failed to send input'}`);
        }
    } catch (error) {
        console.error('Error sending input to process:', error);
        alert('Error: Could not send input to process');
    }
}

// Show or hide the interactive input form based on process status
function toggleInteractiveInput(processId, show) {
    const inputContainer = document.getElementById('interactiveInputContainer');
    if (!inputContainer) return;
    
    if (show) {
        inputContainer.style.display = 'block';
        document.getElementById('interactiveInput')?.focus();
        
        // Add waiting-for-input class to highlight the form
        document.body.classList.add('waiting-for-input');
    } else {
        inputContainer.style.display = 'none';
        document.body.classList.remove('waiting-for-input');
    }
}

// Check if process output is waiting for input
function checkForInputPrompt(message) {
    // Common input prompts in Python and shell scripts
    const inputPrompts = [
        'input', 'Enter ', 'Type ', '? ', 
        'Your choice', 'response', 'Continue',
        'Press', 'Select', 'Choose', 'name',
        'goal', 'experiment', 'title', '[y/n]',
        'password', 'username', 'Overwrite'
    ];
    
    // Check if the message ends with any of these patterns
    if (typeof message === 'string') {
        const endsWithColon = message.trim().endsWith(':');
        const endsWithQuestionMark = message.trim().endsWith('?');
        
        if (endsWithColon || endsWithQuestionMark) {
            return true;
        }
        
        // Check for common input prompts
        for (const prompt of inputPrompts) {
            if (message.toLowerCase().includes(prompt.toLowerCase())) {
                return true;
            }
        }
    }
    
    return false;
}

// Helper function to fetch a list of files in a directory
async function fetchFileList(dirPath) {
    try {
        console.log('Fetching files from:', dirPath);
        
        // Use our new robust endpoint
        const url = `/api/files?path=${encodeURIComponent(dirPath)}`;
        console.log('Using file listing API:', url);
        
        const response = await fetch(url);
        
        if (response.ok) {
            const data = await response.json();
            console.log(`Found ${data.count || 0} files in ${dirPath}`);
            
            // Filter for just JSON files
            const jsonFiles = data.files
                .filter(file => file.type === 'file' && (file.file_type === 'json' || file.name.endsWith('.json')))
                .map(file => file.name);
            
            if (jsonFiles.length > 0) {
                return jsonFiles;
            }
            
            console.warn('No JSON files found via API');
        } else {
            console.warn(`API request failed: ${response.status} ${response.statusText}`);
        }
        
        // Fallback to outputs-directory API for backward compatibility
        try {
            console.log('Trying outputs directory API as fallback...');
            const outputsResponse = await fetch(`/api/outputs-directory?path=${encodeURIComponent(dirPath)}`);
            if (outputsResponse.ok) {
                const data = await outputsResponse.json();
                console.log('Files from outputs directory:', data.files || []);
                return data.files || [];
            }
        } catch (err) {
            console.warn('Error using outputs directory API:', err);
        }
        
        // Try direct directory listing as another fallback
        try {
            console.log('Trying direct directory listing...');
            // Try to access the directory directly via HTTP 
            const directResponse = await fetch(`/${dirPath}/`);
            
            if (directResponse.ok) {
                const text = await directResponse.text();
                
                // Use regex to extract JSON filenames from directory listing
                const regex = /href="([^"]+\.json)"/g;
                const matches = text.matchAll(regex);
                const extractedFiles = Array.from(matches, m => m[1]);
                
                console.log('Files from direct listing:', extractedFiles);
                if (extractedFiles.length > 0) {
                    return extractedFiles;
                }
            }
        } catch (err) {
            console.warn('Error with direct directory listing:', err);
        }
        
        // Final fallback - try a hardcoded list of filenames if nothing else worked
        console.warn('Using fallback file list as last resort');
        return [
            'faf5e4db.json', '6af20338.json', 'a0f4fc21.json', 'ae03f9e6.json',
            '51ddd061.json', 'd9d48807.json', '210e2087.json', '1e4d05a7.json',
            'e9384a05.json', 'a5722f27.json', '3a4eb4fc.json', 'f409f21c.json'
        ];
    } catch (error) {
        console.error('Error fetching file list:', error);
        // Return an empty array on error
        return [];
    }
}

// Function to process log entry and apply special formatting if needed
function processLogEntry(logEntry) {
    if (!logEntry || !logEntry.message) return logEntry;
    
    // Deep clone to avoid modifying the original
    const processedEntry = JSON.parse(JSON.stringify(logEntry));
    let message = processedEntry.message;
    
    // Handle ANSI color codes - replace with HTML
    // Example: Replace \x1b[31m (red) with <span style="color:red">
    message = message.replace(/\x1b\[(\d+)m/g, (match, colorCode) => {
        const colorMap = {
            '30': 'black',
            '31': 'red',
            '32': 'green',
            '33': 'yellow',
            '34': 'blue',
            '35': 'magenta',
            '36': 'cyan',
            '37': 'white',
            '90': '#888', // bright black (gray)
            '91': '#f66', // bright red
            '92': '#6f6', // bright green
            '93': '#ff6', // bright yellow
            '94': '#66f', // bright blue
            '95': '#f6f', // bright magenta
            '96': '#6ff', // bright cyan
            '97': '#fff'  // bright white
        };
        
        if (colorCode === '0') {
            return '</span>'; // Reset
        } else if (colorMap[colorCode]) {
            return `<span style="color:${colorMap[colorCode]}">`;
        }
        return '';
    });
    
    // Replace newlines with <br> for proper display
    message = message.replace(/\n/g, '<br>');
    
    // Save processed message
    processedEntry.message = message;
    
    return processedEntry;
}

// Function to automatically resize textarea based on content
function autoResizeTextarea(textarea) {
    // Reset height to auto to get the right scrollHeight
    textarea.style.height = 'auto';
    
    // Set the height to match content (scrollHeight)
    // Add a small buffer (2px) to avoid scrollbar flicker
    textarea.style.height = (textarea.scrollHeight + 2) + 'px';
    
    // Enforce min-height from CSS if needed
    if (textarea.scrollHeight < parseInt(getComputedStyle(textarea).minHeight)) {
        textarea.style.height = getComputedStyle(textarea).minHeight;
    }
}

// Function to create pagination controls
function createPagination(currentPage, totalPages, tableId) {
    // Check if we need pagination
    if (totalPages <= 1) return;
    
    // Create pagination container if it doesn't exist
    let paginationContainer = document.getElementById(`${tableId}Pagination`);
    if (!paginationContainer) {
        paginationContainer = document.createElement('div');
        paginationContainer.id = `${tableId}Pagination`;
        paginationContainer.className = 'pagination-container mt-3 d-flex justify-content-center';
        
        // Find the table and append pagination after it
        const table = document.getElementById(tableId);
        if (table && table.parentNode) {
            table.parentNode.appendChild(paginationContainer);
        }
    }
    
    // Generate pagination HTML
    let paginationHTML = `
        <nav aria-label="Results pagination">
            <ul class="pagination">
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="1" aria-label="First">
                        <span aria-hidden="true">&laquo;&laquo;</span>
                    </a>
                </li>
                <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${currentPage - 1}" aria-label="Previous">
                        <span aria-hidden="true">&laquo;</span>
                    </a>
                </li>
    `;
    
    // Display page numbers
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    // Adjust if we're near the end
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    // Add ellipsis if needed at the beginning
    if (startPage > 1) {
        paginationHTML += `
            <li class="page-item ${startPage === 1 ? 'active' : ''}">
                <a class="page-link" href="#" data-page="1">1</a>
            </li>
        `;
        if (startPage > 2) {
            paginationHTML += `
                <li class="page-item disabled">
                    <a class="page-link" href="#">...</a>
                </li>
            `;
        }
    }
    
    // Add page numbers
    for (let i = startPage; i <= endPage; i++) {
        if (i !== 1 && i !== totalPages) { // Skip first and last page as they're handled separately
            paginationHTML += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>
            `;
        }
    }
    
    // Add ellipsis if needed at the end
    if (endPage < totalPages) {
        if (endPage < totalPages - 1) {
            paginationHTML += `
                <li class="page-item disabled">
                    <a class="page-link" href="#">...</a>
                </li>
            `;
        }
        paginationHTML += `
            <li class="page-item ${endPage === totalPages ? 'active' : ''}">
                <a class="page-link" href="#" data-page="${totalPages}">${totalPages}</a>
            </li>
        `;
    }
    
    // Add next and last page links
    paginationHTML += `
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${currentPage + 1}" aria-label="Next">
                        <span aria-hidden="true">&raquo;</span>
                    </a>
                </li>
                <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                    <a class="page-link" href="#" data-page="${totalPages}" aria-label="Last">
                        <span aria-hidden="true">&raquo;&raquo;</span>
                    </a>
                </li>
            </ul>
        </nav>
    `;
    
    // Set the pagination HTML
    paginationContainer.innerHTML = paginationHTML;
    
    // Add click event for pagination
    document.querySelectorAll(`#${tableId}Pagination .page-link`).forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const page = parseInt(link.getAttribute('data-page'));
            if (!isNaN(page)) {
                // Save current page to localStorage
                localStorage.setItem('currentResultsPage', page);
                // Reload the table with the new page
                updateTableWithData(currentData);
                // Scroll to top of the table
                document.getElementById(tableId).scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
}

// Function to sort data by a given column
function sortData(data, column, direction) {
    return data.sort((a, b) => {
        let valueA, valueB;
        
        // Extract values based on column
        switch (column) {
            case 'timestamp':
                valueA = a.timestamp || a.unix_timestamp || 0;
                valueB = b.timestamp || b.unix_timestamp || 0;
                break;
            case 'proposal_timestamp':
                valueA = a.proposal_timestamp || 
                         (a.proposal_metadata && a.proposal_metadata.request_transaction_block_time ? 
                             a.proposal_metadata.request_transaction_block_time : 0);
                valueB = b.proposal_timestamp || 
                         (b.proposal_metadata && b.proposal_metadata.request_transaction_block_time ? 
                             b.proposal_metadata.request_transaction_block_time : 0);
                break;
            case 'id':
                valueA = a.question_id_short || a.query_id || '';
                valueB = b.question_id_short || b.query_id || '';
                break;
            case 'title':
                valueA = extractTitle(a).toLowerCase();
                valueB = extractTitle(b).toLowerCase();
                break;
            case 'recommendation':
                valueA = (a.recommendation || a.proposed_price_outcome || '').toLowerCase();
                valueB = (b.recommendation || b.proposed_price_outcome || '').toLowerCase();
                break;
            case 'resolution':
                valueA = (a.resolved_price_outcome !== undefined && a.resolved_price_outcome !== null) ? 
                         a.resolved_price_outcome.toString() : 'zzzz'; // Sort unresolved last
                valueB = (b.resolved_price_outcome !== undefined && b.resolved_price_outcome !== null) ? 
                         b.resolved_price_outcome.toString() : 'zzzz';
                break;
            case 'disputed':
                valueA = a.disputed === true;
                valueB = b.disputed === true;
                break;
            case 'correct':
                const isCorrectA = isRecommendationCorrect(a);
                const isCorrectB = isRecommendationCorrect(b);
                valueA = isCorrectA === true ? 1 : isCorrectA === false ? 0 : -1;
                valueB = isCorrectB === true ? 1 : isCorrectB === false ? 0 : -1;
                break;
            case 'block_number':
                valueA = a.proposal_metadata?.block_number || 0;
                valueB = b.proposal_metadata?.block_number || 0;
                break;
            case 'proposal_bond':
                valueA = a.proposal_metadata?.proposal_bond || 0;
                valueB = b.proposal_metadata?.proposal_bond || 0;
                break;
            case 'tags':
                valueA = (a.tags && a.tags.length) ? a.tags.join(',').toLowerCase() : '';
                valueB = (b.tags && b.tags.length) ? b.tags.join(',').toLowerCase() : '';
                break;
            default:
                valueA = a[column];
                valueB = b[column];
        }
        
        // Ensure values are comparable
        if (typeof valueA === 'string') {
            valueA = valueA.toString().toLowerCase();
        }
        if (typeof valueB === 'string') {
            valueB = valueB.toString().toLowerCase();
        }
        
        // Convert string timestamps to numbers
        if (column === 'timestamp' || column === 'proposal_timestamp') {
            if (typeof valueA === 'string' && !isNaN(parseInt(valueA, 10))) {
                valueA = parseInt(valueA, 10);
            }
            if (typeof valueB === 'string' && !isNaN(parseInt(valueB, 10))) {
                valueB = parseInt(valueB, 10);
            }
        }
        
        // Convert string numbers to actual numbers for numeric columns
        if (column === 'block_number' || column === 'proposal_bond') {
            if (typeof valueA === 'string' && !isNaN(parseInt(valueA, 10))) {
                valueA = parseInt(valueA, 10);
            }
            if (typeof valueB === 'string' && !isNaN(parseInt(valueB, 10))) {
                valueB = parseInt(valueB, 10);
            }
        }
        
        // Compare values based on direction
        if (direction === 'asc') {
            return valueA < valueB ? -1 : valueA > valueB ? 1 : 0;
        } else {
            return valueA > valueB ? -1 : valueA < valueB ? 1 : 0;
        }
    });
}

// Add this function to initialize the sortable headers
function initializeSortableHeaders() {
    const headers = document.querySelectorAll('#resultsTable th');
    if (!headers.length) return;
    
    // Create a mapping of classes to column names
    const columnClassMap = {
        'col-timestamp': 'timestamp',
        'col-proposal-time': 'proposal_timestamp',
        'col-expiration-time': 'expiration_timestamp',
        'col-request-time': 'request_transaction_block_time',
        'col-id': 'id',
        'col-title': 'title',
        'col-recommendation': 'recommendation',
        'col-resolution': 'resolution',
        'col-disputed': 'disputed',
        'col-correct': 'correct',
        'col-block-number': 'block_number',
        'col-proposal-bond': 'proposal_bond',
        'col-tags': 'tags'
    };
    
    // Add sort indicators and click handlers to headers
    headers.forEach((header) => {
        // Skip the icon column (first column with no class)
        if (header.classList.length === 0 || header.classList.contains('icon-column')) {
            return;
        }
        
        // Get column name from class
        let columnName = null;
        for (const className of header.classList) {
            if (columnClassMap[className]) {
                columnName = columnClassMap[className];
                break;
            }
        }
        
        // Skip if we can't determine the column name
        if (!columnName) return;
        
        // Add sort indicator
        const sortIndicator = document.createElement('span');
        sortIndicator.classList.add('sort-indicator', 'ms-1');
        
        // Set initial indicator if this is the current sort column
        if (columnName === currentSort.column) {
            sortIndicator.innerHTML = currentSort.direction === 'asc' ? '&#9650;' : '&#9660;';
        } else {
            sortIndicator.innerHTML = '&#8645;';
            sortIndicator.style.opacity = '0.3';
        }
        
        // Add the indicator to the header
        header.appendChild(sortIndicator);
        
        // Make header sortable
        header.classList.add('sortable');
        header.style.cursor = 'pointer';
        
        // Add click handler
        header.addEventListener('click', () => {
            // Toggle direction if same column, otherwise set to desc
            if (columnName === currentSort.column) {
                currentSort.direction = currentSort.direction === 'asc' ? 'desc' : 'asc';
            } else {
                currentSort.column = columnName;
                currentSort.direction = 'desc'; // Default to descending for new columns
            }
            
            // Update all indicators
            document.querySelectorAll('#resultsTable th .sort-indicator').forEach((indicator) => {
                const parentHeader = indicator.closest('th');
                
                // Get column name from parent header classes
                let parentColumnName = null;
                for (const className of parentHeader.classList) {
                    if (columnClassMap[className]) {
                        parentColumnName = columnClassMap[className];
                        break;
                    }
                }
                
                if (parentColumnName === currentSort.column) {
                    indicator.innerHTML = currentSort.direction === 'asc' ? '&#9650;' : '&#9660;';
                    indicator.style.opacity = '1';
                } else {
                    indicator.innerHTML = '&#8645;';
                    indicator.style.opacity = '0.3';
                }
            });
            
            // Update the table with sorted data
            updateTableWithData(currentData);
        });
    });
}

// Modify displayResultsData to initialize sortable headers after displaying data
function displayResultsData() {
    const tableBody = document.getElementById('resultsTableBody');
    if (!tableBody) return;
    
    if (!currentData || currentData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="8" class="text-center">No data available</td>
            </tr>
        `;
        document.getElementById('displayingCount').textContent = '0';
        document.getElementById('totalEntriesCount').textContent = '0';
        return;
    }
    
    // Ensure all required fields are available
    const processedData = currentData.map(item => {
        // Make a shallow copy to avoid modifying the original
        const processed = {...item};
        
        // Ensure we have consistent field names
        processed.recommendation = 
            item.recommendation || 
            item.proposed_price_outcome || 
            'N/A';
            
        processed.resolved_price_outcome = 
            item.resolved_price_outcome !== undefined ? item.resolved_price_outcome : 
            item.resolved_price !== undefined ? item.resolved_price : 
            null;
            
        // Ensure we have a title field for display
        processed.title = extractTitle(item);
        
        // Ensure we have a query_id field
        processed.query_id = item.query_id || item.id || '';
        
        // Ensure we have a timestamp field
        processed.timestamp = item.timestamp || item.unix_timestamp || 0;
        
        // Extract proposal timestamp from proposal_metadata if available
        processed.proposal_timestamp = 
            (item.proposal_metadata && item.proposal_metadata.request_transaction_block_time) ? 
            item.proposal_metadata.request_transaction_block_time : 0;
        
        return processed;
    });
    
    // Now proceed with normal display logic
    updateTableWithData(processedData);
    
    // Initialize sortable headers after displaying data
    initializeSortableHeaders();
}

// Function to apply date filters
function applyDateFilter() {
    // Get all date inputs
    const dateInputs = document.querySelectorAll('.date-filter');
    
    // Update current date filters
    dateInputs.forEach(input => {
        const filterType = input.getAttribute('data-filter-type');
        const dateValue = input.value;
        
        if (dateValue) {
            // Convert the date input value (YYYY-MM-DD) to Unix timestamp (seconds)
            const dateObj = new Date(dateValue);
            currentDateFilters[filterType] = Math.floor(dateObj.getTime() / 1000);
        } else {
            currentDateFilters[filterType] = null;
        }
    });
    
    // Apply all filters with the current date filters
    applyAllFilters(currentFilter);
}

// Function to clear date filters
function clearDateFilter() {
    // Reset all date inputs
    document.querySelectorAll('.date-filter').forEach(input => {
        input.value = '';
    });
    
    // Reset current date filters
    currentDateFilters = {
        expiration_timestamp: null,
        request_transaction_block_time: null
    };
    
    // Apply all filters with the cleared date filters
    applyAllFilters(currentFilter);
}

// Helper function to detect and format code blocks in responses
function formatCodeBlocks(text) {
    if (!text) return '';
    
    // Pattern to match Markdown code blocks: ```language\ncode\n```
    const codeBlockRegex = /```([a-zA-Z0-9_]*)\n([\s\S]*?)\n```/g;
    
    // Replace code blocks with properly formatted HTML for PrismJS
    return text.replace(codeBlockRegex, (match, language, code) => {
        // Default to plaintext if no language is specified
        const langClass = language ? `language-${language}` : 'language-plaintext';
        
        return `<pre class="code-block"><code class="${langClass}">${code}</code></pre>`;
    });
}

// Apply this function in the showDetails function when displaying responses
// Update the relevant sections with:
// <pre class="mb-0 response-text">${formatCodeBlocks(solverResult.response)}</pre>

// Helper functions for journey rendering
function formatActorName(actor) {
    const actorNames = {
        'router': 'Router',
        'perplexity': 'Perplexity',
        'code_runner': 'Code Runner',
        'overseer': 'Overseer'
    };
    return actorNames[actor] || actor;
}

function formatActionName(action) {
    const actionNames = {
        'route': 'Routing',
        'solve': 'Solving',
        'evaluate': 'Evaluation',
        'reroute': 'Re-routing'
    };
    return actionNames[action] || action;
}

function renderJourneyStepContent(step, stepIndex) {
    let content = '';
    
    switch (step.actor) {
        case 'router':
            content = renderRouterStep(step, stepIndex);
            break;
        case 'overseer':
            content = renderOverseerStep(step, stepIndex);
            break;
        case 'perplexity':
        case 'code_runner':
            content = renderSolverStep(step, stepIndex);
            break;
        default:
            content = `<div class="step-unknown">Unknown actor type: ${step.actor}</div>`;
    }
    
    return content;
}

function renderRouterStep(step, stepIndex) {
    let content = '';
    
    if (step.response && step.response.solvers) {
        content += `
            <div class="router-decision">
                <strong>Selected Solvers:</strong> 
                ${step.response.solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('')}
            </div>
        `;
        
        if (step.response.reason) {
            content += `<div class="mt-2"><strong>Reason:</strong> ${step.response.reason}</div>`;
        }
        
        if (step.response.multi_solver_strategy) {
            content += `<div class="mt-2"><strong>Strategy:</strong> ${step.response.multi_solver_strategy}</div>`;
        }
    }
    
    if (step.prompt) {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="router-prompt-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Router Prompt
                </button>
                <pre class="router-prompt mt-2 content-collapsible collapsed" id="router-prompt-${stepIndex}">${step.prompt}</pre>
            </div>
        `;
    }
    
    if (step.metadata) {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="router-metadata-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Metadata
                </button>
                <pre class="step-metadata mt-2 content-collapsible collapsed" id="router-metadata-${stepIndex}">${JSON.stringify(step.metadata, null, 2)}</pre>
            </div>
        `;
    }
    
    return content;
}

function renderOverseerStep(step, stepIndex) {
    let content = '';
    
    if (step.action === 'evaluate') {
        content += `
            <div><strong>Evaluated:</strong> ${step.solver_evaluated || 'Unknown'}</div>
            <div class="mt-2"><strong>Verdict:</strong> <span class="verdict-${step.verdict}">${formatVerdictName(step.verdict)}</span></div>
        `;
        
        if (step.critique) {
            content += `
                <div class="mt-2">
                    <strong>Critique:</strong>
                    <div class="critique-preview" id="critique-preview-${stepIndex}">
                        ${step.critique ? step.critique.substring(0, 120) + (step.critique.length > 120 ? '...' : '') : 'N/A'}
                    </div>
                    <div class="critique-full content-collapsible collapsed" id="critique-full-${stepIndex}">
                        ${step.critique || 'N/A'}
                    </div>
                    ${step.critique && step.critique.length > 120 ? `
                        <button class="btn btn-sm btn-link toggle-critique-btn" 
                            data-preview="critique-preview-${stepIndex}" 
                            data-target="critique-full-${stepIndex}">
                            Show more
                        </button>
                    ` : ''}
                </div>
            `;
        }
        
        if (step.market_alignment) {
            content += `<div class="mt-2"><strong>Market Alignment:</strong> ${step.market_alignment}</div>`;
        }
    } else if (step.action === 'reroute') {
        content += `
            <div><strong>Excluded Solvers:</strong> ${step.excluded_solvers && step.excluded_solvers.length > 0 ? 
                step.excluded_solvers.map(solver => `<span class="tag-badge">${solver}</span>`).join('') : 'None'}</div>
        `;
        
        if (step.routing_guidance) {
            content += `<div class="mt-2"><strong>Guidance:</strong> ${step.routing_guidance}</div>`;
        }
    }
    
    if (step.prompt) {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-prompt-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Overseer Prompt
                </button>
                <pre class="overseer-prompt mt-2 content-collapsible collapsed" id="overseer-prompt-${stepIndex}">${step.prompt}</pre>
            </div>
        `;
    }
    
    if (step.response) {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-response-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Response
                </button>
                <pre class="overseer-response mt-2 content-collapsible collapsed" id="overseer-response-${stepIndex}">${formatCodeBlocks(step.response)}</pre>
            </div>
        `;
    }
    
    if (step.metadata) {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="overseer-metadata-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Metadata
                </button>
                <pre class="step-metadata mt-2 content-collapsible collapsed" id="overseer-metadata-${stepIndex}">${JSON.stringify(step.metadata, null, 2)}</pre>
            </div>
        `;
    }
    
    return content;
}

function renderSolverStep(step, stepIndex) {
    let content = '';
    
    if (step.recommendation) {
        content += `<div><strong>Recommendation:</strong> ${step.recommendation}</div>`;
    }
    
    // Special handling for code_runner
    if (step.actor === 'code_runner') {
        // Show prompt if available
        if (step.prompt) {
            content += `
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-prompt-${stepIndex}">
                        <i class="bi bi-arrows-expand"></i> Show Prompt
                    </button>
                    <pre class="solver-prompt mt-2 content-collapsible collapsed" id="solver-prompt-${stepIndex}">${step.prompt}</pre>
                </div>
            `;
        }
        
        // If we have a response, display it
        if (step.response) {
            content += `
                <div class="mt-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>Response:</strong>
                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-response-${stepIndex}">
                            <i class="bi bi-arrows-expand"></i> Show Response
                        </button>
                    </div>
                    <pre class="solver-response mt-2 content-collapsible collapsed" id="solver-response-${stepIndex}">${formatCodeBlocks(step.response)}</pre>
                </div>
            `;
        }

        // Handle code_output from both root level (new format) or metadata (old format)
        if (step.code_output || step.metadata?.raw_data?.code_output) {
            const codeOutput = step.code_output || (step.metadata?.raw_data?.code_output || '');
            content += `
                <div class="mt-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>Code Output:</strong>
                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="code-output-${stepIndex}">
                            <i class="bi bi-arrows-expand"></i> Show Code Output
                        </button>
                    </div>
                    <pre class="code-output-block language-python content-collapsible collapsed" id="code-output-${stepIndex}"><code class="language-python">${escapeHtml(codeOutput)}</code></pre>
                </div>
            `;
        }
        
        // Handle code from both root level (new format) or metadata (old format)
        if (step.code || step.metadata?.raw_data?.code) {
            const code = step.code || (step.metadata?.raw_data?.code || '');
            content += `
                <div class="mt-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>Generated Code:</strong>
                        <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="code-block-${stepIndex}">
                            <i class="bi bi-arrows-expand"></i> Show Generated Code
                        </button>
                    </div>
                    <pre class="code-block language-python content-collapsible collapsed" id="code-block-${stepIndex}"><code class="language-python">${escapeHtml(code)}</code></pre>
                </div>
            `;
        }
        
        // Show relevant info in a nice block
        if (step.metadata?.raw_data || step.status === 'success') {
            const rawData = step.metadata?.raw_data || {};
            const relevantInfo = [];
            
            // Try to get execution status from different possible locations
            const executionSuccessful = step.status === 'success' || 
                                       rawData.execution_successful === true || 
                                       step.metadata?.execution_successful === true;
                                       
            relevantInfo.push(`<div><strong>Execution:</strong> ${executionSuccessful ? 'Successful' : 'Failed'}</div>`);
            
            if (rawData.solver || step.solver_name) {
                relevantInfo.push(`<div><strong>Solver:</strong> ${rawData.solver || step.solver_name || 'code_runner'}</div>`);
            }
            
            if (rawData.recommendation || step.recommendation) {
                relevantInfo.push(`<div><strong>Recommendation:</strong> ${rawData.recommendation || step.recommendation}</div>`);
            }
            
            if (rawData.code_runner_recommendation) {
                relevantInfo.push(`<div><strong>Code Runner Recommendation:</strong> ${rawData.code_runner_recommendation}</div>`);
            }
            
            if (relevantInfo.length > 0) {
                content += `
                    <div class="mt-3 code-runner-info">
                        <strong>Execution Info:</strong>
                        <div class="info-block">
                            ${relevantInfo.join('')}
                        </div>
                    </div>
                `;
            }
        }
    } else {
        // For non-code_runner steps
        if (step.response) {
            content += `
                <div class="mt-2">
                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-response-${stepIndex}">
                        <i class="bi bi-arrows-expand"></i> Show Solver Response
                    </button>
                    <pre class="solver-response mt-2 content-collapsible collapsed" id="solver-response-${stepIndex}">${formatCodeBlocks(step.response)}</pre>
                </div>
            `;
        }
        
        if (step.prompt) {
            content += `
                <div class="mt-3">
                    <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-prompt-${stepIndex}">
                        <i class="bi bi-arrows-expand"></i> Show Solver Prompt
                    </button>
                    <pre class="solver-prompt mt-2 content-collapsible collapsed" id="solver-prompt-${stepIndex}">${step.prompt}</pre>
                </div>
            `;
        }
    }
    
    // For code_runner, add toggleable metadata button instead of raw display
    if (step.metadata && step.actor === 'code_runner') {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-metadata-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Additional Details
                </button>
                <div class="solver-metadata mt-2 content-collapsible collapsed" id="solver-metadata-${stepIndex}">
                    <div class="metadata-summary">
                        ${step.metadata.solver_name ? `<div><strong>Solver Name:</strong> ${step.metadata.solver_name}</div>` : ''}
                        ${step.metadata.execution_successful !== undefined ? 
                            `<div><strong>Execution Status:</strong> <span class="${step.metadata.execution_successful ? 'text-success' : 'text-danger'}">${step.metadata.execution_successful ? 'Success' : 'Failed'}</span></div>` : ''}
                    </div>
                </div>
            </div>
        `;
    } else if (step.metadata && step.actor !== 'code_runner') {
        content += `
            <div class="mt-3">
                <button class="btn btn-sm btn-outline-secondary toggle-content-btn" data-target="solver-metadata-${stepIndex}">
                    <i class="bi bi-arrows-expand"></i> Show Metadata
                </button>
                <pre class="step-metadata mt-2 content-collapsible collapsed" id="solver-metadata-${stepIndex}">${JSON.stringify(step.metadata, null, 2)}</pre>
            </div>
        `;
    }
    
    return content;
}

// Helper function to escape HTML special characters
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatVerdictName(verdict) {
    const verdictNames = {
        'satisfied': 'Satisfied',
        'retry': 'Retry',
        'default_to_p4': 'Default to P4'
    };
    return verdictNames[verdict] || verdict;
}

/**
 * Renders a JSON object with collapsible sections for nested objects and arrays
 * @param {Object|Array} data The JSON data to render
 * @param {Number} indent The indentation level (default: 0)
 * @returns {String} HTML string with collapsible JSON
 */
function renderFoldableJSON(data, indent = 0) {
    if (data === null) {
        return '<span class="json-null">null</span>';
    }
    
    if (typeof data === 'boolean') {
        return `<span class="json-boolean">${data}</span>`;
    }
    
    if (typeof data === 'number') {
        return `<span class="json-number">${data}</span>`;
    }
    
    if (typeof data === 'string') {
        // Special handling for very long strings
        if (data.length > 500) {
            const previewLen = Math.min(data.length, 50);
            return `
                <span class="json-property-key collapsible-string" onclick="toggleJsonProperty(this)">
                    <span class="json-string-preview">"${escapeHtml(data.substring(0, previewLen))}${data.length > previewLen ? '...' : ''}"</span>
                </span>
                <div class="code-block collapsed">${escapeHtml(data)}</div>
            `;
        }
        
        // Regular string handling
        return `<span class="json-string">"${escapeHtml(data)}"</span>`;
    }
    
    // Generate indentation for pretty printing
    const indentStr = ' '.repeat(indent * 2);
    const indentStrInner = ' '.repeat((indent + 1) * 2);
    
    // Handle arrays
    if (Array.isArray(data)) {
        if (data.length === 0) {
            return '[]';
        }
        
        // Special handling for journey array
        const isJourneyArray = indent === 0 && data.some(item => item.actor && item.action);
        let html = '';
        
        if (isJourneyArray) {
            html = '<span class="json-property-key" onclick="toggleJsonProperty(this)">Journey Steps</span>: <div class="json-value">';
            
            data.forEach((item, index) => {
                html += `<div class="json-property-key" onclick="toggleJsonProperty(this)">Step ${index + 1}: ${item.actor || ''} - ${item.action || ''}</div>: <div class="json-value collapsed">`;
                html += renderFoldableJSON(item, indent + 1);
                html += '</div><br>';
            });
        } else {
            html = '<span class="json-property-key" onclick="toggleJsonProperty(this)">[</span><div class="json-value">';
            
            data.forEach((item, index) => {
                html += indentStrInner;
                html += renderFoldableJSON(item, indent + 1);
                
                if (index < data.length - 1) {
                    html += ',';
                }
                
                html += '<br>';
            });
        }
        
        html += indentStr + '</div>';
        if (!isJourneyArray) html += ']';
        return html;
    }
    
    // Handle objects
    if (Object.keys(data).length === 0) {
        return '{}';
    }
    
    let html = '<span class="json-property-key" onclick="toggleJsonProperty(this)">{</span><div class="json-value">';
    
    Object.entries(data).forEach(([key, value], index) => {
        const isComplex = value !== null && 
                          typeof value === 'object' && 
                          (Array.isArray(value) ? value.length > 0 : Object.keys(value).length > 0);
        
        // Special handling for code sections
        const isCode = key === 'code' || key === 'prompt' || key === 'code_output' || key === 'full_response';
        const isJourney = key === 'journey' && Array.isArray(value) && value.length > 0;
        
        html += indentStrInner;
        
        if (isJourney) {
            html += `<span class="json-property-key" onclick="toggleJsonProperty(this)">"journey"</span>: `;
            html += renderFoldableJSON(value, indent + 1);
        } else if (isComplex || isCode) {
            html += `<span class="json-property-key" onclick="toggleJsonProperty(this)">"${key}"</span>: `;
            
            if (isCode && typeof value === 'string') {
                html += `<div class="code-block collapsed">${escapeHtml(value)}</div>`;
            } else {
                html += renderFoldableJSON(value, indent + 1);
            }
        } else {
            html += `<span class="json-property">"${key}"</span>: ${renderFoldableJSON(value, indent + 1)}`;
        }
        
        if (index < Object.keys(data).length - 1) {
            html += ',';
        }
        
        html += '<br>';
    });
    
    html += indentStr + '</div>}';
    return html;
}

/**
 * Toggle folding of a JSON section
 * @param {HTMLElement} element The element that was clicked
 */
function toggleJsonFolding(element) {
    // Toggle the collapsed class on the element itself
    element.classList.toggle('collapsed');
    
    // Find the next json-value sibling
    let valueDiv = element.nextElementSibling;
    while (valueDiv && !valueDiv.classList.contains('json-value')) {
        valueDiv = valueDiv.nextElementSibling;
    }
    
    // If we found a value div, toggle its collapsed state
    if (valueDiv) {
        valueDiv.classList.toggle('collapsed');
    }
}

/**
 * Toggle folding of a JSON property
 * @param {HTMLElement} element The element that was clicked
 */
function toggleJsonProperty(element) {
    // Toggle the collapsed class on the element itself
    element.classList.toggle('collapsed');
    
    // The value is the next sibling after the colon and space
    let valueDiv = element.nextElementSibling; // This is the colon and space
    if (valueDiv) {
        valueDiv = valueDiv.nextElementSibling; // This should be the value
    }
    
    // If we found a value div, toggle its collapsed state
    if (valueDiv && (valueDiv.classList.contains('json-value') || valueDiv.classList.contains('code-block'))) {
        valueDiv.classList.toggle('collapsed');
    }
}

/**
 * Escape HTML special characters
 * @param {string} unsafe The unsafe string
 * @returns {string} The escaped string
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Expose the function globally for onclick handlers
window.toggleJsonFolding = toggleJsonFolding;

// Add raw data section with all JSON fields - Modified to use foldable JSON
function addJsonDataSection(content, data) {
    // Process journey array as a special case, prefold all steps
    if (data.journey && Array.isArray(data.journey)) {
        const journeyData = {...data};
        // Pre-process the journey array to handle code sections
        journeyData.journey = data.journey.map(step => {
            const stepCopy = {...step};
            // Special handling for code_runner steps
            if (step.actor === 'code_runner' && step.code) {
                stepCopy._code_display = 'Code section available (click to expand)';
            }
            return stepCopy;
        });
        data = journeyData;
    }
    
    return content + `
        <div class="detail-section">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h4 class="section-title mb-0">Full JSON Data</h4>
                <button class="btn btn-sm btn-outline-secondary toggle-json-btn">
                    <i class="bi bi-arrows-expand"></i> Toggle
                </button>
            </div>
            <div class="card json-data-container" style="display: none;">
                <div class="card-body">
                    <pre class="mb-0" style="max-height: 600px; overflow: auto; font-family: monospace; font-size: 12px; line-height: 1.2; white-space: pre-wrap; word-break: break-word;">${JSON.stringify(data, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
}

// Expose functions to make them accessible from query.js
window.showDetails = showDetails;
window.deduplicateByQueryId = deduplicateByQueryId;
window.extractRunNumber = extractRunNumber;