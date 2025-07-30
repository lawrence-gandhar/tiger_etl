"""
PostgreSQL persistent connection and base CRUD class for the ETL tool.

Implements SQLAlchemy and custom exceptions from exceptions.py.
"""

from sqlalchemy import create_engine, Table, MetaData, select, insert, update, delete, text, Column, Integer, String, Boolean, DateTime, Float, Text, BigInteger
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from typing import Optional, Dict, Any, List, Union
import re

from system.system.database_connections.exceptions import (
    SQLAlchemyConnectionError,
    SQLAlchemyInsertError,
    SQLAlchemyReadError,
    SQLAlchemyUpdateError,
    SQLAlchemyDeleteError,
    SQLAlchemyTableCreationError,
    SQLAlchemyTableValidationError,
    SQLAlchemyTableExistsError
)
from system.system.default_configs.postgres_db_conf import POSTGRES_URL

class PostgresDB:
    """
    Handles persistent PostgreSQL connection and provides basic CRUD operations using SQLAlchemy.

    This class provides a simple interface for common database operations including
    create, read, update, delete, and table truncation operations. All write operations
    (create, update, delete, truncate) are wrapped in transactions with automatic rollback
    on failure to ensure data consistency.

    Transaction Support:
        - All write operations use SQLAlchemy's begin() context manager
        - Automatic rollback on any SQLAlchemyError
        - Manual transaction control available via execute_transaction()
        - Bulk operations supported with transactional safety

    Examples:
        >>> # Initialize database connection
        >>> db = PostgresDB()
        >>> 
        >>> # Create a new user (transactional)
        >>> user_data = {'username': 'john', 'email': 'john@example.com'}
        >>> new_user = db.create('users', user_data)
        >>> 
        >>> # Read users (no transaction needed)
        >>> all_users = db.read('users')
        >>> active_users = db.read('users', {'is_active': True})
        >>> 
        >>> # Update user (transactional)
        >>> updated = db.update('users', {'email': 'new@example.com'}, {'id': 1})
        >>> 
        >>> # Delete user (transactional)
        >>> deleted = db.delete('users', {'id': 1})
        >>> 
        >>> # Bulk operations (transactional)
        >>> users_data = [{'username': f'user{i}'} for i in range(3)]
        >>> created_users = db.bulk_create('users', users_data)
        >>> 
        >>> # Custom transaction
        >>> def my_operations(conn):
        ...     # Your custom database operations here
        ...     return conn.execute("SELECT COUNT(*) FROM users").fetchone()
        >>> results = db.execute_transaction([my_operations])
        >>> 
        >>> # Truncate table and reset auto-increment (transactional)
        >>> db.truncate_and_reset_identity('users')
        >>> 
        >>> # Always close the connection when done
        >>> db.close()
        >>> 
        >>> # Or use as context manager (recommended)
        >>> with PostgresDB() as db:
        ...     users = db.read('users')
    """

    def __init__(self) -> None:
        """
        Initialize the SQLAlchemy engine using POSTGRES_URL from postgres_db_conf.py.
        """
        try:
            self.engine: Engine = create_engine(POSTGRES_URL)
            self.metadata = MetaData()
            # Test connection
            with self.engine.connect() as conn:
                pass
        except SQLAlchemyError as e:
            raise SQLAlchemyConnectionError(f"Failed to connect to database: {e}") from e

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

    def read(self, table_name: str, conditions: Optional[Dict[str, Any]] = None, join: int = 0) -> List[Any]:
        """
        Read records from the specified table with optional conditions and join control.

        Args:
            table_name (str): Table name.
            conditions (dict, optional): Conditions for filtering.
            join (int, optional): Join control parameter:
                - 0 (default): No joins, return only the specified table data
                - 1: Forward joins (fetch related data from referenced tables)
                - -1: Backward joins (fetch data that references this table)

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

    def delete(self, table_name: str, conditions: Dict[str, Any]) -> List[Any]:
        """
        Delete records from the specified table based on conditions with transaction support.

        Args:
            table_name (str): Table name.
            conditions (dict): Conditions for deletion.

        Returns:
            List[Any]: List of deleted records.

        Raises:
            SQLAlchemyDeleteError: If the delete operation fails.

        Examples:
            >>> db = PostgresDB()
            >>> # Delete a specific user
            >>> deleted_users = db.delete('users', {'id': 123})
            >>> if deleted_users:
            ...     print(f"Deleted user: {deleted_users[0].username}")
            >>> 
            >>> # Delete all inactive users
            >>> deleted_inactive = db.delete('users', {'is_active': False})
            >>> print(f"Deleted {len(deleted_inactive)} inactive users")
            >>> 
            >>> # Delete users by multiple conditions
            >>> deleted_temp = db.delete('users', {
            ...     'role': 'temp_user',
            ...     'created_date': '2024-01-01'
            ... })
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = delete(table)
            for key, value in conditions.items():
                stmt = stmt.where(table.c[key] == value)
            stmt = stmt.returning(table)
            
            with self.engine.begin() as conn:
                result = conn.execute(stmt)
                return result.fetchall()
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
        Dispose the SQLAlchemy engine.
        """
        if self.engine:
            self.engine.dispose()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - automatically close connection."""
        self.close()
    
