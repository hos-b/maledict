import curses
import logging as l

from enum import IntEnum
from datetime import datetime
from sqlite3 import OperationalError as SQLiteOperationalError
from sqlite3 import Error as SQLiteError

from misc.utils import variadic_contains_or, check_input
from misc.utils import predict_business, predict_category
from misc.string_manip import format_date, format_time
from misc.utils import change_datetime, rectify_element, parse_expense
from data.record import Record
from data.currency import Euro
from data.sqlite_proxy import SQLiteProxy
from misc.statics import WinID, KeyCombo

def account(database: SQLiteProxy, name: str, initial_balance: str, currency_type = Euro) -> str:
    
    try:
        initial_balance = currency_type.from_str(initial_balance)
    except:
        return [f"{initial_balance} is not a float value"]
    # should stop basic sql injections
    if ';' in name:
        return ["sneaky but no"]
    # this shouldn't be possible anyway but meh
    if ' ' in name:
        return ["account name cannot contain spaces"]
    # other stuff
    forbidden, frch = variadic_contains_or(name, '/', '\\','\'', '\"', '!', '?',\
                                                 '+', '=', '%', '*', '&', '^',\
                                                 '@', '#', '$', '~', '.', '`',\
                                                 '[', ']', '(', ')', '[', ']')
    if forbidden:
        return [f"account name cannot contain {frch}"]
    if initial_balance < 0:
        return [
            "initial account balance cannot be negative. are you really that poor?"
        ]

    try:
        database.create_table(name)
    except SQLiteOperationalError:
        return [f"account {name} already exists"]
    except SQLiteError as e:
        return [f"[sqlite error] {e}"]

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

    return [f"successfully added {name} with {initial_balance} initial balance"]

class State(IntEnum):
    AMOUNT = 0
    BUSINESS = 1
    CATEGORY = 2
    DATE = 3
    TIME = 4
    NOTE = 5

