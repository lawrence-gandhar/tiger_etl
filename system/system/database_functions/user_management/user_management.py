"""User management operations for database interactions using Object-Oriented Programming.

This module provides a comprehensive UserManager class for handling all user-related
database operations including CRUD operations, batch operations, and search functionality.
All operations are transactional and include proper error handling and validation.

Example:
    Basic user management operations using the UserManager class:
    
    >>> # Initialize the user manager
    >>> user_manager = UserManager()
    >>> 
    >>> # Create a new user
    >>> user_data = {"email": "john@example.com", "name": "John Doe"}
    >>> new_user = user_manager.create_user(user_data)
    >>> print(new_user["email"])
    john@example.com
    
    >>> # Get user by ID
    >>> user = user_manager.get_user_by_id(1)
    >>> print(user["name"])
    John Doe
    
    >>> # Update user
    >>> update_data = {"name": "John Smith"}
    >>> updated_user = user_manager.update_user(1, update_data)
    >>> print(updated_user["name"])
    John Smith
    
    >>> # Use as context manager for automatic cleanup
    >>> with UserManager() as user_manager:
    ...     users = user_manager.get_users(limit=10)
    ...     print(f"Found {len(users)} users")
"""

from contextlib import contextmanager
from typing import Dict, List, Optional, Any, Generator

from sqlalchemy.exc import SQLAlchemyError

from system.system.database_connections.pg_db import PostgresDB
from system.system.database_functions.exceptions import (
    UserNotFoundError,
    UserCreateError,
    UserUpdateError,
    UserDeleteError,
    UserAlreadyExistsException,
)
from system.system.database_functions.user_management.user_management_constants import USER_ALREADY_EXISTS, USER_NOT_FOUND, USERS_TABLE
from system.system.database_functions.user_management.validations import UserCreate, UserUpdate, validate_user_id


