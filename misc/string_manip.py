from datetime import datetime, date

def fit_string(input_str: str, length: int) -> str:
    """
    returns input_str if len(input_str) <= length;
    otherwise it replaces the overflowing part with
    ellipses
    """
    return input_str[:length - 3] + '...' \
           if len(input_str) > length else input_str

def format_date(dt: datetime) -> str:
    return str(dt.year).zfill(4) + '.' + \
           str(dt.month).zfill(2) + '.' + \
           str(dt.day).zfill(2)

def format_time(dt: datetime) -> str:
    return str(dt.hour).zfill(2) + ':' + \
           str(dt.minute).zfill(2)

def parse_date(date_str: str) -> date:
    if date_str.count('.') == 1:
        parts = date_str.split('.')
        try:
            day, month, year = 1, int(parts[0]), int(parts[1])
            return date(year=year, month=month, day=day)
        except ValueError:
            return None
    elif date_str.count('.') == 2:
        parts = date_str.split('.')
        try:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            return date(year=year, month=month, day=day)
        except ValueError:
            return None
    else:
        return None

# string checks ----------------------------------------------------------------------------
def variadic_contains_or(name: str, *args):
    for arg in args:
        if arg in name:
            return True, arg
    return False, ''

def variadic_equals_or(first: str, *argv):
    for arg in argv:
        if first == arg:
            return True
    return False