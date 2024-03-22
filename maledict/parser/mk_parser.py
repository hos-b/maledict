"""
Parser for MISA MoneyKeeper exported CSV (from xlsx)
"""
from ..data.record import Record
from datetime import datetime
from .base import ParserBase

class MKParser(ParserBase):
    """
    not catching all exceptions, but hopefully enough of them
    """
    def __init__(self):
        super().__init__()

    def convert_to_record(self, t_date: str, t_time: str, amount: str,
                          cat: str, subcat: str, business: str, note: str,
                          currency_type) -> Record:
        """
        parses >>rectified<< strings into a Record
        """
        # parsing date
        date_lst = t_date.split('/')
        if len(date_lst) != 3:
            return None, f'wrong date format: got {t_date}, expected MM/DD/YYYY'
        # parsing time
        time_lst = t_time.split(':')
        if len(time_lst) != 2:
            return None, f'wrong time format: got {t_time}, expected HH:MM'
        record_datetime = datetime(int(date_lst[2]), int(date_lst[0]), int(date_lst[1]),
                                   int(time_lst[0]), int(time_lst[1]))
        # parsing amount
        try:
            record_amount = currency_type.from_str(float(amount))
        except Exception as e:
            return None, f'{e}'
        return Record(record_datetime, record_amount, cat.strip(),
                      subcat.strip(), business.strip(), note.strip()), 'success'

    def parse_row(self, row: list, currency_type) -> bool:
        """
        rectifies and parses a row read directly from the CSV file. the parsed element is then stored
        each row has
        0 ;   1;   2;            3;             4;      5;              6;       7;    8;    9;         10
        No;Date;Time;Income amount;Expense amount;Balance;Parent Category;Category;Payee;Event;Description
        """
        t_date = row[1].strip()
        t_time = row[2].strip()
        income_amount = row[3].strip().replace('.', '').replace(',', '.')
        expense_amount = row[4].strip().replace('.', '').replace(',', '.')
        amount = 0
        if len(income_amount) > 0:
            amount = income_amount
        else:
            amount = '-' + expense_amount
        category = row[6].strip()
        subcategory = row[7].strip()
        business = row[8].strip()
        note = row[10].strip()
        record, msg = self.convert_to_record(
            t_date, t_time, amount, category, subcategory, business, note, currency_type)
        if record:
            self.records.append(record)
            # adding categories, subcategories, businesses
            if record.category not in self.categories and record.category != '':
                self.categories[record.category] = 'N/A'
            if record.subcategory not in self.subcategories and record.subcategory != '':
                self.subcategories[record.subcategory] = 'N/A'
            if record.business not in self.businesses:
                self.businesses[record.business] = len(self.businesses)
            return True, msg
        return False, msg