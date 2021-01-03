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

    def to_str(self) -> list:
        return ["{}.{}.{}, {}:{}".format(str(self.t_datetime.day).zfill(2),
                                         str(self.t_datetime.month).zfill(2),
                                         str(self.t_datetime.year).zfill(4),
                                         str(self.t_datetime.hour).zfill(2),
                                         str(self.t_datetime.minute).zfill(2)),
                str(self.amount).ljust(10, ' '),
                self.category.ljust(22, ' '),
                self.subcategory.ljust(22, ' '),
                self.business.ljust(22, ' '),
                self.note.ljust(35, ' ')]

    @staticmethod
    def columns() -> list:
        return ["date and time".center(17, ' '),
                "amount".center(10, ' '),
                "category".center(22, ' '),
                "subcategory".center(22, ' '),
                "payee".center(22, ' '),
                "note".center(35, ' ')]
    @staticmethod
    def length() -> int:
        """
        returns the length of a single row
        """
        return 111 + 32