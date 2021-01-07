from datetime import datetime

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