from data.sqlite_proxy import SQLiteProxy
from data.account import Account
from ui.static import WMAIN

def account(terminal, name: str) -> list:
    accounts = terminal.database.list_tables()
    if name in accounts:
        terminal.windows[WMAIN].change_current_account(Account(name, terminal.database, terminal.conf))
        return [f"current account set to {name}"]
    return [f"could not find account {name}"]
