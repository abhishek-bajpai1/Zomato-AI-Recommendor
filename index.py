"""
Vercel entrypoint: exposes FastAPI app for serverless deployment.
"""

from backend.main import app

# Vercel's Python runtime searches for the 'app' variable by default.
# No extra configuration needed for simple deployments.
