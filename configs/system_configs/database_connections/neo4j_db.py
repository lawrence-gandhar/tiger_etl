"""
Neo4j connection and basic insert/delete operations for the ETL tool.

Uses constants from default_configs/neo4j_conf.py and custom exceptions from exceptions.py.
"""

from neo4j import GraphDatabase, basic_auth
from configs.system_configs.default_configs.neo4j_conf import (
    NEO4J_URI,
    NEO4J_USER,
    NEO4J_PASSWORD
)
from configs.system_configs.database_connections.exceptions import (
    DatabaseConnectionError,
    DatabaseInsertError,
    DatabaseDeleteError
)
from typing import Dict, Any

class Neo4jDB:
    """
    Handles Neo4j connection and provides insert and delete functionalities with validation and exception handling.
    """

    def __init__(self) -> None:
        """
        Initialize the Neo4j database connection.
        """
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=basic_auth(NEO4J_USER, NEO4J_PASSWORD)
            )
        except Exception as e:
            raise DatabaseConnectionError(f"Failed to connect to Neo4j: {e}")

    def insert_node(self, label: str, properties: Dict[str, Any]) -> bool:
        """
        Insert a node with the given label and properties.

        Args:
            label (str): Node label.
            properties (dict): Node properties.

        Returns:
            bool: True if successful, False otherwise.
        """
        if not label or not isinstance(properties, dict):
            raise ValueError("Label must be a non-empty string and properties must be a dictionary.")
        query = f"CREATE (n:{label} $props)"
        try:
            with self.driver.session() as session:
                session.run(query, props=properties)
            return True
        except Exception as e:
            raise DatabaseInsertError(f"Insert failed: {e}")

    def delete_node(self, label: str, match_props: Dict[str, Any]) -> int:
        """
        Delete nodes with the given label and matching properties.

        Args:
            label (str): Node label.
            match_props (dict): Properties to match for deletion.

        Returns:
            int: Number of nodes deleted.
        """
        if not label or not isinstance(match_props, dict):
            raise ValueError("Label must be a non-empty string and match_props must be a dictionary.")
        query = f"MATCH (n:{label} $props) DETACH DELETE n RETURN count(n) as deleted_count"
        try:
            with self.driver.session() as session:
                result = session.run(query, props=match_props)
                record = result.single()
                return record["deleted_count"] if record else 0
        except Exception as e:
            raise DatabaseDeleteError(f"Delete failed: {e}")

    def close(self) -> None:
        """
        Close the Neo4j database connection.
        """
        if hasattr(self, "driver"):
            self.driver.close()