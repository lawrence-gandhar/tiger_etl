"""Constants for user permissions management operations.

This module contains constant values used throughout the user permissions management system
including error messages, table names, and permission types.
"""

# Error messages
USER_PERMISSION_ALREADY_EXISTS: str = "User permission with this combination already exists."
USER_PERMISSION_NOT_FOUND: str = "User permission not found."
INVALID_PERMISSION_TYPE: str = "Invalid permission type."
USER_NOT_FOUND_FOR_PERMISSION: str = "User not found for permission assignment."
RESOURCE_NOT_FOUND: str = "Resource not found for permission assignment."

# Table names
USER_PERMISSIONS_TABLE: str = "user_permissions"
USERS_TABLE: str = "users"
RESOURCES_TABLE: str = "resources"

# Permission types
PERMISSION_TYPES = ["read", "write", "delete", "admin", "execute", "view", "edit", "create"]

# Permission levels
PERMISSION_LEVELS = {
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4
}

# Default permission settings
DEFAULT_PERMISSION_LEVEL: int = 1
DEFAULT_PERMISSION_TYPE: str = "read"
DEFAULT_IS_ACTIVE: bool = True
