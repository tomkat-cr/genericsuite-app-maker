"""
JSON file database
"""
import os
import json
import uuid

from lib.codegen_db_abstracts import DatabaseAbstract


class JsonFileDatabase(DatabaseAbstract):
    """
    JSON file database class
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """
        Initialize the JSON file database
        """
        if not os.path.exists(self.db_path):
            with open(self.db_path, 'w') as f:
                json.dump({}, f)

        with open(self.db_path) as f:
            json_db = json.load(f)

        return json_db

    def save_item(self, item_data: dict, id: str = None):
        """
        Save the item in the database
        """
        if not id:
            id = str(uuid.uuid4())
        json_db = self.init_db()
        json_db[id] = dict(item_data)
        with open(self.db_path, 'w') as f:
            json.dump(json_db, f)
        return id

    def get_list(self, sort_attr: str = None, sort_order: str = "desc"):
        """
        Returns the items in the database
        """
        json_db = self.init_db()
        items = []
        for id, item in json_db.items():
            item_to_append = item.copy()
            item_to_append['id'] = id
            items.append(item_to_append)
        if sort_attr:
            items = sorted(items, key=lambda x: x[sort_attr],
                           reverse=sort_order == "desc")
        return items

    def get_item(self, id: str):
        """
        Returns the item in the database
        """
        json_db = self.init_db()
        if id in json_db:
            item = json_db[id]
            item['id'] = id
            return item
        return None

    def delete_item(self, id: str):
        """
        Delete a item from the database
        """
        json_db = self.init_db()
        if id in json_db:
            del json_db[id]
            with open(self.db_path, 'w') as f:
                json.dump(json_db, f)
