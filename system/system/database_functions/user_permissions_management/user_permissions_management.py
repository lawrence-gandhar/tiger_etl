"""User permissions management database operations using Object-Oriented Programming.

This module provides a comprehensive UserPermissionManager class for handling all user permission-related
database operations including CRUD operations, batch operations, search functionality, and
administrative tasks. All operations are transactional with proper error handling and validation.

Example:
    Basic user permission management operations using the UserPermissionManager class:
    
    >>> # Initialize the user permission manager
    >>> perm_manager = UserPermissionManager()
    >>> 
    >>> # Create a new user permission
    >>> permission_data = {
    ...     "user_id": 1,
    ...     "resource_id": 10,
    ...     "permission_type": "read",
    ...     "permission_level": 2,
    ...     "granted_by": 5
    ... }
    >>> new_permission = perm_manager.create_user_permission(permission_data)
    >>> print(new_permission["permission_type"])
    read
    
    >>> # Get permission by ID
    >>> permission = perm_manager.read_user_permission(1)
    >>> print(permission["user_id"])
    1
    
    >>> # Update permission
    >>> update_data = {"permission_level": 3, "modified_by": 5}
    >>> updated_permission = perm_manager.update_user_permission(1, update_data)
    >>> print(updated_permission["permission_level"])
    3
    
    >>> # Use as context manager for automatic cleanup
    >>> with UserPermissionManager() as perm_manager:
    ...     permissions = perm_manager.read_user_permissions(limit=10)
    ...     print(f"Found {len(permissions['permissions'])} permissions")
"""

import logging
from typing import Dict, Any, List, Tuple

from system.system.database_connections.pg_db import PostgresDB
from system.system.database_connections.exceptions import (
    SQLAlchemyDeleteError,
    SQLAlchemyReadError,
    SQLAlchemyInsertError,
    SQLAlchemyUpdateError,
)
from system.system.database_functions.exceptions import (
    UserPermissionDeleteError,
    UserPermissionNotFoundError,
    UserPermissionValidationError,
    UserPermissionCreateError,
    UserPermissionUpdateError,
    UserPermissionAlreadyExistsError,
)
from system.system.database_functions.user_permissions_management.validations import (
    UserPermissionsCreate as UserPermissionCreate,
    UserPermissionsUpdate as UserPermissionUpdate,
)
from system.system.database_functions.user_permissions_management.user_permissions_management_constants import (
    USER_PERMISSIONS_TABLE,
    USER_PERMISSION_ALREADY_EXISTS,
)

# Set up logging
logger = logging.getLogger(__name__)


