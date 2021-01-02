"""
Record class for transactions
"""
from datetime import datetime

class Record:
    def __init__(self, t_dateteim: datetime, amount: float, \
                 cat: str, subcat: str, business: str, note: str):
        self.t_datetime = t_dateteim
        self.amount = amount
        self.category = cat
        self.subcategory = subcat
        self.business = business
        self.note = note