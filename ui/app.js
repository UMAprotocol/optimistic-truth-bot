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
let disableExperimentRunner = false; // Track if experiment runner is disabled

// Date filter variables
let currentDateFilters = {
    expiration_timestamp: null,
    request_timestamp: null,
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
    request_transaction_block_time: false
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

    // Add event listener for modal shown event to apply syntax highlighting
    document.getElementById('detailsModal')?.addEventListener('shown.bs.modal', function () {
        // Reapply syntax highlighting to all code blocks
        Prism.highlightAllUnder(document.getElementById('detailsModalBody'));
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
    
    // Set up polling for process updates - but at a slower rate since logs are handled separately
    setInterval(loadActiveProcesses, 1000); // Once per second is enough for the list
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
        // Standardize recommendation value
        const rec = (entry.recommendation || entry.proposed_price_outcome || '').toLowerCase();
        
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
        
        // Calculate tag statistics
        if (entry.tags && Array.isArray(entry.tags)) {
            entry.tags.forEach(tag => {
                // Initialize tag stats if not already done
                if (!tagStats[tag]) {
                    tagStats[tag] = {
                        total: 0,
                        correct: 0,
                        incorrect: 0,
                        disputed: 0
                    };
                }
                
                // Update counts only if correctness can be determined
                tagStats[tag].total++;
                
                if (isCorrect === true) {
                    tagStats[tag].correct++;
                } else if (isCorrect === false) {
                    tagStats[tag].incorrect++;
                }
                
                if (entry.disputed === true) {
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
        const rec = entry.recommendation?.toLowerCase() || '';
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
            const [day, month, year] = datePart.split('-');
            return `${month}/${day}/${year.slice(-2)} ${timePart}`;
        }
        
        // Handle formats like "DD-MM-YYYY"
        if (dateStr.match(/^\d{2}-\d{2}-\d{4}$/)) {
            const parts = dateStr.split('-');
            return `${parts[1]}/${parts[0]}/${parts[2].slice(-2)}`;
        }
        
        // Handle other date formats
        const date = new Date(dateStr);
        if (!isNaN(date.getTime())) {
            return `${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getDate().toString().padStart(2, '0')}/${date.getFullYear().toString().slice(-2)}`;
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

// Initialize column selector UI
function initializeColumnSelector() {
    // Add column selector button to results table card header
    const resultsTableHeader = document.querySelector('#resultsTableCard .card-header');
    if (!resultsTableHeader) return;
    
    // Find or create the container for the column selector
    let displayInfoContainer = resultsTableHeader.querySelector('p');
    if (!displayInfoContainer) {
        displayInfoContainer = document.createElement('p');
        displayInfoContainer.className = 'mb-0';
        displayInfoContainer.innerHTML = 'Displaying <span id="displayingCount">0</span> of <span id="totalEntriesCount">0</span> entries';
        resultsTableHeader.appendChild(displayInfoContainer);
    }
    
    // Make the display info container a flex container to align items
    displayInfoContainer.style.display = 'flex';
    displayInfoContainer.style.justifyContent = 'space-between';
    displayInfoContainer.style.alignItems = 'center';
    
    // Split the existing content into its own span
    const entriesInfoSpan = document.createElement('span');
    entriesInfoSpan.innerHTML = displayInfoContainer.innerHTML;
    displayInfoContainer.innerHTML = '';
    displayInfoContainer.appendChild(entriesInfoSpan);
    
    // Create column selector dropdown
    const columnSelector = document.createElement('div');
    columnSelector.className = 'dropdown';
    columnSelector.innerHTML = `
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" id="columnSelectorBtn" 
            data-bs-toggle="dropdown" aria-expanded="false">
            <i class="bi bi-columns-gap"></i> Columns
        </button>
        <div class="dropdown-menu p-2 dropdown-menu-end" id="columnSelectorMenu" aria-labelledby="columnSelectorBtn">
            <h6 class="dropdown-header">Select Columns to Display</h6>
            <div class="column-checkbox-container">
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-timestamp" 
                        ${columnPreferences.timestamp ? 'checked' : ''} data-column="timestamp">
                    <label class="form-check-label" for="col-timestamp">Date</label>
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
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-request_timestamp" 
                        ${columnPreferences.request_timestamp ? 'checked' : ''} data-column="request_timestamp">
                    <label class="form-check-label" for="col-request_timestamp">Request Date</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-request_transaction_block_time" 
                        ${columnPreferences.request_transaction_block_time ? 'checked' : ''} data-column="request_transaction_block_time">
                    <label class="form-check-label" for="col-request_transaction_block_time">Request Block Time</label>
                </div>
                <div class="form-check">
                    <input class="form-check-input column-checkbox" type="checkbox" id="col-id" 
                        ${columnPreferences.id ? 'checked' : ''} data-column="id">
                    <label class="form-check-label" for="col-id">ID</label>
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
                    <label class="form-check-label" for="col-block_number">Block Number</label>
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
            <div class="dropdown-divider"></div>
            <div class="d-flex justify-content-between px-2">
                <button class="btn btn-sm btn-outline-secondary" id="resetColumnDefaults">
                    Reset Defaults
                </button>
                <button class="btn btn-sm btn-primary" id="applyColumnSelection">
                    Apply
                </button>
            </div>
        </div>
    `;
    
    displayInfoContainer.appendChild(columnSelector);
    
    // Add event listeners for column selection
    document.querySelectorAll('.column-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', function() {
            const column = this.getAttribute('data-column');
            columnPreferences[column] = this.checked;
        });
    });
    
    // Add event listener for apply button
    document.getElementById('applyColumnSelection')?.addEventListener('click', function() {
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
            request_transaction_block_time: false
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
        // Try to fetch from the API endpoint
        const response = await fetch('/api/results-directories');
        
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
        
        return `
        <tr class="experiment-row" data-directory="${experiment.directory}" data-source="${isMongoDBSource ? 'mongodb' : 'filesystem'}">
            <td>
                <div>
                    <span class="experiment-date">${sourceIcon}${formattedDate}</span>
                    ${experiment.count ? `<span class="badge bg-primary ms-1">${experiment.count} items</span>` : ''}
                    <span class="experiment-title">${experiment.title || experiment.directory}</span>
                </div>
                ${experimentGoal ? `<div class="experiment-description">${experimentGoal}</div>` : ''}
            </td>
        </tr>
    `}).join('');
    
    // Add click event to rows
    document.querySelectorAll('.experiment-row').forEach(row => {
        row.addEventListener('click', () => {
            const directory = row.getAttribute('data-directory');
            const source = row.getAttribute('data-source');
            loadExperimentData(directory, source);
            
            // Highlight the selected row
            document.querySelectorAll('.experiment-row').forEach(r => {
                r.classList.remove('table-active');
            });
            row.classList.add('table-active');
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
        
        // Show loading spinner in experiment metadata card instead of content
        const metadataContainer = document.getElementById('experimentMetadataCard');
        const metadataContent = document.getElementById('experimentMetadataContent');
        if (metadataContainer && metadataContent) {
            metadataContainer.style.display = 'block';
            metadataContent.innerHTML = `
                <div class="text-center py-4">
                    <div class="spinner-border text-primary mb-3" role="status">
                        <span class="visually-hidden">Loading metadata...</span>
                    </div>
                    <p class="mt-2">Loading experiment metadata...</p>
                </div>
            `;
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
                                                    // Check for duplicate data by using ID or content hash
                                                    const dataId = jsonData.query_id || jsonData.id || 
                                                                jsonData._id || JSON.stringify(jsonData);
                                                    
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
                                                // Check for duplicate data by using ID or content hash
                                                const dataId = jsonData.query_id || jsonData.id || 
                                                              jsonData._id || JSON.stringify(jsonData);
                                                
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
            
            // Display the experiment metadata properly now that data is loaded
            displayExperimentMetadata();
            
            // Populate the table with data
            displayResultsData();
            
            // Apply the current filter
            applyTableFilter(currentFilter);
            
            // ADDED: Initialize charts AFTER the analytics tabs are shown
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
        document.getElementById('filterControls').style.display = 'none';
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = 'none';
        }
        
        // Still display experiment metadata even on error
        displayExperimentMetadata();
        
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
    
    // Determine data source - use explicit source if available, otherwise infer
    const isMongoDBSource = currentExperiment.explicitSource === 'mongodb' || 
                           currentExperiment.source === 'mongodb' || 
                           currentExperiment.path?.startsWith('mongodb/');
    
    const sourceType = isMongoDBSource ? 'MongoDB' : 'Filesystem';
    const sourceIcon = isMongoDBSource ? 
        '<i class="bi bi-database-fill" title="MongoDB Data Source"></i>' : 
        '<i class="bi bi-folder-fill" title="Filesystem Data Source"></i>';
    
    // Extract the experiment info from metadata
    const experimentInfo = currentExperiment.metadata?.experiment || {};
    
    // Get system prompt from metadata or modifications
    const systemPrompt = experimentInfo.system_prompt || 
                       (currentExperiment.metadata?.modifications?.system_prompt);
    
    // Basic metadata display
    let metadata = `
        <div class="metadata-section">
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Title:</strong>
                </div>
                <div class="col-md-8">
                    ${currentExperiment.title || currentExperiment.directory}
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
            
            ${currentExperiment.timestamp || (experimentInfo.timestamp ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Date:</strong>
                </div>
                <div class="col-md-8">
                    ${formatDisplayDate(currentExperiment.timestamp || experimentInfo.timestamp)}
                </div>
            </div>
            ` : '')}
            
            ${currentExperiment.goal || experimentInfo.goal ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Goal:</strong>
                </div>
                <div class="col-md-8">
                    ${currentExperiment.goal || experimentInfo.goal}
                </div>
            </div>
            ` : ''}
        </div>
    `;
    
    // Add system prompt toggle with improved styling if system prompt exists
    if (systemPrompt) {
        metadata += `<div class="mt-3 mb-2">
            <a href="#" id="toggleSystemPrompt" class="d-inline-flex align-items-center">
                <strong>System Prompt</strong> <i class="bi bi-chevron-down ms-1"></i>
            </a>
        </div>`;
    }
    
    // Show detailed metadata if available
    if (currentExperiment.metadata) {
        // Format and append the structured metadata
        if (Object.keys(experimentInfo).length > 0) {
            metadata += '<hr>';
            metadata += '<h4>Experiment Details</h4>';
            metadata += '<div class="metadata-section">';
            
            // Loop through experiment metadata
            for (const [key, value] of Object.entries(experimentInfo)) {
                // Skip already displayed fields and system_prompt (handled separately)
                if (['title', 'timestamp', 'goal', 'system_prompt'].includes(key)) continue;
                
                if (key === 'setup' && typeof value === 'object') {
                    // Render setup as a card with a table
                    metadata += `
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <strong>${formatKeyName(key)}:</strong>
                        </div>
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-body p-0">
                                    <table class="table table-sm mb-0">
                                        <tbody>
                    `;
                    
                    // Loop through setup properties
                    for (const [setupKey, setupValue] of Object.entries(value)) {
                        metadata += `
                        <tr>
                            <th style="width: 40%">${formatKeyName(setupKey)}</th>
                            <td>${formatValue(setupValue)}</td>
                        </tr>
                        `;
                    }
                    
                    metadata += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                } else if (key === 'modifications' && typeof value === 'object') {
                    // Render modifications as a card with a table
                    metadata += `
                    <div class="row mb-3">
                        <div class="col-md-4">
                            <strong>${formatKeyName(key)}:</strong>
                        </div>
                        <div class="col-md-8">
                            <div class="card">
                                <div class="card-body p-0">
                                    <table class="table table-sm mb-0">
                                        <tbody>
                    `;
                    
                    // Loop through modifications
                    for (const [modKey, modValue] of Object.entries(value)) {
                        // Skip system_prompt as it's handled separately
                        if (modKey === 'system_prompt') continue;
                        
                        metadata += `
                        <tr>
                            <th style="width: 40%">${formatKeyName(modKey)}</th>
                            <td>${formatValue(modValue)}</td>
                        </tr>
                        `;
                    }
                    
                    metadata += `
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
                } else {
                    // Regular fields
                    metadata += `
                    <div class="row mb-2">
                        <div class="col-md-4">
                            <strong>${formatKeyName(key)}:</strong>
                        </div>
                        <div class="col-md-8">
                            ${formatValue(value)}
                        </div>
                    </div>
                    `;
                }
            }
            
            metadata += '</div>';
        }
        
        // Add modifications section if it exists at the root metadata level
        if (currentExperiment.metadata.modifications && !experimentInfo.modifications) {
            metadata += '<hr>';
            metadata += '<h4>Modifications</h4>';
            metadata += '<div class="metadata-section">';
            
            const modifications = currentExperiment.metadata.modifications;
            for (const [key, value] of Object.entries(modifications)) {
                // Skip system_prompt as it's handled separately
                if (key === 'system_prompt') continue;
                
                metadata += `
                <div class="row mb-2">
                    <div class="col-md-4">
                        <strong>${formatKeyName(key)}:</strong>
                    </div>
                    <div class="col-md-8">
                        ${formatValue(value)}
                    </div>
                </div>
                `;
            }
            
            metadata += '</div>';
        }
        
        // Add setup section if it exists at the root metadata level
        if (currentExperiment.metadata.setup && !experimentInfo.setup) {
            metadata += '<hr>';
            metadata += '<h4>Setup</h4>';
            metadata += '<div class="metadata-section">';
            
            const setup = currentExperiment.metadata.setup;
            for (const [key, value] of Object.entries(setup)) {
                metadata += `
                <div class="row mb-2">
                    <div class="col-md-4">
                        <strong>${formatKeyName(key)}:</strong>
                    </div>
                    <div class="col-md-8">
                        ${formatValue(value)}
                    </div>
                </div>
                `;
            }
            
            metadata += '</div>';
        }
    }
    
    // Set the content and show the card
    metadataContent.innerHTML = metadata;
    metadataCard.style.display = 'block';
    
    // Check if overlay container exists, create if not
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
    if (columnPreferences.proposal_timestamp) headerRow += '<th class="col-proposal-time">Request Time</th>';
    if (columnPreferences.expiration_timestamp) headerRow += '<th class="col-expiration-time">Expiration Time</th>';
    if (columnPreferences.request_timestamp) headerRow += '<th class="col-request-time">Request Time</th>';
    if (columnPreferences.request_transaction_block_time) headerRow += '<th class="col-block-time">Block Time</th>';
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
    
    // Sort the data based on current sort settings
    const sortedData = sortData([...dataArray], currentSort.column, currentSort.direction);
    
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
        
        // Use standardized recommendation field, with fallbacks
        const recommendation = item.recommendation || 
                              item.proposed_price_outcome || 
                              'N/A';
        
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
            (item.proposal_metadata && item.proposal_metadata.request_timestamp ? 
                formatDate(item.proposal_metadata.request_timestamp) : 'N/A');
        
        // Format the expiration timestamp if available
        const expirationTimestamp = item.proposal_metadata?.expiration_timestamp || 0;
        const formattedExpirationDate = expirationTimestamp ? formatDate(expirationTimestamp) : 'N/A';
        
        // Format the request timestamp if available
        const requestTimestamp = item.proposal_metadata?.request_timestamp || 0;
        const formattedRequestDate = requestTimestamp ? formatDate(requestTimestamp) : 'N/A';
        
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
        
        // Store the original data index as a data attribute for the full dataset
        // This ensures we have the correct index when clicking a row
        const originalDataIndex = dataArray === currentData ? 
            currentData.indexOf(item) : currentData.indexOf(item);
        
        // Build the row based on selected columns
        let row = `<tr class="result-row ${recommendation?.toLowerCase() === 'p4' || recommendation?.toLowerCase() === 'p3' ? 'table-warning' : ''}" data-item-id="${originalDataIndex}">`;
        
        // Add icon as the first cell if available
        if (item.icon) {
            row += `<td class="icon-cell"><img src="${item.icon}" alt="Question Icon" class="table-icon"></td>`;
        } else {
            row += `<td class="icon-cell"></td>`;
        }
        
        // Add cells based on column preferences
        if (columnPreferences.timestamp) row += `<td>${formattedDate}</td>`;
        if (columnPreferences.proposal_timestamp) row += `<td>${formattedProposalDate}</td>`;
        if (columnPreferences.expiration_timestamp) row += `<td>${formattedExpirationDate}</td>`;
        if (columnPreferences.request_timestamp) row += `<td>${formattedRequestDate}</td>`;
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
            // Use the data item ID to get the correct data item from currentData
            const itemId = parseInt(row.getAttribute('data-item-id'));
            showDetails(currentData[itemId], itemId);
            
            // Add selected class to the clicked row
            document.querySelectorAll('.result-row').forEach(r => r.classList.remove('table-active'));
            row.classList.add('table-active');
        });
        
        // Add hover cursor style to indicate clickable rows
        row.style.cursor = 'pointer';
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
    
    if (!modalTitle || !modalBody) return;
    
    // Get title directly from the data using our extraction function
    const title = extractTitle(data) || 'Details';
    
    // Set the modal title with icon if available
    if (data.icon) {
        modalTitle.innerHTML = `<img src="${data.icon}" alt="Question Icon" class="modal-icon"> ${title}`;
    } else {
        modalTitle.textContent = title;
    }
    
    // Check if disputed
    const isDisputed = data.disputed === true;
    
    // Get proposed price if available, being careful with 0 values
    // Handle both old and new file structures
    const proposedPrice = data.proposed_price_outcome !== undefined ? data.proposed_price_outcome : 
                         (data.proposed_price !== undefined ? data.proposed_price : 
                         (data.proposal_metadata?.proposed_price_outcome !== undefined ? data.proposal_metadata.proposed_price_outcome : 
                         (data.proposal_metadata?.proposed_price !== undefined ? data.proposal_metadata.proposed_price : 'N/A')));
    
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
    const resolvedPrice = data.resolved_price_outcome || data.resolved_price || 
                         data.proposal_metadata?.resolved_price_outcome || data.proposal_metadata?.resolved_price || 'Unresolved';
    
    // Generate the content
    let content = `
        <div class="alert ${alertClass} mb-4">
            <strong>Recommendation:</strong> ${data.recommendation || 'N/A'} | 
            <strong>Proposed:</strong> ${proposedPrice} | 
            <strong>Resolved:</strong> ${resolvedPrice} | 
            <strong>Disputed:</strong> ${isDisputed ? 'Yes' : 'No'} | 
            <strong>Correct:</strong> ${correctnessText}
        </div>
    `;
    
    // Add tags section if available
    // Check both potential locations for tags
    const tags = data.tags || data.proposal_metadata?.tags;
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
    const condition_id = data.condition_id || data.proposal_metadata?.condition_id || '';
    const process_time = data.timestamp || 0;
    const request_time = data.proposal_metadata?.request_timestamp || 0;
    const block_time = data.proposal_metadata?.request_transaction_block_time || 0;
    const expiration_time = data.proposal_metadata?.expiration_timestamp || 0;
    const end_date = data.end_date_iso || data.proposal_metadata?.end_date_iso || 'N/A';
    const game_start_time = data.game_start_time || data.proposal_metadata?.game_start_time || 'N/A';
    
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
                            <th>Request Time</th>
                            <td>${formatDate(request_time)}</td>
                        </tr>
                        <tr>
                            <th>Block Time</th>
                            <td>${formatDate(block_time)}</td>
                        </tr>
                        <tr>
                            <th>Expiration Time</th>
                            <td>${formatDate(expiration_time)}</td>
                        </tr>
                        <tr>
                            <th>End Date</th>
                            <td>${end_date}</td>
                        </tr>
                        ${game_start_time !== 'N/A' ? `
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

    // Add multi-operator data section if available
    if (data.router_result || data.attempted_solvers) {
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
                    </div>
                </div>
            `;
        }
        
        // Add solver results
        if (data.solver_results && Array.isArray(data.solver_results) && data.solver_results.length > 0) {
            content += `<h5 class="mb-3">Solver Results</h5>`;
            
            data.solver_results.forEach((solverResult, index) => {
                const executionStatus = solverResult.execution_successful === true ? 
                    '<span class="execution-successful"><i class="bi bi-check-circle-fill"></i> Success</span>' : 
                    '<span class="execution-failed"><i class="bi bi-x-circle-fill"></i> Failed</span>';
                
                content += `
                    <div class="solver-card">
                        <div class="solver-header">
                            <div class="solver-name">${solverResult.solver || 'Unknown Solver'}</div>
                            <div class="d-flex align-items-center">
                                <div class="solver-attempt me-3">Attempt ${solverResult.attempt || index + 1}</div>
                                <div>${executionStatus}</div>
                            </div>
                        </div>
                        <div class="solver-body">
                            <div><strong>Recommendation:</strong> ${solverResult.recommendation || 'N/A'}</div>
                            
                            ${solverResult.response ? `
                                <div class="mt-2">
                                    <strong>Response:</strong>
                                    <pre class="response-text mt-2">${formatCodeBlocks(solverResult.response)}</pre>
                                </div>
                            ` : ''}
                            
                            ${solverResult.solver_result && solverResult.solver_result.code ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Generated Code</span>
                                        <button class="copy-btn" onclick="navigator.clipboard.writeText(\`${solverResult.solver_result.code.replace(/`/g, '\\`')}\`)">Copy</button>
                                    </div>
                                    <div class="code-content">
                                        <pre><code class="language-python">${solverResult.solver_result.code}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.code ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Generated Code</span>
                                        <button class="copy-btn" onclick="navigator.clipboard.writeText(\`${solverResult.code.replace(/`/g, '\\`')}\`)">Copy</button>
                                    </div>
                                    <div class="code-content">
                                        <pre><code class="language-python">${solverResult.code}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.code_output ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Code Output</span>
                                    </div>
                                    <div class="code-content">
                                        <pre><code class="language-plaintext">${solverResult.code_output}</code></pre>
                                    </div>
                                </div>
                            ` : ''}
                            
                            ${solverResult.solver_result && solverResult.solver_result.code_output ? `
                                <div class="code-section">
                                    <div class="code-header">
                                        <span>Code Output</span>
                                    </div>
                                    <div class="code-content">
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
    }
    
    // Add overseer section for both old and new file structures
    // Get overseer data from both potential locations 
    const overseerData = data.overseer_data || data.overseer_result || null;
    
    if (overseerData) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Overseer Data</h4>
                <div class="card">
                    <div class="card-body">
                        ${overseerData.attempts ? `<div><strong>Attempts:</strong> ${overseerData.attempts}</div>` : ''}
                        ${overseerData.market_price_info ? `
                            <div class="mt-2">
                                <strong>Market Price Info:</strong> ${overseerData.market_price_info}
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
                                                    <th>Critique</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                ${overseerData.recommendation_journey.map(journey => `
                                                    <tr>
                                                        <td>${journey.attempt}</td>
                                                        <td>${journey.perplexity_recommendation || 'N/A'}</td>
                                                        <td>${formatSatisfactionLevel(journey.overseer_satisfaction_level)}</td>
                                                        <td>${journey.critique || 'N/A'}</td>
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
                                                            <strong>Response:</strong>
                                                            <pre class="response-text mt-2">${formatCodeBlocks(interaction.response)}</pre>
                                                        </div>
                                                    ` : ''}
                                                    ${interaction.metadata ? `
                                                        <div class="mt-3">
                                                            <strong>Metadata:</strong>
                                                            <pre class="mt-2 metadata-json">${JSON.stringify(interaction.metadata, null, 2)}</pre>
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
                                        </table>
                                    </div>
                                </div>
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
                        <div class="p-3">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <strong>Full Metadata:</strong>
                                <button class="btn btn-sm btn-outline-secondary toggle-metadata-btn">Toggle Full View</button>
                            </div>
                            <pre class="mb-0 json-data" style="display: none;">${JSON.stringify(data.proposal_metadata, null, 2)}</pre>
                        </div>
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
    
    // Add raw data section with all JSON fields
    content += `
        <div class="detail-section">
            <h4 class="section-title">Full JSON Data</h4>
            <div class="card">
                <div class="card-body">
                    <pre class="mb-0 json-data">${JSON.stringify(data, null, 2)}</pre>
                </div>
            </div>
        </div>
    `;
    
    // Set the modal content
    modalBody.innerHTML = content;
    
    // Apply syntax highlighting to code blocks
    Prism.highlightAllUnder(modalBody);
    
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
    
    // Add toggle functionality for metadata JSON
    document.querySelectorAll('.toggle-metadata-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const jsonData = this.parentElement.nextElementSibling;
            if (jsonData.style.display === 'none') {
                jsonData.style.display = 'block';
                this.textContent = 'Hide Full View';
            } else {
                jsonData.style.display = 'none';
                this.textContent = 'Toggle Full View';
            }
        });
    });
    
    // Show the modal
    modal.show();
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
    
    if (currentDateFilters.request_timestamp) {
        filteredData = filteredData.filter(item => {
            const request = item.proposal_metadata?.request_timestamp;
            if (!request) return false;
            
            // Filter for items with request date on or after the selected date
            return request >= currentDateFilters.request_timestamp;
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
                <td colspan="5" class="text-center text-muted">No tag data available</td>
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
        const stats = tagStats[tag] || { total: 0, correct: 0, incorrect: 0, accuracyPercent: 0 };
        
        // Ensure we have valid numbers
        const total = stats.total || 0;
        const correct = stats.correct || 0;
        const incorrect = stats.incorrect || 0;
        
        // Recalculate accuracy to ensure it's correct
        const accuracyPercent = total > 0 ? (correct / total) * 100 : 0;
        
        const accuracyClass = accuracyPercent >= 80 ? 'high-accuracy' : 
                             (accuracyPercent >= 50 ? 'medium-accuracy' : 'low-accuracy');
        
        return `
            <tr>
                <td><span class="tag-badge">${tag}</span></td>
                <td>${total}</td>
                <td class="accuracy-cell ${accuracyClass}">${accuracyPercent.toFixed(1)}%</td>
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
        
        // Final fallback - try to list the parent directory
        try {
            console.log('Trying to list parent directory as fallback...');
            const parentPath = dirPath.substring(0, dirPath.lastIndexOf('/'));
            const parentResponse = await fetch(`/api/files?path=${encodeURIComponent(parentPath)}`);
            
            if (parentResponse.ok) {
                const data = await parentResponse.json();
                console.log(`Found ${data.count || 0} files in parent directory ${parentPath}`);
                
                // Look for subdirectories matching our target
                const targetDir = dirPath.split('/').pop();
                const subdirs = data.files.filter(file => file.type === 'directory' && file.name === targetDir);
                
                if (subdirs.length > 0) {
                    console.log(`Found matching subdirectory: ${subdirs[0].path}`);
                    
                    // Try to access this directory
                    const subDirResponse = await fetch(`/api/files?path=${encodeURIComponent(subdirs[0].path)}`);
                    if (subDirResponse.ok) {
                        const subDirData = await subDirResponse.json();
                        const jsonFiles = subDirData.files
                            .filter(file => file.type === 'file' && (file.file_type === 'json' || file.name.endsWith('.json')))
                            .map(file => file.name);
                        
                        if (jsonFiles.length > 0) {
                            console.log(`Found ${jsonFiles.length} JSON files in subdirectory`);
                            return jsonFiles;
                        }
                    }
                }
            }
        } catch (err) {
            console.warn('Error listing parent directory:', err);
        }
        
        // Last resort - try a hardcoded list of filenames if nothing else worked
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
                         (a.proposal_metadata && a.proposal_metadata.request_timestamp ? 
                             a.proposal_metadata.request_timestamp : 0);
                valueB = b.proposal_timestamp || 
                         (b.proposal_metadata && b.proposal_metadata.request_timestamp ? 
                             b.proposal_metadata.request_timestamp : 0);
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
        'col-request-time': 'request_timestamp',
        'col-block-time': 'request_transaction_block_time',
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
            (item.proposal_metadata && item.proposal_metadata.request_timestamp) ? 
            item.proposal_metadata.request_timestamp : 0;
        
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
        request_timestamp: null,
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