class UserPermissionManager:
    """Object-oriented user permission management class for database operations.
    
    This class provides a comprehensive interface for user permission management operations
    including CRUD operations, batch operations, search functionality, and
    administrative tasks. All operations use the singleton PostgresDB connection
    for optimal performance and resource management.
    
    Singleton Connection Benefits:
        - Shared database connection across all UserPermissionManager instances
        - Reduced connection overhead and improved performance  
        - Automatic connection pooling and management
        - Thread-safe database operations
        
    Examples:
        >>> # All instances share the same database connection
        >>> perm_manager1 = UserPermissionManager()
        >>> perm_manager2 = UserPermissionManager()
        >>> # Both use the same underlying connection
        >>> 
        >>> # Standard usage (no need for connection management)
        >>> perm_manager = UserPermissionManager()
        >>> permission = perm_manager.create_user_permission({
        ...     "user_id": 1, "resource_id": 10, "permission_type": "read", "granted_by": 5
        ... })
        >>> 
        >>> # Context manager still supported
        >>> with UserPermissionManager() as perm_manager:
        ...     permissions = perm_manager.read_user_permissions(limit=5)
        ...     for permission in permissions['permissions']:
        ...         print(permission["permission_type"])
    """
    
    def __init__(self) -> None:
        """Initialize the UserPermissionManager.
        
        Uses the singleton PostgresDB instance for optimal performance.
        No connection management needed as the singleton handles it automatically.
        """
        # Get the singleton database instance
        self._db = PostgresDB()
        logger.debug("UserPermissionManager initialized with singleton database connection")

    def _get_db_connection(self):
        """
        Get the singleton database connection.
        
        Returns:
            PostgresDB: The singleton database connection instance
        """
        return self._db

    def _validate_permission_id(self, permission_id: Any) -> int:
        """Validate and convert permission ID to integer (internal helper method).
        
        Args:
            permission_id: The permission ID to validate
            
        Returns:
            Validated integer permission ID
            
        Raises:
            UserPermissionValidationError: If permission ID is invalid
        """
        try:
            if permission_id is None:
                raise UserPermissionValidationError("Permission ID cannot be None")
            
            if isinstance(permission_id, str) and not permission_id.strip():
                raise UserPermissionValidationError("Permission ID cannot be empty string")
            
            permission_id_int = int(permission_id)
            
            if permission_id_int <= 0:
                raise UserPermissionValidationError("Permission ID must be a positive integer")
            
            return permission_id_int
            
        except (ValueError, TypeError) as e:
            raise UserPermissionValidationError(f"Invalid permission ID format: {permission_id}") from e

    def _check_permission_exists(self, db_instance: Any, permission_id: int) -> Dict[str, Any]:
        """Check if a permission exists and return its data (internal helper method).
        
        Args:
            db_instance: Database connection instance
            permission_id: The permission ID to check
            
        Returns:
            Dictionary containing the permission data
            
        Raises:
            UserPermissionNotFoundError: If permission doesn't exist
        """
        try:
            logger.debug(f"Checking if permission {permission_id} exists")
            permissions = db_instance.read(USER_PERMISSIONS_TABLE, {'id': permission_id})
            
            if not permissions or len(permissions) == 0:
                logger.warning(f"Permission with ID {permission_id} not found")
                raise UserPermissionNotFoundError(f"User permission with ID {permission_id} not found")
            
            permission_dict = dict(permissions[0]._mapping)
            logger.debug(f"Permission {permission_id} found for user {permission_dict.get('user_id', 'N/A')}")
            return permission_dict
            
        except SQLAlchemyReadError as e:
            logger.error(f"Database error while checking permission {permission_id}: {e}")
            raise UserPermissionNotFoundError(f"Error checking permission existence: {e}") from e

    def _check_permission_uniqueness(self, db_instance: PostgresDB, user_id: int, resource_id: int, permission_type: str, exclude_permission_id: int = None) -> None:
        """Check if permission combination is unique (internal helper method).
        
        Args:
            db_instance: Database connection instance
            user_id: User ID
            resource_id: Resource ID  
            permission_type: Permission type
            exclude_permission_id: Permission ID to exclude from uniqueness check (for updates)
            
        Raises:
            UserPermissionAlreadyExistsError: If combination is not unique
        """
        try:
            existing_permissions = db_instance.read(USER_PERMISSIONS_TABLE, {
                'user_id': user_id,
                'resource_id': resource_id,
                'permission_type': permission_type
            })
            
            if existing_permissions:
                for permission in existing_permissions:
                    permission_dict = dict(permission._mapping)
                    if exclude_permission_id is None or permission_dict['id'] != exclude_permission_id:
                        raise UserPermissionAlreadyExistsError(USER_PERMISSION_ALREADY_EXISTS)
                        
        except SQLAlchemyReadError as e:
            logger.error(f"Database error checking permission uniqueness: {e}")
            raise UserPermissionValidationError(f"Error checking permission uniqueness: {e}") from e

    def create_user_permission(self, permission_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new user permission.
        
        Validates the permission data and creates a new permission record.
        Checks for existing permissions with the same combination to prevent duplicates.
        
        Args:
            permission_data: Dictionary containing permission information
            
        Returns:
            Dictionary containing the created permission data with database-generated fields
            
        Raises:
            UserPermissionValidationError: If permission data validation fails
            UserPermissionAlreadyExistsError: If permission combination already exists
            UserPermissionCreateError: If permission creation fails
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> permission_data = {
            ...     "user_id": 1,
            ...     "resource_id": 10,
            ...     "permission_type": "read",
            ...     "permission_level": 2,
            ...     "granted_by": 5,
            ...     "notes": "Basic read access"
            ... }
            >>> new_permission = perm_manager.create_user_permission(permission_data)
            >>> print(new_permission["id"])  # Auto-generated ID
            1
            >>> print(new_permission["permission_type"])
            read
        """
        try:
            # Validate permission data
            validated_data = UserPermissionCreate(**permission_data)
            validated_dict = validated_data.model_dump()
            logger.debug(f"Creating user permission with data: {validated_dict}")
            
            db = self._get_db_connection()
            # Check for existing permission combination
            self._check_permission_uniqueness(
                db, 
                validated_data.user_id, 
                validated_data.resource_id, 
                validated_data.permission_type
            )
            
            # Create the permission
            created_permissions = db.create(USER_PERMISSIONS_TABLE, validated_dict)
            
            if not created_permissions:
                raise UserPermissionCreateError("Failed to create user permission - no data returned")
            
            created_permission = dict(created_permissions._mapping)
            logger.info(f"Successfully created user permission for user {created_permission.get('user_id', 'N/A')} (ID: {created_permission.get('id', 'N/A')})")
            
            return created_permission
                
        except (UserPermissionValidationError, UserPermissionAlreadyExistsError):
            raise
        except SQLAlchemyInsertError as e:
            logger.error(f"Database error creating user permission: {e}")
            raise UserPermissionCreateError(f"Database error creating user permission: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating user permission: {e}")
            raise UserPermissionCreateError(f"Unexpected error creating user permission: {e}") from e

    def read_user_permission(self, permission_id: Any) -> Dict[str, Any]:
        """Retrieve a user permission by its ID.
        
        Args:
            permission_id: The unique identifier of the permission
            
        Returns:
            Dictionary containing the permission data
            
        Raises:
            UserPermissionValidationError: If permission ID is invalid
            UserPermissionNotFoundError: If permission doesn't exist
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> permission = perm_manager.read_user_permission(1)
            >>> print(permission["permission_type"])
            read
            >>> print(permission["user_id"])
            1
        """
        permission_id = self._validate_permission_id(permission_id)
        
        try:
            db = self._get_db_connection()
            permission_data = self._check_permission_exists(db, permission_id)
            logger.info(f"Successfully retrieved user permission for user {permission_data.get('user_id', 'N/A')} (ID: {permission_id})")
            return permission_data
                
        except UserPermissionNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading user permission {permission_id}: {e}")
            raise UserPermissionNotFoundError(f"Error reading user permission: {e}") from e

    def read_user_permissions(self, filters: Dict[str, Any] = None, limit: int = None, offset: int = 0) -> Dict[str, Any]:
        """Retrieve multiple user permissions with optional filtering and pagination.
        
        Args:
            filters: Optional dictionary of filters to apply
            limit: Maximum number of permissions to return
            offset: Number of permissions to skip (for pagination)
            
        Returns:
            Dictionary containing:
            - permissions: List of permission dictionaries
            - total_count: Total number of permissions matching filters
            - limit: Applied limit
            - offset: Applied offset
            
        Raises:
            UserPermissionValidationError: If parameters are invalid
            UserPermissionNotFoundError: If database error occurs
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> # Get all permissions
            >>> result = perm_manager.read_user_permissions()
            >>> print(f"Found {result['total_count']} permissions")
            
            >>> # Get permissions with pagination
            >>> result = perm_manager.read_user_permissions(limit=10, offset=0)
            >>> print(f"Page 1: {len(result['permissions'])} permissions")
            
            >>> # Get permissions with filters
            >>> filters = {"is_active": True, "permission_type": "read"}
            >>> result = perm_manager.read_user_permissions(filters=filters)
        """
        try:
            # Validate inputs
            if limit is not None and (not isinstance(limit, int) or limit <= 0):
                raise UserPermissionValidationError("Limit must be a positive integer")
            
            if not isinstance(offset, int) or offset < 0:
                raise UserPermissionValidationError("Offset must be a non-negative integer")
            
            logger.debug(f"Reading user permissions with filters: {filters}, limit: {limit}, offset: {offset}")
            
            db = self._get_db_connection()
            # Read permissions with filters
            filter_dict = filters if filters else {}
            all_permissions = db.read(USER_PERMISSIONS_TABLE, filter_dict)
            
            # Convert to list of dictionaries
            permissions_list = [dict(permission._mapping) for permission in all_permissions]
            total_count = len(permissions_list)
            
            # Apply pagination if specified
            if limit is not None:
                end_index = offset + limit
                paginated_permissions = permissions_list[offset:end_index]
            else:
                paginated_permissions = permissions_list[offset:] if offset > 0 else permissions_list
            
            result = {
                'permissions': paginated_permissions,
                'total_count': total_count,
                'limit': limit,
                'offset': offset
            }
            
            logger.info(f"Retrieved {len(paginated_permissions)} user permissions out of {total_count} total")
            return result
                
        except UserPermissionValidationError:
            raise
        except SQLAlchemyReadError as e:
            logger.error(f"Database error reading user permissions: {e}")
            raise UserPermissionNotFoundError(f"Database error reading user permissions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error reading user permissions: {e}")
            raise UserPermissionNotFoundError(f"Unexpected error reading user permissions: {e}") from e

    def update_user_permission(self, permission_id: Any, update_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing user permission's information.
        
        Performs partial updates - only provided fields will be modified.
        Validates the permission exists before attempting the update.
        
        Args:
            permission_id: The unique identifier of the permission to update
            update_data: Dictionary containing fields to update
            
        Returns:
            Dictionary containing the updated permission data
            
        Raises:
            UserPermissionValidationError: If permission ID or update data is invalid
            UserPermissionNotFoundError: If permission doesn't exist
            UserPermissionUpdateError: If the update operation fails
            UserPermissionAlreadyExistsError: If update would create duplicate
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> # Update permission level only
            >>> update_data = {"permission_level": 3, "modified_by": 5}
            >>> updated_permission = perm_manager.update_user_permission(1, update_data)
            >>> print(updated_permission["permission_level"])
            3
            
            >>> # Update multiple fields
            >>> update_data = {
            ...     "permission_type": "write",
            ...     "is_active": True,
            ...     "notes": "Updated to write access"
            ... }
            >>> updated_permission = perm_manager.update_user_permission(1, update_data)
        """
        permission_id = self._validate_permission_id(permission_id)
        
        try:
            # Validate update data
            validated_update_data = UserPermissionUpdate(**update_data)
            # Remove None values from update data
            update_dict = {k: v for k, v in validated_update_data.model_dump().items() if v is not None}
            
            if not update_dict:
                raise UserPermissionValidationError("No valid fields provided for update")
            
            logger.debug(f"Updating user permission {permission_id} with data: {update_dict}")
            
            db = self._get_db_connection()
            # Check if permission exists and get current data
            current_permission = self._check_permission_exists(db, permission_id)
            
            # Check for unique constraints if key fields are being updated
            if any(field in update_dict for field in ['user_id', 'resource_id', 'permission_type']):
                user_id = update_dict.get('user_id', current_permission['user_id'])
                resource_id = update_dict.get('resource_id', current_permission['resource_id'])
                permission_type = update_dict.get('permission_type', current_permission['permission_type'])
                
                self._check_permission_uniqueness(
                    db, user_id, resource_id, permission_type, 
                    exclude_permission_id=permission_id
                )
            
            # Update the permission
            updated_permissions = db.update(USER_PERMISSIONS_TABLE, update_dict, {'id': permission_id})
            
            if not updated_permissions:
                raise UserPermissionUpdateError(f"Failed to update user permission {permission_id}")
            
            updated_permission = dict(updated_permissions[0]._mapping)
            logger.info(f"Successfully updated user permission for user {updated_permission.get('user_id', 'N/A')} (ID: {permission_id})")
            
            return updated_permission
                
        except (UserPermissionValidationError, UserPermissionNotFoundError, UserPermissionAlreadyExistsError):
            raise
        except SQLAlchemyUpdateError as e:
            logger.error(f"Database error updating user permission {permission_id}: {e}")
            raise UserPermissionUpdateError(f"Database error updating user permission: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error updating user permission {permission_id}: {e}")
            raise UserPermissionUpdateError(f"Unexpected error updating user permission: {e}") from e

    def delete_user_permission(self, permission_id: Any) -> Dict[str, Any]:
        """Delete a user permission by its ID.
        
        Args:
            permission_id: The unique identifier of the permission to delete
            
        Returns:
            Dictionary containing deletion results:
            - success: Boolean indicating if deletion was successful
            - permission_id: The ID of the deleted permission
            - message: Descriptive message about the operation
            
        Raises:
            UserPermissionValidationError: If permission ID is invalid
            UserPermissionNotFoundError: If permission doesn't exist
            UserPermissionDeleteError: If deletion fails
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> result = perm_manager.delete_user_permission(1)
            >>> print(result["success"])
            True
            >>> print(result["message"])
            User permission deleted successfully
        """
        permission_id = self._validate_permission_id(permission_id)
        
        try:
            logger.debug(f"Deleting user permission {permission_id}")
            
            db = self._get_db_connection()
            # Check if permission exists
            permission_data = self._check_permission_exists(db, permission_id)
            
            # Delete the permission
            deleted_count = db.delete(USER_PERMISSIONS_TABLE, {'id': permission_id})
            
            if deleted_count == 0:
                raise UserPermissionDeleteError(f"Failed to delete user permission {permission_id}")
            
            result = {
                'success': True,
                'permission_id': permission_id,
                'message': 'User permission deleted successfully'
            }
            
            logger.info(f"Successfully deleted user permission for user {permission_data.get('user_id', 'N/A')} (ID: {permission_id})")
            return result
                
        except (UserPermissionValidationError, UserPermissionNotFoundError):
            raise
        except SQLAlchemyDeleteError as e:
            logger.error(f"Database error deleting user permission {permission_id}: {e}")
            raise UserPermissionDeleteError(f"Database error deleting user permission: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error deleting user permission {permission_id}: {e}")
            raise UserPermissionDeleteError(f"Unexpected error deleting user permission: {e}") from e

    def get_permissions_by_user_id(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all permissions for a specific user.
        
        Args:
            user_id: The unique identifier of the user
            
        Returns:
            List of dictionaries containing permission data for the user
            
        Raises:
            UserPermissionValidationError: If user_id is invalid
            UserPermissionNotFoundError: If database error occurs
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> user_permissions = perm_manager.get_permissions_by_user_id(1)
            >>> print(f"User has {len(user_permissions)} permissions")
            >>> for permission in user_permissions:
            ...     print(f"{permission['permission_type']} on resource {permission['resource_id']}")
        """
        try:
            if not isinstance(user_id, int) or user_id <= 0:
                raise UserPermissionValidationError("User ID must be a positive integer")
            
            logger.debug(f"Retrieving permissions for user {user_id}")
            
            db = self._get_db_connection()
            permissions = db.read(USER_PERMISSIONS_TABLE, {'user_id': user_id})
            permissions_list = [dict(permission._mapping) for permission in permissions]
            
            logger.info(f"Found {len(permissions_list)} permissions for user {user_id}")
            return permissions_list
                
        except UserPermissionValidationError:
            raise
        except SQLAlchemyReadError as e:
            logger.error(f"Database error retrieving permissions for user {user_id}: {e}")
            raise UserPermissionNotFoundError(f"Database error retrieving user permissions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error retrieving permissions for user {user_id}: {e}")
            raise UserPermissionNotFoundError(f"Unexpected error retrieving user permissions: {e}") from e

    def get_permissions_by_resource_id(self, resource_id: int) -> List[Dict[str, Any]]:
        """Retrieve all permissions for a specific resource.
        
        Args:
            resource_id: The unique identifier of the resource
            
        Returns:
            List of dictionaries containing permission data for the resource
            
        Raises:
            UserPermissionValidationError: If resource_id is invalid
            UserPermissionNotFoundError: If database error occurs
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> resource_permissions = perm_manager.get_permissions_by_resource_id(10)
            >>> print(f"Resource has {len(resource_permissions)} permissions")
            >>> for permission in resource_permissions:
            ...     print(f"User {permission['user_id']} has {permission['permission_type']} access")
        """
        try:
            if not isinstance(resource_id, int) or resource_id <= 0:
                raise UserPermissionValidationError("Resource ID must be a positive integer")
            
            logger.debug(f"Retrieving permissions for resource {resource_id}")
            
            db = self._get_db_connection()
            permissions = db.read(USER_PERMISSIONS_TABLE, {'resource_id': resource_id})
            permissions_list = [dict(permission._mapping) for permission in permissions]
            
            logger.info(f"Found {len(permissions_list)} permissions for resource {resource_id}")
            return permissions_list
                
        except UserPermissionValidationError:
            raise
        except SQLAlchemyReadError as e:
            logger.error(f"Database error retrieving permissions for resource {resource_id}: {e}")
            raise UserPermissionNotFoundError(f"Database error retrieving resource permissions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error retrieving permissions for resource {resource_id}: {e}")
            raise UserPermissionNotFoundError(f"Unexpected error retrieving resource permissions: {e}") from e

    def search_user_permissions(self, search_term: str, search_fields: List[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """Search user permissions by term across specified fields.
        
        Args:
            search_term: Term to search for
            search_fields: List of fields to search in (default: ['permission_type', 'notes'])
            limit: Maximum number of results to return
            
        Returns:
            List of matching permission dictionaries, sorted by relevance
            
        Raises:
            UserPermissionValidationError: If search parameters are invalid
            UserPermissionNotFoundError: If database error occurs
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> # Search by default fields
            >>> results = perm_manager.search_user_permissions("read")
            >>> for permission in results:
            ...     print(f"Found: {permission['permission_type']} for user {permission['user_id']}")
            
            >>> # Search specific fields
            >>> results = perm_manager.search_user_permissions("admin", search_fields=["permission_type"], limit=5)
        """
        try:
            # Validate search parameters
            search_term, search_fields, limit = self._validate_search_params(search_term, search_fields, limit)
            
            logger.debug(f"Searching user permissions for '{search_term}' in fields: {search_fields}")
            
            db = self._get_db_connection()
            # Get all permissions
            all_permissions = db.read(USER_PERMISSIONS_TABLE)
            permissions_list = [dict(permission._mapping) for permission in all_permissions]
            
            # Filter and score results
            matching_permissions = []
            for permission_dict in permissions_list:
                score = self._calculate_relevance_score(permission_dict, search_term, search_fields)
                if score > 0:
                    permission_dict['_relevance_score'] = score
                    matching_permissions.append(permission_dict)
            
            # Sort by relevance and apply limit
            matching_permissions.sort(key=lambda x: x['_relevance_score'], reverse=True)
            
            # Remove the score field before returning
            result_permissions = []
            for permission in matching_permissions[:limit]:
                del permission['_relevance_score']
                result_permissions.append(permission)
                
                logger.info(f"Found {len(result_permissions)} permissions matching '{search_term}'")
                return result_permissions
                
        except UserPermissionValidationError:
            raise
        except SQLAlchemyReadError as e:
            logger.error(f"Database error during search: {e}")
            raise UserPermissionNotFoundError(f"Database error during search: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error during search: {e}")
            raise UserPermissionNotFoundError(f"Unexpected error during search: {e}") from e

    def _validate_search_params(self, search_term: str, search_fields: List[str], limit: int) -> Tuple[str, List[str], int]:
        """Validate and normalize search parameters (internal helper method)."""
        # Validate search term
        if not search_term or not isinstance(search_term, str) or not search_term.strip():
            raise UserPermissionValidationError("Search term must be a non-empty string")
        
        search_term = search_term.strip()
        
        # Validate and set default search fields
        if search_fields is None:
            search_fields = ['permission_type', 'notes']
        elif not isinstance(search_fields, list) or not search_fields:
            raise UserPermissionValidationError("Search fields must be a non-empty list")
        
        # Validate limit
        if not isinstance(limit, int) or limit <= 0:
            raise UserPermissionValidationError("Limit must be a positive integer")
        
        return search_term, search_fields, limit

    def _calculate_relevance_score(self, permission_dict: Dict[str, Any], search_term: str, search_fields: List[str]) -> float:
        """Calculate relevance score for search results (internal helper method)."""
        score = 0.0
        search_lower = search_term.lower()
        
        for field in search_fields:
            if field in permission_dict and permission_dict[field]:
                field_value = str(permission_dict[field]).lower()
                
                # Exact match gets highest score
                if search_lower == field_value:
                    score += 10.0
                # Starts with search term gets high score
                elif field_value.startswith(search_lower):
                    score += 5.0
                # Contains search term gets medium score
                elif search_lower in field_value:
                    score += 2.0
        
        return score

    def count_permissions(self, filters: Dict[str, Any] = None) -> int:
        """Count the total number of permissions matching the given filters.
        
        Args:
            filters: Optional dictionary of filters to apply
            
        Returns:
            Total count of permissions
            
        Raises:
            UserPermissionNotFoundError: If database error occurs
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> total_permissions = perm_manager.count_permissions()
            >>> print(f"Total permissions: {total_permissions}")
            
            >>> # Count active permissions only
            >>> active_permissions = perm_manager.count_permissions({'is_active': True})
            >>> print(f"Active permissions: {active_permissions}")
        """
        try:
            logger.debug(f"Counting permissions with filters: {filters}")
            
            db = self._get_db_connection()
            filter_dict = filters if filters else {}
            permissions = db.read(USER_PERMISSIONS_TABLE, filter_dict)
            count = len(permissions)
            
            logger.info(f"Counted {count} permissions")
            return count
                
        except SQLAlchemyReadError as e:
            logger.error(f"Database error counting permissions: {e}")
            raise UserPermissionNotFoundError(f"Error counting permissions: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error counting permissions: {e}")
            raise UserPermissionNotFoundError(f"Error counting permissions: {e}") from e

    def bulk_create_permissions(self, permissions_data: List[Dict[str, Any]], skip_duplicates: bool = False) -> Dict[str, Any]:
        """Create multiple user permissions in a single transaction.
        
        Args:
            permissions_data: List of permission dictionaries to create
            skip_duplicates: If True, skip existing permissions instead of raising error
            
        Returns:
            Dictionary with creation results including success count and any errors
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> permissions = [
            ...     {"user_id": 1, "resource_id": 10, "permission_type": "read", "granted_by": 5},
            ...     {"user_id": 2, "resource_id": 10, "permission_type": "write", "granted_by": 5}
            ... ]
            >>> result = perm_manager.bulk_create_permissions(permissions)
            >>> print(f"Created {result['created_count']} permissions")
        """
        if not permissions_data or not isinstance(permissions_data, list):
            raise UserPermissionValidationError("Permissions data must be a non-empty list")
        
        results = {
            "created_count": 0,
            "skipped_count": 0,
            "errors": [],
            "created_permissions": []
        }
        
        try:
            logger.debug(f"Bulk creating {len(permissions_data)} permissions")
            
            db = self._get_db_connection()
            for i, permission_data in enumerate(permissions_data):
                try:
                    validated_data = UserPermissionCreate(**permission_data)
                    validated_dict = validated_data.model_dump()
                    
                    # Check for existing permission if skip_duplicates is True
                    if skip_duplicates:
                        try:
                            self._check_permission_uniqueness(
                                db,
                                validated_data.user_id,
                                validated_data.resource_id,
                                validated_data.permission_type
                            )
                        except UserPermissionAlreadyExistsError:
                            results["skipped_count"] += 1
                            continue
                    
                    # Create the permission
                    created_permission = db.create(USER_PERMISSIONS_TABLE, validated_dict)
                    if created_permission:
                        results["created_count"] += 1
                        results["created_permissions"].append(dict(created_permission._mapping))
                    else:
                        results["errors"].append(f"Failed to create permission at index {i}")
                        
                except Exception as exc:
                    error_msg = f"Error at index {i}: {str(exc)}"
                    results["errors"].append(error_msg)
            
            logger.info(f"Bulk create completed: {results['created_count']} created, {results['skipped_count']} skipped, {len(results['errors'])} errors")
            return results
                
        except SQLAlchemyInsertError as e:
            logger.error(f"Database error during bulk create: {e}")
            raise UserPermissionCreateError(f"Bulk create failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error during bulk create: {e}")
            raise UserPermissionCreateError(f"Bulk create failed: {str(e)}") from e

    def bulk_delete_permissions(self, permission_ids: List[int]) -> Dict[str, Any]:
        """Delete multiple user permissions in a single transaction.
        
        Args:
            permission_ids: List of permission IDs to delete
            
        Returns:
            Dictionary with deletion results including success count and any errors
            
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> result = perm_manager.bulk_delete_permissions([1, 2, 3])
            >>> print(f"Deleted {result['deleted_count']} permissions")
        """
        if not permission_ids or not isinstance(permission_ids, list):
            raise UserPermissionValidationError("Permission IDs must be a non-empty list")
        
        results = {
            "deleted_count": 0,
            "errors": []
        }
        
        try:
            logger.debug(f"Bulk deleting {len(permission_ids)} permissions")
            
            db = self._get_db_connection()
            for permission_id in permission_ids:
                try:
                    validated_id = self._validate_permission_id(permission_id)
                    
                    # Check if permission exists
                    self._check_permission_exists(db, validated_id)
                    
                    # Delete the permission
                    deleted_count = db.delete(USER_PERMISSIONS_TABLE, {'id': validated_id})
                    if deleted_count > 0:
                        results["deleted_count"] += 1
                    else:
                        results["errors"].append(f"Failed to delete permission {validated_id}")
                        
                except Exception as exc:
                    error_msg = f"Error deleting permission {permission_id}: {str(exc)}"
                    results["errors"].append(error_msg)
                
                logger.info(f"Bulk delete completed: {results['deleted_count']} deleted, {len(results['errors'])} errors")
                return results
                
        except SQLAlchemyDeleteError as e:
            logger.error(f"Database error during bulk delete: {e}")
            raise UserPermissionDeleteError(f"Bulk delete failed: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected error during bulk delete: {e}")
            raise UserPermissionDeleteError(f"Bulk delete failed: {str(e)}") from e

    def close(self) -> None:
        """
        Close method for backward compatibility.
        
        Note: In singleton mode, the database connection is shared and persistent.
        This method exists for backward compatibility but doesn't actually close
        the connection as it's managed by the singleton.
        
        Example:
            >>> perm_manager = UserPermissionManager()
            >>> # ... perform operations ...
            >>> perm_manager.close()  # No-op in singleton mode
        """
        # No-op in singleton mode - connection is managed globally
        pass

    def __enter__(self) -> 'UserPermissionManager':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - connection is persistent in singleton mode."""
        # No cleanup needed as connection is managed by singleton
        pass


# Backward compatibility functions - delegates to UserPermissionManager class
# These functions maintain the existing functional API while using the new OOP implementation


def create_user_permission(permission_data: Dict[str, Any]) -> Dict[str, Any]:
    """Functional interface for creating a user permission.
    
    This function provides a simple interface that maintains backward compatibility
    while using the UserPermissionManager class internally.
    
    Args:
        permission_data: Dictionary containing permission information
        
    Returns:
        Dictionary containing the created permission data
        
    Example:
        >>> permission = create_user_permission({
        ...     "user_id": 1, "resource_id": 10, "permission_type": "read", "granted_by": 5
        ... })
        >>> print(permission["permission_type"])
        read
    """
    with UserPermissionManager() as manager:
        return manager.create_user_permission(permission_data)


def read_user_permission(permission_id: int) -> Dict[str, Any]:
    """Functional interface for retrieving a user permission by ID."""
    with UserPermissionManager() as manager:
        return manager.read_user_permission(permission_id)


def update_user_permission(permission_id: int, update_data: Dict[str, Any]) -> Dict[str, Any]:
    """Functional interface for updating a user permission."""
    with UserPermissionManager() as manager:
        return manager.update_user_permission(permission_id, update_data)


def delete_user_permission(permission_id: int) -> Dict[str, Any]:
    """Functional interface for deleting a user permission."""
    with UserPermissionManager() as manager:
        return manager.delete_user_permission(permission_id)


def read_user_permissions(filters: Dict[str, Any] = None, limit: int = None, offset: int = 0) -> Dict[str, Any]:
    """Functional interface for retrieving multiple user permissions."""
    with UserPermissionManager() as manager:
        return manager.read_user_permissions(filters, limit, offset)


def get_permissions_by_user_id(user_id: int) -> List[Dict[str, Any]]:
    """Functional interface for retrieving permissions by user ID."""
    with UserPermissionManager() as manager:
        return manager.get_permissions_by_user_id(user_id)


def get_permissions_by_resource_id(resource_id: int) -> List[Dict[str, Any]]:
    """Functional interface for retrieving permissions by resource ID."""
    with UserPermissionManager() as manager:
        return manager.get_permissions_by_resource_id(resource_id)
