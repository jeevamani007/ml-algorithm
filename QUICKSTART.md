# Quick Start Guide

## Installation (5 minutes)

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

**Note**: If you encounter issues with Prophet, you may need to install it separately:
```bash
pip install prophet
```

For Windows users, if Prophet installation fails, you may need:
- Microsoft C++ Build Tools
- Or use conda: `conda install -c conda-forge prophet`

### Step 2: Start the Backend

**Windows:**
```bash
start_backend.bat
```

**Linux/Mac:**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Or manually:**
```bash
cd backend
python main.py
```

The API will start at `http://localhost:8000`

### Step 3: Open the Frontend

**Option 1: Direct File**
- Simply open `frontend/index.html` in your web browser

**Option 2: Local Server (Recommended)**
```bash
# Python
cd frontend
python -m http.server 8080

# Node.js
npx http-server frontend -p 8080
```

Then navigate to `http://localhost:8080`

## Testing the Application

### 1. Prepare a Sample Dataset

Create a CSV file with your data. Example for HR domain:

```csv
employee_id,age,department,salary,tenure,attrition
1,25,IT,50000,2,0
2,30,Sales,60000,5,0
3,45,HR,70000,10,1
...
```

### 2. Use the Web Interface

1. Upload your CSV file
2. Click "Detect Domain(s)"
3. Select a domain from the dropdown
4. Click "Preprocess Data"
5. Select a target column (e.g., "attrition")
6. Click "Train Model"
7. Click "Generate Explanations"
8. Click "Extract Rules"
9. Click "Generate Report"

### 3. Test API Directly (Optional)

You can also test the API using curl or Postman:

```bash
# Upload a file
curl -X POST "http://localhost:8000/upload" \
  -F "file=@your_dataset.csv"

# Detect domain
curl -X POST "http://localhost:8000/detect-domain" \
  -H "Content-Type: application/json" \
  -d '{"dataset_id": "dataset_20240101_120000"}'
```

## Troubleshooting

### Backend won't start
- Check if Python 3.8+ is installed: `python --version`
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Check if port 8000 is available

### Frontend can't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check browser console for CORS errors
- Verify API_BASE_URL in `frontend/app.js` matches your backend URL

### Model training fails
- Ensure you have at least 50 rows of data
- Check that target column exists in dataset
- Verify data types are appropriate

### Prophet installation issues
- Windows: Install Microsoft C++ Build Tools
- Alternative: Use conda environment
- Or skip Prophet and use Random Forest for time series

## Example Datasets

### HR Dataset
Should include columns like:
- employee_id, age, department, salary, tenure, performance_rating, attrition

### Sales Dataset
Should include columns like:
- date, product_id, quantity, price, revenue, customer_id

### Finance Dataset
Should include columns like:
- date, category, amount, budget, actual, variance

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the API documentation at `http://localhost:8000/docs` (Swagger UI)
- Customize models and preprocessing in the backend modules
- Add your own domain detection keywords in `domain_detector.py`

