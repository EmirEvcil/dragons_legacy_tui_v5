#!/usr/bin/env python3
"""
Main entry point for Legend of Dragon's Legacy
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from dragons_legacy.frontend.app import main as run_frontend
from dragons_legacy.backend.main import app as backend_app


def main():
    """Main entry point with options to run frontend or backend."""
    if len(sys.argv) > 1:
        if sys.argv[1] == "backend":
            print("🐉 Starting Legend of Dragon's Legacy Backend Server...")
            print("API will be available at: http://localhost:8000")
            print("API documentation at: http://localhost:8000/docs")
            print("Press Ctrl+C to stop the server")
            
            import uvicorn
            uvicorn.run(backend_app, host="0.0.0.0", port=8000)
            
        elif sys.argv[1] == "frontend":
            print("🐉 Starting Legend of Dragon's Legacy TUI Client...")
            print("Make sure the backend server is running on localhost:8000")
            print("Press Ctrl+C to exit the game")
            
            run_frontend()
            
        else:
            print("Usage:")
            print("  python main.py frontend  - Start the TUI game client")
            print("  python main.py backend   - Start the API server")
    else:
        print("🐉 Welcome to Legend of Dragon's Legacy! 🐉")
        print("")
        print("To start the game:")
        print("1. First, start the backend server:")
        print("   python main.py backend")
        print("")
        print("2. Then, in another terminal, start the game client:")
        print("   python main.py frontend")
        print("")
        print("Or run them directly:")
        print("  python main.py frontend  - Start the TUI game client")
        print("  python main.py backend   - Start the API server")


if __name__ == "__main__":
    main()