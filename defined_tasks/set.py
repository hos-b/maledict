from data.sqlite_proxy import SQLiteProxy

def account(database: SQLiteProxy, name: str) -> (str, bool):
    accounts = database.list_tables()
    if (name,) in accounts:
        return f"current account set to {name}", True
    return f"could not find account {name}", False
