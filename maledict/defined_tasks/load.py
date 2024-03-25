import shutil

from ..data.sqlite_proxy import SQLiteProxy
from ..data.account import Account
from ..misc.statics import WinID
from ..ui.main import MainWindow
from .save import backup as save_backup
from .list import backups as list_backup_files


def backup(terminal, database: SQLiteProxy, backup_id: str):
    try:
        bak_id = int(backup_id)
    except:
        return [f'{backup_id} is not a valid integer']
    bak_str_list, bak_files = list_backup_files(True)
    if bak_id > len(bak_files):
        return [f'cannot find backup file #{bak_id}']
    main_window: MainWindow = terminal.windows[WinID.Main]
    prev_acc_name = None if not main_window.account else main_window.account.name
    main_window.change_current_account(None)
    terminal.append_to_history('backing up current database')
    terminal.append_to_history(save_backup(database))
    database.db_flush()
    database.db_close()
    shutil.copyfile(bak_files[bak_id - 1], database.file_path)
    database.db_open(database.file_path)
    if prev_acc_name:
        if prev_acc_name not in database.list_tables():
            terminal.append_to_history('previously selected account `{}` '
                                       'was not found in the loaded backup')
        else:
            main_window.change_current_account(Account(prev_acc_name, database))
    return [f'loaded checkpoint {bak_str_list[bak_id - 1]}']