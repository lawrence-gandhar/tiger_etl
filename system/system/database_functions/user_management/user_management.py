from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from contextlib import contextmanager
from system.system.database_connections.pg_db import get_session
from system.system.database_functions.exceptions import (
    NotFoundException, DatabaseException, UserAlreadyExistsException
)
from .constants import USER_ALREADY_EXISTS, USER_NOT_FOUND
from .validations import UserCreate, UserUpdate, validate_user_id
from system.system.models.user_management import User

@contextmanager
def get_db_connection():
    """Provide a transactional scope around a series of operations."""
    session: Session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()

def create_user(user_data: dict) -> User:
    """Create a new user in the database."""
    validated_data = UserCreate(**user_data)
    try:
        with get_db_connection() as session:
            if session.query(User).filter_by(email=validated_data.email).first():
                raise UserAlreadyExistsException(USER_ALREADY_EXISTS)
            user = User(**validated_data.dict())
            session.add(user)
            session.flush()
            session.refresh(user)
            return user
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def get_user_by_id(user_id: int) -> User:
    """Retrieve a user by ID."""
    validate_user_id(user_id)
    try:
        with get_db_connection() as session:
            user = session.get(User, user_id)
            if not user:
                raise NotFoundException(USER_NOT_FOUND)
            return user
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def update_user(user_id: int, update_data: dict) -> User:
    """Update an existing user."""
    validate_user_id(user_id)
    validated_data = UserUpdate(**update_data)
    try:
        with get_db_connection() as session:
            user = session.get(User, user_id)
            if not user:
                raise NotFoundException(USER_NOT_FOUND)
            for key, value in validated_data.dict(exclude_unset=True).items():
                setattr(user, key, value)
            session.flush()
            session.refresh(user)
            return user
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def delete_user(user_id: int) -> None:
    """Delete a user by ID."""
    validate_user_id(user_id)
    try:
        with get_db_connection() as session:
            user = session.get(User, user_id)
            if not user:
                raise NotFoundException(USER_NOT_FOUND)
            session.delete(user)
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))
    try:
        with get_db_connection() as session:
            user = session.query(User).get(user_id)
            if not user:
                raise NotFoundException(USER_NOT_FOUND)
            session.delete(user)
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def delete_all_users(user_ids: list[int]) -> int:
    """
    Delete multiple users by their IDs.
    Returns the number of users deleted.
    """
    if not user_ids:
        return 0
    for user_id in user_ids:
        validate_user_id(user_id)
    try:
        with get_db_connection() as session:
            users = session.query(User).filter(User.id.in_(user_ids)).all()
            deleted_count = len(users)
            for user in users:
                session.delete(user)
            return deleted_count
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def get_users(limit: int = 100, offset: int = 0, search: str = None) -> list[User]:
    """
    Retrieve users with optional limit, offset, and search by name or email.
    """
    try:
        with get_db_connection() as session:
            query = session.query(User)
            if search:
                search_pattern = f"%{search}%"
                query = query.filter(
                    (User.name.ilike(search_pattern)) | (User.email.ilike(search_pattern))
                )
            users = query.offset(offset).limit(limit).all()
            return users
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))

def truncate_and_reset_identity_user_table() -> None:
    """
    Truncate the user table and reset its identity/auto-increment counter.
    """
    try:
        with get_db_connection() as session:
            session.execute(f"TRUNCATE TABLE {User.__tablename__} RESTART IDENTITY CASCADE;")
    except SQLAlchemyError as exc:
        raise DatabaseException(str(exc))
