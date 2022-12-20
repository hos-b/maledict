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
    checks whether the input at state x in expense mode is correct,
    returns None if there were no errors
    """
    if state == ExpState.AMOUNT:
        try:
            value = float(input_str)
        except:
            return 'incorrect format for amount. use EUR.CENT'
        if value == 0.0:
            return '0.0 is not a valid value'
        return None
    elif state == ExpState.BUSINESS or state == ExpState.CATEGORY:
        # cannot use [^\w] because it excludes unicode chars
        match = re.match(
            r'.*([/\\\'\"!\?\+=%\*;\^@#\$~\|`\[\]\(\)\{\}\<\>\_]).*',
            input_str, re.UNICODE)
        if match:
            return f'string cannot contain `{match.group(1)}`'
        else:
            # category & subcategory in one string
            if state == ExpState.CATEGORY and input_str.count(':') > 1:
                return 'use cat:subcat for new categories'
            return None
    elif state == ExpState.DATE:
        year, month, day = input_str.split('.')
        try:
            date(int(year), int(month), int(day))
        except ValueError:
            return 'invalid date'
        return None
    elif state == ExpState.TIME:
        hour, minute = input_str.split(':')
        try:
            time(int(hour), int(minute))
        except ValueError:
            return 'invalid time'
        return None
    elif state == ExpState.NOTE:
        # no rules for notes
        return None


# add expense utils ------------------------------------------------------------------------
def change_datetime(dt: datetime, state: int, substate: int,
                    change: int) -> datetime:
    # changing date
    if state == ExpState.DATE:
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
    elif state == ExpState.TIME:
        if substate == 0:
            if change < 0: return dt.replace(hour=max(dt.hour + change, 0))
            elif change > 0: return dt.replace(hour=min(dt.hour + change, 23))
        elif substate == 1:
            if change < 0: return dt.replace(minute=max(dt.minute + change, 0))
            elif change > 0:
                return dt.replace(minute=min(dt.minute + change, 59))
    # increasing or decreasing minute by one to force chronological sort from sqlite
    elif state == ExpState.NOTE:
        if change < 0: return dt - timedelta(minutes=-change)
        elif change > 0: return dt + timedelta(minutes=change)
    return dt


def predict_business(amount: str, biz_temp: str, account: Account):
    # making sure the key is correct
    if '.' not in amount:
        amount += '.0'
    if amount in account.recurring_amounts and \
       biz_temp.casefold() == account.recurring_amounts[amount].business.casefold():
        return account.recurring_amounts[amount].business, \
               account.recurring_amounts[amount]
    elif biz_temp != '':
        predictions = []
        for key in account.businesses:
            if biz_temp.casefold() == key.casefold():
                predictions.append(key)
        if len(predictions) != 0:
            predictions.sort(key=len)
            return predictions[0], None
        return '', None
    else:
        return '', None


def predict_category(business: str, cat_temp: str, account: Account):
    if business in account.recurring_biz and \
       cat_temp.casefold() == account.recurring_biz[business].subcategory.casefold():
        return account.recurring_biz[business].subcategory, \
               account.recurring_biz[business]
    elif cat_temp != '':
        predictions = []
        for key in account.categories:
            if cat_temp.casefold() == key.casefold():
                predictions.append(key)
        for key in account.subcategories:
            if cat_temp.casefold() == key.casefold():
                predictions.append(key)
        if len(predictions) != 0:
            predictions.sort(key=len)
            return predictions[0], None
        return '', None
    else:
        return '', None


def rectify_element(element: str, state: ExpState, account: Account) -> str:
    if state == ExpState.AMOUNT:
        # if there's no sign, it's an expense
        return '-' + element if element[0].isnumeric() else element
    # rectify business:
    elif state == ExpState.BUSINESS:
        for key in account.businesses:
            if key.casefold() == element.casefold():
                return key
        return element
    # rectify category/subcategory:
    elif state == ExpState.CATEGORY:
        for key in account.categories:
            if key.casefold() == element.casefold():
                return key
        for key in account.subcategories:
            if key.casefold() == element.casefold():
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
    cat = elements[ExpState.CATEGORY]
    subcat = ''
    if ':' in elements[ExpState.CATEGORY]:
        cat, subcat = elements[ExpState.CATEGORY].split(':')
    elif elements[ExpState.CATEGORY] in account.subcategories:
        cat = account.subcategories[elements[ExpState.CATEGORY]]
        subcat = elements[ExpState.CATEGORY]
    amount = account.currency_type.from_str(elements[ExpState.AMOUNT])
    return Record(dt.replace(microsecond=0), amount,
        cat, subcat, elements[ExpState.BUSINESS],
        elements[ExpState.NOTE])


def sign(num):
    if num > 0:
        return 1
    elif num < 0:
        return -1
    return 0