"""Constants for user group management module.

This module contains all constants used in user group management operations,
including table names and error messages.
"""

# Table names - using constants for better maintainability
USER_GROUPS_TABLE = 'user_groups'
USER_GROUP_MAPPER_TABLE = 'user_group_mapper'

# Error message constants
MAPPING_ID_POSITIVE_ERROR = "Mapping ID must be a positive integer"
MAPPING_ID_INTEGER_ERROR = "Mapping ID must be a valid integer"