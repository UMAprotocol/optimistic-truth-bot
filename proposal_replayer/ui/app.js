// Global variables to store data and charts
let currentData = [];
let currentExperiment = null;
let experimentsData = [];
let modal = null;
let currentFilter = 'all'; // Track current filter state
let currentSearch = ''; // Track current search term
let currentSourceFilter = 'all'; // Track current source filter

// Chart variables
let recommendationChart = null;
let resolutionChart = null;

// Experiment runner variables
let activeProcesses = [];
let commandHistory = [];
let currentProcessId = null;

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modal
    modal = new bootstrap.Modal(document.getElementById('detailsModal'));
    
    // Initialize tab functionality
    initializeTabs();
    
    // Load experiments directory data
    loadExperimentsData();

    // Setup tag filter when data is loaded
    document.addEventListener('dataLoaded', setupTagFilter);

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
    
    // Set up source filter buttons
    document.getElementById('filterSourceAll')?.addEventListener('click', () => {
        applySourceFilter('all');
    });
    
    document.getElementById('filterSourceFilesystem')?.addEventListener('click', () => {
        applySourceFilter('filesystem');
    });
    
    document.getElementById('filterSourceMongoDB')?.addEventListener('click', () => {
        applySourceFilter('mongodb');
    });
    
    // Set up clear tag filter button
    document.getElementById('clearTagFilter')?.addEventListener('click', clearTagFilter);
    
    // Set up logout button
    document.getElementById('logoutBtn')?.addEventListener('click', handleLogout);
    
    // Set up experiment runner events
    initializeExperimentRunner();
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
    // Load command history from localStorage
    loadCommandHistory();
    
    // Handle experiment form submission
    const experimentForm = document.getElementById('experimentForm');
    if (experimentForm) {
        experimentForm.addEventListener('submit', (event) => {
            event.preventDefault();
            const commandInput = document.getElementById('commandInput');
            const command = commandInput.value.trim();
            
            if (command) {
                // Start a new process via the API
                startProcess(command);
            }
        });
    }
    
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

