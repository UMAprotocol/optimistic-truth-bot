// Global variables to store data and charts
let outputsData = [];
let rerunsData = [];
let modal = null;
let currentRealtimeFilter = 'all'; // Track current filter state for real time data
let currentDelayedFilter = 'all'; // Track current filter state for delayed data
let currentRealtimeSearch = ''; // Track current search term for real time data
let currentDelayedSearch = ''; // Track current search term for delayed data

// Chart variables
let realtimeRecommendationChart = null;
let realtimeResolutionChart = null;
let delayedRecommendationChart = null;
let delayedResolutionChart = null;

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize charts
    try {
        initializeCharts();
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
    
    // Load data files - outputs is now "realtime" data, reruns is now "delayed" data
    loadRealtimeData();
    loadDelayedData();

    // Set up search functionality for realtime data
    document.getElementById('realtimeSearchBtn')?.addEventListener('click', () => {
        currentRealtimeSearch = document.getElementById('realtimeSearch').value.trim().toLowerCase();
        applyTableFilter('realtime', currentRealtimeFilter);
    });

    // Set up search functionality for delayed data
    document.getElementById('delayedSearchBtn')?.addEventListener('click', () => {
        currentDelayedSearch = document.getElementById('delayedSearch').value.trim().toLowerCase();
        applyTableFilter('delayed', currentDelayedFilter);
    });

    // Handle Enter key in search fields
    document.getElementById('realtimeSearch')?.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            currentRealtimeSearch = this.value.trim().toLowerCase();
            applyTableFilter('realtime', currentRealtimeFilter);
        }
    });

    document.getElementById('delayedSearch')?.addEventListener('keyup', function(event) {
        if (event.key === 'Enter') {
            currentDelayedSearch = this.value.trim().toLowerCase();
            applyTableFilter('delayed', currentDelayedFilter);
        }
    });
    
    // Initialize modal
    const modalElement = document.getElementById('detailsModal');
    if (modalElement) {
        modal = new bootstrap.Modal(modalElement);
        
        // Add event listener for modal open/close
        modalElement.addEventListener('show.bs.modal', () => {
            // Remove table styling when modal opens
            document.querySelectorAll('.table-hover').forEach(table => {
                table.classList.remove('table-hover');
            });
        });
        
        modalElement.addEventListener('hidden.bs.modal', () => {
            // Restore table styling when modal closes
            document.querySelectorAll('.table').forEach(table => {
                table.classList.add('table-hover');
            });
        });
    }

    // Event listeners for tab switching
    document.querySelectorAll('button[data-bs-toggle="tab"]').forEach(tab => {
        tab.addEventListener('click', function() {
            // When switching tabs, ensure the correct filter is applied
            const targetId = this.getAttribute('data-bs-target').replace('#', '');
            if (targetId === 'realtime') {
                applyFilter('realtime', currentRealtimeFilter);
            } else if (targetId === 'delayed') {
                applyFilter('delayed', currentDelayedFilter);
            }
        });
    });

    // Add event listeners for real time filter buttons
    document.getElementById('realtimeFilterAll')?.addEventListener('click', () => applyFilter('realtime', 'all'));
    document.getElementById('realtimeFilterCorrect')?.addEventListener('click', () => applyFilter('realtime', 'correct'));
    document.getElementById('realtimeFilterIncorrect')?.addEventListener('click', () => applyFilter('realtime', 'incorrect'));

    // Add event listeners for delayed filter buttons
    document.getElementById('delayedFilterAll')?.addEventListener('click', () => applyFilter('delayed', 'all'));
    document.getElementById('delayedFilterCorrect')?.addEventListener('click', () => applyFilter('delayed', 'correct'));
    document.getElementById('delayedFilterIncorrect')?.addEventListener('click', () => applyFilter('delayed', 'incorrect'));
});

