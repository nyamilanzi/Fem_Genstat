"""
FastAPI main application for Gender Analysis Tool
"""

import os
import time
from contextlib import asynccontextmanager
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from routers import upload, analyze, report, schema, auth, reports_list
from services.cache import DataCache

# Global data cache
data_cache = DataCache()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for cleanup tasks"""
    # Startup
    print("Starting Gender Analysis Tool backend...")
    yield
    # Shutdown
    print("Shutting down Gender Analysis Tool backend...")
    data_cache.cleanup()

app = FastAPI(
    title="Gender Analysis Tool API",
    description="API for gender-stratified statistical analysis",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for reports
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(upload.router, prefix="/api", tags=["upload"])
app.include_router(schema.router, prefix="/api", tags=["schema"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(report.router, prefix="/api", tags=["report"])
app.include_router(reports_list.router, prefix="/api", tags=["reports"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Gender Analysis Tool API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "cache_size": len(data_cache.sessions)
    }

# Make data_cache available to routers
app.state.data_cache = data_cache

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
