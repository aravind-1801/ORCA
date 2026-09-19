"""
Vercel serverless entrypoint for ORCA FastAPI application.
Vercel's Python runtime looks for an ASGI/WSGI 'app' object in api/index.py.
"""
import sys
import os

# Add project root to path so backend package imports work
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.main import app  # noqa: F401 - Vercel picks up 'app' automatically
