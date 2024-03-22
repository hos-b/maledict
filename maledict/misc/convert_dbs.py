from ..data.sqlite_proxy import SQLiteProxy
from .utils import sign

def main():
    sqlp = SQLiteProxy('./database/maledict.db')
    old_tables = sqlp.list_tables()
    cent_max = 100
    for table in old_tables:
        all_records = sqlp.query(f'SELECT * FROM {table} ORDER BY transaction_id ASC;')
        sqlp.query(f'ALTER TABLE {table} RENAME TO _{table}_deprecated;')
        print(f'renamed {table} to _{table}_deprecated;')
        sqlp.create_account(table, 'Euro')
        sql_insert = f"""INSERT INTO {table} (datetime,
                                              amount_primary,
                                              amount_secondary,
                                              category,
                                              subcategory,
                                              business,
                                              note)
                                              values(?, ?, ?, ?, ?, ?, ?);"""
        cursor = sqlp.connection.cursor()
        for (_, dt, amount, cat, subcat, biz, note) in all_records:
            sgn = sign(amount)
            amount = abs(amount)
            prm = int(amount)
            sec = int(round((amount - prm) * cent_max))
            insert_tuple = (dt, prm * sgn, sec * sgn, cat, subcat, biz, note)
            cursor.execute(sql_insert, insert_tuple)
        sqlp.db_flush()
        print(f'recreated {table}')

if __name__ == '__main__':
    main()