class UserManager:
    """Object-oriented user management class for database operations.
    
    This class provides a comprehensive interface for user management operations
    including CRUD operations, batch operations, search functionality, and
    administrative tasks. All operations are transactional with proper error
    handling and validation.
    
    Attributes:
        _db_connection: Optional PostgresDB connection instance
        _auto_close: Whether to automatically close connections
        
    Examples:
        >>> # Basic usage
        >>> user_manager = UserManager()
        >>> user = user_manager.create_user({"email": "test@example.com", "name": "Test User"})
        >>> user_manager.close()
        >>> 
        >>> # Using as context manager (recommended)
        >>> with UserManager() as user_manager:
        ...     users = user_manager.get_users(limit=5)
        ...     for user in users:
        ...         print(user["name"])
        >>> 
        >>> # Persistent connection for multiple operations
        >>> user_manager = UserManager(persistent_connection=True)
        >>> user1 = user_manager.create_user({"email": "user1@example.com", "name": "User 1"})
        >>> user2 = user_manager.create_user({"email": "user2@example.com", "name": "User 2"})
        >>> user_manager.close()  # Manual cleanup required
    """
    
    def __init__(self, persistent_connection: bool = False) -> None:
        """Initialize the UserManager.
        
        Args:
            persistent_connection: If True, maintains a persistent database connection.
                                 If False, creates new connections for each operation.
                                 
        Example:
            >>> # Standard usage (new connection per operation)
            >>> user_manager = UserManager()
            >>> 
            >>> # Persistent connection for better performance with multiple operations
            >>> user_manager = UserManager(persistent_connection=True)
        """
        self._db_connection: Optional[PostgresDB] = None
        self._persistent_connection = persistent_connection
        self._auto_close = True
        
        if persistent_connection:
            self._db_connection = PostgresDB()
            self._auto_close = False

    @contextmanager
    def _get_db_connection(self) -> Generator[PostgresDB, None, None]:
        """Provide a transactional scope around a series of operations.
        
        This internal method handles connection management based on the
        persistent_connection setting.
        
        Yields:
            PostgresDB: An active database connection instance
        """
        if self._persistent_connection and self._db_connection:
            yield self._db_connection
        else:
            db = PostgresDB()
            try:
                yield db
            finally:
                db.close()

    def create_user(self, user_data: Dict[str, Any], join: int = 0) -> Dict[str, Any]:
        """Create a new user in the database.
        
        Validates the user data and creates a new user record. Checks for existing
        users with the same email to prevent duplicates.
        
        Args:
            user_data: Dictionary containing user information (email and name required)
            join: Join control parameter (0=no joins, 1=forward joins, -1=backward joins)
            
        Returns:
            Dictionary containing the created user data with database-generated fields
            
        Raises:
            UserAlreadyExistsException: If a user with the same email already exists
            UserCreateError: If user creation fails or validation errors occur
            
        Example:
            >>> user_manager = UserManager()
            >>> user_data = {
            ...     "email": "alice@example.com",
            ...     "name": "Alice Johnson"
            ... }
            >>> new_user = user_manager.create_user(user_data)
            >>> print(new_user["id"])  # Auto-generated ID
            1
            >>> print(new_user["email"])
            alice@example.com
        """
        validated_data = UserCreate(**user_data)
        try:
            with self._get_db_connection() as db:
                # Check if user already exists
                existing_users = db.read(USERS_TABLE, {'email': validated_data.email}, join=join)
                if existing_users:
                    raise UserAlreadyExistsException(USER_ALREADY_EXISTS)
                
                # Create the user
                created_user = db.create(USERS_TABLE, validated_data.model_dump())
                if created_user:
                    return dict(created_user._mapping)
                else:
                    raise UserCreateError("Failed to create user")
        except SQLAlchemyError as exc:
            raise UserCreateError(str(exc)) from exc

    def get_user_by_id(self, user_id: int, join: int = 0) -> Dict[str, Any]:
        """Retrieve a user by their ID.
        
        Args:
            user_id: The unique identifier of the user
            join: Join control parameter (0=no joins, 1=forward joins, -1=backward joins)
            
        Returns:
            Dictionary containing the user data
            
        Raises:
            UserNotFoundError: If no user exists with the given ID
            
        Example:
            >>> user_manager = UserManager()
            >>> user = user_manager.get_user_by_id(1)
            >>> print(user["name"])
            Alice Johnson
            >>> print(user["email"])
            alice@example.com
            
            >>> # With joins to get related data
            >>> user_with_relations = user_manager.get_user_by_id(1, join=1)
            >>> # May include additional related data based on database schema
        """
        validate_user_id(user_id)
        try:
            with self._get_db_connection() as db:
                users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                if not users:
                    raise UserNotFoundError(USER_NOT_FOUND)
                return dict(users[0]._mapping)
        except SQLAlchemyError as exc:
            raise UserNotFoundError(str(exc)) from exc

    def get_user_by_email(self, email: str, join: int = 0) -> Optional[Dict[str, Any]]:
        """Retrieve a user by their email address.
        
        Args:
            email: The email address of the user
            join: Join control parameter (0=no joins, 1=forward joins, -1=backward joins)
            
        Returns:
            Dictionary containing the user data or None if not found
            
        Example:
            >>> user_manager = UserManager()
            >>> user = user_manager.get_user_by_email("alice@example.com")
            >>> if user:
            ...     print(f"Found user: {user['name']}")
            ... else:
            ...     print("User not found")
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
            
        try:
            with self._get_db_connection() as db:
                users = db.read(USERS_TABLE, {'email': email}, join=join)
                return dict(users[0]._mapping) if users else None
        except SQLAlchemyError as exc:
            raise UserNotFoundError(str(exc)) from exc

    def update_user(self, user_id: int, update_data: Dict[str, Any], join: int = 0) -> Dict[str, Any]:
        """Update an existing user's information.
        
        Performs partial updates - only provided fields will be modified.
        Validates the user exists before attempting the update.
        
        Args:
            user_id: The unique identifier of the user to update
            update_data: Dictionary containing fields to update
            join: Join control parameter (0=no joins, 1=forward joins, -1=backward joins)
            
        Returns:
            Dictionary containing the updated user data
            
        Raises:
            UserNotFoundError: If no user exists with the given ID
            UserUpdateError: If the update operation fails
            
        Example:
            >>> user_manager = UserManager()
            >>> # Update user's name only
            >>> update_data = {"name": "Alice Smith"}
            >>> updated_user = user_manager.update_user(1, update_data)
            >>> print(updated_user["name"])
            Alice Smith
            
            >>> # Update multiple fields
            >>> update_data = {
            ...     "name": "Alice Johnson-Smith",
            ...     "password": "newpassword123"
            ... }
            >>> updated_user = user_manager.update_user(1, update_data)
        """
        validate_user_id(user_id)
        validated_data = UserUpdate(**update_data)
        try:
            with self._get_db_connection() as db:
                # Check if user exists
                users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                if not users:
                    raise UserNotFoundError(USER_NOT_FOUND)
                
                # Update the user
                updated_users = db.update(USERS_TABLE, validated_data.model_dump(exclude_unset=True), {'id': user_id})
                if updated_users:
                    return dict(updated_users[0]._mapping)
                else:
                    raise UserUpdateError("Failed to update user")
        except SQLAlchemyError as exc:
            raise UserUpdateError(str(exc)) from exc

    def delete_user(self, user_id: int, join: int = 0) -> bool:
        """Delete a user by their ID.
        
        Validates the user exists before attempting deletion.
        
        Args:
            user_id: The unique identifier of the user to delete
            join: Join control parameter for existence check
            
        Returns:
            True if user was deleted successfully
            
        Raises:
            UserNotFoundError: If no user exists with the given ID
            UserDeleteError: If the deletion operation fails
            
        Example:
            >>> user_manager = UserManager()
            >>> success = user_manager.delete_user(1)
            >>> if success:
            ...     print("User deleted successfully")
            
            >>> # Verify deletion
            >>> try:
            ...     user_manager.get_user_by_id(1)
            ... except UserNotFoundError:
            ...     print("User successfully deleted")
        """
        validate_user_id(user_id)
        try:
            with self._get_db_connection() as db:
                # Check if user exists
                users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                if not users:
                    raise UserNotFoundError(USER_NOT_FOUND)
                
                # Delete the user
                db.delete(USERS_TABLE, {'id': user_id})
                return True
        except SQLAlchemyError as exc:
            raise UserDeleteError(str(exc)) from exc

    def delete_users_bulk(self, user_ids: List[int], join: int = 0) -> int:
        """Delete multiple users by their IDs.
        
        Processes deletions individually and counts successful deletions.
        Non-existing users are silently skipped.
        
        Args:
            user_ids: List of user IDs to delete
            join: Join control parameter for existence checks
            
        Returns:
            Number of users successfully deleted
            
        Raises:
            UserDeleteError: If a database error occurs during deletion
            
        Example:
            >>> user_manager = UserManager()
            >>> user_ids = [1, 2, 3, 999]  # 999 doesn't exist
            >>> deleted_count = user_manager.delete_users_bulk(user_ids)
            >>> print(deleted_count)
            3
            >>> # Only users 1, 2, 3 were deleted; 999 was skipped
        """
        if not user_ids:
            return 0
        
        for user_id in user_ids:
            validate_user_id(user_id)
            
        try:
            with self._get_db_connection() as db:
                deleted_count = 0
                for user_id in user_ids:
                    users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                    if users:
                        db.delete(USERS_TABLE, {'id': user_id})
                        deleted_count += 1
                return deleted_count
        except SQLAlchemyError as exc:
            raise UserDeleteError(str(exc)) from exc

    def delete_users_with_details(self, user_ids: List[int], join: int = 0) -> Dict[str, Any]:
        """Delete multiple users with detailed operation results.
        
        Provides comprehensive information about the deletion operation including
        which users were found, deleted, or missing.
        
        Args:
            user_ids: List of user IDs to delete
            join: Join control parameter for existence checks
            
        Returns:
            Dictionary containing detailed deletion results:
            - deleted_count: Number of users successfully deleted
            - non_existing_ids: List of IDs that don't exist in the database
            - non_existing_count: Number of non-existing IDs
            - total_requested: Total number of IDs requested for deletion
            - success: Boolean indicating if all requested IDs were found and deleted
            
        Raises:
            UserDeleteError: If a database error occurs during the operation
            
        Example:
            >>> user_manager = UserManager()
            >>> user_ids = [1, 2, 999, 1000]  # 999 and 1000 don't exist
            >>> result = user_manager.delete_users_with_details(user_ids)
            >>> print(result["deleted_count"])
            2
            >>> print(result["non_existing_ids"])
            [999, 1000]
            >>> print(result["success"])
            False
            >>> print(result["total_requested"])
            4
        """
        if not user_ids:
            return {
                'deleted_count': 0,
                'non_existing_ids': [],
                'non_existing_count': 0,
                'total_requested': 0,
                'success': True
            }
        
        # Validate all user IDs first
        for user_id in user_ids:
            validate_user_id(user_id)
        
        try:
            with self._get_db_connection() as db:
                # Find all existing users with the provided IDs
                existing_user_ids = []
                for user_id in user_ids:
                    users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                    if users:
                        existing_user_ids.append(user_id)
                
                # Determine which IDs don't exist
                non_existing_ids = [user_id for user_id in user_ids if user_id not in existing_user_ids]
                
                # Delete the existing users
                deleted_count = 0
                for user_id in existing_user_ids:
                    db.delete(USERS_TABLE, {'id': user_id})
                    deleted_count += 1
                
                return {
                    'deleted_count': deleted_count,
                    'non_existing_ids': non_existing_ids,
                    'non_existing_count': len(non_existing_ids),
                    'total_requested': len(user_ids),
                    'success': len(non_existing_ids) == 0  # Success if all requested IDs were found
                }
                
        except SQLAlchemyError as exc:
            raise UserDeleteError(str(exc)) from exc

    def get_users(
        self, 
        limit: int = 100, 
        offset: int = 0, 
        search: Optional[str] = None, 
        join: int = 0
    ) -> List[Dict[str, Any]]:
        """Retrieve users with pagination and optional search filtering.
        
        Note: Search functionality is limited due to PostgresDB CRUD limitations.
        For complex queries, consider using direct SQLAlchemy queries.
        
        Args:
            limit: Maximum number of users to return (default: 100)
            offset: Number of users to skip (default: 0)
            search: Search term for filtering by username, first_name, or last_name
            join: Join control parameter:
                - 0 (default): No joins, return only user data
                - 1: Forward joins (fetch related data from referenced tables)
                - -1: Backward joins (fetch data that references users)
        
        Returns:
            List of user dictionaries matching the criteria
            
        Raises:
            UserNotFoundError: If a database error occurs during retrieval
            
        Example:
            >>> user_manager = UserManager()
            >>> # Get first 10 users
            >>> users = user_manager.get_users(limit=10, offset=0)
            >>> print(len(users))
            10
            
            >>> # Search for users with "john" in their name
            >>> johns = user_manager.get_users(search="john")
            >>> for user in johns:
            ...     print(user["name"])
            John Doe
            Johnny Smith
            
            >>> # Get next page of results
            >>> next_page = user_manager.get_users(limit=10, offset=10)
            
            >>> # Get users with related data
            >>> users_with_relations = user_manager.get_users(join=1)
        """
        try:
            with self._get_db_connection() as db:
                # Get all users (PostgresDB doesn't support complex filtering)
                all_users = db.read(USERS_TABLE, join=join)
                
                # Convert to list of dictionaries
                users_list = [dict(user._mapping) for user in all_users]
                
                # Apply search filter manually if provided
                if search:
                    users_list = self._filter_users_by_search(users_list, search)
                
                # Apply pagination manually
                start_index = offset
                end_index = offset + limit
                return users_list[start_index:end_index]
                
        except SQLAlchemyError as exc:
            raise UserNotFoundError(str(exc)) from exc

    def _filter_users_by_search(self, users_list: List[Dict[str, Any]], search: str) -> List[Dict[str, Any]]:
        """Filter users by search term (internal helper method).
        
        Args:
            users_list: List of user dictionaries to filter
            search: Search term to match against username, first_name, last_name
            
        Returns:
            Filtered list of user dictionaries
        """
        search_lower = search.lower()
        filtered_users = []
        
        for user in users_list:
            username = user.get('username', '').lower()
            first_name = user.get('first_name', '').lower() if user.get('first_name') else ''
            last_name = user.get('last_name', '').lower() if user.get('last_name') else ''
            name = user.get('name', '').lower() if user.get('name') else ''
            
            if (search_lower in username or 
                search_lower in first_name or 
                search_lower in last_name or
                search_lower in name):
                filtered_users.append(user)
                
        return filtered_users

    def count_users(self, search: Optional[str] = None) -> int:
        """Count the total number of users, optionally filtered by search term.
        
        Args:
            search: Optional search term for filtering
            
        Returns:
            Total number of users matching the criteria
            
        Example:
            >>> user_manager = UserManager()
            >>> total_users = user_manager.count_users()
            >>> print(f"Total users: {total_users}")
            
            >>> # Count users with "john" in their name
            >>> john_count = user_manager.count_users(search="john")
            >>> print(f"Users with 'john': {john_count}")
        """
        try:
            with self._get_db_connection() as db:
                all_users = db.read(USERS_TABLE)
                users_list = [dict(user._mapping) for user in all_users]
                
                if search:
                    users_list = self._filter_users_by_search(users_list, search)
                    
                return len(users_list)
                
        except SQLAlchemyError as exc:
            raise UserNotFoundError(str(exc)) from exc

    def user_exists(self, user_id: int) -> bool:
        """Check if a user exists by their ID.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            True if user exists, False otherwise
            
        Example:
            >>> user_manager = UserManager()
            >>> if user_manager.user_exists(1):
            ...     print("User exists")
            ... else:
            ...     print("User not found")
        """
        validate_user_id(user_id)
        try:
            with self._get_db_connection() as db:
                users = db.read(USERS_TABLE, {'id': user_id})
                return len(users) > 0
        except SQLAlchemyError:
            return False

    def email_exists(self, email: str) -> bool:
        """Check if a user exists with the given email address.
        
        Args:
            email: The email address to check
            
        Returns:
            True if email exists, False otherwise
            
        Example:
            >>> user_manager = UserManager()
            >>> if user_manager.email_exists("test@example.com"):
            ...     print("Email already in use")
            ... else:
            ...     print("Email available")
        """
        if not email or not isinstance(email, str):
            raise ValueError("Email must be a non-empty string")
            
        try:
            with self._get_db_connection() as db:
                users = db.read(USERS_TABLE, {'email': email})
                return len(users) > 0
        except SQLAlchemyError:
            return False

    def truncate_and_reset_identity_user_table(self) -> None:
        """Truncate the user table and reset its identity/auto-increment counter.
        
        WARNING: This operation permanently deletes all user data and cannot be undone.
        Use with extreme caution, typically only in development or testing environments.
        
        Raises:
            UserDeleteError: If the truncate operation fails
            
        Example:
            >>> user_manager = UserManager()
            >>> # This will delete ALL users and reset the ID counter
            >>> user_manager.truncate_and_reset_identity_user_table()
            >>> # Table is now empty and next user will have ID 1
            
            >>> # Verify table is empty
            >>> users = user_manager.get_users()
            >>> print(len(users))
            0
        """
        try:
            with self._get_db_connection() as db:
                db.truncate_and_reset_identity(USERS_TABLE)
        except SQLAlchemyError as exc:
            raise UserDeleteError(str(exc)) from exc

    def close(self) -> None:
        """Close the database connection if using persistent connection.
        
        This method should be called when finished with the UserManager
        if using persistent_connection=True, or when explicitly needed.
        
        Example:
            >>> user_manager = UserManager(persistent_connection=True)
            >>> # ... perform operations ...
            >>> user_manager.close()  # Clean up resources
        """
        if self._db_connection:
            self._db_connection.close()
            self._db_connection = None

    def __enter__(self) -> 'UserManager':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - automatically close connection if needed."""
        if self._auto_close or self._persistent_connection:
            self.close()
