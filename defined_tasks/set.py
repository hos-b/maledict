from data.account import Account
from misc.statics import WinID

def account(terminal, name: str) -> list:
    accounts = terminal.database.list_tables()
    if name in accounts:
        terminal.windows[WinID.Main].change_current_account(Account(name, terminal.database, terminal.conf))
        # blst = [(key, value.business + ':' + value.category + ':' + value.subcategory) for key, value in terminal.windows[WMAIN].account.recurring_amounts.items()]
        # clst = [(key, value.category + ':' + value.subcategory) for key, value in terminal.windows[WMAIN].account.recurring_biz.items()]
        # terminal.terminal_history.append(str(blst))
        # terminal.terminal_history.append(str(clst))
        # terminal.terminal_history.append('')
        return [f'current account set to {name}']
    return [f'could not find account {name}']
