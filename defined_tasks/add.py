from misc.utils import variadic_contains_or
from data.record import Record
from data.sqlite_proxy import SQLiteProxy

from sqlite3 import OperationalError as SQLiteOperationalError
from datetime import datetime

def account(database: SQLiteProxy, name: str, initial_balance: str) -> str:
    try:
        balance_f = float(initial_balance)
    except:
        return f"{initial_balance} is not a float value"
    # should stop basic sql injections
    if name.count(';') > 0:
        return "sneaky but no"
    # this shouldn't be possible anyway but meh
    if name.count(' ') > 0:
        return "account name cannot contain spaces"
    # other stuff
    forbidden, frch = variadic_contains_or(name, '/', '\\','\'', '\"', '!', '?',\
                                                 '+', '=', '%', '*', '&', '^',\
                                                 '@', '#', '$', '~', '.', '`',\
                                                 '[', ']', '(', ')', '[', ']')
    if forbidden:
        return f"account name cannot contain {frch}"
    if balance_f < 0:
        return "initial account balance cannot be negative. are you really that poor?"

    try:
        database.create_table(name)
    except SQLiteOperationalError:
        return f"account {name} already exists"
    except:
        return f"could not create account {name}... go figure out why"
    
    # adding the initial balance
    intial_record = Record(datetime(1, 1, 1, 0, 0, 0, 0), balance_f, '', '', '', 'initial balance')
    expense(database, name, intial_record)
    database.connection.commit()
    return f"successfully added {name} with {balance_f} initial balance"

def expense(database: SQLiteProxy, account: str, record: Record):
    database.add_record(account, record)