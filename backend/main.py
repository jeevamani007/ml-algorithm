from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import pandas as pd
import numpy as np
from typing import Optional, Dict, List, Any
import io
import json
from datetime import datetime
import os
from pathlib import Path

from domain_detector import DomainDetector
from data_preprocessor import DataPreprocessor
from model_trainer import ModelTrainer
from explainability import ExplainabilityEngine
from business_rules import BusinessRulesExtractor
from report_generator import ReportGenerator

app = FastAPI(title="AI Business Rule Discovery & Prediction Engine")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (frontend)
# Get absolute path to frontend directory
frontend_path = Path(__file__).parent.parent / "frontend"
frontend_path = frontend_path.resolve()  # Make it absolute
if frontend_path.exists():
    # Mount static files for CSS, JS, etc.
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Serve CSS and JS files
    @app.get("/styles.css")
    async def get_css():
        css_file = frontend_path / "styles.css"
        if css_file.exists():
            return FileResponse(str(css_file), media_type="text/css")
        raise HTTPException(status_code=404, detail="CSS file not found")
    
    @app.get("/app.js")
    async def get_js():
        js_file = frontend_path / "app.js"
        if js_file.exists():
            return FileResponse(str(js_file), media_type="application/javascript")
        raise HTTPException(status_code=404, detail="JS file not found")
    
    @app.get("/dashboard.css")
    async def get_dashboard_css():
        css_file = frontend_path / "dashboard.css"
        if css_file.exists():
            return FileResponse(str(css_file), media_type="text/css")
        raise HTTPException(status_code=404, detail="Dashboard CSS file not found")
    
    @app.get("/dashboard.js")
    async def get_dashboard_js():
        js_file = frontend_path / "dashboard.js"
        if js_file.exists():
            return FileResponse(str(js_file), media_type="application/javascript")
        raise HTTPException(status_code=404, detail="Dashboard JS file not found")

# Global storage for processed data
processed_data_store: Dict[str, Any] = {}

@app.get("/")
async def root():
    """Serve the frontend HTML file"""
    frontend_file = frontend_path / "index.html"
    if frontend_file.exists():
        return FileResponse(
            str(frontend_file),
            media_type="text/html"
        )
    return JSONResponse(content={
        "message": "AI Business Rule Discovery & Prediction Engine API", 
        "note": "Frontend not found. Please open frontend/index.html directly in your browser.",
        "frontend_path": str(frontend_path),
        "exists": frontend_path.exists()
    })

@app.get("/dashboard")
async def dashboard():
    """Serve the dashboard HTML file"""
    dashboard_file = frontend_path / "dashboard.html"
    if dashboard_file.exists():
        return FileResponse(
            str(dashboard_file),
            media_type="text/html"
        )
    raise HTTPException(status_code=404, detail="Dashboard not found")

@app.get("/api")
async def api_info():
    """API information endpoint"""
    return {"message": "AI Business Rule Discovery & Prediction Engine API"}

@app.post("/upload")
async def upload_dataset(file: UploadFile = File(...)):
    """Upload and parse dataset"""
    try:
        # Read file content
        contents = await file.read()
        
        # Determine file type and parse
        file_extension = file.filename.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(io.BytesIO(contents))
        elif file_extension in ['xls', 'xlsx']:
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV, XLS, or XLSX")
        
        # Store dataset
        dataset_id = f"dataset_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        processed_data_store[dataset_id] = {
            "raw_data": df,
            "filename": file.filename,
            "upload_time": datetime.now().isoformat()
        }
        
        # Basic info
        info = {
            "dataset_id": dataset_id,
            "filename": file.filename,
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "sample_data": df.head(5).to_dict(orient='records')
        }
        
        return JSONResponse(content=info)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")

