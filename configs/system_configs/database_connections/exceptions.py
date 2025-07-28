"""
Custom exceptions for handling CRUD operations in Redis and other database modules.
"""

class RedisConnectionError(Exception):
    """Raised when a Redis connection fails."""
    pass

class RedisInsertError(Exception):
    """Raised when a Redis insert/set operation fails."""
    pass

class RedisReadError(Exception):
    """Raised when a Redis read/get operation fails."""
    pass

class RedisUpdateError(Exception):
    """Raised when a Redis update operation fails."""
    pass

class RedisDeleteError(Exception):
    """Raised when a Redis delete operation fails."""
    pass

class RedisZSetError(Exception):
    """Raised when a Redis ZSET operation fails."""
    pass

class DatabaseConnectionError(Exception):
    """Raised when a database connection fails."""
    pass

class DatabaseInsertError(Exception):
    """Raised when an insert operation fails."""
    pass

class DatabaseReadError(Exception):
    """Raised when a read operation fails."""
    pass

class DatabaseUpdateError(Exception):
    """Raised when an update operation fails."""
    pass

class DatabaseDeleteError(Exception):
    """Raised when a delete operation fails."""
    pass

class DatabaseTransactionError(Exception):
    """Raised when a transaction fails."""
    pass

# For SQLAlchemy-specific exceptions in pg_db
class SQLAlchemyConnectionError(DatabaseConnectionError):
    """Raised when SQLAlchemy fails to connect to the database."""
    pass

class SQLAlchemyCRUDException(Exception):
    """Base exception for SQLAlchemy CRUD errors."""
    pass

class SQLAlchemyInsertError(SQLAlchemyCRUDException):
    """Raised when SQLAlchemy insert fails."""
    pass

class SQLAlchemyReadError(SQLAlchemyCRUDException):
    """Raised when SQLAlchemy read fails."""
    pass

class SQLAlchemyUpdateError(SQLAlchemyCRUDException):
    """Raised when SQLAlchemy update fails."""
    pass

class SQLAlchemyDeleteError(SQLAlchemyCRUDException):
    """Raised when SQLAlchemy delete fails."""
    pass