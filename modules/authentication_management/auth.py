"""Authentication management module for user signup and login operations.

This module provides authentication functions that integrate with the user management
system to handle user registration, login, and password operations.
"""

from typing import Dict, Any, Optional
import hashlib
import re
from email_validator import EmailNotValidError, validate_email

from system.system.database_functions.user_management.user_management import UserManager
from system.system.database_functions.user_management.user_management_constants import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_UPPERCASE_PATTERN,
    PASSWORD_LOWERCASE_PATTERN,
    PASSWORD_DIGIT_PATTERN,
    PASSWORD_SPECIAL_PATTERN,
)
from system.system.database_functions.exceptions import (
    UserAlreadyExistsException,
    UserCreateError
)


# Constants for error messages
USER_ALREADY_EXISTS_ERROR = "An account with this email address already exists"


class AuthenticationError(Exception):
    """Custom exception for authentication-related errors."""
    pass


class SignupError(Exception):
    """Custom exception for signup-related errors."""
    pass


def _hash_password(password: str) -> str:
    """Hash a password using SHA-256.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        str: The hashed password as a hexadecimal string
    """
    return hashlib.sha256(password.encode()).hexdigest()


def _validate_email_format(email: str) -> str:
    """Validate email format using email-validator library.
    
    Args:
        email: The email address to validate
        
    Returns:
        str: The normalized email address
        
    Raises:
        SignupError: If email format is invalid
    """
    try:
        # Validate and get normalized result
        # Use check_deliverability=False to skip domain validation for testing
        validated_email = validate_email(email, check_deliverability=False)
        return validated_email.email
    except EmailNotValidError as e:
        raise SignupError(f"Invalid email format: {str(e)}")


def _validate_password_strength(password: str) -> None:
    """Validate password strength requirements.
    
    Password must contain:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Args:
        password: The password to validate
        
    Raises:
        SignupError: If password doesn't meet strength requirements
    """
    if len(password) < PASSWORD_MIN_LENGTH:
        raise SignupError("Password must be at least 8 characters long")
    
    if not re.search(PASSWORD_UPPERCASE_PATTERN, password):
        raise SignupError("Password must contain at least one uppercase letter")
    
    if not re.search(PASSWORD_LOWERCASE_PATTERN, password):
        raise SignupError("Password must contain at least one lowercase letter")
    
    if not re.search(PASSWORD_DIGIT_PATTERN, password):
        raise SignupError("Password must contain at least one digit")
    
    if not re.search(PASSWORD_SPECIAL_PATTERN, password):
        raise SignupError("Password must contain at least one special character")





def signup_user(email: str, password: str, confirm_password: str, 
                first_name: Optional[str] = None, last_name: Optional[str] = None) -> Dict[str, Any]:
    """Register a new user account.
    
    This function handles the complete user signup process including validation,
    password hashing, and database storage using the UserManager.
    
    Args:
        email: User's email address (will be used as username)
        password: User's plain text password
        confirm_password: Password confirmation
        first_name: Optional first name
        last_name: Optional last name
        
    Returns:
        Dict[str, Any]: Dictionary containing user information (without password)
        
    Raises:
        SignupError: If validation fails or signup process encounters an error
        
    Example:
        >>> user = signup_user(
        ...     email="john@example.com",
        ...     password="SecurePass123!",
        ...     confirm_password="SecurePass123!",
        ...     first_name="John",
        ...     last_name="Doe"
        ... )
        >>> print(user["username"])
        john@example.com
    """
    try:
        # Validate input parameters
        if not email or not email.strip():
            raise SignupError("Email address is required")
        if not password:
            raise SignupError("Password is required")
        if not confirm_password:
            raise SignupError("Password confirmation is required")
        if password != confirm_password:
            raise SignupError("Passwords do not match")
            
        # Validate email format and password strength
        normalized_email = _validate_email_format(email.strip().lower())
        _validate_password_strength(password)
        
        # Prepare user data for creation
        user_data = {
            "username": normalized_email,  # Use email as username
            "passwd": _hash_password(password),
            "first_name": first_name.strip() if first_name else None,
            "last_name": last_name.strip() if last_name else None,
            "is_active": True
        }
        
        # Create user using UserManager (handles duplicate checking internally)
        with UserManager() as user_manager:
            created_user = user_manager.create_user(user_data)
                
        # Remove password from response for security
        return {k: v for k, v in created_user.items() if k != "passwd"}
        
    except SignupError:
        # Re-raise SignupError as-is
        raise
    except UserAlreadyExistsException:
        raise SignupError(USER_ALREADY_EXISTS_ERROR)
    except UserCreateError as e:
        raise SignupError(f"Failed to create user account: {str(e)}")
    except Exception as e:
        raise SignupError(f"Unexpected error during signup: {str(e)}")


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with email and password.
    
    Args:
        email: User's email address
        password: User's plain text password
        
    Returns:
        Optional[Dict[str, Any]]: User information if authentication successful, None otherwise
        
    Raises:
        AuthenticationError: If authentication process encounters an error
        
    Example:
        >>> user = authenticate_user("john@example.com", "SecurePass123!")
        >>> if user:
        ...     print(f"Welcome {user['first_name']}!")
        ... else:
        ...     print("Invalid credentials")
    """
    try:
        if not email or not password:
            return None
            
        # Normalize email and hash password
        normalized_email = email.strip().lower()
        hashed_password = _hash_password(password)
        
        # Get user and validate in one operation
        with UserManager() as user_manager:
            user = user_manager.get_user_by_email(normalized_email)
            
            if (user and 
                user.get("passwd") == hashed_password and 
                user.get("is_active", False)):
                # Remove password from response for security
                return {k: v for k, v in user.items() if k != "passwd"}
                
        return None
        
    except Exception as e:
        raise AuthenticationError(f"Authentication error: {str(e)}")