// Initialize empty charts
function initializeCharts() {
    // Setup for realtime recommendation distribution chart
    const realtimeRecCtx = document.getElementById('realtimeRecommendationChart')?.getContext('2d');
    if (realtimeRecCtx) {
        realtimeRecommendationChart = new Chart(realtimeRecCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.formattedValue || '';
                                const dataset = context.dataset;
                                const total = dataset.data.reduce((acc, data) => acc + data, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Setup for realtime resolution distribution chart
    const realtimeResCtx = document.getElementById('realtimeResolutionChart')?.getContext('2d');
    if (realtimeResCtx) {
        realtimeResolutionChart = new Chart(realtimeResCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.formattedValue || '';
                                const dataset = context.dataset;
                                const total = dataset.data.reduce((acc, data) => acc + data, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Setup for delayed recommendation distribution chart
    const delayedRecCtx = document.getElementById('delayedRecommendationChart')?.getContext('2d');
    if (delayedRecCtx) {
        delayedRecommendationChart = new Chart(delayedRecCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.formattedValue || '';
                                const dataset = context.dataset;
                                const total = dataset.data.reduce((acc, data) => acc + data, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    // Setup for delayed resolution distribution chart
    const delayedResCtx = document.getElementById('delayedResolutionChart')?.getContext('2d');
    if (delayedResCtx) {
        delayedResolutionChart = new Chart(delayedResCtx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            boxWidth: 10,
                            font: {
                                size: 10
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label || '';
                                const value = context.formattedValue || '';
                                const dataset = context.dataset;
                                const total = dataset.data.reduce((acc, data) => acc + data, 0);
                                const percentage = Math.round((context.raw / total) * 100);
                                return `${label}: ${value} (${percentage}%)`;
                            }
                        }
                    }
                }
            }
        });
    }
}

// Calculate analytics from the data
function calculateAnalytics(dataArray) {
    // Filter out entries with no resolved price outcome
    const resolvedData = dataArray.filter(item => {
        return item.resolved_price_outcome && item.resolved_price_outcome !== 'N/A' && item.resolved_price_outcome !== 'None';
    });
    
    const analytics = {
        total: resolvedData.length,
        correct: 0,
        incorrect: 0,
        noData: 0,
        p123Total: 0,
        p123Correct: 0,
        p12Total: 0,
        p12Correct: 0,
        recommendations: {},
        resolutions: {}
    };
    
    resolvedData.forEach(item => {
        const recommendation = item.recommendation || 'None';
        const resolvedOutcome = item.resolved_price_outcome;
        
        // Count in recommendations
        analytics.recommendations[recommendation] = (analytics.recommendations[recommendation] || 0) + 1;
        
        // Count in resolutions
        analytics.resolutions[resolvedOutcome] = (analytics.resolutions[resolvedOutcome] || 0) + 1;
        
        // Check if correct
        if (recommendation === resolvedOutcome) {
            analytics.correct++;
            
            // Count correct p1/p2/p3 predictions
            if (['p1', 'p2', 'p3'].includes(recommendation)) {
                analytics.p123Correct++;
            }
            
            // Count correct p1/p2 predictions
            if (['p1', 'p2'].includes(recommendation)) {
                analytics.p12Correct++;
            }
        } else {
            analytics.incorrect++;
            
            // Check for no data cases (p4 recommendation but different resolution)
            if (recommendation === 'p4' && resolvedOutcome !== 'p4') {
                analytics.noData++;
            }
        }
        
        // Count total p1/p2/p3 recommendations
        if (['p1', 'p2', 'p3'].includes(recommendation)) {
            analytics.p123Total++;
        }
        
        // Count total p1/p2 recommendations
        if (['p1', 'p2'].includes(recommendation)) {
            analytics.p12Total++;
        }
    });
    
    return analytics;
}

// Update analytics display with calculated data
function updateAnalyticsDisplay(type, analytics) {
    try {
        const prefix = type === 'realtime' ? 'realtime' : 'delayed';
        const dataArray = type === 'realtime' ? outputsData : rerunsData;
        
        // Count unresolved entries
        const unresolvedCount = dataArray.filter(item => 
            !item.resolved_price_outcome || 
            item.resolved_price_outcome === 'N/A' || 
            item.resolved_price_outcome === 'None'
        ).length;
        
        // Update counts with null checks
        const correctCountEl = document.getElementById(`${prefix}CorrectCount`);
        const incorrectCountEl = document.getElementById(`${prefix}IncorrectCount`);
        const totalCountEl = document.getElementById(`${prefix}TotalCount`);
        const noDataCountEl = document.getElementById(`${prefix}NoDataCount`);
        
        if (correctCountEl) correctCountEl.textContent = analytics.correct;
        if (incorrectCountEl) incorrectCountEl.textContent = analytics.incorrect;
        if (totalCountEl) totalCountEl.textContent = analytics.total;
        if (noDataCountEl) noDataCountEl.textContent = analytics.noData;
        
        // Update the note about unresolved entries
        const noteEl = document.querySelector(`#${type} .text-muted.small.mt-2`);
        if (noteEl) {
            noteEl.innerHTML = `<strong>Note:</strong> ${unresolvedCount} unresolved entries are excluded from analytics calculations.<br>`;
        }
        
        // Calculate percentages
        const accuracy = analytics.total > 0 ? (analytics.correct / analytics.total) * 100 : 0;
        const p123Accuracy = analytics.p123Total > 0 ? (analytics.p123Correct / analytics.p123Total) * 100 : 0;
        const p12Accuracy = analytics.p12Total > 0 ? (analytics.p12Correct / analytics.p12Total) * 100 : 0;
        
        // Update accuracy circle with null checks
        const accuracyPercentEl = document.getElementById(`${prefix}AccuracyPercent`);
        const accuracyCircleEl = document.getElementById(`${prefix}AccuracyCircle`);
        
        if (accuracyPercentEl) accuracyPercentEl.textContent = `${Math.round(accuracy)}%`;
        if (accuracyCircleEl) accuracyCircleEl.style.background = 
            `conic-gradient(var(--primary-color) ${accuracy}%, #f0f0f0 0%)`;
        
        // Update progress bars with null checks
        const p123Bar = document.getElementById(`${prefix}P123Accuracy`);
        if (p123Bar) {
            p123Bar.style.width = `${p123Accuracy}%`;
            p123Bar.setAttribute('aria-valuenow', p123Accuracy);
            p123Bar.textContent = `${Math.round(p123Accuracy)}%`;
        }
        
        const p12Bar = document.getElementById(`${prefix}P12Accuracy`);
        if (p12Bar) {
            p12Bar.style.width = `${p12Accuracy}%`;
            p12Bar.setAttribute('aria-valuenow', p12Accuracy);
            p12Bar.textContent = `${Math.round(p12Accuracy)}%`;
        }
        
        // Update charts
        updateDistributionCharts(type, analytics);
    } catch (error) {
        console.error(`Error updating ${type} analytics display:`, error);
    }
}

// Update the distribution charts
function updateDistributionCharts(type, analytics) {
    try {
        // Determine which charts to update
        const recommendationChart = type === 'realtime' ? realtimeRecommendationChart : delayedRecommendationChart;
        const resolutionChart = type === 'realtime' ? realtimeResolutionChart : delayedResolutionChart;
        
        // Prepare data for recommendation chart
        const recLabels = Object.keys(analytics.recommendations);
        const recData = recLabels.map(key => analytics.recommendations[key]);
        
        // Update recommendation chart
        if (recommendationChart) {
            recommendationChart.data.labels = recLabels;
            recommendationChart.data.datasets[0].data = recData;
            recommendationChart.update();
        }
        
        // Prepare data for resolution chart
        const resLabels = Object.keys(analytics.resolutions);
        const resData = resLabels.map(key => analytics.resolutions[key]);
        
        // Update resolution chart
        if (resolutionChart) {
            resolutionChart.data.labels = resLabels;
            resolutionChart.data.datasets[0].data = resData;
            resolutionChart.update();
        }
    } catch (error) {
        console.error(`Error updating ${type} distribution charts:`, error);
    }
}

// Helper function to format date in 24-hour format
function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp * 1000);
    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 5);
}

// Helper function to create a transaction link
function createTxLink(hash) {
    if (!hash) return 'N/A';
    const shortHash = hash.substring(0, 8) + '...' + hash.substring(hash.length - 6);
    return `<a href="https://polygonscan.com/tx/${hash}" 
               target="_blank" 
               class="tx-hash-link" 
               title="${hash}">
               ${shortHash}
               <i class="bi bi-box-arrow-up-right ms-1 small"></i>
            </a>`;
}

// Filter data by correctness
function filterByCorrectness(type, isCorrect) {
    // Determine which data source to use
    const tableBody = document.getElementById(`${type}TableBody`);
    const dataArray = type === 'realtime' ? outputsData : rerunsData;
    
    const filteredData = dataArray.filter(item => {
        const isItemCorrect = item.recommendation === item.resolved_price_outcome;
        return isCorrect ? isItemCorrect : !isItemCorrect;
    });
    
    // Update table with filtered data
    if (filteredData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No ${isCorrect ? 'correct' : 'incorrect'} proposals found</td>
            </tr>
        `;
        return;
    }
    
    updateTableWithData(type, filteredData);
}

// Load realtime data (previously "outputs")
async function loadRealtimeData() {
    try {
        const response = await fetch('../outputs/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Extract file links from the directory listing
        const links = Array.from(doc.querySelectorAll('a'))
            .filter(a => a.href.includes('output_') && a.href.endsWith('.json'));
        
        outputsData = await Promise.all(
            links.map(async link => {
                try {
                    const fileResponse = await fetch(`../outputs/${link.textContent}`);
                    return await fileResponse.json();
                } catch (error) {
                    console.error(`Error loading file ${link.textContent}:`, error);
                    return null;
                }
            })
        );
        
        // Filter out any null values from failed loads
        outputsData = outputsData.filter(item => item !== null);
        
        // Populate the table with data
        displayRealtimeData();
        
        // Apply the current filter
        applyTableFilter('realtime', currentRealtimeFilter);
        
        // Calculate and display analytics only if we have data
        if (outputsData.length > 0) {
            const analytics = calculateAnalytics(outputsData);
            updateAnalyticsDisplay('realtime', analytics);
        }
    } catch (error) {
        console.error('Error loading realtime data:', error);
        const tableBody = document.getElementById('realtimeTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">
                        Error loading data. Please check the console for details.
                    </td>
                </tr>
            `;
        }
    }
}

