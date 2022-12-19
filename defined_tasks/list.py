from data.sqlite_proxy import SQLiteProxy

def accounts(database: SQLiteProxy) -> str:
    accounts = database.list_tables()
    # remove the reserved table from the list
    accounts.remove('currencies')
    if len(accounts) == 0:
        return ['no accounts found']
    return [', '.join(accounts)]
