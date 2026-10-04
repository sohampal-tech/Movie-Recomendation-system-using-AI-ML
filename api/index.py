import sys
import os

# Add root directory to sys.path so modules like backend and src can be imported
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from backend.app import app, application, handler

# Entry point for Vercel serverless functions
if __name__ == "__main__":
    app.run()
