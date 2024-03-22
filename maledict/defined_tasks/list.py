import os
import re

from math import log10

from ..data.sqlite_proxy import SQLiteProxy


def accounts(database: SQLiteProxy) -> str:
    accounts = database.list_tables()
    # remove the reserved table from the list
    accounts.remove('currencies')
    if len(accounts) == 0:
        return ['no accounts found']
    return [', '.join(accounts)]


def backups(database: SQLiteProxy, return_file_list: bool) -> str:
    file_list = []

    def amended_output(ret_list: list):
        if return_file_list:
            return ret_list, file_list
        else:
            return ret_list

    bak_dir = os.path.join(os.path.dirname(database.file_path), 'backups')
    if not os.path.exists(bak_dir):
        return amended_output(['no backups found'])
    bak_str_list = os.listdir(bak_dir)
    file_list = [os.path.join(bak_dir, f) for f in bak_str_list]
    if len(bak_str_list) == 0:
        return amended_output(['no backups found'])

    regex = re.compile(
        r'.*_(\d{,4})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})_(\d{1,2})$')
    for i in reversed(range(len(bak_str_list))):
        parsed = regex.match(bak_str_list[i])
        if not parsed:
            bak_str_list.pop(i)
            file_list.pop(i)
            continue
        bak_str_list[i] = '{}.{:02d}.{:02d}, {:02d}:{:02d}:{:02d}'.format(
            *[int(i) for i in parsed.groups()])

    if len(bak_str_list) == 0:
        return amended_output(['no valid backups found'])

    numl = int(log10(len(bak_str_list))) + 1
    for i in range(len(bak_str_list)):
        bak_str_list[i] = f'{str(i + 1).zfill(numl)}: {bak_str_list[i]}'

    return amended_output(bak_str_list)
