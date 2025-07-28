"""
PostgreSQL persistent connection and base CRUD class for the ETL tool.

Implements SQLAlchemy and custom exceptions from exceptions.py.
"""

from sqlalchemy import create_engine, Table, MetaData, select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.engine import Engine
from typing import Optional, Dict, Any, List

from configs.system_configs.database_connections.exceptions import (
    SQLAlchemyConnectionError,
    SQLAlchemyInsertError,
    SQLAlchemyReadError,
    SQLAlchemyUpdateError,
    SQLAlchemyDeleteError
)
from configs.system_configs.default_configs.postgres_db_conf import POSTGRES_URL

class PostgresDB:
    """
    Handles persistent PostgreSQL connection and provides basic CRUD operations using SQLAlchemy.
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
        Insert a new record into the specified table.

        Args:
            table_name (str): Table name.
            data (dict): Data to insert.

        Returns:
            Optional[Any]: The inserted record.
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = insert(table).values(**data).returning(table)
            with self.engine.begin() as conn:
                result = conn.execute(stmt)
                return result.fetchone()
        except SQLAlchemyError as e:
            raise SQLAlchemyInsertError(f"Insert failed: {e}")

    def read(self, table_name: str, conditions: Optional[Dict[str, Any]] = None) -> List[Any]:
        """
        Read records from the specified table with optional conditions.

        Args:
            table_name (str): Table name.
            conditions (dict, optional): Conditions for filtering.

        Returns:
            List[Any]: List of records.
        """
        try:
            table = Table(table_name, self.metadata, autoload_with=self.engine)
            stmt = select(table)
            if conditions:
                for key, value in conditions.items():
                    stmt = stmt.where(table.c[key] == value)
            with self.engine.connect() as conn:
                result = conn.execute(stmt)
                return result.fetchall()
        except SQLAlchemyError as e:
            raise SQLAlchemyReadError(f"Read failed: {e}")

    def update(self, table_name: str, data: Dict[str, Any], conditions: Dict[str, Any]) -> List[Any]:
        """
        Update records in the specified table based on conditions.

        Args:
            table_name (str): Table name.
            data (dict): Data to update.
            conditions (dict): Conditions for updating.

        Returns:
            List[Any]: List of updated records.
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
            raise SQLAlchemyUpdateError(f"Update failed: {e}")

    def delete(self, table_name: str, conditions: Dict[str, Any]) -> List[Any]:
        """
        Delete records from the specified table based on conditions.

        Args:
            table_name (str): Table name.
            conditions (dict): Conditions for deletion.

        Returns:
            List[Any]: List of deleted records.
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
            raise SQLAlchemyDeleteError(f"Delete failed: {e}")

    def close(self) -> None:
        """
        Dispose the SQLAlchemy engine.
        """
        if self.engine:
            self.engine.dispose()