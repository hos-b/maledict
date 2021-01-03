import yaml
import datetime

from data.sqlite_proxy import SQLiteProxy
from data.record import Record
from parser.base import ParserBase

class Account:
    """
    Account class, handles reading to & writing from transaction database
    """
    def __init__(self, name: str, database: SQLiteProxy):
        self.name = name
        self.database = database
        self.balance = 0.0
        self.records = []
        self.categories = {}
        self.subcategories = {}
        self.businesses = {}
        self.reload_transactions(True)
        
    def reload_transactions(self, update: bool):
        """
        reloads the transactions from the database to reflect the latest
        changes. if update is set to true, the dicts of the object are
        also updated.
        """
        db_records = self.database.query(f"SELECT * FROM {self.name} "
                                          "ORDER BY datetime(datetime) DESC;")
        self.records = []
        for (t_id, dt_str, amount, category, \
             subcategory, business, note) in db_records:
            if update:
                self.update_dicts(category, subcategory, business)
            self.balance += amount
            self.records.append(Record(datetime.datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                                       amount,
                                       category,
                                       subcategory,
                                       business,
                                       note,
                                       t_id))

    def add_transaction(self, record: Record):
        """
        adds a transaction to the database
        """
        self.update_dicts(record.category, record.subcategory, record.business)
        self.database.add_record(self.name, record)
        self.balance += record.amount
    
    def flush_transactions(self):
        """
        commits changes to the database
        """
        self.database.connection.commit()
    
    def commit_parser(self, parser: ParserBase, translate_mode: bool):
        """
        adds all the read records in the parser to the account &
        the corresponding database table.
        """
        for record in parser.records:
            if translate_mode:
                if record.category in parser.categories:
                    record.category = parser.categories[record.category]
                if record.subcategory in parser.subcategories:
                    record.subcategory = parser.subcategories[record.subcategory]
            self.add_transaction(record)
        self.flush_transactions()
        self.reload_transactions(False)
    
    def update_dicts(self, category: str, subcategory: str, business: str):
        """
        updates the account dictionaries
        """
        if category not in self.categories:
            self.categories[category] = len(self.categories.keys())
        if subcategory not in self.subcategories:
            self.subcategories[subcategory] = len(self.subcategories.keys())
        if business not in self.businesses:
            self.businesses[business] = len(self.businesses.keys())