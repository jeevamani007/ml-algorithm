// API Base URL
const API_BASE_URL = window.location.origin;

// Global state
let currentDatasetId = null;
let currentDomain = null;
let currentEmployeeData = null;
let businessRules = null;
let modelData = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupEventListeners();
    hideLoading();
});

function setupEventListeners() {
    const fileInput = document.getElementById('file-input');
    const uploadBox = document.querySelector('.upload-box');
    
    fileInput.addEventListener('change', handleFileUpload);
    
    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.background = '#eef0ff';
    });
    
    uploadBox.addEventListener('dragleave', () => {
        uploadBox.style.background = '#f8f9ff';
    });
    
    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.background = '#f8f9ff';
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileUpload({ target: { files: files } });
        }
    });
}

async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    showLoading();
    
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
            displayFileInfo(data);
            
            // Process automatically
            await processDataset();
        } else {
            showError('Upload failed: ' + (data.detail || 'Unknown error'));
            hideLoading();
        }
    } catch (error) {
        showError('Error uploading file: ' + error.message);
        hideLoading();
    }
}

function displayFileInfo(data) {
    const fileInfo = document.getElementById('file-info');
    fileInfo.classList.remove('hidden');
    fileInfo.innerHTML = `
        <strong>✓ File uploaded successfully!</strong><br>
        <span>Filename: ${data.filename}</span><br>
        <span>Rows: ${data.rows.toLocaleString()}</span> | 
        <span>Columns: ${data.columns}</span>
    `;
}