// Load delayed data (previously "reruns")
async function loadDelayedData() {
    try {
        const response = await fetch('../reruns/');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const html = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        
        // Extract file links from the directory listing
        const links = Array.from(doc.querySelectorAll('a'))
            .filter(a => a.href.includes('rerun_') && a.href.endsWith('.json'));
        
        rerunsData = await Promise.all(
            links.map(async link => {
                try {
                    const fileResponse = await fetch(`../reruns/${link.textContent}`);
                    return await fileResponse.json();
                } catch (error) {
                    console.error(`Error loading file ${link.textContent}:`, error);
                    return null;
                }
            })
        );
        
        // Filter out any null values from failed loads
        rerunsData = rerunsData.filter(item => item !== null);
        
        // Populate the table with data
        displayDelayedData();
        
        // Apply the current filter
        applyTableFilter('delayed', currentDelayedFilter);
        
        // Calculate and display analytics
        if (rerunsData.length > 0) {
            const analytics = calculateAnalytics(rerunsData);
            updateAnalyticsDisplay('delayed', analytics);
        }
    } catch (error) {
        console.error('Error loading delayed data:', error);
        const tableBody = document.getElementById('delayedTableBody');
        if (tableBody) {
            tableBody.innerHTML = `
                <tr>
                    <td colspan="6" class="text-center text-danger">
                        Error loading data. Please check the console for details.
                    </td>
                </tr>
            `;
        }
    }
}

