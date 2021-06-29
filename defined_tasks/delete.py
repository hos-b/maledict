import misc.statics as statics
from sqlite3 import OperationalError as SQLiteOperationalError

def account(terminal, name: str) -> str:
    try:
        terminal.database.drop_table(name)
    except SQLiteOperationalError:
        return [f"account {name} doesn't exist"]
    except:
        return [f"could not delete account {name}... go figure out why"]
    # if removing the current account
    current_account = terminal.windows[statics.WMAIN].account
    if current_account and current_account.name == name:
        terminal.windows[statics.WMAIN].change_current_account(None)

    return [f"successfully deleted {name}"]

def expense(main_window, index: str) -> str:
    try:
        transaction_id = int(index, 16)
    except ValueError:
        return [f"expected hex value, got {index}"]
    list_index = -1
    for idx, record in enumerate(main_window.account.records):
        if record.transaction_id == transaction_id:
            list_index = idx
            break
    if list_index == -1:
        return [f"given transaction id does not exist"]

    main_window.update_table_statistics \
        (main_window.account.records[list_index].amount, 0)
    main_window.account.delete_transaction(transaction_id)
    main_window.delete_table_row(list_index)
    return ['expense deleted successfully']