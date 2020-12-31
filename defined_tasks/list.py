from data.sqlite_proxy import SQLiteProxy

def accounts(database: SQLiteProxy) -> str:
    accounts = database.list_tables()
    if len(accounts) == 0:
        return "no accounts found"
    acc_str = ''
    for i in range(len(accounts) - 1):
        acc_str += accounts[i][0] + ', '
    acc_str += accounts[-1][0]
    return acc_str
