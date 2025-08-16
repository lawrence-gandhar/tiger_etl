import hashlib
import re

from system.system.database_functions.user_management.user_management_constants import (
    PASSWORD_MIN_LENGTH,
    PASSWORD_UPPERCASE_PATTERN,
    PASSWORD_LOWERCASE_PATTERN,
    PASSWORD_DIGIT_PATTERN,
    PASSWORD_SPECIAL_PATTERN,
)

from modules.security_management.exceptions import (
   SignupError
)

from email_validator import EmailNotValidError, validate_email


# --------------------
# Utility functions
# --------------------
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def validate_email_format(email: str) -> str:
    try:
        validated_email = validate_email(email, check_deliverability=False)
        return validated_email.email
    except EmailNotValidError as e:
        raise SignupError(f"Invalid email format: {str(e)}")


def validate_password_strength(password: str) -> None:
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
