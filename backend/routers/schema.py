"""
Schema router for variable information
"""

from typing import List
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from services.cache import DataCache

router = APIRouter()

class VariableListResponse(BaseModel):
    variables: List[dict]

def get_data_cache(request: Request) -> DataCache:
    """Dependency to get data cache instance"""
    return request.app.state.data_cache

@router.post("/variables")
async def get_variables(
    session_id: str,
    cache: DataCache = Depends(get_data_cache)
):
    """Get detailed variable information for a session"""
    
    session = cache.get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired"
        )
    
    df = session["data"]
    
    # Get variable information
    variables = []
    for col in df.columns:
        series = df[col]
        
        var_info = {
            "name": col,
            "dtype": str(series.dtype),
            "unique_count": series.nunique(),
            "missing_count": series.isna().sum(),
            "missing_pct": round((series.isna().sum() / len(series)) * 100, 2),
            "sample_values": series.dropna().head(10).tolist()
        }
        
        # Add type-specific information
        if series.dtype in ['int64', 'float64']:
            var_info.update({
                "min": series.min(),
                "max": series.max(),
                "mean": series.mean(),
                "median": series.median()
            })
        
        variables.append(var_info)
    
    return VariableListResponse(variables=variables)
