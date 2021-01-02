from data.sqlite_proxy import SQLiteProxy

from sqlite3 import OperationalError as SQLiteOperationalError

def account(database: SQLiteProxy, name: str) -> str:
    try:
        database.drop_table(name)
    except SQLiteOperationalError:
        return f"account {name} doesn't exist"
    except:
        return f"could not delete account {name}... go figure out why"
    return f"successfully deleted {name}"