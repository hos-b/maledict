import os
import shutil

from datetime import datetime

from ..data.sqlite_proxy import SQLiteProxy
from ..misc.utils import get_data_dir

def backup(database: SQLiteProxy):
    database.db_flush()
    timepoint = datetime.now().replace(microsecond=0)
    dst_filename = '{}_{}_{}_{}_{}_{}_{}'.format(
        database.file_path.name,
        timepoint.year,
        timepoint.month,
        timepoint.day,
        timepoint.hour,
        timepoint.minute,
        timepoint.second,
    )
    dst_dir = get_data_dir("backups")
    dst_path = dst_dir.joinpath(dst_filename)
    iso_time = timepoint.isoformat(' ')
    if dst_path.exists():
        return [f'backup file for {iso_time} already exists!']
    try:
        shutil.copyfile(database.file_path, dst_path)
    except Exception as e:
        return [f'failed to save backup: {e}']
    return [f'saved backup at {iso_time}']
