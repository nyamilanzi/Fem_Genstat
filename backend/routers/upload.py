"""
Upload router for file handling
"""

import os
import tempfile
import shutil
from typing import Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import JSONResponse

from models.schemas import SchemaResponse, ErrorResponse
from services.load import load_file, infer_schema, validate_file_size, get_file_info
from services.cache import DataCache

router = APIRouter()

def get_data_cache(request: Request) -> DataCache:
    """Dependency to get data cache instance"""
    return request.app.state.data_cache

@router.post("/upload", response_model=SchemaResponse)
async def upload_file(
    file: UploadFile = File(...),
    cache: DataCache = Depends(get_data_cache)
):
    """Upload and process a dataset file"""
    
    # Validate file type
    allowed_extensions = {'.csv', '.xlsx', '.xls', '.sav', '.dta', '.parquet'}
    file_extension = os.path.splitext(file.filename)[1].lower()
    
    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {', '.join(allowed_extensions)}"
        )
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
        # Copy uploaded file to temporary file
        shutil.copyfileobj(file.file, tmp_file)
        tmp_file_path = tmp_file.name
    
    try:
        # Validate file size (50MB default)
        max_size_mb = int(os.getenv("MAX_UPLOAD_MB", "50"))
        if not validate_file_size(tmp_file_path, max_size_mb):
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {max_size_mb}MB"
            )
        
        # Determine file type
        file_type = file_extension[1:]  # Remove the dot
        
        # Load the file
        try:
            df = load_file(tmp_file_path, file_type)
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error loading file: {str(e)}"
            )
        
        # Validate DataFrame
        if df.empty:
            raise HTTPException(
                status_code=400,
                detail="File appears to be empty or could not be parsed"
            )
        
        if len(df.columns) == 0:
            raise HTTPException(
                status_code=400,
                detail="File has no columns"
            )
        
        # Limit to first 200 rows for preview (full analysis will use all data)
        df_preview = df.head(200)
        
        # Infer schema
        schema, gender_candidates = infer_schema(df_preview)
        
        # Get file information
        file_info = get_file_info(tmp_file_path)
        
        # Store in cache (use full dataset for analysis)
        session_id = cache.create_session(df, {
            "filename": file.filename,
            "file_type": file_type,
            "file_info": file_info,
            "total_rows": len(df),
            "preview_rows": len(df_preview)
        })
        
        return SchemaResponse(
            session_id=session_id,
            schema=schema,
            gender_candidates=gender_candidates,
            file_info=file_info
        )
    
    finally:
        # Clean up temporary file
        if os.path.exists(tmp_file_path):
            os.unlink(tmp_file_path)

@router.post("/purge/{session_id}")
async def purge_session(
    session_id: str,
    cache: DataCache = Depends(get_data_cache)
):
    """Purge a specific session from cache"""
    
    success = cache.delete_session(session_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )
    
    return {"ok": True, "message": "Session purged successfully"}

@router.post("/purge-all")
async def purge_all_sessions(
    cache: DataCache = Depends(get_data_cache)
):
    """Purge all sessions from cache"""
    
    cache.sessions.clear()
    
    return {"ok": True, "message": "All sessions purged successfully"}
