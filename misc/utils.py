import re

from datetime import date, time, datetime
from calendar import monthrange
from enum import IntEnum

from data.record import Record
from data.account import Account
from datetime import timedelta


class ExpState(IntEnum):
    AMOUNT = 0
    BUSINESS = 1
    CATEGORY = 2
    DATE = 3
    TIME = 4
    NOTE = 5


def check_input(input_str: str, state: int) -> str:
    """
    checks whether the input at state x in expense mode is correct
    """
    if state == 0:
        try:
            value = float(input_str)
        except:
            return 'incorrect format for amount. use EUR.CENT'
        if value == 0.0:
            return '0.0 is not a valid value'
        return ''
    elif state == 1 or state == 2:
        match = re.match(r'.*([^a-zA-Z0-9_ \.&]).*', input_str)
        if match:
            return f'string cannot contain `{match.group(1)}`'
        else:
            # category & subcategory in one string
            if state == 2 and input_str.count(':') > 1:
                return 'use cat:subcat for new categories'
            return ''
    elif state == 3:
        year, month, day = input_str.split('.')
        try:
            date(int(year), int(month), int(day))
        except ValueError:
            return 'invalid date'
        return ''
    elif state == 4:
        hour, minute = input_str.split(':')
        try:
            time(int(hour), int(minute))
        except ValueError:
            return 'invalid time'
        return ''
    elif state == 5:
        # no rules for notes
        return ''


# add expense utils ------------------------------------------------------------------------
def change_datetime(dt: datetime, state: int, substate: int,
                    change: int) -> datetime:
    # changing date
    if state == 3:
        if substate == 0: return dt.replace(year=max(0, dt.year + change))
        elif substate == 1:
            max_day = monthrange(dt.year, min(max(dt.month + change, 1),
                                              12))[1]
            if change < 0:                return dt.replace(month = max(dt.month + change, 1), \
                                  day=min(dt.day, max_day))
            elif change > 0:                return dt.replace(month = min(dt.month + change, 12), \
                                  day=min(dt.day, max_day))
        elif substate == 2:
            if change < 0: return dt.replace(day=max(dt.day + change, 1))
            elif change > 0:
                return dt.replace(day=min(dt.day + change,
                                          monthrange(dt.year, dt.month)[1]))
    # changing time
    elif state == 4:
        if substate == 0:
            if change < 0: return dt.replace(hour=max(dt.hour + change, 0))
            elif change > 0: return dt.replace(hour=min(dt.hour + change, 23))
        elif substate == 1:
            if change < 0: return dt.replace(minute=max(dt.minute + change, 0))
            elif change > 0:
                return dt.replace(minute=min(dt.minute + change, 59))
    # increasing or decreasing minute by one to force chronological sort from sqlite
    elif state == 5:
        if change < 0: return dt - timedelta(minutes=-change)
        elif change > 0: return dt + timedelta(minutes=change)
    return dt


def predict_business(amount: str, biz_temp: str, account: Account):
    # making sure the key is correct
    if '.' not in amount:
        amount += '.0'
    if amount in account.recurring_amounts and \
       bool(re.match(biz_temp, account.recurring_amounts[amount].business, re.I)):
        return account.recurring_amounts[amount].business, \
               account.recurring_amounts[amount]
    elif biz_temp != '':
        predictions = []
        for key in account.businesses:
            if bool(re.match(biz_temp, key, re.I)):
                predictions.append(key)
        if len(predictions) != 0:
            predictions.sort(key=len)
            return predictions[0], None
        return '', None
    else:
        return '', None


def predict_category(business: str, cat_temp: str, account: Account):
    if business in account.recurring_biz and \
       bool(re.match(cat_temp, account.recurring_biz[business].subcategory, re.I)):
        return account.recurring_biz[business].subcategory, \
               account.recurring_biz[business]
    elif cat_temp != '':
        predictions = []
        for key in account.categories:
            if bool(re.match(cat_temp, key, re.I)):
                predictions.append(key)
        for key in account.subcategories:
            if bool(re.match(cat_temp, key, re.I)):
                predictions.append(key)
        if len(predictions) != 0:
            predictions.sort(key=len)
            return predictions[0], None
        return '', None
    else:
        return '', None


def rectify_element(element: str, state: int, account: Account) -> str:
    if state == 0:
        # if there's no sign, it's an expense
        return '-' + element if element[0].isnumeric() else element
    # rectify business:
    elif state == 1:
        for key in account.businesses:
            if key.lower() == element.lower():
                return key
        return element
    # rectify category/subcategory:
    elif state == 2:
        for key in account.categories:
            if key.lower() == element.lower():
                return key
        for key in account.subcategories:
            if key.lower() == element.lower():
                return key
        return element
    else:
        return element


def parse_expense(elements: list, dt: datetime, account: Account) -> Record:
    """
    converts the list of strings to a database record. element indices:
    AMOUNT = 0
    BUSINESS = 1
    CATEGORY = 2
    DATE = 3
    TIME = 4
    NOTE = 5
    """
    cat = elements[2]
    subcat = ''
    if ':' in elements[2]:
        cat, subcat = elements[2].split(':')
    elif elements[2] in account.subcategories:
        cat = account.subcategories[elements[2]]
        subcat = elements[2]
    amount = account.currency_type.from_str(elements[0])
    return Record(dt.replace(microsecond=0), amount, cat, subcat, elements[1],
                  elements[5])


def sign(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    return 0