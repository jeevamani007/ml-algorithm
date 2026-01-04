# AI Business Rule Discovery & Prediction Engine

An intelligent system that automatically detects domains, trains prediction models, and extracts business rules from datasets.

## Features

- **Domain Detection**: Automatically identifies HR, Finance, Sales, or Operations domains
- **Data Preprocessing**: Handles missing values, categorical encoding, and normalization
- **Model Training**: Trains appropriate models based on domain:
  - HR: Random Forest (attrition, leave prediction)
  - Finance: XGBoost (budget, expense forecasting)
  - Sales: Random Forest Regressor / Prophet (demand forecasting)
- **Model Explainability**: Uses SHAP and LIME to explain predictions
- **Business Rules Extraction**: Generates if-then rules and association rules using Apriori algorithm
- **Comprehensive Reports**: Generates detailed reports with insights and recommendations

## Project Structure

```
model-predictions/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── domain_detector.py      # Domain detection logic
│   ├── data_preprocessor.py    # Data cleaning and preprocessing
│   ├── model_trainer.py        # Model training
│   ├── explainability.py       # SHAP/LIME explanations
│   ├── business_rules.py       # Apriori and rule extraction
│   └── report_generator.py     # Report generation
├── frontend/
│   ├── index.html              # Main UI
│   ├── styles.css              # Styling
│   └── app.js                  # Frontend logic
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Start the Backend Server

```bash
cd backend
python main.py
```

Or using uvicorn directly:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

### 3. Open the Frontend

Simply open `frontend/index.html` in your web browser, or serve it using a local server:

```bash
# Using Python
cd frontend
python -m http.server 8080

# Using Node.js
npx http-server frontend -p 8080
```

Then navigate to `http://localhost:8080`

## Usage

### Automatic Mode (Recommended) 🤖

**Perfect for users who want everything done automatically:**

1. **Select Automatic Mode** when the app loads
2. **Upload Dataset**: Upload a CSV, XLS, or XLSX file
3. **Wait for Processing**: The system automatically:
   - Detects domain(s)
   - Preprocesses data
   - Selects best target column
   - Trains prediction model
   - Generates explanations
   - Extracts business rules
   - Creates comprehensive report
4. **View Results**: All results displayed in one comprehensive view

### Manual Mode ⚙️

**For users who want step-by-step control:**

1. **Select Manual Mode** when the app loads
2. **Upload Dataset**: Upload a CSV, XLS, or XLSX file
3. **View Dataset Info**: Review dataset structure and sample data
4. **Detect Domain**: Automatically detect the domain(s) of your dataset
5. **Preprocess Data**: Clean and preprocess data for the selected domain
6. **Train Model**: Select target column and train prediction model
7. **Explain Model**: Generate SHAP/LIME explanations and feature importance
8. **Extract Rules**: Extract business rules using Apriori algorithm
9. **Generate Report**: Get comprehensive report with all insights

### API Endpoints

- `POST /upload` - Upload dataset
- `POST /detect-domain` - Detect domain(s)
- `POST /preprocess` - Preprocess data
- `POST /train-model` - Train prediction model
- `POST /explain-model` - Generate model explanations
- `POST /extract-rules` - Extract business rules
- `POST /generate-report` - Generate comprehensive report
- `GET /datasets` - List all uploaded datasets

## Example Workflow

### For HR Dataset:
1. Upload employee dataset with columns like: employee_id, age, department, salary, attrition
2. System detects "HR" domain
3. Preprocesses data (handles missing values, encodes categories)
4. Train model to predict "attrition"
5. Get explanations showing which factors influence attrition
6. Extract rules like: "IF age < 25 AND leave_count > 10 THEN attrition risk HIGH"

### For Sales Dataset:
1. Upload sales data with: date, product, quantity, revenue
2. System detects "Sales" domain
3. Preprocesses and trains forecasting model
4. Generates demand forecasts
5. Extracts association rules between products

## Model Types by Domain

- **HR**: Random Forest Classifier/Regressor
- **Finance**: XGBoost Classifier/Regressor
- **Sales**: Random Forest Regressor or Prophet (for time series)
- **Operations/General**: Logistic Regression or Linear Regression

## Evaluation Metrics

- **Classification**: Accuracy, Precision, Recall, F1 Score
- **Regression**: RMSE, MAE, R² Score

## Business Rules

The system extracts two types of rules:

1. **Association Rules** (Apriori): Find frequent patterns and associations
   - Example: "IF product_A AND product_B THEN product_C (confidence: 75%)"

2. **If-Then Rules**: Generate rules from data patterns
   - Example: "IF employee_age < 25 THEN attrition_risk = HIGH"

## Requirements

- Python 3.8+
- Modern web browser (Chrome, Firefox, Edge)
- 4GB+ RAM recommended for large datasets

## Troubleshooting

### Backend Issues
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is available
- For Prophet issues, ensure you have a C++ compiler installed

### Frontend Issues
- Ensure backend is running on `http://localhost:8000`
- Check browser console for errors
- Enable CORS if accessing from different origin

### Model Training Issues
- Ensure target column exists in dataset
- Check for sufficient data (minimum 50 rows recommended)
- Verify data types are appropriate

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