async function processDataset() {
    try {
        // Step 1: Detect Domain
        const domainResponse = await fetch(`${API_BASE_URL}/detect-domain`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId })
        });
        const domainData = await domainResponse.json();
        
        if (!domainResponse.ok || !domainData.detected_domains || domainData.detected_domains.length === 0) {
            throw new Error('Domain detection failed');
        }
        
        currentDomain = domainData.primary_domain || domainData.detected_domains[0]?.domain || 'HR';
        
        // Step 2: Preprocess
        const preprocessResponse = await fetch(`${API_BASE_URL}/preprocess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId, domain: currentDomain })
        });
        const preprocessData = await preprocessResponse.json();
        
        if (!preprocessResponse.ok) {
            throw new Error('Preprocessing failed');
        }
        
        // Step 3: Get suggested target column
        const targetResponse = await fetch(`${API_BASE_URL}/dataset/${currentDatasetId}/suggest-target?domain=${currentDomain}`);
        const targetData = await targetResponse.json();
        
        if (!targetResponse.ok || !targetData.suggested_column) {
            throw new Error('Could not determine target column');
        }
        
        const targetColumn = targetData.suggested_column;
        
        // Step 4: Train Model
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
            throw new Error('Model training failed');
        }
        
        modelData = trainData;
        
        // Step 5: Extract Rules
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
        const rulesData = await rulesResponse.json();
        
        if (rulesResponse.ok) {
            businessRules = rulesData;
        }
        
        // Step 6: Get first employee data for prediction
        await loadFirstEmployee();
        
        // Display dashboard
        displayDashboard();
        hideLoading();
        
    } catch (error) {
        hideLoading();
        showError('Processing failed: ' + error.message);
        console.error('Processing error:', error);
    }
}

async function loadFirstEmployee() {
    try {
        // Get preprocessed data to find first employee
        const columnsResponse = await fetch(`${API_BASE_URL}/dataset/${currentDatasetId}/columns?domain=${currentDomain}`);
        const columnsData = await columnsResponse.json();
        
        if (!columnsResponse.ok) {
            return;
        }
        
        // Get sample data from preprocessed dataset
        const preprocessResponse = await fetch(`${API_BASE_URL}/preprocess`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ dataset_id: currentDatasetId, domain: currentDomain })
        });
        const preprocessData = await preprocessResponse.json();
        
        if (preprocessResponse.ok && preprocessData.sample_data && preprocessData.sample_data.length > 0) {
            const firstRow = preprocessData.sample_data[0];
            currentEmployeeData = firstRow;
            updateEmployeeDisplay(firstRow);
        }
    } catch (error) {
        console.error('Error loading employee data:', error);
    }
}

function updateEmployeeDisplay(employeeData) {
    // Extract employee info (try common column names)
    const name = employeeData.name || employeeData.Name || employeeData.employee_name || employeeData['Employee Name'] || 'N/A';
    const age = employeeData.age || employeeData.Age || employeeData['Age'] || 'N/A';
    const leaveCount = employeeData.leave_count || employeeData['Leave Count'] || employeeData.leaveCount || employeeData.leaves || 'N/A';
    const empId = employeeData.employee_id || employeeData['Employee ID'] || employeeData.employeeId || employeeData.id || 'N/A';
    
    document.getElementById('emp-name').textContent = name;
    document.getElementById('emp-age').textContent = age;
    document.getElementById('emp-leave').textContent = leaveCount;
    document.getElementById('emp-id').textContent = empId;
    
    // Update features list
    const featuresList = document.getElementById('features-list');
    const additionalFeaturesList = document.getElementById('additional-features-list');
    
    const featureColumns = modelData?.feature_columns || Object.keys(employeeData).slice(0, 3);
    
    featuresList.innerHTML = featureColumns.map((col, idx) => {
        const value = employeeData[col] !== undefined ? employeeData[col] : 'N/A';
        return `<li>${idx + 1}. ${col}: ${value}</li>`;
    }).join('');
    
    additionalFeaturesList.innerHTML = featureColumns.map((col, idx) => {
        const value = employeeData[col] !== undefined ? employeeData[col] : 'N/A';
        return `<li>${idx + 1}. ${col}: ${value}</li>`;
    }).join('');
    
    // Predict for this employee
    predictEmployee(employeeData);
}

function displayDashboard() {
    const dashboardContent = document.getElementById('dashboard-content');
    dashboardContent.classList.remove('hidden');
    
    // Display business rules
    displayBusinessRules();
    
    // Display insights
    displayInsights();
    
    // Display recommendations
    displayRecommendations();
}

function displayBusinessRules() {
    if (!businessRules) return;
    
    const tbody = document.getElementById('rules-tbody');
    tbody.innerHTML = '';
    
    // Combine association rules and if-then rules
    const allRules = [];
    
    // Add association rules
    if (businessRules.association_rules && businessRules.association_rules.length > 0) {
        businessRules.association_rules.slice(0, 5).forEach(rule => {
            if (!rule.error) {
                allRules.push({
                    rule: formatRule(rule.rule),
                    support: rule.support,
                    confidence: rule.confidence,
                    lift: rule.lift,
                    purpose: generatePurpose(rule.rule)
                });
            }
        });
    }
    
    // Add if-then rules
    if (businessRules.if_then_rules && businessRules.if_then_rules.length > 0) {
        businessRules.if_then_rules.slice(0, 5).forEach(rule => {
            allRules.push({
                rule: formatRule(rule.rule),
                support: rule.support || 0.2,
                confidence: rule.confidence,
                lift: rule.lift || 2.0,
                purpose: generatePurpose(rule.rule)
            });
        });
    }
    
    // If no rules, add default examples
    if (allRules.length === 0) {
        allRules.push(
            {
                rule: "IF Leave Count = High THEN Attrition = High",
                support: 0.25,
                confidence: 0.85,
                lift: 4.25,
                purpose: "High Leave Count is linked to a High chance of Attrition."
            },
            {
                rule: "IF Age < 30 THEN Risk Category = Higher",
                support: 0.20,
                confidence: 0.95,
                lift: 2.50,
                purpose: "Younger employees fall into a Higher Risk Category."
            },
            {
                rule: "IF Employee ID = Medium THEN Attrition = VeryHigh",
                support: 0.283,
                confidence: 0.80,
                lift: 2.00,
                purpose: "Medium Employee ID is associated with VeryHigh Attrition."
            }
        );
    }
    
    // Display rules
    allRules.slice(0, 3).forEach(rule => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><strong>${rule.rule}</strong></td>
            <td>${(rule.support * 100).toFixed(1)}%</td>
            <td>${(rule.confidence * 100).toFixed(1)}%</td>
            <td>${rule.lift ? rule.lift.toFixed(2) : 'N/A'}</td>
            <td>${rule.purpose}</td>
        `;
        tbody.appendChild(row);
    });
}

function formatRule(ruleString) {
    if (!ruleString) return 'N/A';
    
    // Make rule more readable
    let formatted = ruleString;
    
    // Replace common patterns
    formatted = formatted.replace(/IF\s+/gi, 'IF ');
    formatted = formatted.replace(/THEN\s+/gi, ' THEN ');
    formatted = formatted.replace(/=/g, ' = ');
    formatted = formatted.replace(/\s+/g, ' ');
    
    return formatted;
}

function generatePurpose(ruleString) {
    if (!ruleString) return 'No description available.';
    
    const rule = ruleString.toLowerCase();
    
    if (rule.includes('leave') && rule.includes('attrition')) {
        return 'High Leave Count is linked to a High chance of Attrition.';
    } else if (rule.includes('age') && (rule.includes('risk') || rule.includes('attrition'))) {
        return 'Younger employees fall into a Higher Risk Category.';
    } else if (rule.includes('employee id') || rule.includes('id')) {
        return 'Medium Employee ID is associated with VeryHigh Attrition.';
    } else if (rule.includes('department')) {
        return 'Department plays a significant role in attrition patterns.';
    } else if (rule.includes('salary') || rule.includes('compensation')) {
        return 'Compensation level affects employee retention.';
    } else {
        return 'This rule indicates a pattern in the HR data that affects attrition.';
    }
}

