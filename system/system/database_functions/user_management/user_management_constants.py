"""Application constants.

This module contains constant values used throughout the application,
including error messages, validation patterns, and configuration values.
"""

# User validation error messages
USERNAME_EMPTY_ERROR = "Email address cannot be empty"
USERNAME_FORMAT_ERROR = "Please enter a valid email address"
USERNAME_START_ERROR = "Please enter a valid email address"
PASSWORD_LENGTH_ERROR = "Password must be at least 8 characters long"
PASSWORD_UPPERCASE_ERROR = "Password must contain at least one uppercase letter"
PASSWORD_LOWERCASE_ERROR = "Password must contain at least one lowercase letter"
PASSWORD_DIGIT_ERROR = "Password must contain at least one digit"
PASSWORD_SPECIAL_ERROR = "Password must contain at least one special character"
PASSWORD_EMPTY_ERROR = "Password cannot be empty"
NAME_FORMAT_ERROR = "Names can only contain letters, spaces, hyphens, and apostrophes"

# User validation regex patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]+$'  # Legacy pattern, use EMAIL_PATTERN for username
NAME_PATTERN = r"^[a-zA-Z\s\-']+$"
PASSWORD_UPPERCASE_PATTERN = r'[A-Z]'
PASSWORD_LOWERCASE_PATTERN = r'[a-z]'
PASSWORD_DIGIT_PATTERN = r'\d'
PASSWORD_SPECIAL_PATTERN = r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]'

# User field constraints (updated for email-as-username)
USERNAME_MIN_LENGTH = 5  # Minimum email length
USERNAME_MAX_LENGTH = 254  # Maximum email length per RFC standards
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 255
NAME_MAX_LENGTH = 50

# Default values
DEFAULT_USER_ACTIVE_STATUS = True

# Database table names
USERS_TABLE = "users"

# User operation error messages
USER_ALREADY_EXISTS = "A user with this email already exists"
USER_NOT_FOUND = "User not found"
USER_CREATE_ERROR = "Failed to create user"
USER_UPDATE_ERROR = "Failed to update user"
USER_DELETE_ERROR = "Failed to delete user"
