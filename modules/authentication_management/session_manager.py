"""Session management helper for FastAPI integration.

This module provides session management functionality for FastAPI applications,
integrating with the existing session management database system.
"""

import uuid
import secrets
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import Request, Response
from itsdangerous import URLSafeTimedSerializer, BadSignature

from system.system.database_functions.sessions_management.sessions_management import SessionManager
from system.system.database_functions.exceptions import (
    SessionNotFoundError,
    SessionCreateError,
    SessionAlreadyExistsError
)


class FastAPISessionManager:
    """FastAPI session management integration with database sessions."""
    
    def __init__(self, secret_key: str = None, session_cookie_name: str = "session_id", 
                 session_timeout: int = 3600):
        """Initialize the FastAPI session manager.
        
        Args:
            secret_key: Secret key for signing session cookies (auto-generated if None)
            session_cookie_name: Name of the session cookie
            session_timeout: Session timeout in seconds (default 1 hour)
        """
        self.secret_key = secret_key or secrets.token_hex(32)
        self.session_cookie_name = session_cookie_name
        self.session_timeout = session_timeout
        self.serializer = URLSafeTimedSerializer(self.secret_key)
        
    def generate_session_id(self) -> str:
        """Generate a unique session ID.
        
        Returns:
            str: A unique session identifier
        """
        return f"sess-{uuid.uuid4().hex}"
    
    def create_user_session(self, user: Dict[str, Any], request: Request, 
                          response: Response) -> str:
        """Create a new user session and set session cookie.
        
        Args:
            user: User information dictionary
            request: FastAPI request object
            response: FastAPI response object
            
        Returns:
            str: The created session ID
            
        Raises:
            SessionCreateError: If session creation fails
        """
        try:
            # Generate unique session ID
            session_id = self.generate_session_id()
            
            # Get client information
            client_ip = self._get_client_ip(request)
            user_agent = request.headers.get("user-agent", "Unknown")
            
            # Prepare session data
            session_data = {
                "user_id": user.get("id"),
                "session_id": session_id,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "device_info": self._extract_device_info(user_agent),
                "login_datetime": datetime.now(timezone.utc),
                "is_active": True
            }
            
            # Create session in database
            with SessionManager() as session_manager:
                session_manager.create_session(session_data)
            
            # Create signed session token
            session_token = self.serializer.dumps(session_id)
            
            # Set session cookie
            response.set_cookie(
                key=self.session_cookie_name,
                value=session_token,
                max_age=self.session_timeout,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax"
            )
            
            return session_id
            
        except SessionAlreadyExistsError:
            # If session already exists, try with a new ID
            return self.create_user_session(user, request, response)
        except Exception as e:
            raise SessionCreateError(f"Failed to create session: {str(e)}")
    
    def get_user_session(self, request: Request) -> Optional[Dict[str, Any]]:
        """Get user session from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            Optional[Dict[str, Any]]: Session data if valid, None otherwise
        """
        try:
            # Get session token from cookie
            session_token = request.cookies.get(self.session_cookie_name)
            if not session_token:
                return None
            
            # Verify and decode session token
            try:
                session_id = self.serializer.loads(
                    session_token, 
                    max_age=self.session_timeout
                )
            except BadSignature:
                return None
            
            # Get session from database
            with SessionManager() as session_manager:
                session = session_manager.get_session_by_session_id(session_id)
                
            # Check if session is active
            if session and session.get("is_active"):
                # Update last activity
                self._update_session_activity(session_id)
                return session
                
            return None
            
        except SessionNotFoundError:
            return None
        except Exception:
            return None
    
    def logout_user_session(self, request: Request, response: Response) -> bool:
        """Logout user session and clear cookie.
        
        Args:
            request: FastAPI request object
            response: FastAPI response object
            
        Returns:
            bool: True if logout successful, False otherwise
        """
        try:
            # Get session token from cookie
            session_token = request.cookies.get(self.session_cookie_name)
            if not session_token:
                return False
            
            # Verify and decode session token
            try:
                session_id = self.serializer.loads(session_token, max_age=self.session_timeout)
            except BadSignature:
                # Clear invalid cookie anyway
                response.delete_cookie(key=self.session_cookie_name)
                return False
            
            # Logout session in database
            with SessionManager() as session_manager:
                session_manager.logout_session(session_id)
            
            # Clear session cookie
            response.delete_cookie(key=self.session_cookie_name)
            
            return True
            
        except Exception:
            # Clear cookie even if database logout fails
            response.delete_cookie(key=self.session_cookie_name)
            return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request.
        
        Args:
            request: FastAPI request object
            
        Returns:
            str: Client IP address
        """
        # Check for forwarded headers first (proxy/load balancer)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"
    
    def _extract_device_info(self, user_agent: str) -> str:
        """Extract basic device information from user agent.
        
        Args:
            user_agent: User agent string
            
        Returns:
            str: Basic device information
        """
        if not user_agent:
            return "Unknown Device"
        
        # Simple device/browser detection
        device_info = []
        
        # Operating System
        if "Windows NT 10.0" in user_agent:
            device_info.append("Windows 10")
        elif "Windows NT" in user_agent:
            device_info.append("Windows")
        elif "Mac OS X" in user_agent:
            device_info.append("macOS")
        elif "Linux" in user_agent:
            device_info.append("Linux")
        elif "Android" in user_agent:
            device_info.append("Android")
        elif "iOS" in user_agent:
            device_info.append("iOS")
        
        # Browser
        if "Chrome" in user_agent and "Edg" not in user_agent:
            device_info.append("Chrome")
        elif "Firefox" in user_agent:
            device_info.append("Firefox")
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            device_info.append("Safari")
        elif "Edg" in user_agent:
            device_info.append("Edge")
        
        return ", ".join(device_info) if device_info else "Unknown Device"
    
    def _update_session_activity(self, session_id: str) -> None:
        """Update session last activity timestamp.
        
        Args:
            session_id: Session ID to update
        """
        try:
            with SessionManager() as session_manager:
                session_manager.update_session_activity(session_id)
        except Exception:
            # Silently fail - activity update is not critical
            pass


# Global session manager instance
session_manager = FastAPISessionManager()


def get_current_user(request: Request) -> Optional[Dict[str, Any]]:
    """Dependency to get current user from session.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Optional[Dict[str, Any]]: Current user data if authenticated, None otherwise
    """
    session = session_manager.get_user_session(request)
    if session:
        # Return user information from session
        return {
            "id": session.get("user_id"),
            "session_id": session.get("session_id"),
            "login_time": session.get("login_datetime"),
            "ip_address": session.get("ip_address"),
            "user_agent": session.get("user_agent")
        }
    return None


def create_session(user: Dict[str, Any], request: Request, response: Response) -> str:
    """Create a new user session.
    
    Args:
        user: User information
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        str: Created session ID
    """
    return session_manager.create_user_session(user, request, response)


def logout_session(request: Request, response: Response) -> bool:
    """Logout current session.
    
    Args:
        request: FastAPI request object
        response: FastAPI response object
        
    Returns:
        bool: True if logout successful
    """
    return session_manager.logout_user_session(request, response)
