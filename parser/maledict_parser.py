"""
Parser for MISA MoneyKeeper exported CSV (from xlsx)
"""
from typing import Tuple
from data.currency import Euro
from data.record import Record
from datetime import datetime
from parser.base import ParserBase


class MaledictParser(ParserBase):
    """
    not catching all exceptions, but hopefully enough of them
    """

    def __init__(self):
        super().__init__()

    def convert_to_record(self, t_datetime: str, amount_primary: str,
                          amount_secondary, cat: str, subcat: str,
                          business: str, note: str) -> Record:
        """
        parses >>rectified<< strings into a Record
        """
        try:
            record_datetime = datetime.strptime(t_datetime,
                                                '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None, f"got wrong datetime format: {t_datetime}"
        # TODO: remove Euro presumption
        record_amount = Euro(int(amount_primary), int(amount_secondary))
        return Record(record_datetime, record_amount, cat.strip(),
                      subcat.strip(), business.strip(),
                      note.strip()), "success"

    def parse_row(self, row: list) -> Tuple[bool, str]:
        """
        rectifies and parses a row read directly from the CSV file. the parsed element is then stored
        each row has
        0             , 1       , 2               3               , 4       , 5          , 6       , 7
        transaction_id, datetime, amount_primary, amount_secondary, category, subcategory, business, note
        """
        t_datetime = row[1].strip()
        amount_primary = row[2].strip()
        amount_secondary = row[3].strip()
        category = row[4].strip()
        subcategory = row[5].strip()
        business = row[6].strip()
        note = row[7].strip()
        record, msg = self.convert_to_record(t_datetime, amount_primary,
                                             amount_secondary, category,
                                             subcategory, business, note)
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