def expense(terminal, stdscr):
    # exception handling
    if terminal.windows[WinID.Main].account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot add expenses in warmup mode"]

    expense_mode = True
    terminal.print_history.append("expense mode activated")
    terminal.command = ''
    terminal.cursor_x = 0
    curses.curs_set(1)
    tr_date = datetime.now()
    tr_date = tr_date.replace(second=0, microsecond=0)
    sub_element_start = {State.DATE: [0, 5, 8], State.TIME: [0, 3]}
    sub_element_length = {State.DATE: [4, 2, 2], State.TIME: [2, 2]}
    element_hint = ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = 0
    sub_state = 0
    # predictions
    predicted_record = None
    l.basicConfig(filename='/tmp/maledict.log', encoding='utf-8', level=l.DEBUG)

    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == State.AMOUNT or state == State.BUSINESS or \
           state == State.CATEGORY or state == State.NOTE:
            return True
        return False

    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f" {element_hint[state]}:"

    def update_predictions(force_update: bool, predicted_record: Record):
        # global predicted_record
        if state == State.BUSINESS:
            terminal.shadow_string, predicted_record = predict_business(elements[0], \
                terminal.command[element_start[1]:], terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[1]
            l.debug(f'Bshadow: {terminal.shadow_string} @ {terminal.shadow_index}')
        elif state == State.CATEGORY:
            if not force_update and predicted_record is not None:
                terminal.shadow_string = predicted_record.subcategory
                terminal.shadow_index = element_start[2]
                return
            terminal.shadow_string, predicted_record = predict_category(elements[1], \
                terminal.command[element_start[2]:], terminal.windows[WinID.Main].account)
            terminal.shadow_index = element_start[2]
            l.debug(f'Cshadow: {terminal.shadow_string} @ {terminal.shadow_index}')
        else:
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            l.debug(f'shadow cleared')

    # start accepting input -----------------------------------------------------------
    terminal.print_history.append(f"{get_hint()}")
    terminal.redraw()
    kb_interrupt = False
    while expense_mode:
        try:
            input_char = stdscr.get_wch()
            kb_interrupt = False
        except KeyboardInterrupt:
            if kb_interrupt or terminal.command == '':
                break
            kb_interrupt = True
            elements = ['', '', '', '', '', '']
            terminal.command = ''
            terminal.cursor_x = 0
            state = sub_state = 0
            terminal.shadow_string = ''
            terminal.shadow_index = 0
            terminal.print_history[
                -1] = 'press ctrl + c again to exit expense mode'
            terminal.print_history.append(f'{get_hint()}')
            terminal.redraw()
            continue
        except:
            continue
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE or input_char == '\x7f':
            if input_allowed():
                terminal.cursor_x = max(element_start[state],
                                        terminal.cursor_x - 1)
                if terminal.cursor_x == len(terminal.command) - 1:
                    terminal.command = terminal.command[:terminal.cursor_x]
                    update_predictions(True, predicted_record)
                else:
                    terminal.command = terminal.command[:terminal.cursor_x] + \
                                    terminal.command[terminal.cursor_x + 1:]
                    update_predictions(True, predicted_record)
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed() and len(terminal.command) != 0 and \
               terminal.cursor_x < len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                update_predictions(True, predicted_record)
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == '\n':
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[element_start[state]: \
                                               element_end[state] + 1].strip()
            terminal.redraw()
            # adding the expense
            if state == State.NOTE:
                parsed_record = parse_expense(elements, tr_date, \
                                              terminal.windows[WinID.Main].account)
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.windows[WinID.Main].account.add_transaction(
                    parsed_record)
                terminal.windows[WinID.Main].account.query_transactions(
                    terminal.windows[WinID.Main].account.full_query, False)
                terminal.windows[WinID.Main].refresh_table_records(
                    'all transactions')
                terminal.print_history[-1] = str(elements)
                elements = ['', '', '', '', '', '']
                terminal.command = ''
                terminal.cursor_x = 0
                state = sub_state = 0
                terminal.print_history.append(f"{get_hint()}")
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
                continue
            # nothing written?
            elif elements[state] == '':
                continue
            errors = check_input(elements[state], state)
            # accept & rectify the element, prepare next element
            if len(errors) == 0:
                terminal.command += ' | '
                elements[state] = rectify_element(
                    elements[state], state,
                    terminal.windows[WinID.Main].account)
                # skip payee for income
                if state == State.AMOUNT and elements[state][0] == '+':
                    element_start[state + 2] = element_end[state] + 4
                    state += 2
                else:
                    element_start[state + 1] = element_end[state] + 4
                    state += 1
                # handle date & time input
                if state == State.DATE or state == State.TIME:
                    terminal.command += format_date(tr_date) \
                                        if state == State.DATE else \
                                        format_time(tr_date)
                    # prefer day|minute over other fields
                    sub_state = 2 if state == State.DATE else 1
                    # enable reverse text
                    terminal.rtext_start = element_start[state] + \
                                           sub_element_start[state][sub_state]
                    terminal.rtext_end = terminal.rtext_start + \
                                         sub_element_length[state][sub_state]
                    terminal.reverse_text_enable = True
                else:
                    terminal.reverse_text_enable = False
                    terminal.cursor_x = len(terminal.command)
                terminal.print_history[-1] = f"{get_hint()}"
                update_predictions(False, predicted_record)
            # reject & reset input
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.print_history[-1] = errors
                terminal.print_history.append(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # history scrolling -----------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            terminal.scroll_page_up()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll_page_down()
        # record scrolling ------------------------------------------------------------
        elif input_char == KeyCombo.CTRL_PG_UP:
            terminal.windows[WinID.Main].clist.key_pgup()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_PG_DOWN:
            terminal.windows[WinID.Main].clist.key_pgdn()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_UP:
            terminal.windows[WinID.Main].clist.key_up()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        elif input_char == KeyCombo.CTRL_DOWN:
            terminal.windows[WinID.Main].clist.key_down()
            terminal.windows[WinID.Main].redraw()
            terminal.redraw()
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            # TODO add suggestion surfing
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == State.DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                continue
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == State.DATE \
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
        elif input_char == KeyCombo.CTRL_LEFT and input_allowed():
            terminal.cursor_jump_left(element_start[state])
        elif input_char == KeyCombo.CTRL_RIGHT and input_allowed():
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
                sub_state = 2 if state == State.DATE else 1
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        # do predictions --------------------------------------------------------------
        elif input_char == '\t':
            if terminal.shadow_string != '':
                terminal.command = terminal.command[:element_start[state]] + \
                                   terminal.shadow_string
                terminal.cursor_x = len(terminal.command)
                terminal.scroll = 0
                terminal.shadow_string = ''
                terminal.shadow_index = 0
                terminal.redraw()
        # normal input ----------------------------------------------------------------
        else:
            terminal.insert_char(input_char, False)
            update_predictions(True, predicted_record)
            terminal.redraw()

    terminal.windows[WinID.Main].account.flush_transactions()
    terminal.shadow_string = ''
    terminal.shadow_index = 0
    return ["expense mode deactivated"]