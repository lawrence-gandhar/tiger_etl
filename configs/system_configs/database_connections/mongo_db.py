from pymongo import MongoClient
from configs.system_configs.default_configs.mongo_conf import (
    MONGODB_URI,
    MONGODB_DB
)
from configs.system_configs.database_connections.exceptions import (
    MongoConnectionError,
    MongoCRUDError
)


class MongoDBConnection:
    """
    MongoDBConnection handles connection and CRUD operations for MongoDB.

    Attributes:
        client (MongoClient): The MongoDB client instance.
        db (Database): The MongoDB database instance.
    """

    def __init__(self, uri, db_name):
        """
        Initialize the MongoDB connection.

        Args:
            uri (str): MongoDB connection URI.
            db_name (str): Name of the database to connect to.

        Raises:
            MongoConnectionError: If connection fails.
        """
        try:
            self.client = MongoClient(uri)
            self.db = self.client[db_name]
        except Exception as e:
            raise MongoConnectionError(f"Failed to connect to MongoDB: {e}")

    def insert_one(self, collection, document):
        """
        Insert a single document into a collection.

        Args:
            collection (str): Collection name.
            document (dict): Document to insert.

        Returns:
            ObjectId: The inserted document's ID.

        Raises:
            MongoCRUDError: If insert fails.
        """
        try:
            result = self.db[collection].insert_one(document)
            return result.inserted_id
        except Exception as e:
            raise MongoCRUDError(f"Insert failed: {e}")

    def find_one(self, collection, query):
        """
        Find a single document in a collection.

        Args:
            collection (str): Collection name.
            query (dict): Query to match.

        Returns:
            dict or None: The matched document or None.

        Raises:
            MongoCRUDError: If find fails.
        """
        try:
            return self.db[collection].find_one(query)
        except Exception as e:
            raise MongoCRUDError(f"Find failed: {e}")

    def update_one(self, collection, query, update):
        """
        Update a single document in a collection.

        Args:
            collection (str): Collection name.
            query (dict): Query to match.
            update (dict): Fields to update.

        Returns:
            int: Number of documents modified.

        Raises:
            MongoCRUDError: If update fails.
        """
        try:
            result = self.db[collection].update_one(query, {'$set': update})
            return result.modified_count
        except Exception as e:
            raise MongoCRUDError(f"Update failed: {e}")

    def delete_one(self, collection, query):
        """
        Delete a single document from a collection.

        Args:
            collection (str): Collection name.
            query (dict): Query to match.

        Returns:
            int: Number of documents deleted.

        Raises:
            MongoCRUDError: If delete fails.
        """
        try:
            result = self.db[collection].delete_one(query)
            return result.deleted_count
        except Exception as e:
            raise MongoCRUDError(f"Delete failed: {e}")

    def close(self):
        """
        Close the MongoDB connection.
        """
        self.client.close()