
def variadic_contains_or(name: str, *args):
    for arg in args:
        if name.count(arg) > 0:
            return True, arg
    return False, ''

def variadic_equals_or(first: str, *argv):  
    for arg in argv:  
        if first == arg:
            return True
    return False