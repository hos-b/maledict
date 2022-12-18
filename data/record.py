"""
Record class for transactions
"""
from datetime import datetime
from data.currency import Currency
from misc.string_manip import fit_string
from copy import deepcopy

class Record:

    def __init__(self,
                 t_dateteim: datetime,
                 amount: Currency,
                 cat: str,
                 subcat: str,
                 business: str,
                 note: str,
                 transaction_id=-1):
        self.t_datetime = t_dateteim
        self.amount = amount
        self.category = cat
        self.subcategory = subcat
        self.business = business
        self.note = note
        self.transaction_id = transaction_id

    def to_str(self, index_l, amount_l, cat_l, subcat_l, bus_l,
               note_l) -> list:
        """
        converts the record to a list of strings and adjusts the length
        of each element based on the given value. ellipses are added to
        large strings to indicate the overflow.
        """
        amount_str = str(self.amount)
        if self.amount.is_income():
            amount_str = '+' + amount_str
        return [
            hex(self.transaction_id)[2:].zfill(index_l),
            '{}.{}.{}, {}:{}'.format(
                str(self.t_datetime.day).zfill(2),
                str(self.t_datetime.month).zfill(2),
                str(self.t_datetime.year).zfill(4),
                str(self.t_datetime.hour).zfill(2),
                str(self.t_datetime.minute).zfill(2)),
            amount_str.ljust(amount_l),
            fit_string(self.category, cat_l).ljust(cat_l),
            fit_string(self.subcategory, subcat_l).ljust(subcat_l),
            fit_string(self.business, bus_l).ljust(bus_l),
            fit_string(self.note, note_l).ljust(note_l)
        ]

    def __str__(self):
        return self.as_str(True)

    def __repr__(self) -> str:
        return self.as_str(True)

    @staticmethod
    def columns(index_l, amount_l, cat_l, subcat_l, bus_l, note_l) -> list:
        """
        returns the columns names, center-adjusted with the given ints
        """
        return [
            'tr. id'.center(index_l), 'date and time'.center(17),
            'amount'.center(amount_l), 'category'.center(cat_l),
            'subcategory'.center(subcat_l), 'payee'.center(bus_l),
            'note'.center(note_l)
        ]

    def copy(self):
        return deepcopy(self)
