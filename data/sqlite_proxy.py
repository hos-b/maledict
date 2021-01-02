import sqlite3
from data.record import Record

class SQLiteProxy:
    def __init__(self, db_file):
        """
        open/create db file & establish connection
        """
        self.connection = None
        try:
            self.connection = sqlite3.connect(db_file)
            print(sqlite3.version)
        except sqlite3.Error as e:
            print(e)

    def create_table(self, name: str):
        if self.connection is None:
            return
        sql_table_crt = f"""CREATE TABLE {name} (
                                transaction_id integer PRIMARY KEY,
                                datetime text NOT NULL,
                                amount REAL NOT NULL,
                                category text,
                                sub_category text,
                                business text,
                                note text
                            );"""

        cursor = self.connection.cursor()
        cursor.execute(sql_table_crt)
    
    def drop_table(self, name: str):
        if self.connection is None:
            return
        sql_table_dlt = f"DROP TABLE {name};"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_dlt)
        self.connection.commit()

    def add_record(self, table: str, record: Record):
        if self.connection is None:
            return
        # ISO8601: YYYY-MM-DD HH:MM:SS.SSS
        sql_insert = f"""INSERT INTO {table} (datetime,
                                              amount,
                                              category,
                                              sub_category,
                                              business,
                                              note)
                                              VALUES(?, ?, ?, ?, ?, ?);"""
        record_tuple = (record.t_datetime.isoformat(' '), record.amount, record.category,\
                        record.sub_category, record.business, record.note)
        cursor = self.connection.cursor()
        cursor.execute(sql_insert, record_tuple)
        self.connection.commit()

    def list_tables(self) -> list:
        sql_table_query = "select name from sqlite_master where type = 'table';"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_query)
        return cursor.fetchall()

    def edit_record(self):
        pass

    def query(self, qstr: str):
        pass


    def db_close(self):
        self.connection.close()