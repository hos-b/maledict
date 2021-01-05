from datetime import date, time, datetime
from calendar import monthrange

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

def fit_string(input_str: str, length: int) -> str:
    """
    returns input_str if len(input_str) <= length;
    otherwise it replaces the overflowing part with
    ellipses
    """
    return input_str[:length - 3] + '...' \
           if len(input_str) > length else input_str

def check_input(input_str: str, state: int) -> list:
    """
    checks whether the input at state x in expense mode is correct
    """
    if state == 0:
        if input_str.replace('.', '').isnumeric() and \
           input_str.count('.') < 2:
            return []
        else:
            return ["incorrect format for amount. use EUR.CENT"]
    elif state == 1 or state == 2:
        forbidden, ch = variadic_contains_or(input_str, '/', '\\','\'', '\"', '!', '?',\
                                                        '+', '=', '%', '*', '&', '^',\
                                                        '@', '#', '$', '~', '.', '`',\
                                                        '[', ']', '(', ')', '[', ']')
        if forbidden:
            return [f"string cannot contain {ch}"]
        else:
            return []
    elif state == 3:
        year, month, day = input_str.split('.')
        try:
            date(int(year), int(month), int(day))
        except ValueError:
            return ["invalid date"]
        return []
    elif state == 4:
        hour, minute = input_str.split(':')
        try:
            time(int(hour), int(minute))
        except ValueError:
            return ["invalid time"]
        return []
    elif state == 5:
        # TODO: check note? no rules apply ...
        return []

def format_date(dt) -> str:
    return str(dt.year).zfill(4) + '.' + \
           str(dt.month).zfill(2) + '.' + \
           str(dt.day).zfill(2)

def format_time(dt) -> str:
    return str(dt.hour).zfill(2) + ':' + \
           str(dt.minute).zfill(2)

def change_datetime(dt: datetime, state: int, substate: int, change: int) -> datetime:
    if state == 3:
        if substate == 0: return dt.replace(year = max(0, dt.year + change))
        elif substate == 1:
            max_day = monthrange(dt.year, max(dt.month + change, 1))[1]
            if change < 0: return dt.replace(month = max(dt.month + change, 1), day=min(dt.day, max_day))
            elif change > 0: return dt.replace(month = min(dt.month + change, 12), day=min(dt.day, max_day))
        elif substate == 2:
            if change < 0: return dt.replace(day = max(dt.day + change, 1))
            elif change > 0: return dt.replace(day = min(dt.day + change, monthrange(dt.year, dt.month)[1]))
    elif state == 4:
        if substate == 0:
            if change < 0: return dt.replace(hour = max(dt.hour + change, 0))
            elif change > 0: return dt.replace(hour = min(dt.hour + change, 23))
        elif substate == 1:
            if change < 0: return dt.replace(minute = max(dt.minute + change, 0))
            elif change > 0: return dt.replace(minute = min(dt.minute + change, 59))
    return dt

