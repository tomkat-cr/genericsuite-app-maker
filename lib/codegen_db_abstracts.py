"""
Generic database abstracts
"""
from typing import List, Dict, Union
import os
import json

from lib.codegen_utilities import (
    get_new_item_id,
    get_default_resultset,
)


class DatabaseAbstract:
    """
    Database abstract class
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

    def save_item(self, item_data: dict, id: str = None):
        """
        Save the item in the database
        """
        raise NotImplementedError

    def get_list(self, sort_attr: str = None, sort_order: str = "desc"):
        """
        Returns the items in the database
        """
        raise NotImplementedError

    def get_item(self, id: str):
        """
        Returns the item in the database
        """
        raise NotImplementedError

    def delete_item(self, id: str):
        """
        Delete an item from the database
        """
        raise NotImplementedError

    def import_data(self, data: Union[List[Dict], Dict]):
        """
        Import data into the database
        """
        response = get_default_resultset()
        # If data is a list of dictionaries, convert it to a dictionary
        if isinstance(data, list):
            data = {item.get('id', get_new_item_id()): item for item in data}
        for id, item_data in data.items():
            self.save_item(item_data, id)
        response['result'] = f"Imported {len(data)} items"
        return response

    def export_data(self) -> str:
        """
        Export data from the database to JSON
        """
        response = get_default_resultset()
        items = self.get_list()
        # Convert id to str
        for item in items:
            item['id'] = str(item['id'])
        response['json'] = json.dumps(items, indent=4)
        response['result'] = f"Emported {len(items)} items"
        return response

    def import_data_from_file(self, file_path: str = None):
        """
        Import data from a JSON file into the database
        """
        response = get_default_resultset()
        if not file_path:
            response['error'] = True
            response['error_message'] = "file_path is required for " \
                                        "import_data_from_file"
        elif not os.path.exists(file_path):
            response['error'] = True
            response['error_message'] = f"File not found: {file_path}"
        if response['error']:
            return response
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except Exception as e:
            response['error'] = True
            response['error_message'] = str(e)
            return response
        response = self.import_data(data)
        response['file_path'] = file_path
        return response

    def export_data_to_file(self, file_path: str = None,
                            overwrite: bool = False):
        """
        Export data from the database to a JSON file
        """
        response = get_default_resultset()
        if not file_path:
            response['error'] = True
            response['error_message'] = "file_path is required for " \
                                        "export_data_to_file"
        elif os.path.exists(file_path) and not overwrite:
            response['error'] = True
            response['error_message'] = f"File found: {file_path}"
        if response['error']:
            return response
        response = self.export_data()
        if response['error']:
            return response
        with open(file_path, 'w') as f:
            f.write(response['json'])
        response['file_path'] = file_path
        return response
