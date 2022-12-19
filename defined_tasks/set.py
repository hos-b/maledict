from data.account import Account
from misc.statics import WinID

def account(terminal, name: str) -> list:
    accounts = terminal.database.list_tables()
    if name != 'currencies' and name in accounts:
        terminal.windows[WinID.Main].change_current_account(Account(name, terminal.database, terminal.conf))
        return [f'current account set to {name}']
    return [f'could not find {name}']
