/**
 * Helper functions for query.html - displays data from the LLM Oracle API
 */

/**
 * Escape HTML special characters
 */
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

/**
 * Format a timestamp into a user-friendly date string
 */
function formatDate(timestamp) {
    if (!timestamp) return 'N/A';
    
    // Convert to number if it's a string
    if (typeof timestamp === 'string') {
        timestamp = parseInt(timestamp, 10);
    }
    
    // Check if it's a unix timestamp (in seconds)
    if (timestamp < 20000000000) {  // If less than year 2603
        timestamp = timestamp * 1000;  // Convert to milliseconds
    }
    
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) return 'Invalid Date';
    
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true
    });
}

/**
 * Extract a title from a data object based on various possible fields
 */
function extractTitle(data) {
    // Try various possible locations for the title
    if (data.title) return data.title;
    if (data.prompt && typeof data.prompt === 'string' && data.prompt.length < 100) return data.prompt;
    if (data.proposal_metadata && data.proposal_metadata.title) return data.proposal_metadata.title;
    if (data.market_data && data.market_data.title) return data.market_data.title;
    
    // Try to extract from ancillary data if it exists and has title
    if (data.ancillary_data && typeof data.ancillary_data === 'string') {
        // Common pattern: {"title": "Some title", ...}
        const titleMatch = data.ancillary_data.match(/"title"\s*:\s*"([^"]+)"/);
        if (titleMatch && titleMatch[1]) {
            return titleMatch[1];
        }
    }
    
    // Fall back to question_id or query_id if nothing else
    if (data.question_id) return `Question ${data.question_id.slice(0, 10)}...`;
    if (data.query_id) return `Query ${data.query_id.slice(0, 10)}...`;
    
    return 'Query Result';
}

/**
 * Determine if a recommendation is correct based on resolution data
 */
function isRecommendationCorrect(data) {
    const recommendation = data.format_version === 2 
        ? (data.result?.recommendation || data.recommendation) 
        : (data.recommendation || data.proposed_price_outcome);
        
    const resolution = data.format_version === 2
        ? (data.market_data?.resolved_price_outcome || data.market_data?.resolved_price)
        : (data.resolved_price_outcome || data.resolved_price);
    
    // If no resolution, we can't determine correctness
    if (resolution === undefined || resolution === null) {
        return null;  // Unresolved
    }
    
    // Check if the recommendation matches the resolution
    return recommendation === resolution;
}

/**
 * Format an actor name for display
 */
