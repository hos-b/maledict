"""
Record class for transactions
"""
import jdatetime

from datetime import datetime
from copy import deepcopy
from typing import List

import data.config as cfg

from data.currency import Currency
from misc.string_manip import fit_string

class Record:

    def __init__(self,
                 t_datetime: datetime,
                 amount: Currency,
                 cat: str,
                 subcat: str,
                 business: str,
                 note: str,
                 transaction_id=-1):
        self.t_datetime = t_datetime
        self.amount = amount
        self.category = cat
        self.subcategory = subcat
        self.business = business
        self.note = note
        self.transaction_id = transaction_id

    def to_str_list(self) -> str:
        """
        converts the record to a list of strings and adjusts the length
        of each element based on the given value. ellipses are added to
        large strings to indicate the overflow.
        """
        dt = self.t_datetime if not cfg.application.use_jdate else \
            jdatetime.datetime.fromgregorian(datetime=self.t_datetime)
        return [
            hex(self.transaction_id)[2:].zfill(cfg.table.index_length),
            '{}.{}.{}, {}:{}'.format(
                str(dt.day).zfill(2),
                str(dt.month).zfill(2),
                str(dt.year).zfill(4),
                str(dt.hour).zfill(2),
                str(dt.minute).zfill(2)),
            self.amount.as_str(use_plus_sign=True).\
                ljust(cfg.table.amount_length),
            fit_string(self.category, cfg.table.category_length).\
                ljust(cfg.table.category_length),
            fit_string(self.subcategory, cfg.table.subcategory_length).\
                ljust(cfg.table.subcategory_length),
            fit_string(self.business, cfg.table.payee_length).\
                ljust(cfg.table.payee_length),
            fit_string(self.note, cfg.table.note_length).\
                ljust(cfg.table.note_length),
        ]

    def __str__(self):
        datetimestr = '{}.{}.{}, {}:{}'.format(
            str(self.t_datetime.day).zfill(2),
            str(self.t_datetime.month).zfill(2),
            str(self.t_datetime.year).zfill(4),
            str(self.t_datetime.hour).zfill(2),
            str(self.t_datetime.minute).zfill(2))
        record_notes = f'. notes: `{self.note}`' if self.note else ''
        if self.amount.is_income():
            return '{} on {} under `{}`'.format(self.amount,
                datetimestr, self.category) + record_notes
        else:
            return '{} to {} on {} under `{}`'.format(self.amount,
                self.business, datetimestr, self.category) + \
                    record_notes
    
    @staticmethod
    def columns() -> List[str]:
        return [
            'tr. id'.center(cfg.table.index_length),
            'date and time'.center(cfg.table.datetime_length),
            'amount'.center(cfg.table.amount_length),
            'category'.center(cfg.table.category_length),
            'subcategory'.center(cfg.table.subcategory_length),
            'payee'.center(cfg.table.payee_length),
            'note'.center(cfg.table.note_length)
        ]

    def copy(self):
        return deepcopy(self)
