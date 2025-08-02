"""
PostgreSQL persistent connection and base CRUD class for the ETL tool.

Implements SQLAlchemy and custom exceptions from exceptions.py.
Features a singleton pattern for shared persistent connections across all database functions.
"""

from sqlalchemy import create_engine, Table, MetaData, select, insert, update, delete, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from typing import Optional, Dict, Any, List
import threading
import logging

from system.system.database_connections.exceptions import (
    SQLAlchemyConnectionError,
    SQLAlchemyInsertError,
    SQLAlchemyReadError,
    SQLAlchemyUpdateError,
    SQLAlchemyDeleteError,
)
from system.system.default_configs.postgres_db_conf import POSTGRES_URL

# Set up logging
logger = logging.getLogger(__name__)


class PostgresDB:
    """
    Handles persistent PostgreSQL connection and provides basic CRUD operations using SQLAlchemy.
    
    This class implements a singleton pattern to ensure a single shared database connection
    across all database functions in the system. The connection is thread-safe and persistent,
    reducing connection overhead and improving performance.

    Singleton Features:
        - Single shared database connection across the entire application
        - Thread-safe initialization and access
        - Automatic connection recovery on failures
        - Shared connection pool for optimal resource usage
        - Lazy initialization - connection created only when first accessed

    Transaction Support:
        - All write operations use SQLAlchemy's begin() context manager
        - Automatic rollback on any SQLAlchemyError
        - Manual transaction control available via execute_transaction()
        - Bulk operations supported with transactional safety

    Examples:
        >>> # Get the singleton instance (creates connection on first call)
        >>> db = PostgresDB()
        >>> 
        >>> # All subsequent calls return the same instance
        >>> db2 = PostgresDB()
        >>> assert db is db2  # Same instance
        >>> 
        >>> # Create a new user (transactional)
        >>> user_data = {'username': 'john', 'email': 'john@example.com'}
        >>> new_user = db.create('users', user_data)
        >>> 
        >>> # Read users (uses shared connection)
        >>> all_users = db.read('users')
        >>> active_users = db.read('users', {'is_active': True})
        >>> 
        >>> # Update user (transactional)
        >>> updated = db.update('users', {'email': 'new@example.com'}, {'id': 1})
        >>> 
        >>> # Delete user (transactional)
        >>> deleted = db.delete('users', {'id': 1})
        >>> 
        >>> # Connection is automatically managed - no need to close manually
        >>> # But you can still use as context manager if needed
        >>> with PostgresDB() as db:
        ...     users = db.read('users')
    """

    _instance = None
    _lock = threading.Lock()
    _engine = None
    _metadata = None
    _connection_initialized = False

    def __new__(cls):
        """
        Implement singleton pattern with thread-safe initialization.
        
        Returns:
            PostgresDB: The singleton instance
        """
        if cls._instance is None:
            with cls._lock:
                # Double-check locking pattern
                if cls._instance is None:
                    cls._instance = super(PostgresDB, cls).__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """
        Initialize the singleton PostgresDB instance with persistent connection.
        
        This method is called every time PostgresDB() is instantiated, but the actual
        initialization only happens once due to the singleton pattern.
        """
        if not self._connection_initialized:
            with self._lock:
                # Double-check locking for initialization
                if not self._connection_initialized:
                    self._initialize_connection()
                    self._connection_initialized = True

    def _initialize_connection(self) -> None:
        """
        Initialize the SQLAlchemy engine with persistent connection settings.
        
        This method sets up the database engine with optimized settings for
        persistent connections including connection pooling and error handling.
        """
        try:
            logger.info("Initializing PostgresDB singleton with persistent connection")
            
            # Create engine with persistent connection settings
            self._engine: Engine = create_engine(
                POSTGRES_URL,
                # Connection pool settings for persistent connections
                pool_size=20,           # Number of connections to maintain in pool
                max_overflow=30,        # Additional connections beyond pool_size
                pool_timeout=30,        # Timeout for getting connection from pool
                pool_recycle=3600,      # Recycle connections after 1 hour
                pool_pre_ping=True,     # Validate connections before use
                # Performance settings
                echo=False,             # Set to True for SQL logging in development
                connect_args={
                    "connect_timeout": 10,
                    "application_name": "tiger_etl_persistent"
                }
            )
            
            self._metadata = MetaData()
            
            # Test the connection
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("PostgresDB singleton connection established successfully")
                
        except SQLAlchemyError as e:
            logger.error(f"Failed to initialize PostgresDB singleton: {e}")
            raise SQLAlchemyConnectionError(f"Failed to connect to database: {e}") from e

    @property
    def engine(self) -> Engine:
        """
        Get the SQLAlchemy engine instance.
        
        Returns:
            Engine: The SQLAlchemy engine instance
        """
        if self._engine is None:
            self._initialize_connection()
        return self._engine

    @property
    def metadata(self) -> MetaData:
        """
        Get the SQLAlchemy metadata instance.
        
        Returns:
            MetaData: The SQLAlchemy metadata instance
        """
        if self._metadata is None:
            self._initialize_connection()
        return self._metadata

    def get_connection_info(self) -> Dict[str, Any]:
        """
        Get information about the current database connection.
        
        Returns:
            Dict[str, Any]: Connection information including pool status
        """
        if self._engine is None:
            return {"status": "not_initialized"}
        
        pool = self._engine.pool
        return {
            "status": "connected",
            "pool_size": pool.size(),
            "checked_in_connections": pool.checkedin(),
            "checked_out_connections": pool.checkedout(),
            "overflow_connections": pool.overflow(),
            "invalid_connections": pool.invalid(),
            "url": str(self._engine.url).replace(self._engine.url.password, "***") if self._engine.url.password else str(self._engine.url)
        }

    def test_connection(self) -> bool:
        """
        Test if the database connection is working.
        
        Returns:
            bool: True if connection is working, False otherwise
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True
        except SQLAlchemyError as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def create(self, table_name: str, data: Dict[str, Any]) -> Optional[Any]:
        """
        Insert a new record into the specified table with transaction support.

        Args:
            table_name (str): Table name.
            data (dict): Data to insert.

        Returns:
            Optional[Any]: The inserted record.

        Raises:
            SQLAlchemyInsertError: If the insert operation fails.

        Example:
            >>> db = PostgresDB()
            >>> user_data = {
            ...     'username': 'john_doe',
            ...     'email': 'john@example.com',
            ...     'is_active': True
            ... }
            >>> created_user = db.create('users', user_data)
            >>> print(created_user.id)  # Access the created user's ID
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = insert(table).values(**data).returning(table)
            
            with self.engine.begin() as conn:
                result = conn.execute(stmt)
                return result.fetchone()
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyInsertError(f"Insert failed: {e}")

    def read(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, join: int = 0, limit: Optional[int] = None, offset: int = 0) -> List[Any]:
        """
        Read records from the specified table with optional conditions, join control, and pagination.

        Args:
            table_name (str): Table name.
            conditions (dict, optional): Conditions for filtering.
            join (int, optional): Join control parameter:
                - 0 (default): No joins, return only the specified table data
                - 1: Forward joins (fetch related data from referenced tables)
                - -1: Backward joins (fetch data that references this table)
            limit (int, optional): Maximum number of records to return.
            offset (int, optional): Number of records to skip (for pagination).

        Returns:
            List[Any]: List of records.

        Examples:
            >>> db = PostgresDB()
            >>> # Get all users (no joins)
            >>> all_users = db.read('users')
            >>> 
            >>> # Get active users only (no joins)
            >>> active_users = db.read('users', {'is_active': True})
            >>> 
            >>> # Get users with pagination
            >>> paginated_users = db.read('users', limit=10, offset=20)
            >>> 
            >>> # Get users with forward joins (e.g., fetch user's profile data)
            >>> users_with_profiles = db.read('users', {'is_active': True}, join=1)
            >>> 
            >>> # Get users with backward joins (e.g., fetch users who have orders)
            >>> users_with_orders = db.read('users', None, join=-1)
            >>> 
            >>> # Get specific user by ID (no joins)
            >>> user = db.read('users', {'id': 123})
            >>> if user:
            ...     print(f"Found user: {user[0].username}")
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            
            # Build base select statement
            stmt = select(table)
            
            # Apply conditions if provided
            if conditions:
                for key, value in conditions.items():
                    stmt = stmt.where(table.c[key] == value)
            
            # Apply pagination if specified
            if limit is not None:
                stmt = stmt.limit(limit)
            if offset > 0:
                stmt = stmt.offset(offset)
            
            # Note: Join implementation is controlled by the join parameter
            # Currently only supports join=0 (no joins)
            # join=1 (forward) and join=-1 (backward) return base table data
            # Join logic can be implemented when specific relationships are defined
                        
            with self.engine.connect() as conn:
                result = conn.execute(stmt)
                return result.fetchall()
        except SQLAlchemyError as e:
            raise SQLAlchemyReadError(f"Read failed: {e}")

    def update(self, table_name: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> List[Any]:
        """
        Update records in the specified table based on conditions with transaction support.

        Args:
            table_name (str): Table name.
            data (dict): Data to update.
            conditions (dict): Conditions for updating.

        Returns:
            List[Any]: List of updated records.

        Raises:
            SQLAlchemyUpdateError: If the update operation fails.

        Examples:
            >>> db = PostgresDB()
            >>> # Update a specific user's email
            >>> updated_users = db.update(
            ...     'users',
            ...     {'email': 'newemail@example.com'},
            ...     {'id': 123}
            ... )
            >>> 
            >>> # Deactivate all users with a specific role
            >>> deactivated_users = db.update(
            ...     'users',
            ...     {'is_active': False},
            ...     {'role': 'temp_user'}
            ... )
            >>> print(f"Updated {len(deactivated_users)} users")
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = update(table).values(**data)
            for key, value in conditions.items():
                stmt = stmt.where(table.c[key] == value)
            stmt = stmt.returning(table)
            
            with self.engine.begin() as conn:
                result = conn.execute(stmt)
                return result.fetchall()
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyUpdateError(f"Update failed: {e}")

    def delete(self, table_name: str, conditions: Dict[str, Any]) -> int:
        """
        Delete records from the specified table based on conditions with transaction support.

        Args:
            table_name (str): Table name.
            conditions (dict): Conditions for deletion.

        Returns:
            int: Number of deleted records.

        Raises:
            SQLAlchemyDeleteError: If the delete operation fails.

        Examples:
            >>> db = PostgresDB()
            >>> # Delete a specific user
            >>> deleted_count = db.delete('users', {'id': 123})
            >>> print(f"Deleted {deleted_count} users")
            >>> 
            >>> # Delete all inactive users
            >>> deleted_count = db.delete('users', {'is_active': False})
            >>> print(f"Deleted {deleted_count} inactive users")
            >>> 
            >>> # Delete users by multiple conditions
            >>> deleted_count = db.delete('users', {
            ...     'role': 'temp_user',
            ...     'created_date': '2024-01-01'
            ... })
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = delete(table)
            for key, value in conditions.items():
                stmt = stmt.where(table.c[key] == value)
            
            with self.engine.begin() as conn:
                result = conn.execute(stmt)
                return result.rowcount
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyDeleteError(f"Delete failed: {e}")

    def truncate_and_reset_identity(self, table_name: str, cascade: bool = True) -> None:
        """
        Truncate the specified table and reset its identity/auto-increment counter with transaction support.

        Args:
            table_name (str): Table name to truncate.
            cascade (bool): Whether to cascade the truncation to dependent tables.
                          Default is True to handle foreign key constraints.

        Returns:
            None

        Raises:
            SQLAlchemyDeleteError: If the truncate operation fails.

        Examples:
            >>> db = PostgresDB()
            >>> # Truncate users table and reset ID counter (with cascade)
            >>> db.truncate_and_reset_identity('users')
            >>> 
            >>> # Truncate without cascade (will fail if foreign keys exist)
            >>> db.truncate_and_reset_identity('users', cascade=False)
            >>> 
            >>> # Truncate a lookup table safely
            >>> db.truncate_and_reset_identity('user_roles', cascade=True)
            >>> 
            >>> # After truncation, next insert will start with ID = 1
            >>> new_user = db.create('users', {'username': 'first_user'})
            >>> print(new_user.id)  # Will be 1
        """
        try:
            cascade_clause = "CASCADE" if cascade else "RESTRICT"
            sql_statement = f"TRUNCATE TABLE {table_name} RESTART IDENTITY {cascade_clause};"
            
            with self.engine.begin() as conn:
                conn.execute(text(sql_statement))
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyDeleteError(f"Truncate and reset identity failed for table '{table_name}': {e}")

    def execute_transaction(self, operations: List[callable]) -> List[Any]:
        """
        Execute multiple operations in a single transaction with automatic rollback on failure.

        Args:
            operations (List[callable]): List of functions that take a connection as parameter.
                                       Each function should return a result or None.

        Returns:
            List[Any]: List of results from each operation.

        Raises:
            SQLAlchemyError: If any operation in the transaction fails.

        Example:
            >>> db = PostgresDB()
            >>> def create_user(conn):
            ...     stmt = insert(users_table).values(username='john').returning(users_table)
            ...     return conn.execute(stmt).fetchone()
            >>> 
            >>> def update_profile(conn):
            ...     stmt = update(profiles_table).values(bio='Updated bio').where(profiles_table.c.user_id == 1)
            ...     return conn.execute(stmt).fetchall()
            >>> 
            >>> results = db.execute_transaction([create_user, update_profile])
        """
        try:
            results = []
            with self.engine.begin() as conn:
                for operation in operations:
                    result = operation(conn)
                    results.append(result)
                return results
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyError(f"Transaction failed and was rolled back: {e}")

    def bulk_create(self, table_name: str, data_list: List[Dict[str, Any]]) -> List[Any]:
        """
        Insert multiple records in a single transaction with automatic rollback on failure.

        Args:
            table_name (str): Table name.
            data_list (List[Dict[str, Any]]): List of dictionaries containing data to insert.

        Returns:
            List[Any]: List of inserted records.

        Raises:
            SQLAlchemyInsertError: If the bulk insert operation fails.

        Example:
            >>> db = PostgresDB()
            >>> users_data = [
            ...     {'username': 'user1', 'email': 'user1@example.com'},
            ...     {'username': 'user2', 'email': 'user2@example.com'},
            ...     {'username': 'user3', 'email': 'user3@example.com'}
            ... ]
            >>> created_users = db.bulk_create('users', users_data)
            >>> print(f"Created {len(created_users)} users")
        """
        if not data_list:
            return []

        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            results = []
            
            with self.engine.begin() as conn:
                for data in data_list:
                    stmt = insert(table).values(**data).returning(table)
                    result = conn.execute(stmt)
                    results.extend(result.fetchall())
                return results
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager
            raise SQLAlchemyInsertError(f"Bulk insert failed: {e}")

    def execute_raw_sql(self, sql_query: str, parameters: Optional[Dict[str, Any]] = None, 
                       fetch_results: bool = True, use_transaction: bool = False) -> Optional[List[Any]]:
        """
        Execute a raw SQL query with optional parameters and transaction control.

        Args:
            sql_query (str): The raw SQL query to execute.
            parameters (dict, optional): Parameters to bind to the query for safety.
            fetch_results (bool): Whether to fetch and return results (default: True).
                                Set to False for INSERT/UPDATE/DELETE operations where you only need affected row count.
            use_transaction (bool): Whether to wrap the query in a transaction (default: False).
                                  Set to True for write operations that need rollback capability.

        Returns:
            Optional[List[Any]]: Query results if fetch_results=True, None otherwise.

        Raises:
            SQLAlchemyError: If the query execution fails.

        Examples:
            >>> db = PostgresDB()
            >>> 
            >>> # Simple SELECT query
            >>> results = db.execute_raw_sql("SELECT * FROM users WHERE is_active = :active", 
            ...                             {"active": True})
            >>> 
            >>> # Complex JOIN query
            >>> complex_query = '''
            ...     SELECT u.username, p.bio, r.role_name 
            ...     FROM users u 
            ...     LEFT JOIN profiles p ON u.id = p.user_id 
            ...     LEFT JOIN roles r ON u.role_id = r.id 
            ...     WHERE u.created_at > :date
            ... '''
            >>> users_with_details = db.execute_raw_sql(complex_query, {"date": "2024-01-01"})
            >>> 
            >>> # Aggregation query
            >>> count_query = "SELECT COUNT(*) as total_users FROM users WHERE is_active = :active"
            >>> user_count = db.execute_raw_sql(count_query, {"active": True})
            >>> print(f"Active users: {user_count[0].total_users}")
            >>> 
            >>> # Write operation with transaction
            >>> update_query = "UPDATE users SET last_login = NOW() WHERE id = :user_id"
            >>> db.execute_raw_sql(update_query, {"user_id": 123}, 
            ...                   fetch_results=False, use_transaction=True)
            >>> 
            >>> # Bulk update with transaction
            >>> bulk_update = '''
            ...     UPDATE users 
            ...     SET is_active = false 
            ...     WHERE last_login < :cutoff_date
            ... '''
            >>> db.execute_raw_sql(bulk_update, {"cutoff_date": "2023-01-01"}, 
            ...                   fetch_results=False, use_transaction=True)
            >>> 
            >>> # Complex analytical query
            >>> analytics_query = '''
            ...     SELECT 
            ...         DATE_TRUNC('month', created_at) as month,
            ...         COUNT(*) as new_users,
            ...         COUNT(CASE WHEN is_active THEN 1 END) as active_users
            ...     FROM users 
            ...     WHERE created_at >= :start_date
            ...     GROUP BY DATE_TRUNC('month', created_at)
            ...     ORDER BY month DESC
            ... '''
            >>> monthly_stats = db.execute_raw_sql(analytics_query, {"start_date": "2024-01-01"})
        """
        try:
            # Convert parameters dict to SQLAlchemy text parameters if provided
            stmt = text(sql_query)
            
            if use_transaction:
                # Use transaction for write operations
                with self.engine.begin() as conn:
                    if parameters:
                        result = conn.execute(stmt, parameters)
                    else:
                        result = conn.execute(stmt)
                    
                    if fetch_results:
                        return result.fetchall()
                    else:
                        return None
            else:
                # Use regular connection for read operations
                with self.engine.connect() as conn:
                    if parameters:
                        result = conn.execute(stmt, parameters)
                    else:
                        result = conn.execute(stmt)
                    
                    if fetch_results:
                        return result.fetchall()
                    else:
                        return None
                        
        except SQLAlchemyError as e:
            # Transaction automatically rolled back by the context manager if use_transaction=True
            raise SQLAlchemyError(f"Raw SQL execution failed: {e}")

    def close(self) -> None:
        """
        Close the singleton database connection.
        
        Note: In singleton mode, this will close the connection for all instances.
        Use with caution as it affects the entire application.
        """
        if self._engine:
            logger.info("Closing PostgresDB singleton connection")
            self._engine.dispose()
            self._engine = None
            self._metadata = None
            with self._lock:
                self._connection_initialized = False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - connection is persistent, so no automatic close."""
        # In singleton mode, we don't automatically close the connection
        # as it's shared across the entire application
        pass


