"""
Authentication router
"""
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
from models.user import UserCreate, UserLogin, User, Token
from services.auth import (
    create_user, authenticate_user, create_access_token,
    verify_token, get_user_by_id, get_user_count
)

router = APIRouter()

@router.post("/signup", response_model=Token)
async def signup(user_data: UserCreate):
    """User registration"""
    try:
        user = create_user(user_data)
        token = create_access_token(user)
        return Token(access_token=token, user=user)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """User login"""
    user = authenticate_user(credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    token = create_access_token(user)
    return Token(access_token=token, user=user)

@router.get("/me", response_model=User)
async def get_current_user(authorization: Optional[str] = Header(None)):
    """Get current user from token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    token = authorization.split(" ")[1]
    user_id = verify_token(token)
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    user = get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user

@router.get("/stats")
async def get_stats():
    """Get user statistics"""
    return {
        "total_users": get_user_count()
    }

