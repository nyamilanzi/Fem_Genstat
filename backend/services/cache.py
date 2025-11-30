"""
In-memory data cache with session management
"""

import time
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import pandas as pd

class DataCache:
    """In-memory cache for uploaded datasets with session management"""
    
    def __init__(self, ttl_minutes: int = 60):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.ttl_minutes = ttl_minutes
        self.last_cleanup = time.time()
    
    def create_session(self, data: pd.DataFrame, metadata: Dict[str, Any]) -> str:
        """Create a new session with uploaded data"""
        # Generate session ID from data hash and timestamp
        data_hash = hashlib.md5(data.to_string().encode()).hexdigest()[:16]
        timestamp = str(int(time.time()))[-8:]
        session_id = f"{data_hash}_{timestamp}"
        
        self.sessions[session_id] = {
            "data": data,
            "metadata": metadata,
            "created_at": datetime.now(),
            "last_accessed": datetime.now(),
            "file_hash": data_hash
        }
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data if it exists and hasn't expired"""
        if session_id not in self.sessions:
            return None
        
        session = self.sessions[session_id]
        
        # Check if session has expired
        if self._is_expired(session):
            del self.sessions[session_id]
            return None
        
        # Update last accessed time
        session["last_accessed"] = datetime.now()
        return session
    
    def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update session data"""
        if session_id not in self.sessions:
            return False
        
        session = self.sessions[session_id]
        session.update(updates)
        session["last_accessed"] = datetime.now()
        return True
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False
    
    def _is_expired(self, session: Dict[str, Any]) -> bool:
        """Check if session has expired based on TTL"""
        now = datetime.now()
        last_accessed = session["last_accessed"]
        return (now - last_accessed).total_seconds() > (self.ttl_minutes * 60)
    
    def cleanup(self):
        """Remove expired sessions"""
        now = time.time()
        # Only run cleanup every 5 minutes to avoid overhead
        if now - self.last_cleanup < 300:
            return
        
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if self._is_expired(session):
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.sessions[session_id]
        
        self.last_cleanup = now
        print(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "total_sessions": len(self.sessions),
            "ttl_minutes": self.ttl_minutes,
            "last_cleanup": self.last_cleanup
        }

