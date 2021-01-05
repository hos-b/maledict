from misc.utils import variadic_contains_or, check_input
from misc.utils import format_date, format_time
from misc.utils import change_datetime
from data.record import Record
from data.sqlite_proxy import SQLiteProxy

import curses
from sqlite3 import OperationalError as SQLiteOperationalError
from datetime import datetime

def account(database: SQLiteProxy, name: str, initial_balance: str) -> str:
    try:
        balance_f = float(initial_balance)
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
    if balance_f < 0:
        return ["initial account balance cannot be negative. are you really that poor?"]

    try:
        database.create_table(name)
    except SQLiteOperationalError:
        return [f"account {name} already exists"]
    except:
        return [f"could not create account {name}... go figure out why"]
    
    # adding the initial balance
    # the account object doesn't get created until we use set account, therefor
    # we cannot use the much more convenient call: account.add_transaction(...)
    intial_record = Record(datetime(1, 1, 1, 0, 0, 0, 0), balance_f, '', '', '', 'initial balance')
    database.add_record(name, intial_record)
    database.connection.commit()
    return [f"successfully added {name} with {balance_f} initial balance"]


def expense(terminal, stdscr):
    
    # exception handling
    if terminal.main_window.account == None:
        return ["current account not set"]
    if stdscr is None:
        return ["cannot add expenses in warmup mode"]

    terminal.exepnse_mode = True
    terminal.terminal_history.append("exepnse mode activated")
    terminal.command = ''
    terminal.cursor_x = 0
    terminal.redraw()
    tr_date = datetime.now()
    S_AMOUNT = 0; S_BUSINESS = 1; S_CATEGORY = 2
    S_DATE = 3; S_TIME = 4; S_NOTE = 5
    sub_element_start = {S_DATE: [0, 5, 8],
                         S_TIME: [0, 3]}
    element_hint =  ['amount', 'payee', 'category', 'date', 'time', 'note']
    element_start = [0, 0, 0, 0, 0, 0]
    element_end   = [0, 0, 0, 0, 0, 0]
    elements = ['', '', '', '', '', '']
    state = 0
    sub_state = 0
    # some functions ------------------------------------------------------------------
    def input_allowed():
        if state == S_AMOUNT or state == S_BUSINESS or \
           state == S_CATEGORY or state == S_NOTE:
            return True
        return False
    def get_hint() -> str:
        return '=' * (element_start[state] + 3) + f" {element_hint[state]}:"
    # start accepting input -----------------------------------------------------------
    terminal.terminal_history.append(f"{get_hint()}")
    terminal.redraw()
    while terminal.exepnse_mode:
        input_char = stdscr.getch()
        # backspace, del --------------------------------------------------------------
        if input_char == curses.KEY_BACKSPACE:
            if input_allowed():
                terminal.cursor_x = max(element_start[state], terminal.cursor_x - 1)
                if terminal.cursor_x == len(terminal.command) - 1:
                    terminal.command = terminal.command[:terminal.cursor_x]
                else:
                    terminal.command = terminal.command[:terminal.cursor_x] + \
                                    terminal.command[terminal.cursor_x + 1:]
                terminal.redraw()
        elif input_char == curses.KEY_DC:
            if input_allowed() and len(terminal.command) != 0 and \
               terminal.cursor_x < len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + \
                                terminal.command[terminal.cursor_x + 1:]
                terminal.redraw()
        # submit ----------------------------------------------------------------------
        elif input_char == curses.KEY_ENTER or input_char == ord('\n'):
            terminal.command = terminal.command.strip()
            element_end[state] = len(terminal.command) - 1
            elements[state] = terminal.command[element_start[state]: \
                                               element_end[state] + 1]
            if state == S_NOTE:
                terminal.terminal_history[-1] = f'added expense: ' + \
                                                 ', '.join(elements)
                elements = ['', '', '', '', '', '']
                terminal.terminal_history.append(f"{get_hint()}")
                terminal.command = ''
                terminal.cursor_x = 0
                state = sub_state = 0
                terminal.redraw()
                continue
            # nothing written?
            elif elements[state] == '':
                continue
            errors = check_input(elements[state], state)
            if len(errors) == 0:
                terminal.command += ' | '
                element_start[state + 1] = element_end[state] + 4
                state += 1
                if state == S_DATE or state == S_TIME:
                    terminal.command += format_date(tr_date) \
                                        if state == S_DATE else \
                                        format_time(tr_date)
                    sub_state = 0
                    terminal.cursor_x = element_start[state] + \
                                        sub_element_start[state][sub_state]
                else:
                    terminal.cursor_x = len(terminal.command)
                terminal.terminal_history[-1] = f"{get_hint()}"
            else:
                elements[state] = ''
                element_end[state] = 0
                terminal.terminal_history.pop(len(terminal.terminal_history) - 1)
                terminal.terminal_history += errors
                terminal.terminal_history.append(get_hint())
                terminal.command = terminal.command[:element_start[state]]
                terminal.cursor_x = len(terminal.command)
            terminal.redraw()
        # scrolling -------------------------------------------------------------------
        elif input_char == curses.KEY_PPAGE:
            max_scroll = len(terminal.terminal_history) + 3 - terminal.w_height
            # if we can show more than history + 3 reserved lines:
            if max_scroll > 0:
                terminal.scroll = min(terminal.scroll + 1, max_scroll)
            terminal.redraw()
        elif input_char == curses.KEY_NPAGE:
            terminal.scroll = max(terminal.scroll - 1, 0)
            terminal.redraw()
        # suggestion surfing, changing date & time ------------------------------------
        elif input_char == curses.KEY_UP:
            if input_allowed():
                pass
            else:
                tr_date = change_datetime(tr_date, state, sub_state, +1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == S_DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        elif input_char == curses.KEY_DOWN:
            if input_allowed():
                pass
            else:
                tr_date = change_datetime(tr_date, state, sub_state, -1)
                terminal.command = terminal.command[:element_start[state]] + \
                                   format_date(tr_date) if state == S_DATE \
                                   else terminal.command[:element_start[state]] + \
                                   format_time(tr_date)
                terminal.redraw()
        # cursor shift ----------------------------------------------------------------
        elif input_char == curses.KEY_LEFT:
            if input_allowed():
                terminal.cursor_x = max(element_start, terminal.cursor_x - 1)
                terminal.redraw()
            else:
                sub_state = max(0, sub_state - 1)
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_RIGHT:
            if input_allowed():
                terminal.cursor_x = min(len(terminal.command), terminal.cursor_x + 1)
                terminal.redraw()
            else:
                sub_state = min(len(sub_element_start[state]) - 1, sub_state + 1)
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
                terminal.redraw()
        elif input_char == curses.KEY_HOME:
            if input_allowed():
                terminal.cursor_x = element_start[state]
                terminal.redraw()
            else:
                sub_state = 0
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        elif input_char == curses.KEY_END:
            if input_allowed():
                terminal.cursor_x = len(terminal.command)
                terminal.redraw()
            else:
                sub_state = 2 if state == S_DATE else 1
                terminal.cursor_x = element_start[state] + \
                                    sub_element_start[state][sub_state]
        # normal input ----------------------------------------------------------------
        elif input_char <= 256:
            if not input_allowed():
                continue
            if input_char == ord(' '):
                # leading spaces don't count
                if len(terminal.command) == 0:
                    continue
            if terminal.cursor_x == len(terminal.command):
                terminal.command = terminal.command[:terminal.cursor_x] + chr(input_char)
            else:
                terminal.command = terminal.command[:terminal.cursor_x] + chr(input_char) + \
                                terminal.command[terminal.cursor_x:]
        

            terminal.cursor_x += 1
            terminal.cmd_history_index = 0
            terminal.scroll = 0
            terminal.redraw()