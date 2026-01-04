"""
Start script for the full application (Backend + Frontend)
This serves both the API and the frontend from the same server
"""
import uvicorn
from pathlib import Path
import os
import sys

if __name__ == "__main__":
    # Get the project root directory
    project_root = Path(__file__).parent
    backend_dir = project_root / "backend"
    
    # Add backend directory to Python path
    sys.path.insert(0, str(backend_dir))
    
    # Change to project root (not backend) so paths resolve correctly
    os.chdir(project_root)
    
    print("=" * 60)
    print("AI Business Rule Discovery & Prediction Engine")
    print("=" * 60)
    print("\nStarting server...")
    print("Frontend will be available at: http://localhost:8000")
    print("API documentation at: http://localhost:8000/docs")
    print("API info endpoint: http://localhost:8000/api")
    print("\nPress Ctrl+C to stop the server\n")
    
    # Import and run from backend directory
    os.chdir(backend_dir)
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

