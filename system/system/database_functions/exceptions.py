"""Custom exceptions for database functions.

This module contains custom exceptions for database operations
in the database_functions package.
"""


class DatabaseFunctionError(Exception):
    """Base exception for database function operations."""
    pass


class UserGroupManagementError(DatabaseFunctionError):
    """Raised when user group management operations fail."""
    pass


class UserGroupDeleteError(UserGroupManagementError):
    """Raised when user group deletion fails."""
    pass


class UserGroupValidationError(UserGroupManagementError):
    """Raised when user group validation fails."""
    pass


class UserGroupMapperError(UserGroupManagementError):
    """Raised when user group mapper operations fail."""
    pass


class UserGroupNotFoundError(UserGroupManagementError):
    """Raised when a user group is not found."""
    pass


class UserGroupCreateError(UserGroupManagementError):
    """Raised when user group creation fails."""
    pass


class UserGroupUpdateError(UserGroupManagementError):
    """Raised when user group update fails."""
    pass


class UserGroupInUseError(UserGroupManagementError):
    """Raised when attempting to delete a user group that is in use."""
    pass


class TransactionRollbackError(DatabaseFunctionError):
    """Raised when a database transaction rollback fails."""
    pass


class UserAlreadyExistsException(DatabaseFunctionError):
    """Raised when a user with the given unique field already exists."""
    pass


class UserManagementError(DatabaseFunctionError):
    """Base exception for user management operations."""
    pass


class UserNotFoundError(UserManagementError):
    """Raised when a user is not found."""
    pass


class UserCreateError(UserManagementError):
    """Raised when user creation fails."""
    pass


class UserUpdateError(UserManagementError):
    """Raised when user update fails."""
    pass


class UserDeleteError(UserManagementError):
    """Raised when user deletion fails."""
    pass


class UserValidationError(UserManagementError):
    """Raised when user validation fails."""
    pass