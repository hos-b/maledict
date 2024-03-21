import os

from sqlite3 import OperationalError as SQLiteOperationalError

from data.sqlite_proxy import SQLiteProxy
from misc.statics import WinID, KeyCombo
from .list import backups as list_backup_files


def account(terminal, stdscr, name: str) -> str:
    prompt_message = f'delete {name} and all its transactions? ' \
                      'this operation can >>NOT<< be reverted'
    delete_flag = terminal.get_prompt(
        stdscr,
        prompt_message,
        'account deletion canceled',
        {
            True: ['y', 'yes', '1', 'true'],
            False: ['n', 'no', '0', 'false'],
        },
        True,
    )
    if delete_flag:
        try:
            terminal.database.delete_account(name)
        except SQLiteOperationalError:
            return [f"account {name} doesn't exist"]
        except:
            return [f'could not delete account {name}... go figure out why']
        # if removing the current account
        current_account = terminal.windows[WinID.Main].account
        if current_account and current_account.name == name:
            terminal.windows[WinID.Main].change_current_account(None)
        return [f'successfully deleted {name}']
    else:
        return ['account deletion canceled']


def transaction(main_window, index: str) -> str:
    try:
        transaction_id = int(index, 16)
    except ValueError:
        return [f'expected hex value, got {index}']
    list_index = -1
    for idx, record in enumerate(main_window.account.records):
        if record.transaction_id == transaction_id:
            list_index = idx
            break
    if list_index == -1:
        return [f'given transaction id does not exist']

    main_window.update_table_statistics(
        main_window.account.records[list_index].amount,
        main_window.account.currency_type(0, 0))
    main_window.account.delete_transaction(transaction_id)
    main_window.delete_table_row(list_index)
    return ['transaction deleted successfully']


def backup(terminal, stdscr, backup_id: str):
    try:
        bak_id = int(backup_id)
    except:
        return [f'{backup_id} is not a valid integer']
    bak_str_list, bak_files = list_backup_files(terminal.database, True)
    if bak_id > len(bak_files):
        return [f'cannot find backup file #{bak_id}']
    prompt_message = f'delete backup {bak_str_list[bak_id - 1]}? ' \
                      'this operation can >>NOT<< be reverted'
    delete_flag = terminal.get_prompt(
        stdscr,
        prompt_message,
        'backup deletion canceled',
        {
            True: ['y', 'yes', '1', 'true'],
            False: ['n', 'no', '0', 'false'],
        },
        True,
    )
    if delete_flag:
        try:
            os.remove(bak_files[bak_id - 1])
        except Exception as e:
            return [f'faield to remove backup: {e}']
        return [f'removed backup file {bak_files[bak_id - 1]}']
    return [f'backup deletion canceled']

