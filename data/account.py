import yaml
from datetime import datetime, timedelta

from data.sqlite_proxy import SQLiteProxy
from data.record import Record
from parser.base import ParserBase
import re

class Account:
    """
    Account class, handles reading to & writing from transaction database
    """
    def __init__(self, name: str, database: SQLiteProxy, conf: dict):
        self.name = name
        self.database = database
        self.balance = 0.0
        self.records = []
        self.categories = {}
        self.subcategories = {}
        self.businesses = {}

        # extracted patterns
        self.recurring_amounts = {}
        self.recurring_biz = {}
        self.full_query =  f'SELECT * FROM {self.name} ORDER BY datetime(datetime) DESC;'
        self.query_transactions(self.full_query, True)

        # if not empty, find recurring transactions
        if len(self.records) > 0:
            self.find_recurring(conf['recurring']['months'], \
                                conf['recurring']['significance_ratio'], \
                                conf['recurring']['discard_limit'], \
                                conf['recurring']['min_occurance'])

    def query_transactions(self, query: str, update_dicts: bool):
        """
        reloads the transactions from the database to reflect the latest
        changes. if update is set to true, the dicts of the object are
        also updated.
        """
        # if all transactions are being loaded, update balance
        update_balance = query.lower().startswith(f'select * from {self.name}') and\
                         query.lower().count(' where ') == 0
        if update_balance:
            self.balance = 0.0

        db_records = self.database.query(query)
        self.records = []
        for (t_id, dt_str, amount, category, \
             subcategory, business, note) in db_records:
            if update_dicts:
                self.update_dicts(category, subcategory, business)
            # if reloading all 
            if update_balance:
                self.balance += amount
            self.records.append(Record(datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S"),
                                       amount,
                                       category,
                                       subcategory,
                                       business,
                                       note,
                                       t_id))

    def add_transaction(self, record: Record):
        """
        adds a transaction to the database, updates the dictionaries
        """
        self.update_dicts(record.category, record.subcategory, record.business)
        self.database.add_record(self.name, record)
        self.balance += record.amount

    def delete_transaction(self, transaction_id: int):
        """
        deletes a transaction given the id
        """
        for t_id, record in enumerate(self.records):
            if record.transaction_id == transaction_id:
                self.balance -= record.amount
                self.database.delete_record(self.name, transaction_id)
                self.records.pop(t_id)
                break

    def update_transaction(self, transaction_id: int, updated_record: Record):
        """
        updates a transaction given the id, both in the database and
        the local records
        """
        for t_id, record in enumerate(self.records):
            if record.transaction_id == transaction_id:
                self.database.update_record(self.name, transaction_id, updated_record)
                old_amount = self.records[t_id].amount
                self.records[t_id] = updated_record
                self.records[t_id].transaction_id = transaction_id
                new_amount = self.records[t_id].amount
                self.balance += (new_amount - old_amount)
                break

    def flush_transactions(self):
        """
        commits changes to the database
        """
        self.database.connection.commit()

    def commit_parser(self, parser: ParserBase, translate_mode: bool):
        """
        adds all the read records in the parser to the account and
        the corresponding database table, then reloads the records
        """
        for record in reversed(parser.records):
            if translate_mode:
                if record.category in parser.categories:
                    record.category = parser.categories[record.category]
                if record.subcategory in parser.subcategories:
                    record.subcategory = parser.subcategories[record.subcategory]
            self.add_transaction(record)
        self.flush_transactions()
        self.query_transactions(self.full_query, False)

    def update_dicts(self, category: str, subcategory: str, business: str):
        """
        updates the account dictionaries
        """
        if category not in self.categories:
            self.categories[category] = []
        if subcategory not in self.subcategories:
            self.subcategories[subcategory] = category
            self.categories[category].append(subcategory)
        if business not in self.businesses:
            self.businesses[business] = len(self.businesses.keys())

    def find_recurring(self, months: int, significance_ratio: float, \
                       discard_limit: int, min_occurance: int):
        """
        looks in the database for recurring expenses during the last
        x months. the given significance ratio defines the hit, miss
        ratio that determines whether a transaction could be seen as
        recurring. the discard limit defines how many groups will be
        considered before marking the amount|business as irrelevant.
        min_occurance is self-explanatory.
        """
        last_date = None
        try:
            last_date = self.records[0].t_datetime - timedelta(days=31 * months)
        except OverflowError:
            last_date = self.records[-1].t_datetime

        # amount -> list of records and their occurance count
        amount_dict = {}
        # business name -> list of records and their occurance count
        biznes_dict = {}

        current_index = 0
        while self.records[current_index].t_datetime > last_date:
            amount_key = str(self.records[current_index].amount)
            biznes_key = str(self.records[current_index].business.strip())
            # looking for recurring amounts
            if amount_key in amount_dict:
                if len(amount_dict[amount_key]) <= discard_limit:
                    for i in range(len(amount_dict[amount_key])):
                        record, count = amount_dict[amount_key][i]
                        if self.records[current_index].business == record.business and \
                           self.records[current_index].category == record.category and \
                           self.records[current_index].subcategory == record.subcategory:
                            amount_dict[amount_key][i] = (record, count + 1)
                        else:
                            amount_dict[amount_key].append((self.records[current_index].copy(), 1))
            else:
                amount_dict[amount_key] = [(self.records[current_index].copy(), 1)]
            # looking for recurring businesses
            if biznes_key in biznes_dict:
                if len(biznes_dict[biznes_key]) <= discard_limit:
                    for i in range(len(biznes_dict[biznes_key])):
                        record, count = biznes_dict[biznes_key][i]
                        if self.records[current_index].category == record.category and \
                           self.records[current_index].subcategory == record.subcategory:
                            biznes_dict[biznes_key][i] = (record, count + 1)
                        else:
                            biznes_dict[biznes_key].append((self.records[current_index].copy(), 1))
            else:
                biznes_dict[biznes_key] = [(self.records[current_index].copy(), 1)]

            current_index += 1
            # if all out of records
            if current_index == len(self.records):
                break
        
        for amount_key, lst in amount_dict.items():
            key_sum = sum([pair[1] for pair in lst])
            for record, count in lst:
                if count > min_occurance and (count / key_sum) > significance_ratio:
                    record.note = ''
                    self.recurring_amounts[amount_key] = record
                    break

        for biznes_key, lst in biznes_dict.items():
            key_sum = sum([pair[1] for pair in lst])
            for record, count in lst:
                if count > min_occurance and (count / key_sum) > significance_ratio:
                    record.note = ''
                    self.recurring_biz[biznes_key] = record
                    break