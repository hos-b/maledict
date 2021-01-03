from data.sqlite_proxy import SQLiteProxy
from sqlite3 import OperationalError as SQLiteOperationalError

def account(terminal, name: str) -> str:
    try:
        terminal.database.drop_table(name)
    except SQLiteOperationalError:
        return f"account {name} doesn't exist"
    except:
        return f"could not delete account {name}... go figure out why"
    # if removing the current account
    current_account = terminal.main_window.account
    if current_account and current_account.name == name:
        terminal.main_window.change_current_account(None)

    return f"successfully deleted {name}"