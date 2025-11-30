"""
Reports listing router
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, List, Dict, Any
from datetime import datetime
from services.cache import DataCache
from fastapi import Request

router = APIRouter()

def get_data_cache(request: Request) -> DataCache:
    """Dependency to get data cache instance"""
    return request.app.state.data_cache

@router.get("/reports")
async def list_reports(
    cache: DataCache = Depends(get_data_cache),
    authorization: Optional[str] = Header(None)
):
    """List all reports for the current user"""
    # In a real app, you'd get user ID from token
    # For now, return all reports (can filter by user later)
    
    reports = []
    
    # Get all sessions with analysis results
    for session_id, session_data in cache.sessions.items():
        if session_data.get("analysis_results"):
            metadata = session_data.get("metadata", {})
            reports.append({
                "session_id": session_id,
                "title": "Gender Analysis Report",
                "filename": metadata.get("filename", "Unknown"),
                "generated_at": metadata.get("created_at", datetime.now().isoformat()),
                "html_url": f"/static/reports/{session_id}_report.html",
                "pdf_url": f"/static/reports/{session_id}_report.pdf",
                "docx_url": f"/static/reports/{session_id}_report.docx"
            })
    
    # Sort by date, newest first
    reports.sort(key=lambda x: x["generated_at"], reverse=True)
    
    return {"reports": reports}

