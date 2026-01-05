// Use relative URL if served from same origin, otherwise use full URL
const API_BASE_URL = window.location.origin;

let currentDatasetId = null;
let currentDomain = null;
let isAutoMode = true; // Default to automatic mode

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Ensure loading overlay is hidden on page load
    hideLoading();
    setupEventListeners();
});

// Also ensure overlay is hidden immediately (in case DOMContentLoaded already fired)
if (document.readyState === 'loading') {
    // Loading hasn't finished yet
} else {
    // DOMContentLoaded has already fired
    hideLoading();
    setupEventListeners();
}

// Progress and loading functions
function showProgress() {
    const progressDiv = document.getElementById('auto-progress');
    if (progressDiv) {
        progressDiv.classList.remove('hidden');
    }
}

function hideProgress() {
    const progressDiv = document.getElementById('auto-progress');
    if (progressDiv) {
        progressDiv.classList.add('hidden');
    }
}

function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'flex';
        overlay.classList.remove('hidden');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.style.display = 'none';
        overlay.classList.add('hidden');
    }
}

function setupEventListeners() {
    const fileInput = document.getElementById('file-input');
    const uploadArea = document.querySelector('.upload-box');
    
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#eef0ff';
    });
    
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '#f8f9ff';
    });
    
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = '#f8f9ff';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload({ target: { files: files } });
        }
    });
    
    // Buttons (for manual mode if needed)
    const detectBtn = document.getElementById('detect-domain-btn');
    const preprocessBtn = document.getElementById('preprocess-btn');
    const trainBtn = document.getElementById('train-btn');
    const explainBtn = document.getElementById('explain-btn');
    const rulesBtn = document.getElementById('extract-rules-btn');
    const reportBtn = document.getElementById('generate-report-btn');
    
    if (detectBtn) detectBtn.addEventListener('click', detectDomain);
    if (preprocessBtn) preprocessBtn.addEventListener('click', preprocessData);
    if (trainBtn) trainBtn.addEventListener('click', trainModel);
    if (explainBtn) explainBtn.addEventListener('click', explainModel);
    if (rulesBtn) rulesBtn.addEventListener('click', extractRules);
    if (reportBtn) reportBtn.addEventListener('click', generateReport);
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    showLoading();
    showProgress();
    updateProgressStep('upload', 'Uploading dataset...', true);
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API_BASE_URL}/upload`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            currentDatasetId = data.dataset_id;
            updateProgressStep('upload', 'Dataset uploaded successfully', false, true);
            
            // Always use automatic mode
            await processAutomatically(data);
        } else {
            updateProgressStep('upload', 'Upload failed: ' + (data.detail || 'Unknown error'), false, false, true);
            showError('Upload failed: ' + (data.detail || 'Unknown error'));
            hideLoading();
            hideProgress();
        }
    } catch (error) {
        updateProgressStep('upload', 'Error: ' + error.message, false, false, true);
        showError('Error uploading file: ' + error.message);
        hideLoading();
        hideProgress();
    }
}

async function processAutomatically(uploadData) {
    try {
        // Step 1: Detect Domain
        updateProgressStep('detect', 'Detecting domain(s)...', true);
        const domainResponse = await fetch(`${API_BASE_URL}/detect-domain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId })
        });
        const domainData = await domainResponse.json();
        
        if (!domainResponse.ok) {
            const errorMsg = typeof domainData.detail === 'string' 
                ? domainData.detail 
                : domainData.detail?.message || JSON.stringify(domainData.detail) || 'Unknown error';
            throw new Error('Domain detection failed: ' + errorMsg);
        }
        
        if (!domainData.detected_domains || domainData.detected_domains.length === 0) {
            throw new Error('No domains detected. Please check your dataset columns.');
        }
        
        currentDomain = domainData.primary_domain || domainData.detected_domains[0]?.domain || 'General';
        updateProgressStep('detect', `Domain detected: ${currentDomain}`, false, true);
        
        // Step 1.5: Analyze Columns
        let columnAnalysisData = null;
        try {
            updateProgressStep('analyze', 'Analyzing column purposes...', true);
            const analyzeResponse = await fetch(`${API_BASE_URL}/analyze-columns`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ dataset_id: currentDatasetId, domain: currentDomain })
            });
            columnAnalysisData = await analyzeResponse.json();
            if (analyzeResponse.ok) {
                updateProgressStep('analyze', `Analyzed ${columnAnalysisData.total_columns} columns`, false, true);
            } else {
                updateProgressStep('analyze', 'Column analysis skipped (optional)', false, true);
            }
        } catch (e) {
            console.warn('Column analysis skipped:', e);
            updateProgressStep('analyze', 'Column analysis skipped (optional)', false, true);
        }
        
        // Step 2: Preprocess
        updateProgressStep('preprocess', 'Preprocessing data...', true);
        const preprocessResponse = await fetch(`${API_BASE_URL}/preprocess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId, domain: currentDomain })
        });
        const preprocessData = await preprocessResponse.json();
        
        if (!preprocessResponse.ok) {
            const errorMsg = typeof preprocessData.detail === 'string' 
                ? preprocessData.detail 
                : preprocessData.detail?.message || JSON.stringify(preprocessData.detail) || 'Unknown error';
            throw new Error('Preprocessing failed: ' + errorMsg);
        }
        
        updateProgressStep('preprocess', 'Data preprocessed successfully', false, true);
        
        // Step 3: Get suggested target column
        updateProgressStep('target', 'Selecting target column...', true);
        const targetResponse = await fetch(`${API_BASE_URL}/dataset/${currentDatasetId}/suggest-target?domain=${currentDomain}`);
        const targetData = await targetResponse.json();
        
        if (!targetResponse.ok || !targetData.suggested_column) {
            throw new Error('Could not determine target column. Please use manual mode.');
        }
        
        const targetColumn = targetData.suggested_column;
        updateProgressStep('target', `Target column selected: ${targetColumn}`, false, true);
        
        // Step 4: Train Model
        updateProgressStep('train', `Training model for target: ${targetColumn}...`, true);
        const trainResponse = await fetch(`${API_BASE_URL}/train-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain,
                target_column: targetColumn
            })
        });
        const trainData = await trainResponse.json();
        
        if (!trainResponse.ok) {
            const errorMsg = typeof trainData.detail === 'string' 
                ? trainData.detail 
                : Array.isArray(trainData.detail) 
                    ? trainData.detail.map(e => typeof e === 'string' ? e : e.msg || JSON.stringify(e)).join(', ')
                    : trainData.detail?.msg || trainData.detail?.message || JSON.stringify(trainData.detail) || 'Unknown error';
            throw new Error('Model training failed: ' + errorMsg);
        }
        
        updateProgressStep('train', 'Model trained successfully', false, true);
        
        // Step 5: Explain Model
        updateProgressStep('explain', 'Generating model explanations...', true);
        const explainResponse = await fetch(`${API_BASE_URL}/explain-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain,
                sample_size: 100
            })
        });
        const explainData = await explainResponse.json();
        
        if (!explainResponse.ok) {
            console.warn('Explanation failed: ' + (explainData.detail || 'Unknown error'));
            updateProgressStep('explain', 'Explanation skipped (optional)', false, true);
        } else {
            updateProgressStep('explain', 'Model explanations generated', false, true);
        }
        
        // Step 6: Extract Rules
        let rulesData = { association_rules: [], if_then_rules: [] };
        try {
            updateProgressStep('rules', 'Extracting business rules...', true);
            const rulesResponse = await fetch(`${API_BASE_URL}/extract-rules`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_id: currentDatasetId,
                    domain: currentDomain,
                    min_support: 0.1,
                    min_confidence: 0.5
                })
            });
            rulesData = await rulesResponse.json();
            
            if (!rulesResponse.ok) {
                console.warn('Rule extraction failed: ' + (rulesData.detail || 'Unknown error'));
                updateProgressStep('rules', 'Rule extraction skipped (optional)', false, true);
            } else {
                updateProgressStep('rules', 'Business rules extracted', false, true);
            }
        } catch (e) {
            console.warn('Rule extraction error:', e);
            updateProgressStep('rules', 'Rule extraction skipped (optional)', false, true);
        }
        
        // Step 7: Generate Report
        updateProgressStep('report', 'Generating comprehensive report...', true);
        const reportResponse = await fetch(`${API_BASE_URL}/generate-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain
            })
        });
        const reportData = await reportResponse.json();
        
        if (!reportResponse.ok) {
            const errorMsg = typeof reportData.detail === 'string' 
                ? reportData.detail 
                : Array.isArray(reportData.detail) 
                    ? reportData.detail.map(e => typeof e === 'string' ? e : e.msg || JSON.stringify(e)).join(', ')
                    : reportData.detail?.msg || reportData.detail?.message || JSON.stringify(reportData.detail) || 'Unknown error';
            throw new Error('Report generation failed: ' + errorMsg);
        }
        
        updateProgressStep('report', 'Report generated successfully', false, true);
        
        // Display all results
        hideLoading();
        hideProgress();
        displayAutomaticResults(uploadData, domainData, preprocessData, trainData, explainData, rulesData, reportData, columnAnalysisData);
        
    } catch (error) {
        hideLoading();
        hideProgress();
        const errorMsg = error.message || 'Unknown error occurred';
        showError('Automatic processing failed: ' + errorMsg);
        updateProgressStep('error', errorMsg, false, false, true);
        console.error('Processing error:', error);
    }
}

