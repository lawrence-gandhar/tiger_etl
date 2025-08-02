"""Session management operations for database interactions using Object-Oriented Programming.

This module provides a comprehensive SessionManager class for handling all session-related
database operations including CRUD operations, batch operations, and search functionality.
All operations are transactional and include proper error handling and validation.

Example:
    Basic session management operations using the SessionManager class:
    
    >>> # Initialize the session manager
    >>> session_manager = SessionManager()
    >>> 
    >>> # Create a new session
    >>> session_data = {
    ...     "user_id": 123,
    ...     "session_id": "unique-session-token",
    ...     "ip_address": "192.168.1.100",
    ...     "user_agent": "Mozilla/5.0..."
    ... }
    >>> new_session = session_manager.create_session(session_data)
    >>> print(new_session["session_id"])
    unique-session-token
    
    >>> # Get session by ID
    >>> session = session_manager.get_session_by_id(1)
    >>> print(session["user_id"])
    123
    
    >>> # End session
    >>> session_manager.logout_session("unique-session-token")
    
    >>> # Use as context manager for automatic cleanup
    >>> with SessionManager() as session_manager:
    ...     active_sessions = session_manager.get_active_sessions_by_user(123)
    ...     print(f"User has {len(active_sessions)} active sessions")
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from system.system.database_connections.pg_db import PostgresDB
from system.system.database_connections.exceptions import (
    SQLAlchemyInsertError,
    SQLAlchemyReadError,
    SQLAlchemyUpdateError,
    SQLAlchemyDeleteError,
)
from system.system.database_functions.exceptions import (
    SessionNotFoundError,
    SessionCreateError,
    SessionUpdateError,
    SessionDeleteError,
    SessionValidationError,
    SessionAlreadyExistsError,
)
from system.system.database_functions.sessions_management.sessions_management_constants import (
    USER_SESSIONS_TABLE,
    SESSION_NOT_FOUND,
    SESSION_ALREADY_EXISTS,
    INVALID_USER_ID,
    INVALID_SESSION_ID,
    SESSION_ID_NON_EMPTY_STRING,
    IP_ADDRESS_NON_EMPTY_STRING,
    ACTIVE_SESSION_NOT_FOUND
)
from system.system.database_functions.sessions_management.validations import (
    SessionCreate,
    SessionUpdate,
    SessionSearch,
    SessionActivityUpdate,
    SessionLogout,
    SessionCleanup,
    BulkSessionOperation
)


class SessionManager:
    """Object-oriented session management class for database operations.
    
    This class provides a comprehensive interface for session management operations
    including CRUD operations, batch operations, search functionality, and
    administrative tasks. All operations are transactional with proper error
    handling and validation.
    
    Attributes:
        _db_connection: Optional PostgresDB connection instance
        _auto_close: Whether to automatically close connections
        
    Examples:
        >>> # Basic usage
        >>> session_manager = SessionManager()
        >>> session = session_manager.create_session({
        ...     "user_id": 123, 
        ...     "session_id": "unique-token"
        ... })
        >>> session_manager.close()
        >>> 
        >>> # Using as context manager (recommended)
        >>> with SessionManager() as session_manager:
        ...     sessions = session_manager.get_sessions_by_user(123)
        ...     for session in sessions:
        ...         print(session["session_id"])
    """
    
    def __init__(self) -> None:
        """Initialize the SessionManager with singleton database connection."""
        pass

    def _get_db_connection(self) -> PostgresDB:
        """Get the singleton database connection.
        
        Returns:
            PostgresDB: The singleton database connection instance
        """
        return PostgresDB()

    def create_session(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new session in the database.
        
        Validates the session data using Pydantic models and creates a new session record. 
        Checks for existing sessions with the same session_id to prevent duplicates.
        
        Args:
            session_data: Dictionary containing session information (user_id and session_id required)
            
        Returns:
            Dictionary containing the created session data with database-generated fields
            
        Raises:
            SessionAlreadyExistsError: If a session with the same session_id already exists
            SessionCreateError: If session creation fails or validation errors occur
            
        Example:
            >>> session_manager = SessionManager()
            >>> session_data = {
            ...     "user_id": 123,
            ...     "session_id": "unique-session-token-12345",
            ...     "ip_address": "192.168.1.100",
            ...     "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            ...     "device_info": "Windows 10, Chrome Browser"
            ... }
            >>> new_session = session_manager.create_session(session_data)
            >>> print(new_session["id"])  # Auto-generated ID
            1
            >>> print(new_session["session_id"])
            unique-session-token-12345
        """
        try:
            # Validate session data using Pydantic model
            validated_data = SessionCreate(**session_data)
            processed_data = validated_data.dict(exclude_unset=True)
            
            db = self._get_db_connection()
            
            # Check if session already exists
            existing_sessions = db.read(USER_SESSIONS_TABLE, {'session_id': processed_data['session_id']})
            if existing_sessions:
                raise SessionAlreadyExistsError(SESSION_ALREADY_EXISTS)
            
            # Set default values for session creation
            processed_data = self._prepare_session_data_for_creation(processed_data)
            
            # Create the session
            created_session = db.create(USER_SESSIONS_TABLE, processed_data)
            if created_session:
                return dict(created_session._mapping)
            else:
                raise SessionCreateError("Failed to create session")
                
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyInsertError as e:
            raise SessionCreateError(f"Database error creating session: {e}") from e
        except Exception as e:
            if isinstance(e, (SessionAlreadyExistsError, SessionValidationError)):
                raise
            raise SessionCreateError(f"Unexpected error creating session: {e}") from e

    def get_session_by_id(self, session_id: int) -> Dict[str, Any]:
        """Retrieve a session by its ID.
        
        Args:
            session_id: The unique identifier of the session
            
        Returns:
            Dictionary containing the session data
            
        Raises:
            SessionNotFoundError: If no session exists with the given ID
            
        Example:
            >>> session_manager = SessionManager()
            >>> session = session_manager.get_session_by_id(1)
            >>> print(session["user_id"])
            123
            >>> print(session["session_id"])
            unique-session-token-12345
        """
        self._validate_session_id_int(session_id)
        
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'id': session_id})
            if not sessions:
                raise SessionNotFoundError(SESSION_NOT_FOUND)
            return dict(sessions[0]._mapping)
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error retrieving session: {e}") from e
        except Exception as e:
            if isinstance(e, SessionNotFoundError):
                raise
            raise SessionNotFoundError(f"Unexpected error retrieving session: {e}") from e

    def get_session_by_session_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a session by its session_id string.
        
        Args:
            session_id: The unique session identifier string
            
        Returns:
            Dictionary containing the session data or None if not found
            
        Example:
            >>> session_manager = SessionManager()
            >>> session = session_manager.get_session_by_session_id("unique-session-token-12345")
            >>> if session:
            ...     print(f"Found session for user: {session['user_id']}")
            ... else:
            ...     print("Session not found")
        """
        if not session_id or not isinstance(session_id, str):
            raise SessionValidationError(SESSION_ID_NON_EMPTY_STRING)
            
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'session_id': session_id})
            return dict(sessions[0]._mapping) if sessions else None
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error retrieving session: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionNotFoundError(f"Unexpected error retrieving session: {e}") from e

    def get_sessions_by_user(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve all sessions for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            limit: Maximum number of sessions to return (default: 100)
            
        Returns:
            List of dictionaries containing session data
            
        Example:
            >>> session_manager = SessionManager()
            >>> user_sessions = session_manager.get_sessions_by_user(123)
            >>> print(f"User has {len(user_sessions)} total sessions")
            >>> for session in user_sessions:
            ...     status = "Active" if session["is_active"] else "Ended"
            ...     print(f"Session {session['session_id'][:8]}... - {status}")
        """
        self._validate_user_id(user_id)
        
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'user_id': user_id})
            sessions_list = [dict(session._mapping) for session in sessions[:limit]]
            
            # Sort by login_datetime descending (most recent first)
            sessions_list.sort(key=lambda x: x.get('login_datetime', ''), reverse=True)
            return sessions_list
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error retrieving sessions: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionNotFoundError(f"Unexpected error retrieving sessions: {e}") from e

    def get_active_sessions_by_user(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all active sessions for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of dictionaries containing active session data
            
        Example:
            >>> session_manager = SessionManager()
            >>> active_sessions = session_manager.get_active_sessions_by_user(123)
            >>> print(f"User has {len(active_sessions)} active sessions")
            >>> for session in active_sessions:
            ...     print(f"Active since: {session['login_datetime']}")
        """
        self._validate_user_id(user_id)
        
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'user_id': user_id, 'is_active': True})
            sessions_list = [dict(session._mapping) for session in sessions]
            
            # Sort by login_datetime descending (most recent first)
            sessions_list.sort(key=lambda x: x.get('login_datetime', ''), reverse=True)
            return sessions_list
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error retrieving active sessions: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionNotFoundError(f"Unexpected error retrieving active sessions: {e}") from e

    def update_session(self, session_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing session's information.
        
        Performs partial updates using Pydantic validation - only provided fields will be modified.
        Validates the session exists before attempting the update.
        
        Args:
            session_id: The unique identifier of the session to update
            update_data: Dictionary containing fields to update
            
        Returns:
            Dictionary containing the updated session data
            
        Raises:
            SessionNotFoundError: If no session exists with the given ID
            SessionUpdateError: If the update operation fails
            
        Example:
            >>> session_manager = SessionManager()
            >>> # Update session activity
            >>> update_data = {"last_activity": datetime.now(timezone.utc)}
            >>> updated_session = session_manager.update_session(1, update_data)
            >>> print(updated_session["last_activity"])
        """
        self._validate_session_id_int(session_id)
        
        try:
            # Validate update data using Pydantic model
            validated_data = SessionUpdate(**update_data)
            processed_data = validated_data.dict(exclude_unset=True)
            
            db = self._get_db_connection()
            
            # Check if session exists
            sessions = db.read(USER_SESSIONS_TABLE, {'id': session_id})
            if not sessions:
                raise SessionNotFoundError(SESSION_NOT_FOUND)
            
            # Update the session
            updated_sessions = db.update(USER_SESSIONS_TABLE, processed_data, {'id': session_id})
            if updated_sessions:
                return dict(updated_sessions[0]._mapping)
            else:
                raise SessionUpdateError("Failed to update session")
                
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyUpdateError as e:
            raise SessionUpdateError(f"Database error updating session: {e}") from e
        except Exception as e:
            if isinstance(e, (SessionNotFoundError, SessionValidationError)):
                raise
            raise SessionUpdateError(f"Unexpected error updating session: {e}") from e

    def update_session_activity(self, session_id: str) -> Dict[str, Any]:
        """Update the last activity timestamp for a session.
        
        Args:
            session_id: The session_id string to update
            
        Returns:
            Dictionary containing the updated session data
            
        Raises:
            SessionNotFoundError: If no session exists with the given session_id
            
        Example:
            >>> session_manager = SessionManager()
            >>> updated_session = session_manager.update_session_activity("unique-session-token-12345")
            >>> print("Activity updated")
        """
        try:
            # Validate session ID using Pydantic model
            validated_data = SessionActivityUpdate(session_id=session_id)
            
            db = self._get_db_connection()
            
            # Check if session exists and is active
            sessions = db.read(USER_SESSIONS_TABLE, {'session_id': validated_data.session_id, 'is_active': True})
            if not sessions:
                raise SessionNotFoundError(ACTIVE_SESSION_NOT_FOUND)
            
            # Update last activity
            update_data = {'last_activity': datetime.now(timezone.utc)}
            updated_sessions = db.update(USER_SESSIONS_TABLE, update_data, {'session_id': validated_data.session_id})
            
            if updated_sessions:
                return dict(updated_sessions[0]._mapping)
            else:
                raise SessionUpdateError("Failed to update session activity")
                
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyUpdateError as e:
            raise SessionUpdateError(f"Database error updating session activity: {e}") from e
        except Exception as e:
            if isinstance(e, (SessionNotFoundError, SessionValidationError)):
                raise
            raise SessionUpdateError(f"Unexpected error updating session activity: {e}") from e

    def logout_session(self, session_id: str) -> Dict[str, Any]:
        """End a session by setting logout time and deactivating it.
        
        Args:
            session_id: The session_id string to logout
            
        Returns:
            Dictionary containing the updated session data
            
        Raises:
            SessionNotFoundError: If no active session exists with the given session_id
            
        Example:
            >>> session_manager = SessionManager()
            >>> ended_session = session_manager.logout_session("unique-session-token-12345")
            >>> print(f"Session ended at: {ended_session['logout_datetime']}")
        """
        try:
            # Validate session ID using Pydantic model
            validated_data = SessionLogout(session_id=session_id)
            
            db = self._get_db_connection()
            
            # Check if session exists and is active
            sessions = db.read(USER_SESSIONS_TABLE, {'session_id': validated_data.session_id, 'is_active': True})
            if not sessions:
                raise SessionNotFoundError(ACTIVE_SESSION_NOT_FOUND)
            
            # Calculate session duration if login_datetime exists
            session_data = dict(sessions[0]._mapping)
            logout_time = datetime.now(timezone.utc)
            
            update_data = {
                'logout_datetime': logout_time,
                'is_active': False,
                'last_activity': logout_time
            }
            
            # Calculate duration if login_datetime exists
            if session_data.get('login_datetime'):
                login_time = session_data['login_datetime']
                if hasattr(login_time, 'replace'):  # datetime object
                    if login_time.tzinfo is None:
                        login_time = login_time.replace(tzinfo=timezone.utc)
                    duration = (logout_time - login_time).total_seconds()
                    update_data['session_duration'] = int(duration)
            
            # Update the session
            updated_sessions = db.update(USER_SESSIONS_TABLE, update_data, {'session_id': validated_data.session_id})
            
            if updated_sessions:
                return dict(updated_sessions[0]._mapping)
            else:
                raise SessionUpdateError("Failed to logout session")
                
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyUpdateError as e:
            raise SessionUpdateError(f"Database error logging out session: {e}") from e
        except Exception as e:
            if isinstance(e, (SessionNotFoundError, SessionValidationError)):
                raise
            raise SessionUpdateError(f"Unexpected error logging out session: {e}") from e

    def delete_session(self, session_id: int) -> bool:
        """Delete a session by its ID.
        
        Validates the session exists before attempting deletion.
        
        Args:
            session_id: The unique identifier of the session to delete
            
        Returns:
            True if session was deleted successfully
            
        Raises:
            SessionNotFoundError: If no session exists with the given ID
            SessionDeleteError: If the deletion operation fails
            
        Example:
            >>> session_manager = SessionManager()
            >>> success = session_manager.delete_session(1)
            >>> if success:
            ...     print("Session deleted successfully")
        """
        self._validate_session_id_int(session_id)
        
        try:
            db = self._get_db_connection()
            
            # Check if session exists
            sessions = db.read(USER_SESSIONS_TABLE, {'id': session_id})
            if not sessions:
                raise SessionNotFoundError(SESSION_NOT_FOUND)
            
            # Delete the session
            deleted_count = db.delete(USER_SESSIONS_TABLE, {'id': session_id})
            return deleted_count > 0
            
        except SQLAlchemyDeleteError as e:
            raise SessionDeleteError(f"Database error deleting session: {e}") from e
        except Exception as e:
            if isinstance(e, (SessionNotFoundError, SessionValidationError)):
                raise
            raise SessionDeleteError(f"Unexpected error deleting session: {e}") from e

    def delete_user_sessions(self, user_id: int, keep_active: bool = False) -> int:
        """Delete all sessions for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            keep_active: If True, only delete inactive sessions (default: False)
            
        Returns:
            Number of sessions deleted
            
        Raises:
            SessionDeleteError: If the deletion operation fails
            
        Example:
            >>> session_manager = SessionManager()
            >>> # Delete all sessions for user
            >>> count = session_manager.delete_user_sessions(123)
            >>> print(f"Deleted {count} sessions")
            
            >>> # Delete only inactive sessions
            >>> count = session_manager.delete_user_sessions(123, keep_active=True)
            >>> print(f"Deleted {count} inactive sessions")
        """
        try:
            # Validate bulk operation data using Pydantic model
            validated_data = BulkSessionOperation(user_id=user_id, keep_active=keep_active)
            
            db = self._get_db_connection()
            
            # Build delete criteria
            delete_criteria = {'user_id': validated_data.user_id}
            if validated_data.keep_active:
                delete_criteria['is_active'] = False
            
            # Delete sessions
            deleted_count = db.delete(USER_SESSIONS_TABLE, delete_criteria)
            return deleted_count
            
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyDeleteError as e:
            raise SessionDeleteError(f"Database error deleting user sessions: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionDeleteError(f"Unexpected error deleting user sessions: {e}") from e

    def search_sessions(self, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for sessions using comprehensive criteria.
        
        Args:
            search_criteria: Dictionary containing search parameters
            
        Returns:
            List of dictionaries containing matching session data
            
        Example:
            >>> session_manager = SessionManager()
            >>> search_criteria = {
            ...     "user_id": 123,
            ...     "is_active": True,
            ...     "limit": 50
            ... }
            >>> sessions = session_manager.search_sessions(search_criteria)
            >>> print(f"Found {len(sessions)} matching sessions")
        """
        try:
            # Validate search criteria using Pydantic model
            validated_data = SessionSearch(**search_criteria)
            
            db = self._get_db_connection()
            
            # Build search criteria for database query
            db_criteria = {}
            if validated_data.user_id is not None:
                db_criteria['user_id'] = validated_data.user_id
            if validated_data.session_id is not None:
                db_criteria['session_id'] = validated_data.session_id
            if validated_data.ip_address is not None:
                db_criteria['ip_address'] = validated_data.ip_address
            if validated_data.is_active is not None:
                db_criteria['is_active'] = validated_data.is_active
            
            # Get sessions from database
            sessions = db.read(USER_SESSIONS_TABLE, db_criteria)
            sessions_list = [dict(session._mapping) for session in sessions]
            
            # Apply datetime filters if specified
            if validated_data.login_datetime_from or validated_data.login_datetime_to:
                sessions_list = self._filter_by_login_datetime(
                    sessions_list, 
                    validated_data.login_datetime_from,
                    validated_data.login_datetime_to
                )
            
            if validated_data.last_activity_from or validated_data.last_activity_to:
                sessions_list = self._filter_by_last_activity(
                    sessions_list,
                    validated_data.last_activity_from,
                    validated_data.last_activity_to
                )
            
            # Sort by login_datetime descending (most recent first)
            sessions_list.sort(key=lambda x: x.get('login_datetime', ''), reverse=True)
            
            # Apply pagination
            offset = validated_data.offset or 0
            limit = validated_data.limit or 100
            
            return sessions_list[offset:offset + limit]
            
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error searching sessions: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionNotFoundError(f"Unexpected error searching sessions: {e}") from e
    
    def _filter_by_login_datetime(self, sessions: List[Dict], from_dt, to_dt) -> List[Dict]:
        """Filter sessions by login datetime range."""
        if not from_dt and not to_dt:
            return sessions
        
        filtered = []
        for session in sessions:
            login_dt = session.get('login_datetime')
            if login_dt:
                if from_dt and login_dt < from_dt:
                    continue
                if to_dt and login_dt > to_dt:
                    continue
                filtered.append(session)
        
        return filtered
    
    def _filter_by_last_activity(self, sessions: List[Dict], from_dt, to_dt) -> List[Dict]:
        """Filter sessions by last activity datetime range."""
        if not from_dt and not to_dt:
            return sessions
        
        filtered = []
        for session in sessions:
            activity_dt = session.get('last_activity')
            if activity_dt:
                if from_dt and activity_dt < from_dt:
                    continue
                if to_dt and activity_dt > to_dt:
                    continue
                filtered.append(session)
        
        return filtered

    def get_sessions_by_ip(self, ip_address: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieve sessions by IP address for security monitoring.
        
        Args:
            ip_address: The IP address to search for
            limit: Maximum number of sessions to return (default: 100)
            
        Returns:
            List of dictionaries containing session data
            
        Example:
            >>> session_manager = SessionManager()
            >>> suspicious_sessions = session_manager.get_sessions_by_ip("192.168.1.100")
            >>> print(f"Found {len(suspicious_sessions)} sessions from this IP")
        """
        if not ip_address or not isinstance(ip_address, str):
            raise SessionValidationError(IP_ADDRESS_NON_EMPTY_STRING)
        
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'ip_address': ip_address})
            sessions_list = [dict(session._mapping) for session in sessions[:limit]]
            
            # Sort by login_datetime descending (most recent first)
            sessions_list.sort(key=lambda x: x.get('login_datetime', ''), reverse=True)
            return sessions_list
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error retrieving sessions by IP: {e}") from e
        except Exception as e:
            if isinstance(e, SessionValidationError):
                raise
            raise SessionNotFoundError(f"Unexpected error retrieving sessions by IP: {e}") from e

    def count_active_sessions(self) -> int:
        """Count total number of active sessions across all users.
        
        Returns:
            Total count of active sessions
            
        Example:
            >>> session_manager = SessionManager()
            >>> active_count = session_manager.count_active_sessions()
            >>> print(f"Total active sessions: {active_count}")
        """
        try:
            db = self._get_db_connection()
            sessions = db.read(USER_SESSIONS_TABLE, {'is_active': True})
            return len(sessions)
            
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error counting active sessions: {e}") from e
        except Exception as e:
            raise SessionNotFoundError(f"Unexpected error counting active sessions: {e}") from e

    def cleanup_expired_sessions(self, hours_inactive: int = 24) -> int:
        """Clean up sessions that have been inactive for too long.
        
        Args:
            hours_inactive: Hours of inactivity before considering session expired (default: 24)
            
        Returns:
            Number of sessions cleaned up
            
        Example:
            >>> session_manager = SessionManager()
            >>> # Clean up sessions inactive for more than 12 hours
            >>> cleaned = session_manager.cleanup_expired_sessions(12)
            >>> print(f"Cleaned up {cleaned} expired sessions")
        """
        try:
            # Validate cleanup parameters using Pydantic model
            validated_data = SessionCleanup(hours_inactive=hours_inactive)
            
            db = self._get_db_connection()
            
            # Calculate cutoff time
            cutoff_time = datetime.now(timezone.utc) - timezone.timedelta(hours=validated_data.hours_inactive)
            
            # Find expired sessions (active but last_activity older than cutoff)
            all_active_sessions = db.read(USER_SESSIONS_TABLE, {'is_active': True})
            expired_sessions = self._find_expired_sessions(all_active_sessions, cutoff_time)
            
            # Update expired sessions to inactive
            cleanup_count = self._deactivate_expired_sessions(db, expired_sessions)
            
            return cleanup_count
            
        except ValueError as e:
            # Pydantic validation error
            raise SessionValidationError(f"Validation error: {e}") from e
        except SQLAlchemyReadError as e:
            raise SessionNotFoundError(f"Database error during cleanup: {e}") from e
        except Exception as e:
            raise SessionDeleteError(f"Unexpected error during cleanup: {e}") from e
    
    def _find_expired_sessions(self, active_sessions, cutoff_time) -> List[int]:
        """Find sessions that have expired based on last activity."""
        expired_sessions = []
        
        for session in active_sessions:
            session_data = dict(session._mapping)
            last_activity = session_data.get('last_activity')
            
            if last_activity and hasattr(last_activity, 'replace'):  # datetime object
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                if last_activity < cutoff_time:
                    expired_sessions.append(session_data['id'])
        
        return expired_sessions
    
    def _deactivate_expired_sessions(self, db, expired_sessions: List[int]) -> int:
        """Deactivate expired sessions and return count."""
        cleanup_count = 0
        logout_time = datetime.now(timezone.utc)
        
        for session_id in expired_sessions:
            try:
                update_data = {
                    'is_active': False,
                    'logout_datetime': logout_time
                }
                updated = db.update(USER_SESSIONS_TABLE, update_data, {'id': session_id})
                if updated:
                    cleanup_count += 1
            except Exception:
                continue  # Skip failed updates
        
        return cleanup_count

    def close(self) -> None:
        """Close method for backward compatibility.
        
        Note: In singleton mode, the database connection is shared and persistent.
        This method exists for backward compatibility but doesn't actually close
        the connection as it's managed by the singleton.
        """
        # No-op in singleton mode - connection is managed globally
        pass

    def __enter__(self) -> 'SessionManager':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - connection is persistent in singleton mode."""
        # No cleanup needed as connection is managed by singleton
        pass

    # Private validation methods
    def _validate_user_id(self, user_id: Any) -> None:
        """Validate user ID."""
        if not isinstance(user_id, int) or user_id <= 0:
            raise SessionValidationError(INVALID_USER_ID)

    def _validate_session_id_int(self, session_id: Any) -> None:
        """Validate integer session ID."""
        if not isinstance(session_id, int) or session_id <= 0:
            raise SessionValidationError("Session ID must be a positive integer")

    def _validate_session_data_for_creation(self, session_data: Dict[str, Any]) -> None:
        """Validate session data for creation."""
        if not isinstance(session_data, dict):
            raise SessionValidationError("Session data must be a dictionary")
        
        if 'user_id' not in session_data:
            raise SessionValidationError("user_id is required")
        
        if 'session_id' not in session_data:
            raise SessionValidationError("session_id is required")
        
        self._validate_user_id(session_data['user_id'])
        
        if not session_data['session_id'] or not isinstance(session_data['session_id'], str):
            raise SessionValidationError(INVALID_SESSION_ID)

    def _prepare_session_data_for_creation(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare session data for database insertion."""
        processed_data = session_data.copy()
        
        # Set default timestamps if not provided
        current_time = datetime.now(timezone.utc)
        
        if 'login_datetime' not in processed_data:
            processed_data['login_datetime'] = current_time
        
        if 'last_activity' not in processed_data:
            processed_data['last_activity'] = current_time
        
        if 'is_active' not in processed_data:
            processed_data['is_active'] = True
        
        return processed_data

    def _prepare_session_data_for_update(self, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare session data for database update."""
        processed_data = {}
        
        # Only include non-None values and valid fields
        allowed_fields = {
            'user_id', 'session_id', 'login_datetime', 'logout_datetime', 
            'is_active', 'ip_address', 'user_agent', 'device_info', 
            'last_activity', 'session_duration'
        }
        
        for key, value in update_data.items():
            if key in allowed_fields and value is not None:
                processed_data[key] = value
        
        return processed_data


def generate_session_id(prefix: str = "sess") -> str:
    """Generate a unique session ID.
    
    Args:
        prefix: Optional prefix for the session ID (default: "sess")
        
    Returns:
        str: Generated session ID in format "prefix-uuid"
    """
    unique_id = str(uuid.uuid4()).replace('-', '')
    return f"{prefix}-{unique_id}"


# Convenience functions for quick operations
def create_session(user_id: int, ip_address: str = None, user_agent: str = None, device_info: str = None) -> Dict[str, Any]:
    """Create a new session with automatic session ID generation.
    
    Args:
        user_id: The user ID for the session
        ip_address: Optional client IP address
        user_agent: Optional client user agent
        device_info: Optional device information
        
    Returns:
        Dictionary containing the created session data
    """
    session_data = {
        'user_id': user_id,
        'session_id': generate_session_id(),
        'ip_address': ip_address,
        'user_agent': user_agent,
        'device_info': device_info
    }
    
    session_manager = SessionManager()
    return session_manager.create_session(session_data)


def end_session(session_id: str) -> Dict[str, Any]:
    """End a session by session ID.
    
    Args:
        session_id: The session ID to end
        
    Returns:
        Dictionary containing the ended session data
    """
    session_manager = SessionManager()
    return session_manager.logout_session(session_id)
