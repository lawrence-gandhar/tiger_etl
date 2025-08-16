"""Authentication management module for user signup and login operations."""

from typing import Dict, Any, Optional


from system.system.database_functions.user_management.user_management import UserManager

from system.system.database_functions.exceptions import (
    UserAlreadyExistsException,
    UserCreateError,
)

from modules.security_management.exceptions import (
    AuthenticationError, SignupError
)

from modules.security_management.constants import USER_ALREADY_EXISTS_ERROR

from modules.security_management.passwords import (
    hash_password as _hash_password,
    validate_email_format as _validate_email_format,
    validate_password_strength as _validate_password_strength 
)    


# --------------------
# Main functions
# --------------------
def signup_user(
    email: str,
    password: str,
    confirm_passwd: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Register a new user account."""
    try:
        if not email or not email.strip():
            raise SignupError("Email address is required")
        if not password:
            raise SignupError("Password is required")
        if not confirm_passwd:
            raise SignupError("Password confirmation is required")
        if password != confirm_passwd:
            raise SignupError("Passwords do not match")

        normalized_email = _validate_email_format(email.strip().lower())
        _validate_password_strength(password)

        user_data = {
            "username": normalized_email,
            "passwd": _hash_password(password),
            "confirm_passwd" : _hash_password(confirm_passwd),
            "first_name": first_name.strip() if first_name else None,
            "last_name": last_name.strip() if last_name else None,
            "is_active": True,
        }

        with UserManager() as user_manager:
            created_user = user_manager.create_user(user_data)

        return {k: v for k, v in created_user.items() if k != "passwd"}

    except SignupError:
        raise
    except UserAlreadyExistsException:
        raise SignupError(USER_ALREADY_EXISTS_ERROR)
    except UserCreateError as e:
        raise SignupError(f"Failed to create user account: {str(e)}")
    except Exception as e:
        raise SignupError(f"Unexpected error during signup: {str(e)}")


def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Authenticate a user with email and password."""
    try:
        if not email or not password:
            return None

        normalized_email = email.strip().lower()
        hashed_password = _hash_password(password)

        with UserManager() as user_manager:
            user = user_manager.get_user_by_email(normalized_email)
            if (
                user
                and user.get("passwd") == hashed_password
                and user.get("is_active", False)
            ):
                return {k: v for k, v in user.items() if k != "passwd"}

        return None

    except Exception as e:
        raise AuthenticationError(f"Authentication error: {str(e)}")
