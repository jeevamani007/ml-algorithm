"""
Quick test script to verify the server setup
"""
from pathlib import Path
import sys

# Add backend to path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

# Check paths
frontend_path = backend_dir.parent / "frontend"
print("=" * 60)
print("Server Setup Test")
print("=" * 60)
print(f"\nBackend directory: {backend_dir}")
print(f"Backend exists: {backend_dir.exists()}")
print(f"\nFrontend directory: {frontend_path}")
print(f"Frontend exists: {frontend_path.exists()}")

if frontend_path.exists():
    print("\nFrontend files:")
    for file in frontend_path.iterdir():
        if file.is_file():
            print(f"  - {file.name} ({file.stat().st_size} bytes)")
else:
    print("\n❌ Frontend directory not found!")
    print("Expected location:", frontend_path)

print("\n" + "=" * 60)
print("To start the server, run: python start_full_app.py")
print("=" * 60)