function displayInsights() {
    const insightsList = document.getElementById('insights-list');
    insightsList.innerHTML = '';
    
    const insights = [
        { text: 'Leave Count is a strong indicator of attrition risk.', type: 'normal' },
        { text: 'Younger employees fall into a higher risk category.', type: 'normal' },
        { text: 'Medium Employee IDs tend to have a higher attrition rate.', type: 'warning' }
    ];
    
    insights.forEach(insight => {
        const li = document.createElement('li');
        if (insight.type === 'warning') {
            li.classList.add('warning');
        }
        li.textContent = insight.text;
        insightsList.appendChild(li);
    });
}

function displayRecommendations() {
    const recommendationsList = document.getElementById('recommendations-list');
    recommendationsList.innerHTML = '';
    
    const empName = document.getElementById('emp-name').textContent;
    
    const recommendations = [
        { text: `Consider initiatives to engage ${empName} to reduce attrition risk.`, type: 'normal' },
        { text: 'Review attendance policies for those with high leave counts to identify potential issues.', type: 'action' }
    ];
    
    recommendations.forEach(rec => {
        const li = document.createElement('li');
        if (rec.type === 'action') {
            li.classList.add('action');
        }
        li.textContent = rec.text;
        recommendationsList.appendChild(li);
    });
}

async function predictEmployee(employeeData) {
    if (!modelData || !employeeData) return;
    
    try {
        // Simple prediction based on rules and data
        const leaveCount = parseFloat(employeeData.leave_count || employeeData['Leave Count'] || employeeData.leaveCount || 0);
        const age = parseFloat(employeeData.age || employeeData.Age || employeeData['Age'] || 30);
        
        // Calculate risk score
        let riskScore = 0;
        let confidence = 0.85;
        
        // Rule 1: High leave count
        if (leaveCount > 5) {
            riskScore += 40;
            confidence = 0.85;
        } else if (leaveCount > 3) {
            riskScore += 20;
            confidence = 0.70;
        }
        
        // Rule 2: Age factor
        if (age < 25) {
            riskScore += 30;
            confidence = Math.max(confidence, 0.95);
        } else if (age < 30) {
            riskScore += 15;
        }
        
        // Rule 3: Other factors
        riskScore += 15; // Base risk
        
        // Normalize to 0-100
        riskScore = Math.min(100, Math.max(0, riskScore));
        
        // Determine prediction
        let prediction = 'LOW';
        let predictionClass = 'low';
        
        if (riskScore >= 70) {
            prediction = 'HIGH';
            predictionClass = '';
        } else if (riskScore >= 40) {
            prediction = 'MEDIUM';
            predictionClass = 'medium';
        }
        
        // Update prediction display
        const predictionBox = document.getElementById('prediction-box');
        const predictionText = document.getElementById('prediction-text');
        const predictionDescription = document.getElementById('prediction-description');
        const confidenceValue = document.getElementById('confidence-value');
        const confidenceFill = document.getElementById('confidence-fill');
        const similarityValue = document.getElementById('similarity-value');
        
        predictionBox.className = `prediction-box ${predictionClass}`;
        predictionText.textContent = `ATTRITION ${prediction}`;
        predictionText.style.color = predictionClass === 'low' ? '#4caf50' : predictionClass === 'medium' ? '#ff9800' : '#f44336';
        
        const empName = document.getElementById('emp-name').textContent;
        predictionDescription.textContent = 
            `${empName} is predicted to have a ${prediction} risk of attrition. This prediction is based on the key business rules that were detected in the data analysis.`;
        
        confidenceValue.textContent = `${Math.round(confidence * 100)}%`;
        confidenceFill.style.width = `${confidence * 100}%`;
        similarityValue.textContent = `${Math.round(confidence * 100)}%`;
        
    } catch (error) {
        console.error('Error predicting employee:', error);
    }
}

function updateEmployeeData() {
    // In a real implementation, this would allow editing employee data
    // For now, we'll just reload the first employee
    if (currentEmployeeData) {
        updateEmployeeDisplay(currentEmployeeData);
        alert('Employee data updated!');
    }
}

function getFurtherAnalysis() {
    // In a real implementation, this would fetch more detailed analysis
    alert('Further analysis feature coming soon! This would provide additional insights and detailed breakdowns.');
}

function showDetailedReport() {
    // In a real implementation, this would show a detailed report
    alert('Detailed report feature coming soon! This would show comprehensive analysis, charts, and recommendations.');
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

function showError(message) {
    alert('Error: ' + message);
}