// Show logs for a history entry
async function showHistoryLogs(historyEntry) {
    try {
        // Update the logs title first to provide immediate feedback
        const logsTitle = document.getElementById('logsTitle');
        if (logsTitle) {
            logsTitle.innerHTML = `Process Logs: <code>${historyEntry.command}</code> <span class="loading-indicator"><i class="bi bi-hourglass"></i> Loading...</span>`;
        }
        
        // Clear current logs to show we're loading new ones
        const logsContainer = document.getElementById('processLogs');
        if (logsContainer) {
            logsContainer.innerHTML = `
                <div class="text-center p-3">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading logs...</span>
                    </div>
                    <p class="mt-2">Loading logs for: ${historyEntry.command}</p>
                </div>
            `;
        }
        
        // Check if this is an active process
        const activeProcess = activeProcesses.find(p => p.id === historyEntry.id);
        if (activeProcess) {
            // If it's an active process, just select it and show current logs
            currentProcessId = historyEntry.id;
            updateProcessLogs(historyEntry.id);
        } else {
            console.log(`Fetching historical logs for process ID: ${historyEntry.id}`);
            
            // First check if we have logs in the history entry
            if (historyEntry.logs && historyEntry.logs.length > 0) {
                console.log(`Using cached logs for process: ${historyEntry.command}`);
                
                // Generate log entries from the cached logs
                const logHtml = historyEntry.logs.map(log => {
                    const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
                    return `<div class="log-entry log-${log.type || 'info'}"><span class="log-timestamp">[${formattedTime}]</span><span class="log-message">${log.message}</span></div>`;
                }).join('');
                
                logsContainer.innerHTML = logHtml;
                
                // Scroll to bottom to show the most recent logs
                logsContainer.scrollTop = logsContainer.scrollHeight;
                
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
                
                // Scroll to bottom to show the most recent logs
                logsContainer.scrollTop = logsContainer.scrollHeight;
                
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
                        
                        // Scroll to bottom to show the most recent logs
                        logsContainer.scrollTop = logsContainer.scrollHeight;
                        
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
async function startProcess(command) {
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
            logsContainer.scrollTop = logsContainer.scrollHeight;
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
        if (historyEntry && processId) {
            const entryIndex = commandHistory.findIndex(h => h.id === historyEntry.id);
            if (entryIndex !== -1) {
                commandHistory[entryIndex].id = processId;
                localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
            }
        }
        
        // Set current process ID
        currentProcessId = processId;
        
        // Add spinner to show we're still loading logs
        const spinner = document.createElement('div');
        spinner.className = 'text-center mt-3';
        spinner.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Running command...</span>
            </div>
        `;
        logsContainer.appendChild(spinner);
        
        // Force an immediate refresh of active processes to get the new process
        await loadActiveProcesses();
        
        // Update tables
        updateProcessesTable();
        updateCommandHistoryTable();
        
        // Start a more aggressive polling for logs
        let processedLogLines = 0;
        let lastContent = "";
        
        // Start the log polling interval
        const logPollingInterval = setInterval(async () => {
            try {
                // Get the latest process status
                const activeProcess = activeProcesses.find(p => p.id === processId);
                if (!activeProcess) {
                    // Process isn't in the active list anymore, might have completed
                    const response = await fetch(`/api/process/${processId}?t=${Date.now()}`);
                    if (response.ok) {
                        const data = await response.json();
                        if (data.logs && data.logs.length > 0) {
                            // Stream ALL logs at once for completed processes
                            appendLogsToDisplay(logsContainer, data.logs, 0);
                            
                            // Update tables
                            await loadActiveProcesses();
                            updateProcessesTable();
                            updateCommandHistoryTable();
                            
                            // Remove spinner
                            const existingSpinner = logsContainer.querySelector('.spinner-border');
                            if (existingSpinner) {
                                existingSpinner.parentElement.remove();
                            }
                            
                            // Update log title with status
                            if (logsTitle) {
                                const statusBadge = data.status ? 
                                    `<span class="badge ${
                                        data.status === 'completed' ? 'bg-success' : 
                                        data.status === 'failed' ? 'bg-danger' : 
                                        data.status === 'stopped' ? 'bg-warning' : 'bg-primary'
                                    }">${data.status}</span>` : '';
                                
                                logsTitle.innerHTML = `Process Logs: <code>${command}</code> ${statusBadge}`;
                            }
                        }
                    }
                    clearInterval(logPollingInterval);
                    return;
                }
                
                // Skip if no logs
                if (!activeProcess.logs || activeProcess.logs.length === 0) {
                    return;
                }
                
                // If we have more logs than before, append them immediately
                if (activeProcess.logs.length > processedLogLines) {
                    // Check content difference using a hash to avoid unnecessary DOM updates
                    const newContent = activeProcess.logs.map(log => log.message).join('\n');
                    if (newContent !== lastContent) {
                        // Get only the new logs
                        const newLogs = activeProcess.logs.slice(processedLogLines);
                        
                        // Append each new log line individually
                        appendLogsToDisplay(logsContainer, newLogs, processedLogLines);
                        
                        // Update the processed line count
                        processedLogLines = activeProcess.logs.length;
                        lastContent = newContent;
                    }
                }
                
                // If process is completed, update UI and stop polling
                if (activeProcess.status !== 'running') {
                    // Remove spinner
                    const existingSpinner = logsContainer.querySelector('.spinner-border');
                    if (existingSpinner) {
                        existingSpinner.parentElement.remove();
                    }
                    
                    // Update log title with final status
                    if (logsTitle) {
                        const statusBadge = activeProcess.status ? 
                            `<span class="badge ${
                                activeProcess.status === 'completed' ? 'bg-success' : 
                                activeProcess.status === 'failed' ? 'bg-danger' : 
                                activeProcess.status === 'stopped' ? 'bg-warning' : 'bg-primary'
                            }">${activeProcess.status}</span>` : '';
                        
                        logsTitle.innerHTML = `Process Logs: <code>${command}</code> ${statusBadge}`;
                    }
                    
                    // Stop polling
                    clearInterval(logPollingInterval);
                    
                    // Do one final update of tables
                    await loadActiveProcesses();
                    updateProcessesTable();
                    updateCommandHistoryTable();
                }
            } catch (error) {
                console.warn('Error in log polling:', error);
            }
        }, 100); // Poll 10 times per second for more responsive logs
        
        // Clear command input
        const commandInput = document.getElementById('commandInput');
        if (commandInput) {
            commandInput.value = '';
        }
        
        return data;
    } catch (error) {
        console.error('Error starting process:', error);
        
        // Show error message in logs
        const logsContainer = document.getElementById('processLogs');
        if (logsContainer) {
            logsContainer.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>
                    Error running command: ${error.message}
                </div>
            `;
        }
        
        // Update status in command history to failed
        const historyEntries = commandHistory.filter(h => h.command === command && h.status === 'running');
        historyEntries.forEach(entry => {
            entry.status = 'failed';
        });
        
        // Save updated history to localStorage
        localStorage.setItem('commandHistory', JSON.stringify(commandHistory));
        
        // Update history table
        updateCommandHistoryTable();
        
        // Update the logs title
        const logsTitle = document.getElementById('logsTitle');
        if (logsTitle) {
            logsTitle.innerHTML = `Process Logs: <code>${command}</code> <span class="badge bg-danger">Failed</span>`;
        }
        
        return null;
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
    
    // Was the container scrolled to the bottom before adding content?
    const wasAtBottom = logsContainer.scrollHeight - logsContainer.scrollTop <= logsContainer.clientHeight + 50;
    
    // Loop through each log entry and add it to the display
    logs.forEach((log, index) => {
        const formattedTime = formatLogTime(new Date(log.timestamp * 1000));
        const logEntry = document.createElement('div');
        logEntry.className = `log-entry log-${log.type || 'info'}`;
        logEntry.innerHTML = `<span class="log-timestamp">[${formattedTime}]</span><span class="log-message">${log.message}</span>`;
        logsContainer.appendChild(logEntry);
    });
    
    // Scroll to bottom if we were already at the bottom
    if (wasAtBottom) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
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
                    
                    // Update logs if we have more logs than before OR we're still running
                    if (currentLogs.length !== prevLogs.length || process.status === 'running') {
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
        } else {
            console.error('Failed to load processes');
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

// Update the process logs display
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
        return;
    }
    
    // Clear container and show all logs
    logsContainer.innerHTML = '';
    appendLogsToDisplay(logsContainer, process.logs, 0);
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
        
        // Set fixed height to prevent excessive resizing
        document.getElementById('recommendationChart').height = 200;
        document.getElementById('resolutionChart').height = 200;
        
        // Initialize recommendation chart
        const recommendationChartCtx = document.getElementById('recommendationChart').getContext('2d');
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
        const resolutionChartCtx = document.getElementById('resolutionChart').getContext('2d');
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
    
    // Update counts
    document.getElementById('correctCount').textContent = analytics.correctCount;
    document.getElementById('incorrectCount').textContent = analytics.incorrectCount;
    document.getElementById('totalCount').textContent = analytics.totalCount;
    document.getElementById('noDataCount').textContent = analytics.noDataCount;
    
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
    if (!timestamp) return 'N/A';
    
    try {
        // Handle string timestamps that are in ISO format
        if (typeof timestamp === 'string') {
            // Try parsing as ISO format first
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
        // Handle formats like "13-03-2025"
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

// Load data about available experiment directories
async function loadExperimentsData() {
    try {
        // Try to fetch from the API endpoint
        const response = await fetch('/api/results-directories');
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        experimentsData = await response.json();
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
    if (currentSourceFilter !== 'all') {
        filteredExperiments = filteredExperiments.filter(exp => {
            const isMongoDBSource = exp.source === 'mongodb' || exp.path?.startsWith('mongodb/');
            return (currentSourceFilter === 'mongodb' && isMongoDBSource) || 
                   (currentSourceFilter === 'filesystem' && !isMongoDBSource);
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
        let formattedDate = formatDisplayDate(experiment.timestamp);
        
        // For MongoDB sources, make sure we're using the experiment metadata
        const experimentGoal = experiment.goal || (experiment.metadata && experiment.metadata.experiment?.goal) || '';
        
        return `
        <tr class="experiment-row" data-directory="${experiment.directory}" data-source="${isMongoDBSource ? 'mongodb' : 'filesystem'}">
            <td>
                <div>
                    <span class="experiment-date">${sourceIcon}${formattedDate}</span>
                    <span class="experiment-title">${experiment.title || experiment.directory}</span>
                </div>
                ${experimentGoal ? `<div class="experiment-description">${experimentGoal}</div>` : ''}
                ${experiment.count ? `<div class="badge bg-primary ms-2">${experiment.count} items</div>` : ''}
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
        
        // Display the experiment metadata
        displayExperimentMetadata();
        
        // Initially show sections - we'll hide analytics if needed
        document.getElementById('analyticsDashboard').style.display = 'block';
        document.getElementById('filterControls').style.display = 'flex';
        document.getElementById('resultsTableCard').style.display = 'block';
        document.querySelector('.results-section').style.display = 'block';
        
        // Hide tag filter until we know if we have tags
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = 'none';
        }
        
        // Reset analytics display with empty data
        updateAnalyticsDisplay(null);
        
        // Set the results table title
        document.getElementById('resultsTableTitle').textContent = `${currentExperiment.title || directory} Results`;
        
        // Initialize charts for this experiment
        initializeCharts();
        
        // Check the source of the experiment data
        const isMongoDBSource = source === 'mongodb' || 
                               currentExperiment.source === 'mongodb' || 
                               currentExperiment.path?.startsWith('mongodb/');
        
        // Show loading indicator
        document.getElementById('resultsTableBody').innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading results from ${isMongoDBSource ? 'MongoDB' : currentExperiment.path}...</p>
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
                // Load specific files from the outputs directory since directory browsing might not work
                const response = await fetch(`/api/results-directories`);
                if (response.ok) {
                    // Get the list of files to load for this directory
                    const allDirectories = await response.json();
                    const targetDir = allDirectories.find(dir => dir.directory === directory);
                    
                    if (targetDir && targetDir.path) {
                        const outputsDir = `${targetDir.path}/outputs`;
                        
                        // Try to fetch specific JSON files directly
                        const sampleFileNames = await fetchFileList(outputsDir);
                        
                        if (sampleFileNames && sampleFileNames.length > 0) {
                            // Load each found file
                            for (const filename of sampleFileNames) {
                                try {
                                    const fileUrl = `/${outputsDir}/${filename}`;
                                    const fileResponse = await fetch(fileUrl);
                                    
                                    if (fileResponse.ok) {
                                        const jsonData = await fileResponse.json();
                                        if (jsonData && typeof jsonData === 'object') {
                                            currentData.push(jsonData);
                                        }
                                    } else {
                                        console.error(`Error loading ${filename}: ${fileResponse.status}`);
                                    }
                                } catch (fileError) {
                                    console.error(`Error loading ${filename}: ${fileError.message}`);
                                }
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
            // Populate the table with data
            displayResultsData();
            
            // Apply the current filter
            applyTableFilter(currentFilter);
            
            // Calculate and display analytics
            const analytics = calculateAnalytics(currentData);
            updateAnalyticsDisplay(analytics);
            
            // Trigger custom event to setup tag filter
            const dataLoadedEvent = new CustomEvent('dataLoaded');
            document.dispatchEvent(dataLoadedEvent);
        } else {
            // Hide analytics, filter, and tag filter when there's no data
            document.getElementById('analyticsDashboard').style.display = 'none';
            document.getElementById('filterControls').style.display = 'none';
            const tagFilterCard = document.getElementById('tagFilterCard');
            if (tagFilterCard) {
                tagFilterCard.style.display = 'none';
            }
            
            // Show error message if we couldn't load any data
            document.getElementById('resultsTableBody').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center">
                        <div class="alert alert-warning">
                            <i class="bi bi-exclamation-triangle-fill me-2"></i>
                            No data found for experiment <strong>${directory}</strong>
                        </div>
                    </td>
                </tr>
            `;
        }
    } catch (error) {
        console.error('Error loading experiment data:', error);
        
        // Hide analytics, filter, and tag filter on error
        document.getElementById('analyticsDashboard').style.display = 'none';
        document.getElementById('filterControls').style.display = 'none';
        const tagFilterCard = document.getElementById('tagFilterCard');
        if (tagFilterCard) {
            tagFilterCard.style.display = 'none';
        }
        
        document.getElementById('resultsTableBody').innerHTML = `
            <tr>
                <td colspan="7" class="text-center text-danger">
                    Error loading experiment data: ${error.message}
                </td>
            </tr>
        `;
    }
}

// Helper function to fetch a list of files in a directory
async function fetchFileList(dirPath) {
    try {
        console.log('Attempting to fetch files from:', dirPath);
        
        // First try the directory listing API if it exists
        console.log('Trying directory listing API...');
        const response = await fetch(`/api/list-files?path=${dirPath}`);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Files found via API:', data.files || []);
            return data.files || [];
        }
        
        // If that fails, try to scrape the directory listing
        console.log('Trying directory scraping...');
        const dirResponse = await fetch(`/${dirPath}/`);
        if (dirResponse.ok) {
            const html = await dirResponse.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract links to JSON files
            const links = Array.from(doc.querySelectorAll('a'))
                .filter(a => a.href.endsWith('.json'))
                .map(a => a.href.split('/').pop());
            
            console.log('Files found via scraping:', links);
            return links;
        }
        
        // If scraping doesn't work, check for specific known files directly
        console.log('Trying direct file checks...');
        const potentialFiles = [
            'faf5e4db.json', '6af20338.json', 'a0f4fc21.json', 'ae03f9e6.json',
            '51ddd061.json', 'd9d48807.json', '210e2087.json', '1e4d05a7.json',
            'e9384a05.json', 'a5722f27.json', '3a4eb4fc.json', 'f409f21c.json'
        ];
        
        const foundFiles = [];
        for (const filename of potentialFiles) {
            try {
                const fileUrl = `/${dirPath}/${filename}`;
                console.log('Checking for file:', fileUrl);
                const testResponse = await fetch(fileUrl, { method: 'HEAD' });
                if (testResponse.ok) {
                    console.log('Found file:', filename);
                    foundFiles.push(filename);
                }
            } catch (err) {
                console.warn(`Error checking for ${filename}:`, err);
            }
        }
        
        if (foundFiles.length > 0) {
            console.log('Files found by direct check:', foundFiles);
            return foundFiles;
        }
        
        // Try to list all files in the outputs directory if available
        try {
            console.log('Trying to check outputs directory content...');
            const outputsResponse = await fetch(`/api/outputs-directory?path=${dirPath}`);
            if (outputsResponse.ok) {
                const data = await outputsResponse.json();
                console.log('Files from outputs directory:', data.files || []);
                return data.files || [];
            }
        } catch (err) {
            console.warn('Error checking outputs directory:', err);
        }
        
        // As a fallback, use this hardcoded list of sample filenames that we've seen
        console.log('Using fallback file list');
        return [
            'faf5e4db.json', '6af20338.json', 'a0f4fc21.json', 'ae03f9e6.json',
            '51ddd061.json', 'd9d48807.json', '210e2087.json', '1e4d05a7.json',
            'e9384a05.json', 'a5722f27.json', '3a4eb4fc.json', 'f409f21c.json'
        ];
    } catch (error) {
        console.error('Error fetching file list:', error);
        // Return a fallback list of common filenames
        return [
            'faf5e4db.json', '6af20338.json', 'a0f4fc21.json', 'ae03f9e6.json',
            '51ddd061.json', 'd9d48807.json', '210e2087.json', '1e4d05a7.json'
        ];
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
            
            ${currentExperiment.timestamp ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Date:</strong>
                </div>
                <div class="col-md-8">
                    ${formatDisplayDate(currentExperiment.timestamp)}
                </div>
            </div>
            ` : ''}
            
            ${currentExperiment.goal ? `
            <div class="row mb-3">
                <div class="col-md-4">
                    <strong>Goal:</strong>
                </div>
                <div class="col-md-8">
                    ${currentExperiment.goal}
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
    const tableBody = document.getElementById('resultsTableBody');
    if (!tableBody) return;
    
    if (!currentData || currentData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No data available</td>
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
        
        return processed;
    });
    
    // Now proceed with normal display logic
    updateTableWithData(processedData);
}

// Update the table with the provided data
function updateTableWithData(dataArray) {
    const tableBody = document.getElementById('resultsTableBody');
    if (!tableBody) return;
    
    if (!dataArray || dataArray.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="text-center">No data available</td>
            </tr>
        `;
        document.getElementById('displayingCount').textContent = '0';
        document.getElementById('totalEntriesCount').textContent = '0';
        return;
    }
    
    // Sort the data by timestamp (newest first)
    const sortedData = [...dataArray].sort((a, b) => {
        // Ensure timestamps are numbers for comparison
        let timestampA = a.timestamp || a.unix_timestamp || 0;
        let timestampB = b.timestamp || b.unix_timestamp || 0;
        
        // Convert string timestamps to numbers if needed
        if (typeof timestampA === 'string') {
            timestampA = parseInt(timestampA, 10) || 0;
        }
        if (typeof timestampB === 'string') {
            timestampB = parseInt(timestampB, 10) || 0;
        }
        
        return timestampB - timestampA; // Descending order (newest first)
    });
    
    // Generate table rows
    tableBody.innerHTML = sortedData.map((item, index) => {
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
        
        // Store the actual data index as a data attribute
        const originalDataIndex = dataArray === currentData ? index : currentData.indexOf(item);
        
        return `
            <tr class="result-row ${recommendation?.toLowerCase() === 'p4' ? 'table-warning' : ''}" data-item-id="${originalDataIndex}">
                <td>${formattedDate}</td>
                <td><code class="code-font">${queryId}</code></td>
                <td>${title}</td>
                <td class="recommendation">${recommendation}</td>
                <td>${resolution}</td>
                <td>
                    <span class="${disputedClass}"><i class="bi ${disputedIcon}"></i> ${isDisputed ? 'Yes' : 'No'}</span>
                </td>
                <td>
                    ${canCalculateCorrectness ? 
                      `<span class="${correctnessClass}"><i class="bi ${correctnessIcon}"></i> ${isCorrect ? 'Yes' : 'No'}</span>` :
                      'N/A'}
                </td>
            </tr>
        `;
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
    document.getElementById('displayingCount').textContent = sortedData.length;
    document.getElementById('totalEntriesCount').textContent = currentData.length;
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
    
    // Get the title from the table row
    const tableRow = document.querySelector(`.result-row[data-item-id="${index}"]`);
    let title = 'Details';
    if (tableRow) {
        const titleCell = tableRow.querySelector('td:nth-child(3)');
        if (titleCell) {
            title = titleCell.textContent.trim();
        }
    }
    
    // Set the modal title
    modalTitle.textContent = title;
    
    // Check if disputed
    const isDisputed = data.disputed === true;
    
    // Get proposed price if available, being careful with 0 values
    const proposedPrice = data.proposed_price_outcome !== undefined ? data.proposed_price_outcome : 
                         (data.proposed_price !== undefined ? data.proposed_price : 'N/A');
    
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
    
    // Generate the content
    let content = `
        <div class="alert ${alertClass} mb-4">
            <strong>Recommendation:</strong> ${data.recommendation || 'N/A'} | 
            <strong>Proposed:</strong> ${proposedPrice} | 
            <strong>Resolved:</strong> ${data.resolved_price_outcome || data.resolved_price || 'Unresolved'} | 
            <strong>Disputed:</strong> ${isDisputed ? 'Yes' : 'No'} | 
            <strong>Correct:</strong> ${correctnessText}
        </div>
    `;
    
    // Add tags section if available
    if (data.tags && Array.isArray(data.tags) && data.tags.length > 0) {
        content += `
            <div class="mb-3">
                <strong>Tags:</strong> 
                ${data.tags.map(tag => `<span class="tag-badge">${tag}</span>`).join('')}
            </div>
        `;
    }
    
    // Add overview section with clickable query ID for copying
    content += `
        <div class="detail-section">
            <h4 class="section-title">Overview</h4>
            <div class="card">
                <div class="card-body p-0">
                    <table class="table meta-table mb-0">
                        <tr>
                            <th>Query ID</th>
                            <td>
                                <code class="code-font copy-to-clipboard" title="Click to copy" data-copy="${data.query_id || ''}" id="copyQueryId">
                                    ${data.query_id || 'N/A'}
                                </code>
                                <span class="copy-feedback" id="copyFeedback" style="display:none;">Copied!</span>
                            </td>
                        </tr>
                        <tr>
                            <th>Short ID</th>
                            <td>
                                <code class="code-font copy-to-clipboard" title="Click to copy" data-copy="${data.question_id_short || ''}" id="copyShortId">
                                    ${data.question_id_short || 'N/A'}
                                </code>
                            </td>
                        </tr>
                        <tr>
                            <th>Proposal Time</th>
                            <td>${formatDate(data.timestamp || data.unix_timestamp)}</td>
                        </tr>
                        <tr>
                            <th>Disputed</th>
                            <td>${isDisputed ? '<span class="text-warning"><i class="bi bi-exclamation-triangle-fill"></i> Yes</span>' : 'No'}</td>
                        </tr>
                        <tr>
                            <th>Proposal Transaction</th>
                            <td>${createTxLink(data.proposal_data?.transaction_hash || data.transaction_hash)}</td>
                        </tr>
                    </table>
                </div>
            </div>
        </div>
    `;
    
    // Add user prompt section if available
    if (data.user_prompt) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">User Prompt</h4>
                <div class="card">
                    <div class="card-body">
                        <pre class="mb-0 prompt-text">${data.user_prompt}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add prompt section if available
    if (data.proposal_data?.prompt) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Proposal Data Prompt</h4>
                <div class="card">
                    <div class="card-body">
                        <pre class="mb-0 prompt-text">${data.proposal_data.prompt}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add system prompt if available
    if (data.system_prompt) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">System Prompt</h4>
                <div class="card">
                    <div class="card-body">
                        <pre class="mb-0 prompt-text">${data.system_prompt}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add response section
    if (data.response) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Response</h4>
                <div class="card">
                    <div class="card-body">
                        <pre class="mb-0 response-text">${data.response}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add response metadata if available
    if (data.response_metadata) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Response Metadata</h4>
                <div class="card">
                    <div class="card-body p-0">
                        <table class="table meta-table mb-0">
                            ${Object.entries(data.response_metadata).map(([key, value]) => `
                                <tr>
                                    <th>${formatKeyName(key)}</th>
                                    <td>${formatValue(value)}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add overseer data section if available
    if (data.overseer_data) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Overseer Data</h4>
                <div class="card mb-3">
                    <div class="card-header">
                        <strong>Overseer Summary</strong>
                    </div>
                    <div class="card-body">
                        <p><strong>Attempts:</strong> ${data.overseer_data.attempts}</p>
                        <div class="recommendation-journey mt-3 mb-2">
                            <strong>Recommendation Journey:</strong>
                            <div class="journey-steps mt-2">
                                ${data.overseer_data.recommendation_journey.map((step, idx) => `
                                    <div class="journey-step">
                                        <span class="step-number">${idx + 1}</span>
                                        <div class="step-details">
                                            <div><strong>Attempt:</strong> ${step.attempt}</div>
                                            <div><strong>Perplexity:</strong> <code>${step.perplexity_recommendation}</code></div>
                                            <div><strong>Overseer:</strong> ${formatSatisfactionLevel(step.overseer_satisfaction_level || step.overseer_decision)}</div>
                                            <div><strong>Prompt Updated:</strong> ${step.prompt_updated ? 'Yes' : 'No'}</div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="accordion" id="interactionsAccordion">
                    ${data.overseer_data.interactions.map((interaction, idx) => `
                        <div class="accordion-item">
                            <h2 class="accordion-header" id="heading${idx}">
                                <button class="accordion-button ${idx > 0 ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" 
                                    data-bs-target="#collapse${idx}" aria-expanded="${idx === 0 ? 'true' : 'false'}" aria-controls="collapse${idx}">
                                    <strong>${interaction.interaction_type === 'perplexity_query' ? 
                                        `Attempt ${interaction.attempt}: ${formatStageName(interaction.stage)}` : 
                                        `ChatGPT: ${formatStageName(interaction.stage)}`}</strong>
                                    ${interaction.recommendation ? ` - Recommendation: <code>${interaction.recommendation}</code>` : ''}
                                    ${interaction.decision || interaction.satisfaction_level ? 
                                        ` - Decision: <code>${interaction.decision || interaction.satisfaction_level}</code>` : ''}
                                </button>
                            </h2>
                            <div id="collapse${idx}" class="accordion-collapse collapse ${idx === 0 ? 'show' : ''}" 
                                aria-labelledby="heading${idx}" data-bs-parent="#interactionsAccordion">
                                <div class="accordion-body">
                                    ${interaction.interaction_type === 'perplexity_query' ? `
                                        <div class="card mb-3">
                                            <div class="card-header">Response</div>
                                            <div class="card-body">
                                                <pre class="mb-0 response-text">${interaction.response}</pre>
                                            </div>
                                        </div>
                                        ${interaction.citations && interaction.citations.length > 0 ? `
                                            <div class="card mb-3">
                                                <div class="card-header">Citations</div>
                                                <div class="card-body">
                                                    <ul class="citation-list">
                                                        ${interaction.citations.map(citation => `
                                                            <li><a href="${citation}" target="_blank">${citation}</a></li>
                                                        `).join('')}
                                                    </ul>
                                                </div>
                                            </div>
                                        ` : ''}
                                        <div class="card">
                                            <div class="card-header">Response Metadata</div>
                                            <div class="card-body p-0">
                                                <table class="table meta-table mb-0">
                                                    ${Object.entries(interaction.response_metadata || {}).map(([key, value]) => `
                                                        <tr>
                                                            <th>${formatKeyName(key)}</th>
                                                            <td>${formatValue(value)}</td>
                                                        </tr>
                                                    `).join('')}
                                                </table>
                                            </div>
                                        </div>
                                    ` : `
                                        <div class="card mb-3">
                                            <div class="card-header">Evaluation</div>
                                            <div class="card-body">
                                                <pre class="mb-0 response-text">${interaction.response}</pre>
                                            </div>
                                        </div>
                                        <div class="alert ${interaction.decision === 'satisfied' || interaction.satisfaction_level === 'satisfied' ? 'alert-success' : 
                                            interaction.decision === 'not_satisfied' || interaction.satisfaction_level === 'not_satisfied' ? 'alert-danger' : 
                                            interaction.satisfaction_level && interaction.satisfaction_level.includes('retry') ? 'alert-warning' : 'alert-secondary'}">
                                            <strong>Decision:</strong> ${formatSatisfactionLevel(interaction.satisfaction_level || interaction.decision)}
                                            ${interaction.critique ? `<p class="mt-2 mb-0"><strong>Critique:</strong> ${interaction.critique}</p>` : ''}
                                        </div>
                                        ${interaction.recommendation_overridden ? `
                                            <div class="alert alert-info override-alert">
                                                <strong><i class="bi bi-arrow-repeat"></i> Recommendation was overridden</strong>
                                                ${interaction.override_action ? 
                                                    `<p class="mt-2 mb-0 small">${interaction.override_action.replace(/_/g, ' ')}</p>` : ''}
                                            </div>
                                        ` : ''}
                                        ${interaction.prompt_updated ? `
                                            <div class="alert alert-info">
                                                <strong>Prompt was updated</strong>
                                                ${interaction.system_prompt_before ? `
                                                    <div class="mt-2">
                                                        <button class="btn btn-sm btn-outline-secondary" type="button" data-bs-toggle="collapse" 
                                                            data-bs-target="#promptBefore${idx}" aria-expanded="false" aria-controls="promptBefore${idx}">
                                                            Show Prompt Before
                                                        </button>
                                                        <button class="btn btn-sm btn-outline-secondary ms-2" type="button" data-bs-toggle="collapse" 
                                                            data-bs-target="#promptAfter${idx}" aria-expanded="false" aria-controls="promptAfter${idx}">
                                                            Show Prompt After
                                                        </button>
                                                    </div>
                                                    <div class="collapse mt-3" id="promptBefore${idx}">
                                                        <div class="card card-body">
                                                            <h6>Before:</h6>
                                                            <pre class="mb-0 prompt-text">${interaction.system_prompt_before}</pre>
                                                        </div>
                                                    </div>
                                                    <div class="collapse mt-3" id="promptAfter${idx}">
                                                        <div class="card card-body">
                                                            <h6>After:</h6>
                                                            <pre class="mb-0 prompt-text">${interaction.system_prompt_after}</pre>
                                                        </div>
                                                    </div>
                                                ` : ''}
                                            </div>
                                        ` : ''}
                                        <div class="card">
                                            <div class="card-header">Metadata</div>
                                            <div class="card-body p-0">
                                                <table class="table meta-table mb-0">
                                                    ${Object.entries(interaction.metadata || {}).map(([key, value]) => `
                                                        <tr>
                                                            <th>${formatKeyName(key)}</th>
                                                            <td>${formatValue(value)}</td>
                                                        </tr>
                                                    `).join('')}
                                                </table>
                                            </div>
                                        </div>
                                    `}
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
                
                ${data.overseer_data.final_response_metadata ? `
                    <div class="card mt-3">
                        <div class="card-header">Final Response Metadata</div>
                        <div class="card-body p-0">
                            <table class="table meta-table mb-0">
                                ${Object.entries(data.overseer_data.final_response_metadata).map(([key, value]) => `
                                    <tr>
                                        <th>${formatKeyName(key)}</th>
                                        <td>${formatValue(value)}</td>
                                    </tr>
                                `).join('')}
                            </table>
                        </div>
                    </div>
                ` : ''}
            </div>
        `;
    }
    
    // Add API response section
    if (data.api_response && data.api_response.text) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">API Response</h4>
                <div class="card">
                    <div class="card-header">
                        <div class="d-flex justify-content-between align-items-center">
                            <span>Response from ${data.api_response.model || 'AI Model'}</span>
                            <span class="text-muted">${formatDate(data.api_response.timestamp)}</span>
                        </div>
                    </div>
                    <div class="card-body">
                        <pre class="mb-0 response-text">${data.api_response.text}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add ancillary data if available
    if (data.ancillary_data) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Ancillary Data</h4>
                <div class="card">
                    <div class="card-body">
                        <pre class="mb-0 ancillary-data">${data.ancillary_data}</pre>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add processed file if available
    if (data.processed_file) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Processed File</h4>
                <div class="card">
                    <div class="card-body">
                        <code>${data.processed_file}</code>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add citations if available - simplified version
    if (data.citations && data.citations.length > 0) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Citations</h4>
                <div class="card">
                    <div class="card-body">
                        <ul class="list-group">
                            ${data.citations.map(citation => {
                                const url = typeof citation === 'string' ? citation : citation.url;
                                return `<li class="list-group-item"><a href="${url}" target="_blank">${url}</a></li>`;
                            }).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add proposal metadata
    if (data.proposal_metadata) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Proposal Metadata</h4>
                <div class="card">
                    <div class="card-body p-0">
                        <table class="table meta-table mb-0">
                            ${Object.entries(data.proposal_metadata).map(([key, value]) => `
                                <tr>
                                    <th>${formatKeyName(key)}</th>
                                    <td>${formatValue(value)}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Add any remaining fields as a "More Details" section
    const commonFields = [
        'query_id', 'question_id_short', 'recommendation', 'proposed_price', 'resolved_price', 
        'resolved_price_outcome', 'timestamp', 'unix_timestamp', 'transaction_hash', 
        'proposal_data', 'api_response', 'response', 'system_prompt', 'user_prompt',
        'ancillary_data', 'citations', 'proposal_metadata', 'response_metadata', 'processed_file',
        'overseer_data', 'tags', 'disputed', 'proposed_price_outcome'
    ];
    
    const remainingEntries = Object.entries(data).filter(([key]) => !commonFields.includes(key));
    
    if (remainingEntries.length > 0) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Additional Details</h4>
                <div class="card">
                    <div class="card-body p-0">
                        <table class="table meta-table mb-0">
                            ${remainingEntries.map(([key, value]) => `
                                <tr>
                                    <th>${formatKeyName(key)}</th>
                                    <td>${formatValue(value)}</td>
                                </tr>
                            `).join('')}
                        </table>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Set the modal content
    modalBody.innerHTML = content;
    
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
}

// Extracts a title from all potential sources
function extractTitle(item) {
    // First try the explicit title field
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
    
    // Try to extract from question_id_short (often the most reliable for MongoDB)
    if (item.question_id_short) {
        return `Question ${item.question_id_short}`;
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
    
    // Try to extract from ancillary_data as fallback
    if (item.ancillary_data) {
        const ancillaryMatch = item.ancillary_data.match(/title:\s*([^,\n]+)/i);
        if (ancillaryMatch && ancillaryMatch[1]) {
            return ancillaryMatch[1].trim();
        }
    }
    
    // Fallback to proposal_data.prompt first line
    if (item.proposal_data?.prompt) {
        const firstLine = item.proposal_data.prompt.split('\n')[0] || '';
        return firstLine.substring(0, 50) + (firstLine.length > 50 ? '...' : '');
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
function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
    
    if (Array.isArray(value)) {
        if (value.length === 0) return 'Empty Array';
        
        // For short arrays of primitive values, format as comma-separated list
        if (value.length <= 5 && value.every(item => 
            typeof item !== 'object' || item === null)) {
            return value.map(formatValue).join(', ');
        }
        
        // For longer arrays or arrays of objects, format as a list
        return `<ul class="mb-0 ps-3">${value.map(item => 
            `<li>${formatValue(item)}</li>`).join('')}</ul>`;
    }
    
    if (typeof value === 'object') {
        // For small objects, format as a simple table
        if (Object.keys(value).length <= 3) {
            let html = '<div class="metadata-section small-object">';
            for (const [key, val] of Object.entries(value)) {
                html += `<div><strong>${formatKeyName(key)}:</strong> ${formatValue(val)}</div>`;
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
        const stats = tagStats[tag];
        const accuracyClass = stats.accuracyPercent >= 80 ? 'high-accuracy' : 
                             (stats.accuracyPercent >= 50 ? 'medium-accuracy' : 'low-accuracy');
        
        return `
            <tr>
                <td><span class="tag-badge">${tag}</span></td>
                <td>${stats.total}</td>
                <td class="accuracy-cell ${accuracyClass}">${stats.accuracyPercent.toFixed(1)}%</td>
                <td>${stats.correct}</td>
                <td>${stats.incorrect}</td>
            </tr>
        `;
    }).join('');
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
    // Update current source filter
    currentSourceFilter = source;
    
    // Reset active class on source filter buttons
    document.querySelectorAll('.source-filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Set active class on the clicked button - fix the capitalization issue
    if (source === 'all') {
        document.getElementById('filterSourceAll')?.classList.add('active');
    } else if (source === 'filesystem') {
        document.getElementById('filterSourceFilesystem')?.classList.add('active');
    } else if (source === 'mongodb') {
        document.getElementById('filterSourceMongoDB')?.classList.add('active');
    }
    
    // Update the experiment list
    displayExperimentsTable();
}