# Convenience function to get the singleton instance
def get_session() -> PostgresDB:
    """
    Get the singleton PostgresDB instance.
    
    This function provides a convenient way to get the shared database
    connection instance without needing to instantiate the class.
    
    Returns:
        PostgresDB: The singleton PostgresDB instance
        
    Example:
        >>> db = get_session()
        >>> users = db.read('users')
        >>> # Connection is automatically shared across all get_session() calls
    """
    return PostgresDB()


# Global instance management
def close_global_connection() -> None:
    """
    Close the global singleton database connection.
    
    This function should be called at application shutdown to properly
    close the database connection and clean up resources.
    
    Example:
        >>> # At application startup
        >>> db = PostgresDB()
        >>> 
        >>> # ... application runs ...
        >>> 
        >>> # At application shutdown
        >>> close_global_connection()
    """
    if PostgresDB._instance:
        PostgresDB._instance.close()


def get_connection_status() -> Dict[str, Any]:
    """
    Get the status of the global database connection.
    
    Returns:
        Dict[str, Any]: Connection status information
        
    Example:
        >>> status = get_connection_status()
        >>> print(f"Connection status: {status['status']}")
        >>> print(f"Pool size: {status['pool_size']}")
    """
    if PostgresDB._instance:
        return PostgresDB._instance.get_connection_info()
    else:
        return {"status": "not_initialized"}
    
