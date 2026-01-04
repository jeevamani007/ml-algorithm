# How to Run the Application

## Quick Start (Recommended)

### Option 1: Use the Startup Script (Easiest)

**Windows:**
```bash
start_full_app.bat
```

**Linux/Mac:**
```bash
chmod +x start_full_app.sh
./start_full_app.sh
```

Then open your browser and go to: **http://localhost:8000**

### Option 2: Manual Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the server:**
   ```bash
   python start_full_app.py
   ```

3. **Open in browser:**
   - Go to: **http://localhost:8000**
   - The frontend will be served automatically

## What You Should See

When you open **http://localhost:8000**, you should see:
- A beautiful purple gradient background
- Header: "🤖 AI Business Rule Discovery & Prediction Engine"
- Step 1: Upload Dataset section with a file upload box

**If you see JSON like `{"message":"..."}`, you're accessing the wrong endpoint!**

## Troubleshooting

### Still seeing JSON instead of HTML?

1. **Check if the server is running:**
   - Look for "Starting server..." message
   - Check terminal for any errors

2. **Verify frontend files exist:**
   - Check that `frontend/index.html` exists
   - Check that `frontend/styles.css` exists
   - Check that `frontend/app.js` exists

3. **Try accessing directly:**
   - Open `frontend/index.html` in your browser
   - But note: API calls won't work this way due to CORS

4. **Check the server logs:**
   - Look for any error messages about missing files
   - Check if port 8000 is already in use

### Port Already in Use?

If port 8000 is busy, you can change it:

1. Edit `start_full_app.py`
2. Change `port=8000` to another port (e.g., `port=8001`)
3. Update `frontend/app.js` to use the new port

### API Documentation

Once the server is running, you can also access:
- **API Docs (Swagger):** http://localhost:8000/docs
- **API Info:** http://localhost:8000/api

## Expected Behavior

1. **Homepage (http://localhost:8000):**
   - Shows the full frontend UI
   - File upload interface
   - All workflow steps

2. **API Endpoint (http://localhost:8000/api):**
   - Returns JSON: `{"message": "AI Business Rule Discovery & Prediction Engine API"}`

3. **API Docs (http://localhost:8000/docs):**
   - Interactive API documentation
   - Test endpoints directly

## File Structure Check

Make sure your project structure looks like this:

```
model-predictions/
├── backend/
│   ├── main.py
│   ├── domain_detector.py
│   ├── data_preprocessor.py
│   ├── model_trainer.py
│   ├── explainability.py
│   ├── business_rules.py
│   └── report_generator.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── start_full_app.py
├── requirements.txt
└── README.md
```

If any files are missing, the frontend won't load properly!