@app.post("/detect-domain")
async def detect_domain(request_data: Dict[str, Any] = Body(...)):
    """Detect domain(s) of the dataset"""
    try:
        dataset_id = request_data.get("dataset_id")
        
        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required in request body")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = processed_data_store[dataset_id]["raw_data"]
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty")
        
        detector = DomainDetector()
        domains = detector.detect_domains(df)
        
        if not domains or len(domains) == 0:
            # Return a default domain if none detected
            domains = [{
                "domain": "General",
                "confidence": 0.5,
                "score": 0,
                "matched_columns": [],
                "data_types": {}
            }]
        
        processed_data_store[dataset_id]["detected_domains"] = domains
        
        return JSONResponse(content={
            "dataset_id": dataset_id,
            "detected_domains": domains,
            "primary_domain": domains[0]["domain"] if domains else "General"
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error detecting domain: {str(e)}"
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/preprocess")
async def preprocess_data(request_data: Dict[str, Any] = Body(...)):
    """Preprocess data for a specific domain"""
    try:
        dataset_id = request_data.get("dataset_id")
        domain = request_data.get("domain")
        
        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        df = processed_data_store[dataset_id]["raw_data"]
        
        if df is None or df.empty:
            raise HTTPException(status_code=400, detail="Dataset is empty")
        
        detected_domains = processed_data_store[dataset_id].get("detected_domains", [])
        
        # Use provided domain or primary detected domain
        if not domain and detected_domains:
            domain = detected_domains[0]["domain"]
        
        if not domain:
            domain = "General"  # Default domain
        
        preprocessor = DataPreprocessor()
        preprocessed_df, preprocessing_info = preprocessor.preprocess(df, domain)
        
        # Store preprocessed data
        if "preprocessed_data" not in processed_data_store[dataset_id]:
            processed_data_store[dataset_id]["preprocessed_data"] = {}
        
        processed_data_store[dataset_id]["preprocessed_data"][domain] = {
            "data": preprocessed_df,
            "info": preprocessing_info
        }
        
        # Ensure all data is JSON serializable
        # Convert any numpy types to native Python types
        def make_serializable(obj):
            """Recursively convert numpy types to native Python types"""
            if isinstance(obj, dict):
                return {k: make_serializable(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [make_serializable(item) for item in obj]
            elif isinstance(obj, (np.integer, np.int64)):
                return int(obj)
            elif isinstance(obj, (np.floating, np.float64)):
                return float(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif pd.isna(obj):
                return None
            else:
                return obj
        
        # Make preprocessing_info serializable
        serializable_info = make_serializable(preprocessing_info)
        
        # Convert sample data to ensure it's serializable
        sample_data = preprocessed_df.head(5).copy()
        # Convert any numpy types in sample data
        for col in sample_data.columns:
            if sample_data[col].dtype in ['int64', 'int32']:
                sample_data[col] = sample_data[col].astype('Int64')  # Nullable integer
            elif sample_data[col].dtype in ['float64', 'float32']:
                sample_data[col] = sample_data[col].astype('float64')
        
        sample_data_dict = sample_data.to_dict(orient='records')
        serializable_sample = make_serializable(sample_data_dict)
        
        return JSONResponse(content={
            "dataset_id": dataset_id,
            "domain": domain,
            "preprocessing_info": serializable_info,
            "preprocessed_shape": list(preprocessed_df.shape),  # Convert tuple to list
            "sample_data": serializable_sample
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error preprocessing data: {str(e)}"
        print(f"Preprocessing error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/train-model")
async def train_model(request_data: Dict[str, Any] = Body(...)):
    """Train prediction model for a domain"""
    try:
        dataset_id = request_data.get("dataset_id")
        domain = request_data.get("domain")
        target_column = request_data.get("target_column")
        
        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")
        if not domain:
            raise HTTPException(status_code=400, detail="domain is required")
        if not target_column:
            raise HTTPException(status_code=400, detail="target_column is required")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        preprocessed_data = processed_data_store[dataset_id]["preprocessed_data"].get(domain)
        if not preprocessed_data:
            raise HTTPException(status_code=404, detail="Preprocessed data not found. Run preprocessing first.")
        
        df = preprocessed_data["data"]
        
        if target_column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Target column '{target_column}' not found in preprocessed data. Available columns: {', '.join(df.columns.tolist()[:10])}")
        
        # Check if target column is an ID column (should not be used for prediction)
        id_keywords = ['id', 'identifier', 'key', 'index']
        if any(keyword in target_column.lower() for keyword in id_keywords):
            raise HTTPException(
                status_code=400, 
                detail=f"Target column '{target_column}' appears to be an identifier. Please select a different column for prediction."
            )
        
        trainer = ModelTrainer()
        model_result = trainer.train(df, domain, target_column)
        
        # Clean metrics to ensure JSON serializability
        def clean_metrics(metrics_dict):
            """Remove NaN and inf values from metrics"""
            cleaned = {}
            for key, value in metrics_dict.items():
                try:
                    # Handle numpy types first
                    if isinstance(value, (np.integer, np.int64, np.int32)):
                        cleaned[key] = int(value)
                    elif isinstance(value, (np.floating, np.float64, np.float32)):
                        val = float(value)
                        if np.isnan(val) or np.isinf(val):
                            cleaned[key] = 0.0
                        else:
                            cleaned[key] = val
                    elif isinstance(value, (int, float)):
                        val = float(value)
                        if np.isnan(val) or np.isinf(val):
                            cleaned[key] = 0.0
                        else:
                            cleaned[key] = val
                    elif pd.isna(value):
                        cleaned[key] = 0.0
                    else:
                        cleaned[key] = value
                except (ValueError, TypeError, OverflowError) as e:
                    print(f"Error cleaning metric {key}: {e}")
                    cleaned[key] = 0.0
            return cleaned
        
        cleaned_metrics = clean_metrics(model_result["metrics"])
        
        # Also clean sample predictions
        def clean_predictions(predictions_list):
            """Clean prediction values to handle NaN/inf"""
            cleaned = []
            for pred in predictions_list:
                cleaned_pred = {}
                for key, value in pred.items():
                    try:
                        if isinstance(value, (np.integer, np.int64, np.int32)):
                            cleaned_pred[key] = int(value)
                        elif isinstance(value, (np.floating, np.float64, np.float32)):
                            val = float(value)
                            if np.isnan(val) or np.isinf(val):
                                cleaned_pred[key] = 0.0 if key != 'index' else 0
                            else:
                                cleaned_pred[key] = float(val) if key != 'index' else int(val)
                        elif isinstance(value, (int, float)):
                            val = float(value) if key != 'index' else int(value)
                            if key == 'index':
                                cleaned_pred[key] = val
                            else:
                                if np.isnan(val) or np.isinf(val):
                                    cleaned_pred[key] = 0.0
                                else:
                                    cleaned_pred[key] = val
                        elif pd.isna(value):
                            cleaned_pred[key] = 0.0 if key != 'index' else 0
                        else:
                            cleaned_pred[key] = value
                    except (ValueError, TypeError, OverflowError) as e:
                        cleaned_pred[key] = 0.0 if key != 'index' else 0
                cleaned.append(cleaned_pred)
            return cleaned
        
        cleaned_predictions = clean_predictions(model_result.get("sample_predictions", []))
        
        # Store model
        if "models" not in processed_data_store[dataset_id]:
            processed_data_store[dataset_id]["models"] = {}
        
        processed_data_store[dataset_id]["models"][domain] = {
            "model": model_result["model"],
            "target_column": target_column,
            "metrics": cleaned_metrics,
            "model_type": model_result["model_type"],
            "feature_columns": model_result["feature_columns"],
            "sample_predictions": cleaned_predictions
        }
        
        return JSONResponse(content={
            "dataset_id": dataset_id,
            "domain": domain,
            "target_column": target_column,
            "model_type": model_result["model_type"],
            "metrics": cleaned_metrics,
            "feature_columns": model_result["feature_columns"],
            "sample_predictions": cleaned_predictions
        })
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error training model: {str(e)}"
        print(f"Model training error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/explain-model")
async def explain_model(request_body: Dict[str, Any] = Body(...)):
    """Generate model explainability using manual feature tracking"""
    try:
        dataset_id = request_body.get("dataset_id")
        domain = request_body.get("domain")
        sample_size = request_body.get("sample_size", 100)
        
        if not dataset_id or not domain:
            raise HTTPException(status_code=400, detail="dataset_id and domain are required")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        model_data = processed_data_store[dataset_id]["models"].get(domain)
        preprocessed_data = processed_data_store[dataset_id]["preprocessed_data"].get(domain)
        
        if not model_data or not preprocessed_data:
            raise HTTPException(status_code=404, detail="Model or preprocessed data not found")
        
        df = preprocessed_data["data"]
        model = model_data["model"]  # This is now rules (list or dict)
        target_column = model_data["target_column"]
        feature_columns = model_data["feature_columns"]
        model_type = model_data["model_type"]
        
        # Convert DataFrame to lists for pure Python processing
        X_data = []
        y_data = []
        n_samples = min(sample_size, len(df))
        
        for idx in range(n_samples):
            row_features = []
            for col in feature_columns:
                val = df.iloc[idx][col]
                try:
                    row_features.append(float(val))
                except:
                    row_features.append(0.0)
            X_data.append(row_features)
            
            target_val = df.iloc[idx][target_column]
            y_data.append(target_val)
        
        explainer = ExplainabilityEngine()
        explanation = explainer.explain(
            model, X_data, y_data, feature_columns, model_type
        )
        
        # Store explanation
        if "explanations" not in processed_data_store[dataset_id]:
            processed_data_store[dataset_id]["explanations"] = {}
        
        processed_data_store[dataset_id]["explanations"][domain] = explanation
        
        return JSONResponse(content=explanation)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error explaining model: {str(e)}"
        print(f"Explainability error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/extract-rules")
async def extract_rules(request_body: Dict[str, Any] = Body(...)):
    """Extract business rules using threshold and frequency analysis"""
    try:
        dataset_id = request_body.get("dataset_id")
        domain = request_body.get("domain")
        min_support = request_body.get("min_support", 0.1)
        min_confidence = request_body.get("min_confidence", 0.5)
        
        if not dataset_id or not domain:
            raise HTTPException(status_code=400, detail="dataset_id and domain are required")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        preprocessed_data = processed_data_store[dataset_id]["preprocessed_data"].get(domain)
        model_data = processed_data_store[dataset_id].get("models", {}).get(domain)
        
        if not preprocessed_data:
            raise HTTPException(status_code=404, detail="Preprocessed data not found. Run preprocessing first.")
        
        df = preprocessed_data["data"]
        target_column = model_data.get("target_column") if model_data else None
        
        extractor = BusinessRulesExtractor()
        rules = extractor.extract_rules(df, domain, target_column, min_support, min_confidence)
        
        # Store rules
        if "rules" not in processed_data_store[dataset_id]:
            processed_data_store[dataset_id]["rules"] = {}
        
        processed_data_store[dataset_id]["rules"][domain] = rules
        
        return JSONResponse(content=rules)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error extracting rules: {str(e)}"
        print(f"Rule extraction error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/generate-report")
async def generate_report(request_data: Dict[str, Any] = Body(...)):
    """Generate comprehensive report"""
    try:
        dataset_id = request_data.get("dataset_id")
        domain = request_data.get("domain")
        
        if not dataset_id:
            raise HTTPException(status_code=400, detail="dataset_id is required")
        if not domain:
            raise HTTPException(status_code=400, detail="domain is required")
        
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        dataset_info = processed_data_store[dataset_id]
        generator = ReportGenerator()
        
        report = generator.generate(
            dataset_id,
            dataset_info,
            domain
        )
        
        return JSONResponse(content=report)
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Error generating report: {str(e)}"
        print(f"Report generation error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.get("/datasets")
async def list_datasets():
    """List all uploaded datasets"""
    datasets = []
    for dataset_id, data in processed_data_store.items():
        datasets.append({
            "dataset_id": dataset_id,
            "filename": data.get("filename", "Unknown"),
            "upload_time": data.get("upload_time"),
            "rows": len(data["raw_data"]),
            "columns": len(data["raw_data"].columns),
            "has_domains": "detected_domains" in data,
            "has_models": "models" in data
        })
    return JSONResponse(content={"datasets": datasets})

@app.get("/dataset/{dataset_id}/columns")
async def get_dataset_columns(dataset_id: str, domain: Optional[str] = None):
    """Get column names from dataset or preprocessed data"""
    try:
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        data = processed_data_store[dataset_id]
        
        if domain and "preprocessed_data" in data and domain in data["preprocessed_data"]:
            # Return preprocessed columns
            df = data["preprocessed_data"][domain]["data"]
            return JSONResponse(content={
                "columns": df.columns.tolist(),
                "is_preprocessed": True
            })
        else:
            # Return raw columns
            df = data["raw_data"]
            return JSONResponse(content={
                "columns": df.columns.tolist(),
                "is_preprocessed": False
            })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting columns: {str(e)}")

@app.get("/dataset/{dataset_id}/suggest-target")
async def suggest_target_column(dataset_id: str, domain: Optional[str] = None):
    """Suggest the best target column for prediction"""
    try:
        if dataset_id not in processed_data_store:
            raise HTTPException(status_code=404, detail="Dataset not found")
        
        data = processed_data_store[dataset_id]
        
        if domain and "preprocessed_data" in data and domain in data["preprocessed_data"]:
            df = data["preprocessed_data"][domain]["data"]
        else:
            df = data["raw_data"]
        
        # Suggest target column based on domain and data characteristics
        columns = df.columns.tolist()
        
        # Exclude ID columns and similar identifiers
        id_keywords = ['id', 'identifier', 'key', 'index', 'number', 'code', 'uuid', 'guid']
        exclude_cols = [col for col in columns if any(keyword in col.lower() for keyword in id_keywords)]
        candidate_cols = [col for col in columns if col not in exclude_cols]
        
        # Domain-specific suggestions
        domain_keywords = {
            "HR": ["attrition", "leave", "turnover", "resignation", "performance", "rating", "satisfaction"],
            "Finance": ["budget", "expense", "cost", "revenue", "profit", "loss", "amount", "balance"],
            "Sales": ["sales", "revenue", "quantity", "demand", "orders", "target", "conversion"],
            "Operations": ["efficiency", "throughput", "capacity", "utilization", "defect", "quality", "performance"]
        }
        
        suggested = None
        if domain and domain in domain_keywords:
            for keyword in domain_keywords[domain]:
                for col in candidate_cols:
                    if keyword.lower() in col.lower():
                        suggested = col
                        break
                if suggested:
                    break
        
        # If no domain-specific match, use first numeric column (excluding IDs)
        if not suggested:
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            # Filter out ID columns
            numeric_cols = [col for col in numeric_cols if col not in exclude_cols]
            if numeric_cols:
                suggested = numeric_cols[0]
            elif candidate_cols:
                # Fallback to any non-ID column
                suggested = candidate_cols[0]
            elif columns:
                # Last resort: use any column
                suggested = columns[-1]
        
        return JSONResponse(content={
            "suggested_column": suggested,
            "all_columns": columns,
            "excluded_columns": exclude_cols,
            "reason": f"Selected based on domain: {domain}" if domain and suggested else "Selected first numeric column"
        })
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error suggesting target: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

