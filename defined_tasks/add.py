import re
import curses

from datetime import datetime
from sqlite3 import OperationalError as SQLiteOperationalError
from sqlite3 import Error as SQLiteError

import data.config as cfg

from misc.utils import check_input
from misc.utils import predict_business, predict_category
from misc.string_manip import format_date, format_time
from misc.utils import change_datetime, rectify_element 
from misc.utils import parse_expense, ExpState
from data.account import Account
from data.record import Record
from data.currency import supported_currencies
from data.sqlite_proxy import SQLiteProxy
from misc.statics import WinID, KeyCombo

def account(database: SQLiteProxy, name: str, initial_balance: str, currency_name: str) -> str:
    if name == 'currencies':
        return [f'`currencies` is reserved. choose another name.']
    # check whether the currency is implemented
    try:
        currency_type = supported_currencies[currency_name]
    except KeyError:
        return [f"maledict currently only supports {', '.join(supported_currencies.keys())}"]
    try:
        initial_balance = currency_type.from_str(initial_balance)
    except:
        return [f'{initial_balance} is not a float value']
    # prevent non alpha-numeric characters from landing in sqlite db, especially ;
    match = re.match(r'.*(\W).*', name)
    if match:
        return [f'account name cannot contain {match.group(1)}']
    if initial_balance < 0:
        return [
            'initial account balance cannot be negative. are you really that poor?'
        ]

    try:
        database.create_account(name, currency_name)
    except SQLiteOperationalError:
        return [f'account {name} already exists']
    except SQLiteError as e:
        return [f'[sqlite error] {e}']

    # adding the initial balance
    # the account object doesn't get created until we use set account, therefor
    # we cannot use the much more convenient call: account.add_transaction(...)
    if initial_balance > 0:
        intial_record = Record(
            datetime(1970, 1, 1, 0, 0, 0, 0), 
            initial_balance, '',
            '', '', 'initial balance')
        database.add_record(name, intial_record)
        database.connection.commit()

    return [f'successfully added {name} with {initial_balance} initial balance']