// Display realtime data in the table
function displayRealtimeData() {
    const tableBody = document.getElementById('realtimeTableBody');
    
    if (outputsData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No data available</td>
            </tr>
        `;
        return;
    }
    
    updateTableWithData('realtime', outputsData);
}

// Display delayed data in the table
function displayDelayedData() {
    const tableBody = document.getElementById('delayedTableBody');
    
    if (rerunsData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No data available</td>
            </tr>
        `;
        return;
    }
    
    updateTableWithData('delayed', rerunsData);
}

// Update table with data
function updateTableWithData(type, dataArray) {
    const tableBody = document.getElementById(`${type}TableBody`);
    
    tableBody.innerHTML = dataArray.map((item, index) => {
        const title = extractTitle(item.user_prompt);
        const isCorrect = item.recommendation === item.resolved_price_outcome;
        const correctIcon = isCorrect 
            ? '<i class="bi bi-check-lg text-success"></i>' 
            : '<i class="bi bi-x-lg text-danger"></i>';
        
        // Format timestamp from unix_timestamp in proposal_metadata
        let proposalTime = 'N/A';
        let fullTimestamp = '';
        if (item.proposal_metadata && item.proposal_metadata.unix_timestamp) {
            const timestamp = item.proposal_metadata.unix_timestamp;
            proposalTime = formatDate(timestamp);
            fullTimestamp = new Date(timestamp * 1000).toLocaleString();
        }
        
        return `
            <tr data-index="${index}" data-type="${type}">
                <td>${item.question_id_short}</td>
                <td>${title}</td>
                <td>${item.recommendation || 'N/A'}</td>
                <td>${item.resolved_price_outcome || 'N/A'}</td>
                <td class="text-center">${correctIcon}</td>
                <td title="${fullTimestamp}">${proposalTime}</td>
            </tr>
        `;
    }).join('');
    
    // Make entire row clickable
    document.querySelectorAll(`#${type}TableBody tr`).forEach(row => {
        row.addEventListener('click', () => {
            const index = row.dataset.index;
            const dataType = row.dataset.type;
            showDetails(dataType === 'realtime' ? outputsData[index] : rerunsData[index], dataType);
        });
    });

    // After updating the table, apply the current filter
    if (type === 'realtime') {
        applyTableFilter(type, currentRealtimeFilter);
    } else {
        applyTableFilter(type, currentDelayedFilter);
    }
}

