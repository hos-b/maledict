from data.sqlite_proxy import SQLiteProxy
from data.account import Account

def account(terminal, name: str) -> list:
    accounts = terminal.database.list_tables()
    if name in accounts:
        terminal.main_window.change_current_account(Account(name, terminal.database))
        return [f"current account set to {name}"]
    return [f"could not find account {name}"]
