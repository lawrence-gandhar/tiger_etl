"""Constants for user permissions management models.

This module contains constants specific to user permissions management
including validation error messages, permission types, and field constraints.
"""

from typing import Set

# Permission types
VALID_PERMISSION_TYPES: Set[str] = {
    'full_access',
    'read_access', 
    'write_access',
    'create_access',
    'edit_access',
    'delete_access',
    'execute_access',
    'drop_access',
    'view_access',
    'insert_access',
    'update_access'
}

# Permission field names (for iteration and validation)
PERMISSION_FIELDS = [
    'full_access',
    'read_access',
    'write_access', 
    'create_access',
    'edit_access',
    'delete_access',
    'execute_access',
    'drop_access',
    'view_access',
    'insert_access',
    'update_access'
]

# Error messages for user permissions validation
PERMISSION_TYPE_ERROR = "Invalid permission type. Must be one of: {types}"
USER_ID_ERROR = "User ID must be a positive integer"
DUPLICATE_PERMISSIONS_ERROR = "Duplicate permission types are not allowed in bulk update"
NO_PERMISSIONS_PROVIDED_ERROR = "At least one permission must be provided"
INVALID_USER_REFERENCE_ERROR = "Invalid user reference provided"

# Default permission values
DEFAULT_PERMISSION_VALUE = False

# Permission categories for logical grouping
READ_PERMISSIONS = {'read_access', 'view_access'}
WRITE_PERMISSIONS = {'write_access', 'create_access', 'edit_access', 'insert_access', 'update_access'}
DESTRUCTIVE_PERMISSIONS = {'delete_access', 'drop_access'}
EXECUTION_PERMISSIONS = {'execute_access'}
ADMIN_PERMISSIONS = {'full_access'}

# All permission categories
PERMISSION_CATEGORIES = {
    'read': READ_PERMISSIONS,
    'write': WRITE_PERMISSIONS,
    'destructive': DESTRUCTIVE_PERMISSIONS,
    'execution': EXECUTION_PERMISSIONS,
    'admin': ADMIN_PERMISSIONS
}

# Permission hierarchy (higher level permissions may imply lower level ones)
PERMISSION_HIERARCHY = {
    'full_access': VALID_PERMISSION_TYPES - {'full_access'},  # Full access implies all others
    'write_access': {'read_access', 'view_access'},  # Write implies read
    'edit_access': {'read_access', 'view_access'},   # Edit implies read
    'update_access': {'read_access', 'view_access'}, # Update implies read
    'insert_access': {'read_access', 'view_access'}, # Insert implies read
    'delete_access': {'read_access', 'view_access'}, # Delete implies read
    'drop_access': {'read_access', 'view_access'},   # Drop implies read
    'execute_access': {'read_access', 'view_access'}, # Execute implies read
}

# Field constraints
USER_ID_MIN_VALUE = 1
PERMISSION_FIELD_MAX_LENGTH = 50

# Database related constants
USER_PERMISSIONS_TABLE_NAME = 'user_permissions'
USER_PERMISSIONS_FOREIGN_KEY = 'users.id'
USER_PERMISSIONS_CASCADE_DELETE = 'CASCADE'

# Validation constants
MIN_BULK_PERMISSIONS = 1
MAX_BULK_PERMISSIONS = len(VALID_PERMISSION_TYPES)

# Query defaults
DEFAULT_GRANTED_ONLY = False
DEFAULT_INCLUDE_INACTIVE_USERS = False

# Field validation constants
PERMISSION_DESCRIPTION_MAX_LENGTH = 255
PERMISSION_NAME_MAX_LENGTH = 50

# Bulk operation limits
MAX_PERMISSIONS_PER_USER = 20
MAX_USERS_PER_BULK_OPERATION = 100

# Permission level constants (for priority/hierarchy)
PERMISSION_LEVELS = {
    'full_access': 10,      # Highest level
    'execute_access': 8,    # High level
    'drop_access': 7,       # High destructive
    'delete_access': 6,     # Destructive
    'write_access': 5,      # Modify data
    'update_access': 4,     # Modify existing
    'edit_access': 3,       # Modify existing
    'create_access': 3,     # Create new
    'insert_access': 3,     # Create new
    'read_access': 2,       # Read data
    'view_access': 1,       # View only
}

# Permission groups for mass operations
BASIC_PERMISSIONS = {'read_access', 'view_access'}
STANDARD_PERMISSIONS = {'read_access', 'view_access', 'write_access', 'create_access'}
ADVANCED_PERMISSIONS = {'read_access', 'view_access', 'write_access', 'create_access', 'edit_access', 'update_access', 'delete_access'}
ADMIN_LEVEL_PERMISSIONS = VALID_PERMISSION_TYPES

# Permission templates for common roles
PERMISSION_TEMPLATES = {
    'viewer': {'read_access', 'view_access'},
    'editor': {'read_access', 'view_access', 'write_access', 'edit_access', 'update_access'},
    'contributor': {'read_access', 'view_access', 'write_access', 'create_access', 'insert_access'},
    'moderator': {'read_access', 'view_access', 'write_access', 'edit_access', 'update_access', 'delete_access'},
    'admin': VALID_PERMISSION_TYPES,
}

# Validation messages for specific permission operations
PERMISSION_GRANT_SUCCESS = "Permission '{permission}' granted successfully to user {user_id}"
PERMISSION_REVOKE_SUCCESS = "Permission '{permission}' revoked successfully from user {user_id}"
BULK_PERMISSION_SUCCESS = "{count} permissions updated successfully for user {user_id}"
PERMISSION_ALREADY_EXISTS = "Permission '{permission}' already granted to user {user_id}"
PERMISSION_NOT_EXISTS = "Permission '{permission}' not found for user {user_id}"

# Status constants
PERMISSION_STATUS_ACTIVE = "active"
PERMISSION_STATUS_INACTIVE = "inactive"
PERMISSION_STATUS_PENDING = "pending"
PERMISSION_STATUS_REVOKED = "revoked"

VALID_PERMISSION_STATUSES = {
    PERMISSION_STATUS_ACTIVE,
    PERMISSION_STATUS_INACTIVE,
    PERMISSION_STATUS_PENDING,
    PERMISSION_STATUS_REVOKED
}

# API response constants
PERMISSIONS_RESPONSE_LIMIT = 100
DEFAULT_PERMISSIONS_PAGE_SIZE = 20
MAX_PERMISSIONS_PAGE_SIZE = 500
