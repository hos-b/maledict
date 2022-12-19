import sqlite3

from typing import List, Tuple
from data.record import Record

class SQLiteProxy:
    table_map = {
        'transaction_id': 0,
        'datetime': 1,
        'amount_primary': 2,
        'amount_secondary': 3,
        'category': 4,
        'subcategory': 5,
        'business': 6,
        'note': 7,
    }

    def __init__(self, db_file):
        """
        creates the db file (if it doesn't already exist) and
        establishes a connection.
        """
        self.connection = None
        self.db_open(db_file)
        self.__create_currency_table()

    def create_account(self, name: str, currency: str):
        if self.connection is None:
            return
        sql_table_crt = f"""CREATE TABLE {name} (
                                transaction_id integer PRIMARY KEY,
                                datetime text NOT NULL,
                                amount_primary integer NOT NULL,
                                amount_secondary integer NOT NULL,
                                category text,
                                subcategory text,
                                business text,
                                note text
                            );"""
        sql_table_insert = f"""INSERT INTO currencies (account_name, currency)
                             values(?, ?);"""
        insert_tuple = (name, currency)

        cursor = self.connection.cursor()
        cursor.execute(sql_table_crt)
        cursor.execute(sql_table_insert, insert_tuple)
        self.connection.commit()

    def delete_account(self, name: str):
        if self.connection is None:
            return
        sql_table_dlt = f'DROP TABLE {name};'
        sql_curr_rmv = f'DELETE FROM currencies WHERE account_name = ?;'

        cursor = self.connection.cursor()
        cursor.execute(sql_table_dlt)
        cursor.execute(sql_curr_rmv, (name, ))
        self.connection.commit()

    def add_record(self, table: str, record: Record):
        if self.connection is None:
            return
        # ISO8601: YYYY-MM-DD HH:MM:SS.SSS
        sql_insert = f"""INSERT INTO {table} (datetime,
                                              amount_primary,
                                              amount_secondary,
                                              category,
                                              subcategory,
                                              business,
                                              note)
                                              values(?, ?, ?, ?, ?, ?, ?);"""
        record_tuple = (record.t_datetime.isoformat(' '),
                        record.amount._primary, record.amount._secondary,
                        record.category, record.subcategory, record.business,
                        record.note)
        cursor = self.connection.cursor()
        cursor.execute(sql_insert, record_tuple)

    def list_tables(self) -> List[str]:
        sql_table_query = "SELECT name FROM sqlite_master WHERE type = 'table';"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_query)
        return [item[0] for item in cursor.fetchall()]

    def update_record(self, table: str, transaction_id: id, record: Record):
        sql_update = f"""UPDATE {table} SET datetime = ?,
                                            amount_primary = ?,
                                            amount_secondary = ?,
                                            category = ?,
                                            subcategory = ?,
                                            business = ?,
                                            note = ?
                                        WHERE transaction_id = ?;"""
        update_tuple = (record.t_datetime.isoformat(' '),
                        record.amount._primary, record.amount._secondary,
                        record.category, record.subcategory, record.business,
                        record.note, transaction_id)
        cursor = self.connection.cursor()
        cursor.execute(sql_update, update_tuple)
        self.connection.commit()

    def delete_record(self, table: str, transaction_id: int):
        sql_remove = f'DELETE FROM {table} WHERE transaction_id = ?;'
        cursor = self.connection.cursor()
        cursor.execute(sql_remove, (transaction_id, ))
        self.connection.commit()

    def query(
            self,
            query: str) -> List[Tuple[int, str, int, int, str, str, str, str]]:
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def get_account_currency(self, name: str) -> str:
        sql_table_query = "SELECT currency FROM currencies WHERE account_name = ?;"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_query, (name, ))
        all_items = cursor.fetchall()
        assert len(all_items) == 1, \
            'expected a single entry for table `{}`, got {}'.format(name, len(all_items))
        return all_items[0][0]

    def db_close(self):
        self.connection.close()
        self.connection = None

    def db_open(self, db_file: str):
        try:
            self.connection = sqlite3.connect(db_file)
            print(f'sqlite3.version: {sqlite3.version}')
        except sqlite3.Error as e:
            print(e)

    def db_flush(self):
        self.connection.commit()

    def __create_currency_table(self):
        if 'currencies' not in self.list_tables():
            sql_table_crt = f"""CREATE TABLE currencies (
                                account_name text PRIMARY KEY,
                                currency text NOT NULL
                            );"""
            cursor = self.connection.cursor()
            cursor.execute(sql_table_crt)
            self.connection.commit()