"""
Generic database
"""
from lib.codegen_db_abstracts import DatabaseAbstract
from lib.codegen_db_json import JsonFileDatabase
from lib.codegen_db_mongodb import MongoDBDatabase
# from lib.codegen_utilities import log_debug


DEBUG = False


class CodegenDatabase(DatabaseAbstract):
    """
    Generic database class
    """
    def __init__(self, db_type, other_data=None):
        """
        Initialize the appropriate database based on db_type
        """
        if other_data is None:
            other_data = {}
        self.other_data = other_data
        self.db = None
        self.db_type = db_type
        if db_type == 'json':
            db_path = self.other_data.get('JSON_DB_PATH')
            if not db_path:
                raise ValueError("Invalid JSON_DB_PATH in other_data")
            self.db = JsonFileDatabase(db_path)
        elif db_type == 'mongodb':
            uri = self.other_data.get('MONGODB_URI')
            db_name = self.other_data.get('MONGODB_DB_NAME')
            collection_name = self.other_data.get('MONGODB_COLLECTION_NAME')
            if not uri or not db_name or not collection_name:
                raise ValueError("Invalid MONGODB_URI, MONGODB_DB_NAME or "
                                 "MONGODB_COLLECTION_NAME in other_data")
            # log_debug(f"CodegenDatabase | "
            #           f"uri: {uri} | db_name: {db_name} | "
            #           f"collection_name: {collection_name}",
            #           debug=DEBUG)
            self.db = MongoDBDatabase(uri, db_name, collection_name)
        else:
            raise ValueError("Invalid db_type. Must be 'json' or 'mongodb'")

    def save_item(self, item_data: dict, id: str = None):
        """
        Save the item in the database
        """
        return self.db.save_item(item_data, id)

    def get_list(self, sort_attr: str = None, sort_order: str = "desc"):
        """
        Returns the items in the database
        """
        return self.db.get_list(sort_attr, sort_order)

    def get_item(self, id: str):
        """
        Returns the item in the database
        """
        return self.db.get_item(id)

    def delete_item(self, id: str):
        """
        Delete an item from the database
        """
        return self.db.delete_item(id)


# Example usage:
# db = CodegenDatabase("json")
# db.save_item({"name": "Item 1", "value": 100})
# item = db.get_item("some_id")
# db.delete_item("some_id")
