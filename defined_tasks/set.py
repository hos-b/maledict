from data.sqlite_proxy import SQLiteProxy

def account(terminal, name: str) -> list:
    accounts = terminal.database.list_tables()
    if (name,) in accounts:
        terminal.current_account = name
        return [f"current account set to {name}"]
    return [f"could not find account {name}"]
