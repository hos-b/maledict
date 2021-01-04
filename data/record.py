"""
Record class for transactions
"""
from datetime import datetime
from datetime import date

class Record:
    def __init__(self, t_dateteim: datetime, amount: float, \
                 cat: str, subcat: str, business: str, note: str, \
                 transaction_id = -1):
        self.t_datetime = t_dateteim
        self.amount = amount
        self.category = cat
        self.subcategory = subcat
        self.business = business
        self.note = note
        self.transaction_id = transaction_id

    def to_str(self, amount_l, cat_l, subcat_l, bus_l, note_l) -> list:
        """
        converts the record to a list of strings and adjusts the length
        of each element based on the given value. if an element exceeds
        this limit, ... is appeneded at the point where it overflows.
        """
        amount_str = str(self.amount)
        if self.amount > 0:
            amount_str = '+' + amount_str
        cat_str = self.category[:cat_l - 3] + '...' \
                  if len(self.category) > cat_l else self.category
        sub_str = self.subcategory[:subcat_l - 3] + '...' \
                  if len(self.subcategory) > subcat_l else self.subcategory
        bus_str = self.business[:bus_l - 3] + '...' \
                  if len(self.business) > bus_l else self.business
        not_str = self.note[:note_l - 3] + '...' \
                  if len(self.note) > note_l else self.note
        return ["{}.{}.{}, {}:{}".format(str(self.t_datetime.day).zfill(2),
                                         str(self.t_datetime.month).zfill(2),
                                         str(self.t_datetime.year).zfill(4),
                                         str(self.t_datetime.hour).zfill(2),
                                         str(self.t_datetime.minute).zfill(2)),
                amount_str.ljust(amount_l),
                cat_str.ljust(cat_l),
                sub_str.ljust(subcat_l),
                bus_str.ljust(bus_l),
                not_str.ljust(note_l)]

    @staticmethod
    def columns(amount_l, cat_l, subcat_l, bus_l, note_l) -> list:
        """
        returns the columns names, center-adjusted with the given ints
        """
        return ["date and time".center(17),
                "amount".center(amount_l),
                "category".center(cat_l),
                "subcategory".center(subcat_l),
                "payee".center(bus_l),
                "note".center(note_l)]

    def copy(self):
        return Record(self.t_datetime, self.amount, self.category, \
                      self.subcategory, self.business, self.note)
