import sqlite3
from data.record import Record

class SQLiteProxy:
    def __init__(self, db_file):
        """
        creates the db file (if it doesn't already exist) and
        establishes a connection.
        """
        self.connection = None
        self.db_open(db_file)

    def create_table(self, name: str):
        if self.connection is None:
            return
        sql_table_crt = f"""create table {name} (
                                transaction_id integer PRIMARY KEY,
                                datetime text NOT NULL,
                                amount REAL NOT NULL,
                                category text,
                                subcategory text,
                                business text,
                                note text
                            );"""

        cursor = self.connection.cursor()
        cursor.execute(sql_table_crt)
    
    def drop_table(self, name: str):
        if self.connection is None:
            return
        sql_table_dlt = f"drop table {name};"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_dlt)
        self.connection.commit()

    def add_record(self, table: str, record: Record):
        if self.connection is None:
            return
        # ISO8601: YYYY-MM-DD HH:MM:SS.SSS
        sql_insert = f"""insert into {table} (datetime,
                                              amount,
                                              category,
                                              subcategory,
                                              business,
                                              note)
                                              values(?, ?, ?, ?, ?, ?);"""
        record_tuple = (record.t_datetime.isoformat(' '), record.amount, record.category,\
                        record.subcategory, record.business, record.note)
        cursor = self.connection.cursor()
        cursor.execute(sql_insert, record_tuple)

    def list_tables(self) -> list:
        sql_table_query = "select name from sqlite_master where type = 'table';"
        cursor = self.connection.cursor()
        cursor.execute(sql_table_query)
        return [item[0] for item in cursor.fetchall()]

    def update_record(self, table: str, transaction_id: id, record: Record):
        sql_update = f"""update {table} set datetime = ?,
                                            amount = ?,
                                            category = ?,
                                            subcategory = ?,
                                            business = ?,
                                            note = ?
                                        where transaction_id = ?;"""
        update_tuple = (record.t_datetime.isoformat(' '), record.amount, record.category,\
                        record.subcategory, record.business, record.note, transaction_id)
        cursor = self.connection.cursor()
        cursor.execute(sql_update, update_tuple)
        self.connection.commit()

    def delete_record(self, table: str, transaction_id: int):
        sql_remove = f'delete from {table} where transaction_id = ?'
        cursor = self.connection.cursor()
        cursor.execute(sql_remove, (transaction_id,))
        self.connection.commit()

    def query(self, query: str) -> list:
        cursor = self.connection.cursor()
        cursor.execute(query)
        return cursor.fetchall()

    def db_close(self):
        self.connection.close()
        self.connection = None
    
    def db_open(self, db_file: str):
        try:
            self.connection = sqlite3.connect(db_file)
            print(sqlite3.version)
        except sqlite3.Error as e:
            print(e)