#!/usr/bin/env python3
"""
StitchGuard API Startup Script
Run this to start the development server
"""

import os
import sys
import subprocess
from pathlib import Path

def check_requirements():
    """Check if required packages are installed"""
    try:
        import fastapi
        import sqlalchemy
        import uvicorn
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("📦 Please install requirements: pip install -r requirements.txt")
        return False

def setup_database():
    """Setup and seed the database"""
    print("🗄️  Setting up database...")
    
    # Change to db directory and run seed script
    db_dir = Path(__file__).parent / "db"
    original_dir = os.getcwd()
    
    try:
        os.chdir(db_dir)
        result = subprocess.run([sys.executable, "seed.py"], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database setup completed")
            print(result.stdout)
        else:
            print("❌ Database setup failed")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        return False
    finally:
        os.chdir(original_dir)
    
    return True

def start_server():
    """Start the FastAPI development server"""
    print("🚀 Starting StitchGuard API server...")
    print("📚 API documentation will be available at: http://localhost:8000/docs")
    print("🔧 Press Ctrl+C to stop the server")
    
    try:
        import uvicorn
        uvicorn.run(
            "backend.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Server stopped")
    except Exception as e:
        print(f"❌ Error starting server: {e}")

def main():
    print("🧵 StitchGuard API Setup")
    print("=" * 40)
    
    # Check if requirements are installed
    if not check_requirements():
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup failed, but continuing...")
    
    # Start the server
    start_server()

if __name__ == "__main__":
    main() 