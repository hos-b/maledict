import os
import shutil

from datetime import datetime

from data.sqlite_proxy import SQLiteProxy


def backup(database: SQLiteProxy):
    database.db_flush()
    timepoint = datetime.now().replace(microsecond=0)
    dst_filename = '{}_{}_{}_{}_{}_{}_{}'.format(
        os.path.basename(database.file_path),
        timepoint.year,
        timepoint.month,
        timepoint.day,
        timepoint.hour,
        timepoint.minute,
        timepoint.second,
    )
    dst_dir = os.path.join(os.path.dirname(database.file_path), 'backups')
    os.makedirs(dst_dir, exist_ok=True)
    dst_path = os.path.join(dst_dir, dst_filename)
    iso_time = timepoint.isoformat(' ')
    if os.path.exists(dst_path):
        return [f'backup file for {iso_time} already exists!']
    try:
        shutil.copyfile(database.file_path, dst_path)
    except Exception as e:
        return [f'failed to save backup: {e}']
    return [f'saved backup at {iso_time}']
