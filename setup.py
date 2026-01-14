#!/usr/bin/env python3
"""
Setup script for the Electronic Lab Notebook
This script will:
1. Install dependencies
2. Initialize the database
3. Create sample data (optional)
4. Start the Streamlit app
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"STEP: {description}")
    print(f"COMMAND: {command}")
    print('='*50)
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print("✅ SUCCESS!")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ ERROR!")
        print(f"Return code: {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False

def main():
    print("🔬 Electronic Lab Notebook Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python version: {sys.version}")
    
    # Step 1: Install dependencies
    if not run_command("python3 -m pip install -r requirements.txt", "Installing dependencies"):
        print("\n❌ Failed to install dependencies. Please install manually:")
        print("python3 -m pip install -r requirements.txt")
        sys.exit(1)
    
    # Step 2: Initialize database
    if not run_command("python3 init_database.py", "Initializing database"):
        print("\n❌ Failed to initialize database")
        sys.exit(1)
    
    # Step 3: Start the app
    print("\n" + "="*50)
    print("🚀 Starting Electronic Lab Notebook...")
    print("="*50)
    print("The app will open in your browser at: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    print("="*50)
    
    try:
        subprocess.run(["streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Failed to start Streamlit app: {e}")
        print("\nYou can try starting manually:")
        print("streamlit run app.py")
        sys.exit(1)

if __name__ == "__main__":
    main()
