// Global variables to store data and charts
let currentData = [];
let currentExperiment = null;
let experimentsData = [];
let modal = null;
let currentFilter = 'all'; // Track current filter state
let currentSearch = ''; // Track current search term

// Chart variables
let recommendationChart = null;
let resolutionChart = null;

// Initialize the application when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize modal
    modal = new bootstrap.Modal(document.getElementById('detailsModal'));
    
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
    
    // Set up clear tag filter button
    document.getElementById('clearTagFilter')?.addEventListener('click', clearTagFilter);
});

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
        // Count recommendations
        const rec = entry.recommendation?.toLowerCase();
        if (rec === 'p1') p1Count++;
        else if (rec === 'p2') p2Count++;
        else if (rec === 'p3') p3Count++;
        else if (rec === 'p4') p4Count++;
        
        // Count resolutions - using only resolved_price_outcome
        const resolution = entry.resolved_price_outcome.toString().toLowerCase();
                           
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
    // Only compare if resolved_price_outcome is available
    if (entry.resolved_price_outcome !== undefined && entry.resolved_price_outcome !== null) {
        const rec = entry.recommendation?.toLowerCase();
        const resolved = entry.resolved_price_outcome.toString().toLowerCase();
        
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
    
    // Update specialized accuracy metrics
    const p12Accuracy = document.getElementById('p12Accuracy');
    if (p12Accuracy) {
        p12Accuracy.style.width = `${analytics.p12Accuracy}%`;
        p12Accuracy.setAttribute('aria-valuenow', analytics.p12Accuracy);
        p12Accuracy.textContent = `${Math.round(analytics.p12Accuracy)}%`;
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

// Helper function to format date in 24-hour format
function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    
    const date = new Date(timestamp * 1000);
    return date.toISOString().slice(0, 10) + ' ' + date.toTimeString().slice(0, 5);
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
    
    // Sort experiments by timestamp (newest first - descending order)
    const sortedExperiments = [...experimentsData].sort((a, b) => {
        // Try to compare timestamps
        const dateA = a.timestamp ? new Date(a.timestamp.replace(/(\d+)[\/\-](\d+)[\/\-](\d+)/, '$3-$2-$1')) : new Date(0);
        const dateB = b.timestamp ? new Date(b.timestamp.replace(/(\d+)[\/\-](\d+)[\/\-](\d+)/, '$3-$2-$1')) : new Date(0);
        return dateB - dateA; // Changed to sort in descending order (newest first)
    });
    
    // Generate table rows with full-width format
    tableBody.innerHTML = sortedExperiments.map(experiment => `
        <tr class="experiment-row" data-directory="${experiment.directory}">
            <td>
                <div>
                    <span class="experiment-date">${formatDisplayDate(experiment.timestamp)}</span>
                    <span class="experiment-title">${experiment.title || experiment.directory}</span>
                </div>
                ${experiment.goal ? `<div class="experiment-description">${experiment.goal}</div>` : ''}
            </td>
        </tr>
    `).join('');
    
    // Add click event to rows
    document.querySelectorAll('.experiment-row').forEach(row => {
        row.addEventListener('click', () => {
            const directory = row.getAttribute('data-directory');
            loadExperimentData(directory);
            
            // Highlight the selected row
            document.querySelectorAll('.experiment-row').forEach(r => {
                r.classList.remove('table-active');
            });
            row.classList.add('table-active');
        });
    });
    
    // Load the first experiment by default
    if (sortedExperiments.length > 0) {
        const firstRow = document.querySelector('.experiment-row');
        if (firstRow) {
            firstRow.classList.add('table-active');
            loadExperimentData(sortedExperiments[0].directory);
        }
    }
}

// Load data for a specific experiment
async function loadExperimentData(directory) {
    try {
        // Reset current data to prevent showing old data
        currentData = [];
        
        // Find the experiment in our data
        currentExperiment = experimentsData.find(exp => exp.directory === directory);
        if (!currentExperiment) {
            throw new Error(`Experiment directory ${directory} not found`);
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
        
        // Load data from the experiment's outputs directory
        const outputsPath = `/results/${directory}/outputs/`;
        console.log(`Loading data from ${outputsPath}`);
        
        // Show loading indicator
        document.getElementById('resultsTableBody').innerHTML = `
            <tr>
                <td colspan="7" class="text-center">
                    <div class="spinner-border text-primary" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <p class="mt-2">Loading results from ${outputsPath}...</p>
                </td>
            </tr>
        `;
        
        // Try to load data from all JSON files in the outputs directory
        let fileErrors = [];
        
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
                    // Since we can't browse directories, we'll try loading common JSON files
                    // that might be there, or add API endpoints to list files
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
                                    fileErrors.push(`Error loading ${filename}: ${fileResponse.status}`);
                                }
                            } catch (fileError) {
                                fileErrors.push(`Error loading ${filename}: ${fileError.message}`);
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
            console.log(`Successfully loaded ${currentData.length} result items`);
            
            // If we didn't load any data, show error
            if (currentData.length === 0) {
                throw new Error(`No valid data files found in ${outputsPath}. Errors: ${fileErrors.join(', ')}`);
            }
        } catch (error) {
            console.error('Error loading output files:', error);
            
            // Hide analytics, filter, and tag filter when there's an error loading files
            document.getElementById('analyticsDashboard').style.display = 'none';
            document.getElementById('filterControls').style.display = 'none';
            const tagFilterCard = document.getElementById('tagFilterCard');
            if (tagFilterCard) {
                tagFilterCard.style.display = 'none';
            }
            
            // Show error message
            document.getElementById('resultsTableBody').innerHTML = `
                <tr>
                    <td colspan="7" class="text-center text-danger">
                        Error loading output files: ${error.message}
                    </td>
                </tr>
            `;
            return;
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
        // First try the directory listing API if it exists
        const response = await fetch(`/api/list-files?path=${dirPath}`);
        
        if (response.ok) {
            const data = await response.json();
            return data.files || [];
        }
        
        // If that fails, try to scrape the directory listing
        const dirResponse = await fetch(`/${dirPath}/`);
        if (dirResponse.ok) {
            const html = await dirResponse.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Extract links to JSON files
            return Array.from(doc.querySelectorAll('a'))
                .filter(a => a.href.endsWith('.json'))
                .map(a => a.href.split('/').pop());
        }
        
        // As a fallback, use this hardcoded list of sample filenames that we've seen
        // This is not ideal but will help in case directory listing is not available
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
    const metadataCard = document.getElementById('experimentMetadataCard');
    const metadataContent = document.getElementById('experimentMetadataContent');
    
    if (!metadataCard || !metadataContent || !currentExperiment) {
        if (metadataCard) metadataCard.style.display = 'none';
        return;
    }
    
    metadataCard.style.display = 'block';
    
    // Extract the experiment info from metadata
    const experimentInfo = currentExperiment.metadata?.experiment || {};
    
    // Create a formatted display of the metadata
    let content = '';
    
    // Title and timestamp
    content += `<h4>${experimentInfo.title || currentExperiment.title || currentExperiment.directory}</h4>`;
    if (experimentInfo.timestamp || currentExperiment.timestamp) {
        content += `<p><strong>Date:</strong> ${experimentInfo.timestamp || currentExperiment.timestamp}</p>`;
    }
    
    // Goal
    if (experimentInfo.goal || currentExperiment.goal) {
        content += `<p><strong>Goal:</strong> ${experimentInfo.goal || currentExperiment.goal}</p>`;
    }
    
    // Previous experiment reference
    if (experimentInfo.previous_experiment) {
        content += `<p><strong>Previous Experiment:</strong> ${experimentInfo.previous_experiment}</p>`;
    }
    
    // Prompt version
    if (experimentInfo.prompt_version) {
        content += `<p><strong>Prompt Version:</strong> ${experimentInfo.prompt_version}</p>`;
    }
    
    // Modifications
    if (experimentInfo.modifications) {
        content += `<div><strong>Modifications:</strong><ul>`;
        for (const [key, value] of Object.entries(experimentInfo.modifications)) {
            content += `<li><strong>${formatKeyName(key)}:</strong> ${value}</li>`;
        }
        content += `</ul></div>`;
    }
    
    // Setup details
    if (experimentInfo.setup) {
        content += `<div><strong>Setup:</strong><ul>`;
        for (const [key, value] of Object.entries(experimentInfo.setup)) {
            content += `<li><strong>${formatKeyName(key)}:</strong> ${value}</li>`;
        }
        content += `</ul></div>`;
    }
    
    // Add system prompt toggle with improved styling
    content += `<div class="mt-3 mb-2">
        <a href="#" id="toggleSystemPrompt" class="d-inline-flex align-items-center">
            <strong>System Prompt</strong> <i class="bi bi-chevron-down ms-1"></i>
        </a>
    </div>`;
    
    // Set the content
    metadataContent.innerHTML = content;
    
    // Check if overlay container exists, create if not
    let overlayContainer = document.getElementById('systemPromptOverlay');
    if (!overlayContainer) {
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
        
        overlayContainer.appendChild(closeButton);
        overlayContainer.appendChild(contentDiv);
        document.body.appendChild(overlayContainer);
    }
    
    // Add system prompt content
    if (experimentInfo.system_prompt) {
        document.getElementById('systemPromptContent').innerHTML = `
            <h3>System Prompt</h3>
            <pre class="system-prompt-pre">${experimentInfo.system_prompt}</pre>
        `;
        
        // Add toggle logic
        document.getElementById('toggleSystemPrompt').addEventListener('click', function(e) {
            e.preventDefault();
            overlayContainer.style.display = 'block';
            document.body.style.overflow = 'hidden';
        });
    } else {
        // If no system prompt available
        document.getElementById('toggleSystemPrompt').style.display = 'none';
    }
    
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
}

// Display the results data in the table
function displayResultsData() {
    updateTableWithData(currentData);
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
    
    // Generate table rows
    tableBody.innerHTML = dataArray.map((item, index) => {
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
        const queryId = item.question_id_short || (item.query_id ? item.query_id.substring(0, 10) : 'N/A');
        const recommendation = item.recommendation || item.proposed_price_outcome || 'N/A';
        const resolution = item.resolved_price_outcome !== undefined && item.resolved_price_outcome !== null ? 
                          item.resolved_price_outcome : 'Unresolved';
        
        const formattedDate = formatDate(item.timestamp || item.unix_timestamp);
        
        // Store the actual data index as a data attribute
        const originalDataIndex = dataArray === currentData ? index : currentData.indexOf(item);
        
        return `
            <tr class="result-row ${item.recommendation?.toLowerCase() === 'p4' ? 'table-warning' : ''}" data-item-id="${originalDataIndex}">
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
    document.getElementById('displayingCount').textContent = dataArray.length;
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
        'ancillary_data', 'citations', 'proposal_metadata', 'response_metadata', 'processed_file'
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

// Extracts a title from user_prompt or ancillary data
function extractTitle(item) {
    // Try to extract from user_prompt first
    if (item.user_prompt) {
        const titleMatch = item.user_prompt.match(/title:\s*([^,\n]+)/i);
        if (titleMatch && titleMatch[1]) {
            return titleMatch[1].trim();
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
    
    return 'No title';
}

// Format a key name for display
function formatKeyName(key) {
    return key.replace(/_/g, ' ').replace(/\b\w/g, letter => letter.toUpperCase());
}

// Format a value for display
function formatValue(value) {
    if (value === null || value === undefined) return 'N/A';
    
    if (typeof value === 'object') {
        try {
            return `<pre class="mb-0">${JSON.stringify(value, null, 2)}</pre>`;
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