def expense(terminal, stdscr):
    account: Account = terminal.windows[WinID.Main].account
    # exception handling
    if account == None:
        return ['current account not set']
    if stdscr is None:
        return ['cannot add expenses in warmup mode']
    terminal.append_to_history('expense mode activated')
    terminal.reset_input_field()
    curses.curs_set(1)
    tr_date = datetime.now()
    tr_date = tr_date.replace(second=0, microsecond=0)
    sub_element_start = {ExpState.DATE: [0, 5, 8], ExpState.TIME: [0, 3]}
    sub_element_length = {ExpState.DATE: [4, 2, 2], ExpState.TIME: [2, 2]}
    element_hint = ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = ExpState.AMOUNT
    sub_state = 0
    # predictions
    predicted_record = None
    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == ExpState.AMOUNT or state == ExpState.BUSINESS or \
           state == ExpState.CATEGORY or state == ExpState.NOTE:
            return True
        return False

    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f' {element_hint[state]}:'

    def update_predictions(force_new_prediction: bool):
        global predicted_record
        if state == ExpState.BUSINESS:
            terminal.shadow_string, predicted_record = predict_business(
                elements[ExpState.AMOUNT],
                terminal.command[element_start[ExpState.BUSINESS]:],
                account)
            terminal.shadow_index = element_start[ExpState.BUSINESS]
        elif state == ExpState.CATEGORY:
            if not force_new_prediction and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory \
                    if predicted_record.subcategory != '' \
                    else predicted_record.category
                terminal.shadow_index = element_start[ExpState.CATEGORY]
                return
            terminal.shadow_string, predicted_record = predict_category(
                elements[ExpState.BUSINESS],
                terminal.command[element_start[ExpState.CATEGORY]:],
                account)
            terminal.shadow_index = element_start[ExpState.CATEGORY]
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0

    # start accepting input -----------------------------------------------------------
    terminal.append_to_history(get_hint())
    terminal.redraw()
    kb_interrupt = False
    ec_interrupt = False
    while True:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
            ec_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            state = sub_state = 0
            elements = ['', '', '', '', '', '']
            terminal.reset_input_field()
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.print_history[-1] = 'press ctrl + c again to exit expense mode'
            terminal.append_to_history(get_hint())
            terminal.redraw()
            continue
        except:
            continue
        # escape = interrupt ----------------------------------------------------------
        if input_char == '\x1b':
            if ec_interrupt or terminal.command == '':
                break
            ec_interrupt = True
            state = sub_state = 0
            elements = ['', '', '', '', '', '']
            terminal.reset_input_field()
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.print_history[-1] = 'press escape again to exit expense mode'
            terminal.append_to_history(get_hint())
            terminal.redraw()
            continue
        # backspace, del --------------------------------------------------------------
        elif input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.delete_previous_char(element_start[state], False)
                update_predictions(True)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed():
                terminal.delete_next_char(False)
                update_predictions(True)
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[element_start[state]:
                                               element_end[state] + 1].strip()
            terminal.redraw()
            # adding the expense
            if state == ExpState.NOTE:
                parsed_record = parse_expense(elements, tr_date, account)
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                account.add_transaction(parsed_record)
                account.query_transactions(account.full_query, False)
                terminal.windows[WinID.Main].refresh_table_records('all transactions')
                terminal.print_history[-1] = str(parsed_record)
                elements = ['', '', '', '', '', '']
                terminal.reset_input_field()
                state = sub_state = 0
                # state needs to be reset before the hint is displayed
                terminal.append_to_history(get_hint())
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
                continue
            # nothing written?
            elif elements[state] == '':
                continue
            error = check_input(elements[state], state, account.currency_type)
            # accept & rectify the element, prepare next element
            if error is None:
                # greek letter to enforce RTL/LTR consistency
                terminal.command += ' ǁ ' if cfg.application.enable_utf8_support else ' | '
                elements[state] = rectify_element(elements[state], state, account)
                # skip payee for income
                if state == ExpState.AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                # handle date & time input
                if state == ExpState.DATE or state == ExpState.TIME:
                    terminal.command += format_date(tr_date, cfg.application.use_jdate) \
                                        if state == ExpState.DATE else \
                                        format_time(tr_date)
                    # prefer day|minute over other fields
                    sub_state = 2 if state == ExpState.DATE else 1
                    # enable reverse text
                    terminal.rtext_start = element_start[state] + \
                                           sub_element_start[state][sub_state]
                    terminal.rtext_end = terminal.rtext_start + \
                                         sub_element_length[state][sub_state]
                    terminal.reverse_text_enable = True
                else:
                    terminal.reverse_text_enable = False
                    terminal.cursor_x = len(terminal.command)
                terminal.print_history[-1] = get_hint()
                update_predictions(False)
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.print_history[-1] = error
                terminal.append_to_history(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # history scrolling -----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            terminal.scroll_page_up()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll_page_down()
        # record scrolling ------------------------------------------------------------
        elif input_char == KeyCombo.CTRL_UP:
            terminal.windows[WinID.Main].clist.move_selection_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_DOWN:
            terminal.windows[WinID.Main].clist.move_selection_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_UP:
            terminal.windows[WinID.Main].clist.scroll_page_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_DOWN:
            terminal.windows[WinID.Main].clist.scroll_page_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date, cfg.application.use_jdate) \
                                   if state == ExpState.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date, cfg.application.use_jdate) \
                                   if state == ExpState.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            if input_allowed():
                terminal.cursor_move_left(element_start[state])
            else:
                sub_state = max(0, sub_state - 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            if input_allowed():
                terminal.cursor_move_right()
            else:
                sub_state = min(
                    len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.rtext_start = element_start[state] + \
                                       sub_element_start[state][sub_state]
                terminal.rtext_end = terminal.rtext_start + \
                                     sub_element_length[state][sub_state]
                terminal.redraw()
        elif input_char == KeyCombo.CTRL_LEFT:
            if input_allowed():
                terminal.cursor_jump_left(element_start[state])
        elif input_char == KeyCombo.CTRL_RIGHT:
            if input_allowed():
                terminal.cursor_jump_right()
        elif input_char == curses.KEY_HOME:
            if input_allowed():
                terminal.cursor_jump_start(element_start[state])
            else:
                sub_state = 0
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        elif input_char == curses.KEY_END:
            if input_allowed():
                terminal.cursor_jump_end()
            else:
                sub_state = 2 if state == ExpState.DATE else 1
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        # do predictions --------------------------------------------------------------
        elif input_char == '\t':
            if terminal.shadow_string != '':
                terminal.command = terminal.command[:element_start[state]] + \
                                   terminal.shadow_string
                terminal.cursor_x = len(terminal.command)
                terminal.vscroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        elif input_allowed():
            terminal.insert_char(input_char, False)
            update_predictions(True)
            terminal.redraw()

    account.flush_transactions()
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    return ['expense mode deactivated']