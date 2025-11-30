"""
Authentication service
"""
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import jwt, JWTError
from models.user import User, UserCreate

# In-memory user storage (in production, use a database)
users_db: Dict[str, Dict] = {}
SECRET_KEY = "femstat-secret-key-change-in-production"  # Change in production!

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == hashed

def create_user(user_data: UserCreate) -> User:
    """Create a new user"""
    user_id = secrets.token_urlsafe(16)
    
    # Check if email already exists
    for existing_user in users_db.values():
        if existing_user["email"] == user_data.email:
            raise ValueError("Email already registered")
    
    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(),
        "last_login": None
    }
    
    users_db[user_id] = user
    
    return User(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        created_at=user["created_at"],
        last_login=None
    )

def authenticate_user(email: str, password: str) -> Optional[User]:
    """Authenticate user and return User object"""
    for user_data in users_db.values():
        if user_data["email"] == email:
            if verify_password(password, user_data["password_hash"]):
                # Update last login
                user_data["last_login"] = datetime.now()
                return User(
                    id=user_data["id"],
                    email=user_data["email"],
                    name=user_data["name"],
                    created_at=user_data["created_at"],
                    last_login=user_data["last_login"]
                )
    return None

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get user by ID"""
    user_data = users_db.get(user_id)
    if user_data:
        return User(
            id=user_data["id"],
            email=user_data["email"],
            name=user_data["name"],
            created_at=user_data["created_at"],
            last_login=user_data["last_login"]
        )
    return None

def create_access_token(user: User) -> str:
    """Create JWT access token"""
    payload = {
        "sub": user.id,
        "email": user.email,
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")

def verify_token(token: str) -> Optional[str]:
    """Verify JWT token and return user ID"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        return payload.get("sub")
    except JWTError:
        return None

def get_user_count() -> int:
    """Get total number of registered users"""
    return len(users_db)

