"""
Unified entry point for the Algo Hub Financial Dashboard
Combines Streamlit frontend with FastAPI backend
"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import threading
import subprocess
import sys
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    from database import init_db
    init_db()
    # Run migrations
    from run_migrations import run_migrations
    run_migrations()
    yield
    # Shutdown

app = FastAPI(lifespan=lifespan)

# Include API routes
from api.main import app as api_app
app.mount("/api/v1", api_app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "algohub-financial-dashboard"}

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

def run_streamlit():
    """Run the Streamlit app in a separate thread"""
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py", "--server.port", "8502"])


def start_scheduled_backups():
    """Start the scheduled backup system"""
    try:
        from scheduled_backup import start_scheduler
        start_scheduler()
    except ImportError:
        print("Scheduled backup module not found")
    except Exception as e:
        print(f"Error starting scheduled backups: {str(e)}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8000, help="Port to run the API on")
    parser.add_argument("--host", default="0.0.0.0", help="Host to run the API on")
    parser.add_argument("--streamlit", action="store_true", help="Also run the Streamlit app")
    args = parser.parse_args()
    
    # Start scheduled backups
    start_scheduled_backups()
    
    if args.streamlit:
        # Run Streamlit in a separate thread
        streamlit_thread = threading.Thread(target=run_streamlit)
        streamlit_thread.daemon = True
        streamlit_thread.start()
    
    # Run the FastAPI application
    uvicorn.run(app, host=args.host, port=args.port)