// Filter table based on search text
function filterTable(type, dataArray, searchText) {
    const tableBody = document.getElementById(`${type}TableBody`);
    
    if (searchText === '') {
        // If search is empty, reset to show all data
        if (type === 'realtime') {
            displayRealtimeData();
        } else {
            displayDelayedData();
        }
        return;
    }
    
    // Filter the data array
    const filteredData = dataArray.filter(item => {
        const title = extractTitle(item.user_prompt);
        return (
            item.question_id_short.toLowerCase().includes(searchText) ||
            title.toLowerCase().includes(searchText) ||
            item.recommendation?.toLowerCase().includes(searchText) ||
            item.resolved_price_outcome?.toLowerCase().includes(searchText)
        );
    });
    
    // Update table with filtered data
    if (filteredData.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">No matching results</td>
            </tr>
        `;
        return;
    }
    
    updateTableWithData(type, filteredData);
}

// Show details in the modal
function showDetails(data, type) {
    const modalTitle = document.getElementById('detailsModalLabel');
    const modalBody = document.getElementById('detailsModalBody');
    
    // Set the modal title
    const title = extractTitle(data.user_prompt);
    modalTitle.textContent = `${title} (${data.question_id_short})`;
    
    // Determine if recommendation matches resolved price outcome
    const isCorrect = data.recommendation === data.resolved_price_outcome;
    const correctnessText = isCorrect ? 'Correct' : 'Incorrect';
    
    // Format proposal time
    let proposalTime = 'N/A';
    if (data.proposal_metadata && data.proposal_metadata.unix_timestamp) {
        proposalTime = formatDate(data.proposal_metadata.unix_timestamp);
    }
    
    // Prepare modal content
    let content = `
        <div class="detail-section">
            <h4>Basic Information</h4>
            <table class="table meta-table">
                <tr>
                    <th>Question</th>
                    <td>${data.question_id_short}</td>
                </tr>
                <tr>
                    <th>Recommended</th>
                    <td>${data.recommendation || 'N/A'}</td>
                </tr>
                <tr>
                    <th>Resolved</th>
                    <td>${data.resolved_price_outcome || 'N/A'}</td>
                </tr>
                <tr>
                    <th>Correctness</th>
                    <td><strong>${correctnessText}</strong></td>
                </tr>
                <tr>
                    <th>Proposal Time</th>
                    <td>${proposalTime}</td>
                </tr>
                <tr>
                    <th>Transaction Hash</th>
                    <td>${createTxLink(data.transaction_hash)}</td>
                </tr>
                <tr>
                    <th>Timestamp</th>
                    <td>${formatDate(data.timestamp)}</td>
                </tr>
                <tr>
                    <th>Data Type</th>
                    <td>${type === 'realtime' ? 'Real Time' : 'Delayed Run'}</td>
                </tr>
            </table>
        </div>
        
        <div class="detail-section">
            <h4>User Prompt</h4>
            <div class="card detail-card">
                <div class="card-body">
                    <pre>${data.user_prompt}</pre>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>System Prompt</h4>
            <div class="card detail-card">
                <div class="card-body">
                    <pre>${data.system_prompt || 'N/A'}</pre>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4>Response</h4>
            <div class="card detail-card">
                <div class="card-body">
                    <pre>${data.response}</pre>
                </div>
            </div>
        </div>
    `;
    
    // Add citations if available
    if (data.citations && data.citations.length > 0) {
        content += `
            <div class="detail-section">
                <h4>Citations (${data.citations.length})</h4>
                <ul class="citation-list">
                    ${data.citations.map(citation => `
                        <li><a href="${citation}" target="_blank">${citation}</a></li>
                    `).join('')}
                </ul>
            </div>
        `;
    }
    
    // Add response metadata
    if (data.response_metadata) {
        content += `
            <div class="detail-section">
                <h4>Response Metadata</h4>
                <table class="table meta-table">
                    ${Object.entries(data.response_metadata).map(([key, value]) => `
                        <tr>
                            <th>${formatKeyName(key)}</th>
                            <td>${formatValue(value)}</td>
                        </tr>
                    `).join('')}
                </table>
            </div>
        `;
    }
    
    // Add proposal metadata
    if (data.proposal_metadata) {
        content += `
            <div class="detail-section">
                <h4>Proposal Metadata</h4>
                <table class="table meta-table">
                    ${Object.entries(data.proposal_metadata).map(([key, value]) => `
                        <tr>
                            <th>${formatKeyName(key)}</th>
                            <td>${formatValue(value)}</td>
                        </tr>
                    `).join('')}
                </table>
            </div>
        `;
    }
    
    // Set the modal content
    modalBody.innerHTML = content;
    
    // Show the modal
    modal.show();
}

// Helper function to extract title from user prompt
function extractTitle(prompt) {
    if (!prompt) return 'Unknown';
    
    const titleMatch = prompt.match(/title:\s*([^,\n]+)/i);
    if (titleMatch && titleMatch[1]) {
        return titleMatch[1].trim();
    }
    
    return 'No Title Found';
}

// Format key names for display (capitalize and replace underscores with spaces)
function formatKeyName(key) {
    return key
        .replace(/_/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase());
}

// Format values for display
function formatValue(value) {
    if (value === null) return '<span class="json-null">null</span>';
    
    if (typeof value === 'string') {
        // Handle date strings
        if (value.match(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)) {
            return value;
        }
        return `<span class="json-string">${value}</span>`;
    }
    
    if (typeof value === 'number') {
        // Format timestamps as dates if they look like Unix timestamps
        if (value > 1500000000 && value < 2000000000) {
            return `${value} <small>(${formatDate(value)})</small>`;
        }
        return `<span class="json-number">${value}</span>`;
    }
    
    if (typeof value === 'boolean') {
        return `<span class="json-boolean">${value}</span>`;
    }
    
    if (Array.isArray(value)) {
        if (value.length === 0) return '[]';
        return `<ul class="mb-0 ps-3">
            ${value.map(item => `<li>${formatValue(item)}</li>`).join('')}
        </ul>`;
    }
    
    if (typeof value === 'object') {
        return `<pre class="mb-0">${JSON.stringify(value, null, 2)}</pre>`;
    }
    
    return String(value);
}

// Function to apply filters to the tables
function applyFilter(type, filter) {
    // Store current filter
    if (type === 'realtime') {
        currentRealtimeFilter = filter;
        
        // Update active button state
        document.querySelectorAll('#realtime .filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`realtimeFilter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).classList.add('active');
    } else {
        currentDelayedFilter = filter;
        
        // Update active button state
        document.querySelectorAll('#delayed .filter-btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`delayedFilter${filter.charAt(0).toUpperCase() + filter.slice(1)}`).classList.add('active');
    }
    
    // Apply filter to the table
    applyTableFilter(type, filter);
}