function formatActorName(actor) {
    if (!actor) return 'Unknown';
    
    // Convert snake_case to Title Case
    return actor
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Format an action name for display
 */
function formatActionName(action) {
    if (!action) return 'Unknown';
    
    // Convert snake_case to Title Case
    return action
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
}

/**
 * Render content from a journey step
 */
function renderJourneyStepContent(step, stepIndex) {
    let content = '';
    
    if (step.code && step.actor === 'code_runner') {
        content += `
            <div class="code-section">
                <div class="mb-2">
                    <strong>Code:</strong>
                    <button class="btn btn-sm btn-outline-secondary toggle-code-btn" data-target="step-code-${stepIndex}">
                        <i class="bi bi-code-slash"></i> Toggle Code
                    </button>
                </div>
                <div class="code-content collapsed" id="step-code-${stepIndex}">
                    <pre class="language-python"><code>${escapeHtml(step.code)}</code></pre>
                </div>
            </div>
        `;
    }
    
    if (step.prompt) {
        content += `
            <div class="mb-3">
                <div>
                    <strong>Prompt:</strong>
                    <button class="btn btn-sm btn-outline-secondary toggle-prompt-btn" data-target="step-prompt-${stepIndex}">
                        <i class="bi bi-chat-left-text"></i> Toggle Prompt
                    </button>
                </div>
                <div class="prompt-content collapsed" id="step-prompt-${stepIndex}">
                    <pre>${escapeHtml(step.prompt)}</pre>
                </div>
            </div>
        `;
    }
    
    if (step.code_output && step.actor === 'code_runner') {
        content += `
            <div class="mb-3">
                <div>
                    <strong>Code Output:</strong>
                    <button class="btn btn-sm btn-outline-secondary toggle-output-btn" data-target="step-output-${stepIndex}">
                        <i class="bi bi-terminal"></i> Toggle Output
                    </button>
                </div>
                <div class="output-content collapsed" id="step-output-${stepIndex}">
                    <pre>${escapeHtml(step.code_output)}</pre>
                </div>
            </div>
        `;
    }
    
    if (step.full_response) {
        content += `
            <div class="mb-3">
                <div>
                    <strong>Response:</strong>
                    <button class="btn btn-sm btn-outline-secondary toggle-response-btn" data-target="step-response-${stepIndex}">
                        <i class="bi bi-chat-right-text"></i> Toggle Response
                    </button>
                </div>
                <div class="response-content collapsed" id="step-response-${stepIndex}">
                    <pre>${escapeHtml(step.full_response)}</pre>
                </div>
            </div>
        `;
    }
    
    if (step.recommendation) {
        content += `<div class="mb-2"><strong>Recommendation:</strong> ${step.recommendation}</div>`;
    }
    
    if (step.reason) {
        content += `<div class="mb-2"><strong>Reason:</strong> ${step.reason}</div>`;
    }
    
    return content;
}

/**
 * Render JSON data with collapsible sections
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
 * Add the JSON data section to the content
 */
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
            <h4 class="section-title">Full JSON Data</h4>
            <div class="card">
                <div class="card-body">
                    <div class="json-container">${renderFoldableJSON(data)}</div>
                </div>
            </div>
        </div>
    `;
}

/**
 * Toggle folding of a JSON section
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
 */
function toggleJsonProperty(element) {
    // Toggle the collapsed class on the element itself
    element.classList.toggle('collapsed');
    
    // First, check if this is a collapsible string or step heading
    if (element.classList.contains('collapsible-string')) {
        let codeBlock = element.nextElementSibling;
        if (codeBlock && codeBlock.classList.contains('code-block')) {
            codeBlock.classList.toggle('collapsed');
        }
        return;
    }
    
    // Handle step headings (special case for journey array)
    if (element.textContent.startsWith('Step ') && element.textContent.includes(':')) {
        // Special case for steps in journey array
        let valueDiv = element.nextElementSibling;
        if (valueDiv && valueDiv.classList.contains('json-value')) {
            valueDiv.classList.toggle('collapsed');
        }
        return;
    }
    
    // Check for code runner steps - we need to handle the code sections specifically
    if (element.textContent.includes('code_runner') && element.textContent.includes('step')) {
        // Look for code sections in this step
        const stepContainer = element.closest('.journey-step-card');
        if (stepContainer) {
            // Find all code-section elements in this step
            const codeSections = stepContainer.querySelectorAll('.code-section .code-content');
            codeSections.forEach(section => {
                // Make sure the code sections are visible when the step is expanded
                section.classList.remove('collapsed');
            });
        }
    }
    
    // Find the value container - could be right after a property key or after a colon
    let valueDiv = null;
    let next = element.nextElementSibling;
    
    if (next && next.textContent === ':') {
        // If followed by a colon, the value is after the colon
        valueDiv = next.nextElementSibling;
    } else {
        // Otherwise it's the next element
        valueDiv = next;
    }
    
    if (valueDiv && (valueDiv.classList.contains('json-value') || 
                  valueDiv.classList.contains('code-block') || 
                  valueDiv.classList.contains('content-collapsible'))) {
        valueDiv.classList.toggle('collapsed');
    }
}

/**
 * Show the query result details
 */
function showQueryResult(data) {
    const container = document.getElementById('queryResultContainer');
    const title = document.getElementById('queryTitle');
    const queryInfo = document.getElementById('queryInfo');
    
    if (!container || !data) return;
    
    // Update title and query info
    const titleText = extractTitle(data);
    title.textContent = titleText;
    
    // Set query info with query_id and timestamp
    const query_id = data.query_id || 'N/A';
    const timestamp = data.timestamp || data.unix_timestamp || 0;
    queryInfo.innerHTML = `
        <strong>Query ID:</strong> ${query_id} | 
        <strong>Time:</strong> ${formatDate(timestamp)}
    `;
    
    // Check if this is format_version 2
    const isFormatV2 = data.format_version === 2;
    
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
    
    // Generate the content
    let content = `
        <div class="alert ${alertClass} mb-4">
            <strong>Recommendation:</strong> ${recommendation} | 
            <strong>Resolved:</strong> ${data.resolved_price_outcome || 'Unresolved'} | 
            <strong>Proposed:</strong> ${proposedPrice} | 
            <strong>Disputed:</strong> ${isDisputed ? 'Yes' : 'No'} | 
            <strong>Correct:</strong> ${correctnessText}
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
    const short_id = data.question_id_short || data.short_id || '';
    const condition_id = data.condition_id || data.proposal_metadata?.condition_id || (data.market_data ? data.market_data.condition_id : '');
    const process_time = data.timestamp || 0;
    const request_time = data.proposal_metadata?.request_transaction_block_time || 0;
    const expiration_time = data.proposal_metadata?.expiration_timestamp || 0;
    const end_date = data.end_date_iso || data.proposal_metadata?.end_date_iso || (data.market_data ? data.market_data.end_date_iso : 'N/A');
    const game_start_time = data.game_start_time || data.proposal_metadata?.game_start_time || (data.market_data ? data.market_data.game_start_time : 'N/A');
    
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
    
    // For format_version 2, add journey section
    if (isFormatV2 && data.journey && Array.isArray(data.journey) && data.journey.length > 0) {
        content += `
            <div class="detail-section">
                <h4 class="section-title">Journey</h4>
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
                                <div class="step-timestamp">${formatDate(step.timestamp)}</div>
                            </div>
                            <div class="journey-step-body" id="journey-step-body-${stepIndex}">
                                ${renderJourneyStepContent(step, stepIndex)}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }
    
    // Add result section for format_version 2
    if (isFormatV2 && data.result) {
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
        
        content += `
                </div>
            </div>
        `;
    }
    
    // Use the new function for JSON folding
    content = addJsonDataSection(content, data);
    
    // Set the content
    container.innerHTML = content;
    
    // Show the container and hide the loading spinner
    document.getElementById('loadingSpinner').style.display = 'none';
    container.style.display = 'block';
    
    // Apply syntax highlighting to code blocks
    Prism.highlightAllUnder(container);
    
    // Initialize toggle buttons for code sections
    document.querySelectorAll('.toggle-content-btn').forEach(button => {
        button.addEventListener('click', function() {
            const targetId = this.getAttribute('data-target');
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                targetElement.classList.toggle('collapsed');
                const icon = this.querySelector('i');
                if (icon) {
                    icon.classList.toggle('bi-arrows-expand');
                    icon.classList.toggle('bi-arrows-collapse');
                }
            }
        });
    });
    
    // Add journey step click handlers
    document.querySelectorAll('.journey-step-header').forEach(header => {
        header.addEventListener('click', function() {
            const stepIndex = this.getAttribute('data-step');
            const body = document.getElementById(`journey-step-body-${stepIndex}`);
            if (body) {
                this.classList.toggle('active');
                body.classList.toggle('active');
            }
        });
    });
    
    // Setup copy to clipboard functionality
    document.querySelectorAll('.copy-to-clipboard').forEach(element => {
        element.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            if (!textToCopy) return;
            
            navigator.clipboard.writeText(textToCopy).then(() => {
                // Show feedback
                const feedback = this.nextElementSibling;
                if (feedback && feedback.classList.contains('copy-feedback')) {
                    feedback.style.display = 'inline';
                    setTimeout(() => {
                        feedback.style.display = 'none';
                    }, 1500);
                }
            });
        });
    });
}

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
            showQueryResult(data[0]);
        } else if (data && typeof data === 'object') {
            // For question endpoint, it returns a single object
            showQueryResult(data);
        } else {
            showError('No data found for the specified parameters.');
        }
    } catch (error) {
        showError(`Error fetching data: ${error.message}`);
        console.error('API Error:', error);
    }
}

/**
 * Show error message
 */
function showError(message) {
    const errorElement = document.getElementById('errorMessage');
    const loadingElement = document.getElementById('loadingSpinner');
    
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
    }
    
    if (loadingElement) {
        loadingElement.style.display = 'none';
    }
}

// Make toggle functions globally available
window.toggleJsonFolding = toggleJsonFolding;
window.toggleJsonProperty = toggleJsonProperty;

// Initialize when document is ready
document.addEventListener('DOMContentLoaded', fetchQueryData);