function displayAutomaticResults(uploadData, domainData, preprocessData, trainData, explainData, rulesData, reportData, columnAnalysisData) {
    const resultsSection = document.createElement('section');
    resultsSection.className = 'card';
    resultsSection.id = 'auto-results-section';
    resultsSection.innerHTML = `
        <h2>📊 Complete Analysis Results</h2>
        
        <div class="success-message" style="margin-bottom: 20px;">
            <h3>✅ Processing Complete!</h3>
            <p>All steps completed successfully. Review the results below.</p>
        </div>
        
        <!-- Column Analysis & Purposes -->
        ${columnAnalysisData && columnAnalysisData.columns ? `
        <h3 style="margin-top: 20px;">1. Column Analysis & Purposes</h3>
        <div class="results">
            <p style="margin-bottom: 15px;"><strong>Understanding Your Data:</strong> Each column in your dataset has been analyzed to explain its purpose and how it's used in the analysis.</p>
            <div class="table-container" style="max-height: 400px; overflow-y: auto;">
                <table>
                    <thead>
                        <tr>
                            <th>Column Name</th>
                            <th>Purpose</th>
                            <th>Category</th>
                            <th>Data Type</th>
                            <th>Usage in Analysis</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.values(columnAnalysisData.columns).map(col => `
                            <tr>
                                <td><strong>${col.column_name}</strong></td>
                                <td>${col.purpose}</td>
                                <td><span class="domain-badge">${col.category}</span></td>
                                <td>${col.data_type}</td>
                                <td style="font-size: 0.9em; color: #666;">${col.usage_in_analysis || 'Used as a feature in analysis'}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
            ${Object.values(columnAnalysisData.columns).slice(0, 3).map(col => `
                <div class="insight-item" style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 5px;">
                    <h4 style="margin: 0 0 8px 0; color: #667eea;">${col.column_name}</h4>
                    <p style="margin: 5px 0;"><strong>Purpose:</strong> ${col.purpose}</p>
                    ${col.business_context ? `<p style="margin: 5px 0; color: #555;"><strong>Business Context:</strong> ${col.business_context}</p>` : ''}
                    ${col.statistics && col.statistics.mean !== undefined ? `
                        <p style="margin: 5px 0; font-size: 0.9em; color: #666;">
                            <strong>Statistics:</strong> 
                            Mean: ${col.statistics.mean.toFixed(2)}, 
                            Min: ${col.statistics.min.toFixed(2)}, 
                            Max: ${col.statistics.max.toFixed(2)}
                        </p>
                    ` : ''}
                </div>
            `).join('')}
        </div>
        ` : ''}
        
        <!-- Domain Detection -->
        <h3 style="margin-top: 20px;">${columnAnalysisData ? '2' : '1'}. Domain Detection</h3>
        <div class="results">
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Domain</th>
                            <th>Confidence</th>
                            <th>Relevant Columns</th>
                            <th>Rows</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${domainData.detected_domains.map(domain => `
                            <tr>
                                <td><strong>${domain.domain}</strong></td>
                                <td>
                                    <span class="confidence-badge confidence-${domain.confidence > 0.7 ? 'high' : domain.confidence > 0.4 ? 'medium' : 'low'}">
                                        ${(domain.confidence * 100).toFixed(1)}%
                                    </span>
                                </td>
                                <td>${domain.matched_columns.join(', ') || 'None'}</td>
                                <td>${uploadData.rows.toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Preprocessed Dataset Sample -->
        <h3 style="margin-top: 30px;">${columnAnalysisData ? '3' : '2'}. Preprocessed Dataset Sample</h3>
        <div class="results">
            ${preprocessData && preprocessData.sample_data ? `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                ${Object.keys(preprocessData.sample_data[0] || {}).map(col => `<th>${col}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>
                            ${preprocessData.sample_data.slice(0, 5).map(row => `
                                <tr>
                                    ${Object.values(row).map(val => `<td>${val}</td>`).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : '<p>Preprocessed data sample not available</p>'}
        </div>
        
        <!-- Model Performance & Predictions -->
        <h3 style="margin-top: 30px;">${columnAnalysisData ? '4' : '3'}. Model Performance & Sample Predictions</h3>
        <div class="results">
            <div style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #1976d2;">🤖 ML Algorithm Explanation</h4>
                <p style="margin: 5px 0;"><strong>Model Type:</strong> ${trainData.model_type}</p>
                <p style="margin: 5px 0;"><strong>How It Works:</strong> 
                    ${trainData.model_type.includes('classifier') 
                        ? 'This is a rule-based classification model. It learns patterns from your data by identifying thresholds and conditions that best separate different classes. For example, it might learn that "IF leave_count > 5 THEN attrition = High". The model combines multiple such rules to make predictions with confidence scores.'
                        : 'This is a rule-based regression model. It learns relationships between features and the target variable by calculating weighted contributions from each feature. The model predicts numeric values (like salary amounts or sales figures) based on patterns it discovered in your data.'}
                </p>
                <p style="margin: 5px 0;"><strong>Why This Model:</strong> 
                    Rule-based models are chosen because they are <strong>explainable</strong> - you can understand exactly why a prediction was made. Unlike "black box" models, every prediction can be traced back to specific business rules extracted from your data.
                </p>
            </div>
        <div class="results">
            <p><strong>Model Type:</strong> ${trainData.model_type}</p>
            <p><strong>Target Column:</strong> ${trainData.target_column}</p>
            <h4 style="margin-top: 15px;">Performance Metrics:</h4>
            <div style="margin-top: 10px;">
                ${Object.entries(trainData.metrics).map(([key, value]) => `
                    <div class="metric-card">
                        <div class="metric-label">${key.toUpperCase()}</div>
                        <div class="metric-value">${typeof value === 'number' ? value.toFixed(4) : value}</div>
                    </div>
                `).join('')}
            </div>
            ${trainData.sample_predictions && trainData.sample_predictions.length > 0 ? `
                <h4 style="margin-top: 20px;">Sample Predictions:</h4>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Index</th>
                                <th>Actual Value</th>
                                <th>Predicted Value</th>
                                ${trainData.sample_predictions[0].confidence !== undefined ? '<th>Confidence</th>' : ''}
                            </tr>
                        </thead>
                        <tbody>
                            ${trainData.sample_predictions.map(pred => `
                                <tr>
                                    <td>${pred.index}</td>
                                    <td>${pred.actual}</td>
                                    <td><strong>${pred.predicted}</strong></td>
                                    ${pred.confidence !== undefined ? `<td>${(pred.confidence * 100).toFixed(1)}%</td>` : ''}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            ` : ''}
        </div>
        
        <!-- Feature Impact Table -->
        <h3 style="margin-top: 30px;">${columnAnalysisData ? '5' : '4'}. Feature Impact Analysis</h3>
        <div class="results">
            ${explainData && explainData.feature_impact_table && explainData.feature_impact_table.length > 0 ? `
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Feature</th>
                                <th>Importance</th>
                                <th>Impact Level</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${explainData.feature_impact_table.map(item => `
                                <tr>
                                    <td><strong>${item.feature}</strong></td>
                                    <td>${(item.importance * 100).toFixed(2)}%</td>
                                    <td>
                                        <span class="confidence-badge confidence-${item.impact.toLowerCase()}">
                                            ${item.impact}
                                        </span>
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${explainData.human_readable_insights ? `
                    <h4 style="margin-top: 20px;">Key Insights:</h4>
                    ${explainData.human_readable_insights.map(insight => `
                        <div class="insight-item">
                            <p>${insight}</p>
                        </div>
                    `).join('')}
                ` : ''}
            ` : explainData && explainData.feature_importance ? `
                <p>Feature impact table not available. Showing feature importance:</p>
                ${Object.entries(explainData.feature_importance).slice(0, 10).map(([feature, importance]) => `
                    <div class="insight-item">
                        <strong>${feature}</strong>
                        <span class="confidence-badge confidence-high">${(importance * 100).toFixed(2)}%</span>
                    </div>
                `).join('')}
            ` : '<p>Feature importance data not available</p>'}
        </div>
        
        <!-- Business Rules -->
        <h3 style="margin-top: 30px;">${columnAnalysisData ? '6' : '5'}. Business Rules</h3>
        <div class="results">
            <div style="background: #fff3e0; padding: 15px; border-radius: 5px; margin-bottom: 15px;">
                <h4 style="margin: 0 0 10px 0; color: #f57c00;">📋 Understanding Business Rules</h4>
                <p style="margin: 5px 0;"><strong>What are Business Rules?</strong> These are patterns discovered in your data that describe relationships between different columns. For example, "IF leave_count is High THEN attrition is High" tells you that employees with many leave days are more likely to leave.</p>
                <p style="margin: 5px 0;"><strong>Support:</strong> How often this pattern appears in your data (higher = more common).</p>
                <p style="margin: 5px 0;"><strong>Confidence:</strong> How reliable this rule is (higher = more trustworthy).</p>
                <p style="margin: 5px 0;"><strong>Lift:</strong> How much stronger this pattern is compared to random chance (lift > 1 means it's a meaningful pattern).</p>
            </div>
        <div class="results">
            <h4>Association Rules (Apriori Algorithm):</h4>
            ${rulesData && rulesData.association_rules && rulesData.association_rules.length > 0 ? 
                `<div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Rule</th>
                                <th>Support</th>
                                <th>Confidence</th>
                                <th>Lift</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rulesData.association_rules.slice(0, 10).map(rule => {
                                if (rule.error) return `<tr><td colspan="4"><div class="error-message">${rule.error}</div></td></tr>`;
                                return `
                                    <tr>
                                        <td><strong>${rule.rule}</strong></td>
                                        <td>${(rule.support * 100).toFixed(1)}%</td>
                                        <td>${(rule.confidence * 100).toFixed(1)}%</td>
                                        <td>${rule.lift ? rule.lift.toFixed(2) : 'N/A'}</td>
                                    </tr>
                                `;
                            }).join('')}
                        </tbody>
                    </table>
                </div>` : '<p>No association rules found. Try lowering min_support or min_confidence.</p>'
            }
            
            <h4 style="margin-top: 20px;">If-Then Business Rules:</h4>
            ${rulesData && rulesData.if_then_rules && rulesData.if_then_rules.length > 0 ?
                `<div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Rule</th>
                                <th>Confidence</th>
                                <th>Lift</th>
                                <th>Impact</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rulesData.if_then_rules.slice(0, 10).map(rule => `
                                <tr>
                                    <td><strong>${rule.rule}</strong></td>
                                    <td>${(rule.confidence * 100).toFixed(1)}%</td>
                                    <td>${rule.lift ? rule.lift.toFixed(2) : 'N/A'}</td>
                                    <td><span class="confidence-badge confidence-${rule.impact}">${rule.impact.toUpperCase()}</span></td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>` : '<p>No if-then rules extracted.</p>'
            }
        </div>
        
        <!-- Report Summary -->
        <h3 style="margin-top: 30px;">${columnAnalysisData ? '7' : '6'}. Summary Report & Recommendations</h3>
        <div class="results">
            ${reportData && reportData.sections ? `
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                    <h4>📋 Complete Analysis Summary</h4>
                    <ul style="margin-top: 10px; padding-left: 20px; line-height: 1.8;">
                        <li><strong>Domain Detected:</strong> ${currentDomain}</li>
                        <li><strong>Model Type:</strong> ${trainData.model_type}</li>
                        <li><strong>Target Column:</strong> ${trainData.target_column}</li>
                        <li><strong>Total Features:</strong> ${trainData.feature_columns ? trainData.feature_columns.length : 'N/A'}</li>
                        <li><strong>Dataset Rows:</strong> ${uploadData.rows.toLocaleString()}</li>
                        <li><strong>Dataset Columns:</strong> ${uploadData.columns}</li>
                    </ul>
                </div>
                ${reportData.sections.recommendations ? `
                    <h4>💡 Recommendations:</h4>
                    <ul style="margin-top: 10px; padding-left: 20px; line-height: 1.8;">
                        ${reportData.sections.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                ` : ''}
                ${reportData.sections.visualization_suggestions ? `
                    <h4 style="margin-top: 20px;">📊 Visualization Suggestions:</h4>
                    <div style="margin-top: 10px;">
                        ${reportData.sections.visualization_suggestions.map(viz => `<span class="domain-badge">${viz}</span>`).join('')}
                    </div>
                ` : ''}
            ` : '<p>Report data not available</p>'}
        </div>
    `;
    
    // Insert before the loading overlay
    const mainContent = document.querySelector('.main-content');
    mainContent.appendChild(resultsSection);
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
}

function updateProgressStep(step, message, inProgress = false, completed = false, error = false) {
    const progressDiv = document.getElementById('auto-progress');
    if (!progressDiv) return;
    
    progressDiv.classList.remove('hidden');
    const stepsDiv = document.getElementById('progress-steps');
    if (!stepsDiv) return;
    
    const stepId = `step-${step}`;
    let stepElement = document.getElementById(stepId);
    
    if (!stepElement) {
        stepElement = document.createElement('div');
        stepElement.id = stepId;
        stepElement.className = 'progress-step';
        stepElement.style.cssText = 'padding: 10px; margin: 5px 0; border-radius: 5px; background: #f0f0f0; border-left: 4px solid #667eea;';
        stepsDiv.appendChild(stepElement);
    }
    
    const icon = error ? '❌' : completed ? '✅' : inProgress ? '⏳' : '⏸️';
    stepElement.innerHTML = `<strong>${icon} ${step.toUpperCase()}:</strong> ${message}`;
    stepElement.style.background = error ? '#ffebee' : completed ? '#e8f5e9' : inProgress ? '#fff3e0' : '#f0f0f0';
    stepElement.style.borderLeftColor = error ? '#c62828' : completed ? '#4caf50' : inProgress ? '#ff9800' : '#667eea';
}

function displayDatasetInfo(info) {
    const section = document.getElementById('dataset-info-section');
    const content = document.getElementById('dataset-info-content');
    
    content.innerHTML = `
        <div class="file-info">
            <h3>📄 ${info.filename}</h3>
            <div class="metric-card">
                <div class="metric-label">Rows</div>
                <div class="metric-value">${info.rows.toLocaleString()}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Columns</div>
                <div class="metric-value">${info.columns}</div>
            </div>
            <div class="metric-card">
                <div class="metric-label">Column Names</div>
                <div style="margin-top: 10px;">
                    ${info.column_names.map(col => `<span class="domain-badge">${col}</span>`).join('')}
                </div>
            </div>
            <h4 style="margin-top: 20px;">Sample Data:</h4>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            ${Object.keys(info.sample_data[0] || {}).map(col => `<th>${col}</th>`).join('')}
                        </tr>
                    </thead>
                    <tbody>
                        ${info.sample_data.map(row => `
                            <tr>
                                ${Object.values(row).map(val => `<td>${val}</td>`).join('')}
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            </div>
        </div>
    `;
    
    showSection('domain-section');
}

async function detectDomain() {
    if (!currentDatasetId) {
        showError('Please upload a dataset first');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/detect-domain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayDomainResults(data);
            showSection('preprocess-section');
            populateDomainSelect(data.detected_domains);
        } else {
            showError('Domain detection failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error detecting domain: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayDomainResults(data) {
    const resultsDiv = document.getElementById('domain-results');
    resultsDiv.classList.remove('hidden');
    
    resultsDiv.innerHTML = `
        <h3>Detected Domains:</h3>
        ${data.detected_domains.map(domain => `
            <div class="insight-item">
                <strong>${domain.domain}</strong>
                <span class="confidence-badge confidence-${domain.confidence > 0.7 ? 'high' : domain.confidence > 0.4 ? 'medium' : 'low'}">
                    Confidence: ${(domain.confidence * 100).toFixed(1)}%
                </span>
                <p style="margin-top: 10px;">Matched Columns: ${domain.matched_columns.join(', ') || 'None'}</p>
            </div>
        `).join('')}
    `;
}

function populateDomainSelect(domains) {
    const select = document.getElementById('domain-select');
    select.innerHTML = '<option value="">Select a domain...</option>';
    domains.forEach(domain => {
        const option = document.createElement('option');
        option.value = domain.domain;
        option.textContent = `${domain.domain} (${(domain.confidence * 100).toFixed(1)}%)`;
        select.appendChild(option);
    });
}

async function preprocessData() {
    if (!currentDatasetId) {
        showError('Please upload a dataset first');
        return;
    }
    
    const domain = document.getElementById('domain-select').value;
    if (!domain) {
        showError('Please select a domain');
        return;
    }
    
    currentDomain = domain;
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/preprocess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId, domain: domain })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayPreprocessResults(data);
            showSection('train-section');
            await populateTargetColumn(domain);
        } else {
            showError('Preprocessing failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error preprocessing: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayPreprocessResults(data) {
    const resultsDiv = document.getElementById('preprocess-results');
    resultsDiv.classList.remove('hidden');
    
    resultsDiv.innerHTML = `
        <div class="success-message">
            <h3>✅ Preprocessing Complete</h3>
            <p>Final shape: ${data.preprocessed_shape[0]} rows × ${data.preprocessed_shape[1]} columns</p>
            <h4 style="margin-top: 15px;">Operations Performed:</h4>
            <ul style="margin-top: 10px; padding-left: 20px;">
                ${data.preprocessing_info.operations.map(op => `<li>${op.operation}</li>`).join('')}
            </ul>
        </div>
    `;
}

async function populateTargetColumn(domain) {
    if (!currentDatasetId) return;
    
    try {
        const response = await fetch(
            `${API_BASE_URL}/dataset/${currentDatasetId}/columns?domain=${domain || ''}`
        );
        const data = await response.json();
        
        const select = document.getElementById('target-column');
        select.innerHTML = '<option value="">Select target column...</option>';
        
        if (data.columns) {
            data.columns.forEach(col => {
                const option = document.createElement('option');
                option.value = col;
                option.textContent = col;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error fetching columns:', error);
    }
}

async function trainModel() {
    if (!currentDatasetId || !currentDomain) {
        showError('Please complete previous steps first');
        return;
    }
    
    const targetColumn = document.getElementById('target-column').value;
    if (!targetColumn) {
        showError('Please select a target column');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/train-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain,
                target_column: targetColumn
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayTrainResults(data);
            showSection('explain-section');
        } else {
            showError('Model training failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error training model: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayTrainResults(data) {
    const resultsDiv = document.getElementById('train-results');
    resultsDiv.classList.remove('hidden');
    
    const metrics = Object.entries(data.metrics).map(([key, value]) => `
        <div class="metric-card">
            <div class="metric-label">${key.toUpperCase()}</div>
            <div class="metric-value">${typeof value === 'number' ? value.toFixed(4) : value}</div>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = `
        <div class="success-message">
            <h3>✅ Model Trained Successfully</h3>
            <p><strong>Model Type:</strong> ${data.model_type}</p>
            <p><strong>Target Column:</strong> ${data.target_column}</p>
            <h4 style="margin-top: 15px;">Performance Metrics:</h4>
            <div style="margin-top: 10px;">
                ${metrics}
            </div>
        </div>
    `;
}

async function explainModel() {
    if (!currentDatasetId || !currentDomain) {
        showError('Please complete previous steps first');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/explain-model`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain,
                sample_size: 100
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayExplainResults(data);
            showSection('rules-section');
        } else {
            showError('Explanation failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error explaining model: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayExplainResults(data) {
    const resultsDiv = document.getElementById('explain-results');
    resultsDiv.classList.remove('hidden');
    
    const topFeatures = Object.entries(data.feature_importance)
        .slice(0, 10)
        .map(([feature, importance]) => `
            <div class="insight-item">
                <strong>${feature}</strong>
                <span class="confidence-badge confidence-high">${(importance * 100).toFixed(2)}%</span>
            </div>
        `).join('');
    
    const insights = data.human_readable_insights.map(insight => `
        <div class="insight-item">
            <p>${insight}</p>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = `
        <h3>Feature Importance (Top 10)</h3>
        ${topFeatures}
        <h3 style="margin-top: 20px;">Human-Readable Insights</h3>
        ${insights}
    `;
}

async function extractRules() {
    if (!currentDatasetId || !currentDomain) {
        showError('Please complete previous steps first');
        return;
    }
    
    const minSupport = parseFloat(document.getElementById('min-support').value);
    const minConfidence = parseFloat(document.getElementById('min-confidence').value);
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/extract-rules`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain,
                min_support: minSupport,
                min_confidence: minConfidence
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayRulesResults(data);
            showSection('report-section');
        } else {
            showError('Rule extraction failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error extracting rules: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayRulesResults(data) {
    const resultsDiv = document.getElementById('rules-results');
    resultsDiv.classList.remove('hidden');
    
    const associationRules = (data.association_rules || []).slice(0, 10).map(rule => {
        if (rule.error) return `<div class="error-message">${rule.error}</div>`;
        return `
            <div class="rule-item">
                <strong>${rule.rule}</strong>
                <div style="margin-top: 8px;">
                    <span class="confidence-badge confidence-high">Support: ${(rule.support * 100).toFixed(1)}%</span>
                    <span class="confidence-badge confidence-medium">Confidence: ${(rule.confidence * 100).toFixed(1)}%</span>
                    <span class="confidence-badge confidence-low">Lift: ${rule.lift.toFixed(2)}</span>
                </div>
            </div>
        `;
    }).join('');
    
    const ifThenRules = (data.if_then_rules || []).slice(0, 10).map(rule => `
        <div class="rule-item">
            <strong>${rule.rule}</strong>
            <div style="margin-top: 8px;">
                <span class="confidence-badge confidence-${rule.impact}">${rule.impact.toUpperCase()} Impact</span>
                <span class="confidence-badge confidence-medium">Confidence: ${(rule.confidence * 100).toFixed(1)}%</span>
            </div>
        </div>
    `).join('');
    
    resultsDiv.innerHTML = `
        <h3>Association Rules (Apriori Algorithm)</h3>
        ${associationRules || '<p>No association rules found. Try lowering min_support or min_confidence.</p>'}
        <h3 style="margin-top: 30px;">If-Then Business Rules</h3>
        ${ifThenRules || '<p>No if-then rules extracted.</p>'}
    `;
}

async function generateReport() {
    if (!currentDatasetId || !currentDomain) {
        showError('Please complete previous steps first');
        return;
    }
    
    showLoading();
    
    try {
        const response = await fetch(`${API_BASE_URL}/generate-report`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                dataset_id: currentDatasetId,
                domain: currentDomain
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            displayReport(data);
        } else {
            showError('Report generation failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (error) {
        showError('Error generating report: ' + error.message);
    } finally {
        hideLoading();
    }
}

function displayReport(data) {
    const resultsDiv = document.getElementById('report-results');
    resultsDiv.classList.remove('hidden');
    
    const sections = data.sections || {};
    
    let html = '<div class="success-message"><h2>📊 Comprehensive Report</h2>';
    
    // Model Performance
    if (sections.model_performance) {
        const mp = sections.model_performance;
        html += `
            <h3 style="margin-top: 20px;">Model Performance</h3>
            <p><strong>Model Type:</strong> ${mp.model_type}</p>
            <p><strong>Target:</strong> ${mp.target_column}</p>
            <div style="margin-top: 10px;">
                ${Object.entries(mp.metrics).map(([key, value]) => `
                    <div class="metric-card">
                        <div class="metric-label">${key.toUpperCase()}</div>
                        <div class="metric-value">${typeof value === 'number' ? value.toFixed(4) : value}</div>
                    </div>
                `).join('')}
            </div>
        `;
    }
    
    // Recommendations
    if (sections.recommendations) {
        html += `
            <h3 style="margin-top: 20px;">Recommendations</h3>
            <ul style="margin-top: 10px; padding-left: 20px;">
                ${sections.recommendations.map(rec => `<li>${rec}</li>`).join('')}
            </ul>
        `;
    }
    
    // Visualization Suggestions
    if (sections.visualization_suggestions) {
        html += `
            <h3 style="margin-top: 20px;">Visualization Suggestions</h3>
            <div style="margin-top: 10px;">
                ${sections.visualization_suggestions.map(viz => `<span class="domain-badge">${viz}</span>`).join('')}
            </div>
        `;
    }
    
    html += '</div>';
    
    resultsDiv.innerHTML = html;
}

function showSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.classList.remove('hidden');
    }
}

function showError(message) {
    alert('Error: ' + message);
}

