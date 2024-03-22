from typing import List
from ..data.account import Account


def recurring(account: Account) -> List[str]:
    """
    return the detected recurring amounts and businesses for debugging
    """
    if account is None:
        return ['no account set']
    str_list = ['recurring amounts:']
    for amount, record in account.recurring_amounts.items():
        cat = record.subcategory if record.subcategory else record.category
        str_list.append(' o {} from {}, {}'.format(
            amount,
            record.business,
            cat,
        ))
    str_list.append('recurring businesses:')
    for biz, record in account.recurring_biz.items():
        cat = record.subcategory if record.subcategory else record.category
        str_list.append(' o {} under {}'.format(biz, cat))

    return str_list