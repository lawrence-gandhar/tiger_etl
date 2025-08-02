"""Constants for session management operations.

This module contains all constants used by the session management system
including table names, error messages, validation messages, and default values.
"""

# Database table names
USER_SESSIONS_TABLE = 'user_sessions'

# Error messages
SESSION_NOT_FOUND = "Session not found"
SESSION_ALREADY_EXISTS = "Session with this session_id already exists"
INVALID_USER_ID = "User ID must be a positive integer"
INVALID_SESSION_ID = "Session ID cannot be empty"

# Validation messages
SESSION_ID_NON_EMPTY_STRING = "Session ID must be a non-empty string"
IP_ADDRESS_NON_EMPTY_STRING = "IP address must be a non-empty string"
ACTIVE_SESSION_NOT_FOUND = "Active session not found"

# Default values
DEFAULT_SESSION_PREFIX = "sess"
DEFAULT_SESSIONS_LIMIT = 100
DEFAULT_INACTIVE_HOURS = 24

# Session field constraints
ALLOWED_UPDATE_FIELDS = {
    'user_id', 'session_id', 'login_datetime', 'logout_datetime', 
    'is_active', 'ip_address', 'user_agent', 'device_info', 
    'last_activity', 'session_duration'
}

# Pydantic validation constants
DESCRIPTION_UNIQUE_SESSION_IDENTIFIER = "Unique session identifier"
DESCRIPTION_CLIENT_USER_AGENT_STRING = "Client user agent string"
DESCRIPTION_DEVICE_INFORMATION = "Device information"
EXAMPLE_WINDOWS_CHROME_DEVICE = "Windows 10, Chrome Browser"
EXAMPLE_DATETIME_ISO = "2024-01-01T12:00:00Z"

# Validation error messages
ERROR_SESSION_ID_EMPTY = "Session ID cannot be empty or whitespace"
ERROR_SESSION_ID_INVALID_CHARACTERS = "Session ID can only contain alphanumeric characters, hyphens, and underscores"
ERROR_INVALID_IP_ADDRESS_FORMAT = "Invalid IP address format"

# Additional validation messages
VALIDATION_MESSAGES = {
    'session_data_not_dict': "Session data must be a dictionary",
    'user_id_required': "user_id is required",
    'session_id_required': "session_id is required",
    'session_id_positive_int': "Session ID must be a positive integer",
    'session_id_non_empty_string': SESSION_ID_NON_EMPTY_STRING,
    'ip_address_non_empty_string': IP_ADDRESS_NON_EMPTY_STRING,
    'active_session_not_found': ACTIVE_SESSION_NOT_FOUND
}