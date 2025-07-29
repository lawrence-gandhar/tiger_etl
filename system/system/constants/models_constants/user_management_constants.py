"""Application constants.

This module contains constant values used throughout the application,
including error messages, validation patterns, and configuration values.
"""

# User validation error messages
USERNAME_EMPTY_ERROR = "Username cannot be empty"
USERNAME_FORMAT_ERROR = "Username can only contain letters, numbers, underscores, and hyphens"
USERNAME_START_ERROR = "Username cannot start with a number"
PASSWORD_LENGTH_ERROR = "Password must be at least 8 characters long"
PASSWORD_UPPERCASE_ERROR = "Password must contain at least one uppercase letter"
PASSWORD_LOWERCASE_ERROR = "Password must contain at least one lowercase letter"
PASSWORD_DIGIT_ERROR = "Password must contain at least one digit"
PASSWORD_SPECIAL_ERROR = "Password must contain at least one special character"
PASSWORD_EMPTY_ERROR = "Password cannot be empty"
NAME_FORMAT_ERROR = "Names can only contain letters, spaces, hyphens, and apostrophes"

# User validation regex patterns
USERNAME_PATTERN = r'^[a-zA-Z0-9_-]+$'
NAME_PATTERN = r"^[a-zA-Z\s\-']+$"
PASSWORD_UPPERCASE_PATTERN = r'[A-Z]'
PASSWORD_LOWERCASE_PATTERN = r'[a-z]'
PASSWORD_DIGIT_PATTERN = r'\d'
PASSWORD_SPECIAL_PATTERN = r'[!@#$%^&*()_+\-=\[\]{};:"\\|,.<>\/?]'

# User field constraints
USERNAME_MIN_LENGTH = 3
USERNAME_MAX_LENGTH = 50
PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 255
NAME_MAX_LENGTH = 50

# Default values
DEFAULT_USER_ACTIVE_STATUS = True
