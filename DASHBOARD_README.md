# Business Rules & Predict Outcomes Dashboard

## Overview

This dashboard provides a user-friendly interface for analyzing HR data, detecting business rules, and predicting employee attrition outcomes. The dashboard matches the design shown in the reference image and provides:

- **Data Upload**: Upload HR datasets (CSV, XLS, XLSX)
- **Business Rules Display**: Shows key business rules in a readable format with Support, Confidence, Lift, and Purpose
- **Employee Predictions**: Predicts attrition risk for individual employees
- **Insights & Recommendations**: Provides actionable insights and recommendations

## Features

### 1. Data Upload
- Drag and drop or click to upload HR data files
- Supports CSV, XLS, and XLSX formats
- Automatic processing of uploaded data

### 2. Input Data Summary
- Displays employee information (Name, Age, Leave Count, Employee ID)
- Shows features used for prediction
- Indicates use of 3 months of HR data

### 3. Key Business Rules Table
- **Rule**: Human-readable if-then business rules
- **Support**: Percentage of data supporting the rule
- **Confidence**: Probability that the rule is correct
- **Lift**: Strength of the association
- **Purpose**: Plain English explanation of what the rule means

### 4. Insights Section
- Highlights key findings from the data analysis
- Visual indicators (checkmarks and warnings) for different insight types

### 5. Predicted Outcome
- **Similarity Score**: Confidence in the prediction
- **Attrition Risk**: HIGH, MEDIUM, or LOW
- **Confidence Bar**: Visual representation of prediction confidence
- **Description**: Explanation of the prediction

### 6. Recommendations
- Actionable recommendations based on the analysis
- Specific suggestions for reducing attrition risk

## How to Use

### Starting the Dashboard

1. **Start the Backend Server**:
   ```bash
   cd ml-algorithm/backend
   python main.py
   ```
   Or use the provided scripts:
   ```bash
   # Windows
   start_backend.bat
   
   # Linux/Mac
   ./start_backend.sh
   ```

2. **Access the Dashboard**:
   - Open your browser and navigate to: `http://localhost:8000/dashboard`
   - The main application is available at: `http://localhost:8000`

### Using the Dashboard

1. **Upload Data**:
   - Click the upload area or drag and drop your HR data file
   - Supported formats: CSV, XLS, XLSX
   - The system will automatically process the data

2. **View Results**:
   - After upload, the dashboard will automatically:
     - Detect the domain (HR, Finance, Sales, etc.)
     - Preprocess the data
     - Train a prediction model
     - Extract business rules
     - Display predictions for the first employee

3. **Update Employee Data**:
   - Click "Update Data" to refresh the employee information
   - The prediction will update based on the current data

4. **Get Further Analysis**:
   - Click "Get Further Analysis" for additional insights
   - Click "See Detailed Report" for comprehensive analysis

## Business Rules Format

The dashboard displays business rules in a user-friendly format:

**Example Rules:**
- `IF Leave Count = High THEN Attrition = High`
- `IF Age < 30 THEN Risk Category = Higher`
- `IF Employee ID = Medium THEN Attrition = VeryHigh`

Each rule includes:
- **Support**: How often this pattern appears in the data (e.g., 25.0%)
- **Confidence**: How reliable the rule is (e.g., 85.0%)
- **Lift**: How much stronger the association is compared to random (e.g., 4.25)
- **Purpose**: Plain English explanation (e.g., "High Leave Count is linked to a High chance of Attrition.")

## Data Requirements

For best results, your HR dataset should include:
- Employee ID or identifier
- Age or tenure information
- Leave count or attendance data
- Target column (e.g., attrition, turnover, resignation)

The system will automatically:
- Detect relevant columns
- Handle missing values
- Encode categorical variables
- Normalize numeric data

## Technical Details

### Frontend Files
- `dashboard.html`: Main dashboard page
- `dashboard.css`: Dashboard styling
- `dashboard.js`: Dashboard logic and API integration

### Backend Endpoints
- `GET /dashboard`: Serves the dashboard page
- `POST /upload`: Upload dataset
- `POST /detect-domain`: Detect data domain
- `POST /preprocess`: Preprocess data
- `POST /train-model`: Train prediction model
- `POST /extract-rules`: Extract business rules
- `POST /generate-report`: Generate comprehensive report

### Business Rules Formatting

The system automatically formats business rules to be:
- **Readable**: Uses plain English instead of technical jargon
- **Understandable**: Includes purpose explanations
- **Actionable**: Provides clear if-then statements

## Troubleshooting

### Dashboard Not Loading
- Ensure the backend server is running on port 8000
- Check browser console for errors
- Verify all frontend files are in the `frontend/` directory

### No Rules Displayed
- Ensure your dataset has sufficient data (at least 10 rows recommended)
- Check that the target column is correctly identified
- Try lowering min_support and min_confidence thresholds

### Predictions Not Showing
- Verify the dataset includes employee information columns
- Check that the first row has valid data
- Ensure the model training completed successfully

## Future Enhancements

- Individual employee selection from a dropdown
- Real-time prediction updates
- Export functionality for reports
- Interactive charts and visualizations
- Multi-employee batch predictions

