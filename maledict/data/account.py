
from datetime import datetime, timedelta
from typing import List, Dict, Set, Tuple

from . import config as cfg
from .currency import Currency, supported_currencies
from .sqlite_proxy import SQLiteProxy
from .record import Record
from ..misc.utils import ExpState, max_element
from ..parser.base import ParserBase


class Account:
    """
    Account class, handles reading to & writing from transaction database
    """

    def __init__(self, name: str, database: SQLiteProxy):
        self.name = name
        self.database = database
        self.currency_type = supported_currencies[
            database.get_account_currency(name)]
        self.balance: Currency = self.currency_type(0, 0)
        self.records: List[Record] = []
        # category -> list of subcategories
        self.categories: Dict[List[str]] = dict()
        # subcategory -> parent category
        self.subcategories: Dict[str] = dict()
        self.businesses: Set[str] = set()
        # extracted patterns
        self.recurring_amounts: Dict[str, Record] = dict()
        self.recurring_biz: Dict[str, Record] = dict()
        self.prediction_rating: Dict[str, int] = dict()
        self.query_transactions(self.full_query, True)

        # if not empty, find recurring transactions
        if len(self.records) > 0:
            self.find_recurring()

    @property
    def full_query(self):
        return f'SELECT * FROM {self.name} ORDER BY datetime(datetime) DESC;'

    def query_transactions(self, query: str, update_dicts: bool):
        """
        reloads the transactions from the database to reflect the latest
        changes. if update is set to true, the dicts of the object are
        also updated.
        """
        # if all transactions are being loaded, update balance [regex is overkill]
        update_balance = query.lower().startswith(f'select * from {self.name}') and \
                         query.lower().count(' where ') == 0
        if update_balance:
            self.balance = self.currency_type(0, 0)

        db_records = self.database.query(query)
        self.records = []
        for (t_id, dt_str, amount_primary, amount_secondary, category,
             subcategory, business, note) in db_records:
            if update_dicts:
                self.update_dicts(category, subcategory, business)
            amount = self.currency_type(amount_primary, amount_secondary)
            # if reloading all
            if update_balance:
                self.balance += amount
            self.records.append(
                Record(datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S'), amount,
                       category, subcategory, business, note, t_id))

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
        for t_idx, record in enumerate(self.records):
            if record.transaction_id == transaction_id:
                self.balance -= record.amount
                self.database.delete_record(self.name, transaction_id)
                self.records.pop(t_idx)
                break

    def update_transaction(self, transaction_id: int, updated_record: Record):
        """
        updates a transaction given the id, both in the database and
        the local records
        """
        for t_id, record in enumerate(self.records):
            if record.transaction_id == transaction_id:
                self.database.update_record(self.name, transaction_id,
                                            updated_record)
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
                    record.subcategory = parser.subcategories[
                        record.subcategory]
            self.add_transaction(record)
        self.flush_transactions()
        self.query_transactions(self.full_query, False)

    def update_dicts(self, category: str, subcategory: str, business: str):
        """
        updates the account dictionaries for categories, subcategories,
        businesses and ratings.
        """
        if category not in self.categories:
            self.categories[category] = list()
            self.prediction_rating[category] = 1
        else:
            self.prediction_rating[category] += 1
        if subcategory:
            if subcategory not in self.subcategories:
                self.prediction_rating[subcategory] = 1
                self.subcategories[subcategory] = category
                self.categories[category].append(subcategory)
            else:
                self.prediction_rating[subcategory] += 1
        if business not in self.businesses:
            self.businesses.add(business)
            self.prediction_rating[business] = 1
        else:
            self.prediction_rating[business] += 1

    def find_recurring(self):
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
            last_date = self.records[0].t_datetime - \
                timedelta(days=31 * cfg.recurring.months)
        except OverflowError:
            last_date = self.records[-1].t_datetime

        # amount -> list of (record, occurance)
        amount_dict: Dict[str, List[Tuple[Record, int]]] = dict()
        # business name -> list of (record, occurance)
        biznes_dict: Dict[str, List[Tuple[Record, int]]] = dict()

        idx = 0
        while self.records[idx].t_datetime > last_date:
            db_record = self.records[idx].copy()
            amount_str = str(db_record.amount)
            # strip irrelevant info
            db_record.t_datetime = None
            db_record.transaction_id = None
            db_record.note = None
            db_record.amount = None
            # looking for recurring amounts
            if amount_str in amount_dict:
                found = False
                for i in range(len(amount_dict[amount_str])):
                    recurring, count = amount_dict[amount_str][i]
                    if db_record.business == recurring.business and \
                        db_record.category == recurring.category and \
                        db_record.subcategory == recurring.subcategory:
                        amount_dict[amount_str][i] = (recurring, count + 1)
                        found = True
                        break
                if not found:
                    amount_dict[amount_str].append((db_record, 1))
            else:
                amount_dict[amount_str] = [(db_record, 1)]
            # looking for recurring businesses, keeping a list because
            # some businesses can have more than one category => ML
            biznes_key = db_record.business
            if biznes_key in biznes_dict:
                found = False
                for i in range(len(biznes_dict[biznes_key])):
                    recurring, count = biznes_dict[biznes_key][i]
                    if db_record.category == recurring.category and \
                        db_record.subcategory == recurring.subcategory:
                        biznes_dict[biznes_key][i] = (recurring, count + 1)
                        found = True
                if not found:
                    biznes_dict[biznes_key].append((db_record, 1))
            else:
                biznes_dict[biznes_key] = [(db_record, 1)]

            idx += 1
            if idx == len(self.records):
                break
        # process recurring amounts
        for amount_key, lst in amount_dict.items():
            key_sum = sum([pair[1] for pair in lst])
            record, count = max_element(lst, lambda x: x[1])
            occ_ratio = count / key_sum
            if count > cfg.recurring.min_occurance and \
                occ_ratio > cfg.recurring.significance_ratio:
                self.recurring_amounts[amount_key] = record

        # process recurring businesses, increase their pred. ratings
        for biznes_key, lst in biznes_dict.items():
            key_sum = sum([pair[1] for pair in lst])
            record, count = max_element(lst, lambda x: x[1])
            occ_ratio = count / key_sum
            self.prediction_rating[record.business] += \
                int(self.prediction_rating[record.business] * occ_ratio)
            self.prediction_rating[record.category] += \
                int(self.prediction_rating[record.business] * occ_ratio)
            if record.subcategory:
                self.prediction_rating[record.subcategory] += \
                    int(self.prediction_rating[record.subcategory] * occ_ratio)
            if count > cfg.recurring.min_occurance and \
                occ_ratio > cfg.recurring.significance_ratio:
                self.recurring_biz[biznes_key] = record

    def predict_string(self,
                       partial: str,
                       state: ExpState,
                       prev_strs: List[str],
                       exp_record: Record = None,
                       prev_prediction: str = '',
                       surf_index_shift: int = 0):
        """
        returns a predicted string given the state, current & previous elements
        """
        # handle easy prediction if an expected state of the record is provided
        if exp_record is not None:
            if state == ExpState.AMOUNT:
                exp_amount = exp_record.amount.as_str(use_plus_sign=True)
                if exp_amount.startswith(partial):
                    return exp_amount
            if state == ExpState.BUSINESS and \
                exp_record.business.casefold().\
                    startswith(partial.casefold()):
                return exp_record.business
            elif state == ExpState.CATEGORY:
                prev_cat = exp_record.category
                if not prev_cat:
                    prev_cat = exp_record.subcategory
                if prev_cat.casefold().startswith(partial.casefold()):
                    return prev_cat
            elif state == ExpState.NOTE and \
                exp_record.note.casefold().startswith(partial.casefold()):
                return exp_record.note

        predictions = []
        if state == ExpState.BUSINESS:
            amount = self.currency_type.from_str(
                prev_strs[ExpState.AMOUNT]).as_str(True, True)
            if amount in self.recurring_amounts and \
                self.recurring_amounts[amount].business.\
                casefold().startswith(partial.casefold()):
                return self.recurring_amounts[amount].business
            elif partial != '':
                for key in self.businesses:
                    if key.casefold().startswith(partial.casefold()):
                        predictions.append(key)
        elif state == ExpState.CATEGORY:
            business = prev_strs[ExpState.BUSINESS]
            if business in self.recurring_biz:
                recurring_str = self.recurring_biz[business].subcategory
                if recurring_str == '':
                    recurring_str = self.recurring_biz[business].category
                if recurring_str.casefold().startswith(partial.casefold()):
                    return recurring_str
            elif partial != '':
                for key in self.categories:
                    if key.casefold().startswith(partial.casefold()):
                        predictions.append(key)
                for key in self.subcategories:
                    if key.casefold().startswith(partial.casefold()):
                        predictions.append(key)

        if len(predictions) == 0:
            return ''
        # sort in descending order
        predictions.sort(key=lambda x: self.prediction_rating[x], reverse=True)
        highest_rank_pred = predictions[0]
        if surf_index_shift == 0 or not prev_prediction:
            return highest_rank_pred
        try:
            prev_index = predictions.index(prev_prediction)
        except ValueError:
            return highest_rank_pred
        return predictions[min(max(0, prev_index + surf_index_shift),
                               len(predictions) - 1)]
