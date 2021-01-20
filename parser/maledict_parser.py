"""
Parser for MISA MoneyKeeper exported CSV (from xlsx)
"""
from data.record import Record
from datetime import datetime
from parser.base import ParserBase

class MaledictParser(ParserBase):
    """
    not catching all exceptions, but hopefully enough of them
    """
    def __init__(self):
        super().__init__()

    def convert_to_record(self, t_datetime: str, amount: str, \
                          cat: str, subcat: str, business: str, note: str) -> Record:
        """
        parses >>rectified<< strings into a Record
        """
        try:
            record_datetime = datetime.strptime(t_datetime, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None, f"got wrong datetime format, got {t_datetime}"
        # parsing amount
        if amount.count('.') > 1:
            return None, f"wrong amount format: got {amount}, expected EUR.CENT"
        record_amount = float(amount)
        return Record(record_datetime, record_amount, cat.strip(), \
                      subcat.strip(), business.strip(), note.strip()), "success"

    def parse_row(self, row: list) -> (bool, str):
        """
        rectifies and parses a row read directly from the CSV file. the parsed element is then stored
        each row has
        0             , 1       , 2     , 3       , 4          , 5       , 6
        transaction_id, datetime, amount, category, subcategory, business, note
        """
        t_datetime = row[1].strip()
        amount = row[2].strip()
        category = row[3].strip()
        subcategory = row[4].strip()
        business = row[5].strip()
        note = row[6].strip()
        record, msg = self.convert_to_record(t_datetime, amount, category, subcategory, business, note)
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