function applyTableFilter(type, filter) {
    const tableBody = document.getElementById(`${type}TableBody`);
    if (!tableBody) return;
    
    const rows = tableBody.querySelectorAll('tr');
    const searchInput = document.getElementById(`${type}Search`);
    const searchTerm = searchInput ? searchInput.value.trim().toLowerCase() : 
                       (type === 'realtime' ? currentRealtimeSearch : currentDelayedSearch);
    
    rows.forEach(row => {
        if (row.cells.length <= 1) return; // Skip rows with just loading message or error
        
        const correctnessCell = row.querySelector('td:nth-child(5)');
        const isCorrect = correctnessCell && correctnessCell.innerHTML.includes('check-lg');
        
        // Apply correctness filter
        let showByFilter = filter === 'all' || 
                          (filter === 'correct' && isCorrect) || 
                          (filter === 'incorrect' && !isCorrect);
        
        // Apply search filter if there's a search term
        let showBySearch = true;
        if (searchTerm) {
            showBySearch = false;
            const cells = row.querySelectorAll('td');
            cells.forEach(cell => {
                if (cell.textContent.toLowerCase().includes(searchTerm)) {
                    showBySearch = true;
                }
            });
        }
        
        // Show row only if it passes both filters
        row.style.display = (showByFilter && showBySearch) ? '' : 'none';
    });
} 