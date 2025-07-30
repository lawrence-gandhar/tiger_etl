from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from system.system.database_connections.pg_db import PostgresDB
from system.system.database_functions.exceptions import (
    UserNotFoundError,
    UserCreateError,
    UserUpdateError,
    UserDeleteError,
    UserAlreadyExistsException,
)
from .constants import USER_ALREADY_EXISTS, USER_NOT_FOUND, USERS_TABLE
from .validations import UserCreate, UserUpdate, validate_user_id

@contextmanager
def get_db_connection():
    """Provide a transactional scope around a series of operations."""
    db = PostgresDB()
    try:
        yield db
    finally:
        db.close()

def create_user(user_data: dict, join: int = 0) -> dict:
    """Create a new user in the database."""
    validated_data = UserCreate(**user_data)
    try:
        with get_db_connection() as db:
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
        raise UserCreateError(str(exc))

def get_user_by_id(user_id: int, join: int = 0) -> dict:
    """Retrieve a user by ID."""
    validate_user_id(user_id)
    try:
        with get_db_connection() as db:
            users = db.read(USERS_TABLE, {'id': user_id}, join=join)
            if not users:
                raise UserNotFoundError(USER_NOT_FOUND)
            return dict(users[0]._mapping)
    except SQLAlchemyError as exc:
        raise UserNotFoundError(str(exc))

def update_user(user_id: int, update_data: dict, join: int = 0) -> dict:
    """Update an existing user."""
    validate_user_id(user_id)
    validated_data = UserUpdate(**update_data)
    try:
        with get_db_connection() as db:
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
        raise UserUpdateError(str(exc))

def delete_user(user_id: int, join: int = 0) -> None:
    """Delete a user by ID."""
    validate_user_id(user_id)
    try:
        with get_db_connection() as db:
            # Check if user exists
            users = db.read(USERS_TABLE, {'id': user_id}, join=join)
            if not users:
                raise UserNotFoundError(USER_NOT_FOUND)
            
            # Delete the user
            db.delete(USERS_TABLE, {'id': user_id})
    except SQLAlchemyError as exc:
        raise UserDeleteError(str(exc))

def delete_all_users(user_ids: list[int], join: int = 0) -> int:
    """
    Delete multiple users by their IDs.
    Returns the number of users deleted.
    """
    if not user_ids:
        return 0
    for user_id in user_ids:
        validate_user_id(user_id)
    try:
        with get_db_connection() as db:
            # Find existing users
            deleted_count = 0
            for user_id in user_ids:
                users = db.read(USERS_TABLE, {'id': user_id}, join=join)
                if users:
                    db.delete(USERS_TABLE, {'id': user_id})
                    deleted_count += 1
            return deleted_count
    except SQLAlchemyError as exc:
        raise UserDeleteError(str(exc))

def delete_users_with_details(user_ids: list[int], join: int = 0) -> dict:
    """
    Delete multiple users by their IDs and return detailed information about the operation.
    
    Args:
        user_ids: List of user IDs to delete
        
    Returns:
        dict: Contains detailed information about the deletion operation including:
            - deleted_count: Number of users successfully deleted
            - non_existing_ids: List of IDs that don't exist in the database
            - non_existing_count: Number of non-existing IDs
            - total_requested: Total number of IDs requested for deletion
            - success: Boolean indicating if all requested IDs were found and deleted
    
    Raises:
        UserDeleteError: If a database error occurs during the operation
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
        with get_db_connection() as db:
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
        raise UserDeleteError(str(exc))

def get_users(limit: int = 100, offset: int = 0, search: str = None, join: int = 0) -> list[dict]:
    """
    Retrieve users with optional limit, offset, search by name or email, and join control.
    Note: Search functionality is limited due to PostgresDB CRUD limitations.
    For complex queries, consider using direct SQLAlchemy queries.
    
    Args:
        limit (int): Maximum number of users to return (default: 100)
        offset (int): Number of users to skip (default: 0)
        search (str, optional): Search term for filtering by username, first_name, or last_name
        join (int): Join control parameter:
            - 0 (default): No joins, return only user data
            - 1: Forward joins (fetch related data from referenced tables)
            - -1: Backward joins (fetch data that references users)
    
    Returns:
        list[dict]: List of user dictionaries
    """
    try:
        with get_db_connection() as db:
            # Get all users (PostgresDB doesn't support complex filtering)
            all_users = db.read(USERS_TABLE, join=join)
            
            # Convert to list of dictionaries
            users_list = [dict(user._mapping) for user in all_users]
            
            # Apply search filter manually if provided
            if search:
                search_lower = search.lower()
                filtered_users = []
                for user in users_list:
                    username = user.get('username', '').lower()
                    first_name = user.get('first_name', '').lower() if user.get('first_name') else ''
                    last_name = user.get('last_name', '').lower() if user.get('last_name') else ''
                    
                    if (search_lower in username or 
                        search_lower in first_name or 
                        search_lower in last_name):
                        filtered_users.append(user)
                users_list = filtered_users
            
            # Apply pagination manually
            start_index = offset
            end_index = offset + limit
            return users_list[start_index:end_index]
            
    except SQLAlchemyError as exc:
        raise UserNotFoundError(str(exc))

def truncate_and_reset_identity_user_table() -> None:
    """
    Truncate the user table and reset its identity/auto-increment counter.
    """
    try:
        with get_db_connection() as db:
            db.truncate_and_reset_identity(USERS_TABLE)
    except SQLAlchemyError as exc:
        raise UserDeleteError(str(exc))
