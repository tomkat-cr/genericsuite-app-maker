"""
MongoDB database
"""
import uuid
import os

from pymongo import MongoClient

from lib.codegen_db_abstracts import DatabaseAbstract


class MongoDBDatabase(DatabaseAbstract):
    """
    MongoDB database class
    """
    def __init__(self, uri, db_name, collection_name):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def save_item(self, item_data: dict, id: str = None):
        """
        Save the item in the MongoDB collection
        """
        if not id:
            id = str(uuid.uuid4())
        item_data['_id'] = id
        self.collection.replace_one({'_id': id}, item_data, upsert=True)
        return id

    def get_list(self, sort_attr: str = None, sort_order: str = "desc"):
        """
        Returns the items in the MongoDB collection
        """
        sort_order = -1 if sort_order == "desc" else 1
        if sort_attr:
            items = list(self.collection.find().sort(sort_attr, sort_order))
        else:
            items = list(self.collection.find())
        # Assign id from _id field
        for item in items:
            item['id'] = str(item['_id'])  # Convert ObjectId to str
        return items

    def get_item(self, id: str):
        """
        Returns the item from the MongoDB collection
        """
        item = self.collection.find_one({'_id': id})
        if item:
            item['id'] = str(item['_id'])  # Convert ObjectId to str
            return item
        return None

    def delete_item(self, id: str):
        """
        Delete an item from the MongoDB collection
        """
        self.collection.delete_one({'_id': id})

    def import_data_from_file(self, file_path: str = None):
        """
        Import data from a JSON file into the database
        """
        if not file_path:
            file_path = os.environ.get('JSON_DB_PATH')
        return super().import_data_from_file(file_path)

    def export_data_to_file(self, file_path: str = None,
                            overwrite: bool = False):
        """
        Export data from the database to a JSON file
        """
        if not file_path:
            file_path = os.environ.get('JSON_DB_PATH')
        return super().export_data_to_file(file_path, overwrite)
